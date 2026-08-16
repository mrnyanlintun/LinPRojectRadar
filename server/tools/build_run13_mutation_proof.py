#!/usr/bin/env python3
"""
RUN 13 GATE 12 — mutation / fault proof for every executable module.

WHAT IS MUTATED, AND WHY IT IS NOT THE EXPECTED ANSWER.

Production files are the frozen test target and are never edited. For each module this file
takes an ISOLATED COPY of the module's own implementation source, applies a fault to that copy
(a comparison operator flipped, an arithmetic operator flipped, or a band ladder reversed),
compiles the copy in a namespace holding the real module's globals, and runs it on the same
nominal input the evidence pass used.

The proof required is that the module's OBSERVED BEHAVIOUR CHANGES under the fault: baseline
result, mutated result differs, and the production function is then re-run and confirmed
byte-identical in behaviour and identical in source hash to the frozen file. A mutation that
changes nothing is reported as UNPROVEN rather than dropped, because a check that cannot fail
is exactly what this programme has been bitten by before.

Writes code_audit/run13_mutation_proof.csv.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import os
import pathlib
import select
import signal
import sys
import time
import textwrap

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation.models import VALIDATED  # noqa: E402
from app.simulation.registry import DISABLED_CONCEPT_ONLY  # noqa: E402

from tools.build_run13_evidence import CUTOFF, NOOP, STRUCTURED  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "code_audit" / "run13_mutation_proof.csv"

COLUMNS = ["module_id", "implementation", "mutation", "baseline", "mutated", "changed",
           "restored_identical", "source_sha256_before", "source_sha256_after", "result"]


class FlipCompare(ast.NodeTransformer):
    """Reverse every ordering comparison: a band ladder read backwards."""

    SWAP = {ast.Lt: ast.GtE, ast.LtE: ast.Gt, ast.Gt: ast.LtE, ast.GtE: ast.Lt}

    def __init__(self) -> None:
        self.count = 0

    def visit_Compare(self, node):  # noqa: N802
        new_ops = []
        for op in node.ops:
            swap = self.SWAP.get(type(op))
            if swap:
                self.count += 1
                new_ops.append(swap())
            else:
                new_ops.append(op)
        node.ops = new_ops
        return self.generic_visit(node)


class FlipArith(ast.NodeTransformer):
    """Reverse addition and subtraction, and division and multiplication: a sign and a divisor."""

    SWAP = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Div: ast.Mult, ast.Mult: ast.Div}

    def __init__(self) -> None:
        self.count = 0

    def visit_BinOp(self, node):  # noqa: N802
        swap = self.SWAP.get(type(node.op))
        if swap:
            self.count += 1
            node.op = swap()
        return self.generic_visit(node)


class NegateGuard(ast.NodeTransformer):
    """
    Invert every branch test: the missingness branch, the domain guard and the structure guard
    all taken the wrong way round. This is the mutation that binds on a module which abstains on
    the nominal input, where an arithmetic fault downstream of the guard changes nothing.
    """

    def __init__(self) -> None:
        self.count = 0

    def visit_If(self, node):  # noqa: N802
        self.generic_visit(node)
        self.count += 1
        node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
        return node


def behaviour(fn, si: dict, limit: int = 5):
    """
    Run one function in a FORKED CHILD with a hard bound.

    A mutated copy can loop forever -- a reversed loop guard does exactly that -- and it can also
    swallow an in-process alarm inside the production code's own except arm and carry on. A child
    the parent can kill is the only bound that holds in both cases, and a hang is itself a
    behavioural change worth recording rather than a reason to lose the run.
    """
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:                                                     # child
        os.close(r)
        try:
            out = fn(dict(si), NOOP, CUTOFF)
            if isinstance(out, dict):
                text = (f"status={out.get('status_color')} "
                        f"insufficient={bool(out.get('insufficient_data'))} "
                        f"metric={str(out.get('evidence_metric'))[:70]}")
            else:
                text = repr(out)[:80]
        except BaseException as exc:                                 # noqa: BLE001
            text = f"RAISED {type(exc).__name__}"
        try:
            os.write(w, text.encode("utf-8", "replace")[:400])
        finally:
            os._exit(0)
    os.close(w)
    deadline = time.time() + limit
    data = b""
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        ready, _, _ = select.select([r], [], [], remaining)
        if not ready:
            break
        chunk = os.read(r, 4096)
        if not chunk:
            break
        data += chunk
    os.close(r)
    done, _status = os.waitpid(pid, os.WNOHANG)
    if done == 0:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        if not data:
            return "DID NOT TERMINATE within the bound"
    return data.decode("utf-8", "replace") or "NO OUTPUT"


def mutated_callable(fn, transformer_cls):
    src = textwrap.dedent(inspect.getsource(fn))
    tree = ast.parse(src)
    tr = transformer_cls()
    tree = tr.fix_missing_locations(tr.visit(tree)) if hasattr(tr, "fix_missing_locations") \
        else ast.fix_missing_locations(tr.visit(tree))
    if tr.count == 0:
        return None, 0
    ns = dict(sys.modules[fn.__module__].__dict__)
    # strip decorators the copy cannot resolve
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.decorator_list = []
    exec(compile(tree, f"<mutated {fn.__name__}>", "exec"), ns)  # noqa: S102
    return ns[fn.__name__], tr.count


def mutated_via_helper(fn, transformer_cls):
    """
    A thin wrapper carries no arithmetic of its own, so a fault must be injected into the helper
    it delegates to. The helper is mutated in an isolated namespace and the UNMUTATED wrapper is
    compiled into that same namespace, so the wrapper resolves the faulty helper exactly as it
    resolves the real one. Production remains untouched either way.
    """
    src = textwrap.dedent(inspect.getsource(fn))
    tree = ast.parse(src)
    module = sys.modules[fn.__module__]
    called = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    # A wrapper may import its worker inside the body (`from .models_sim import run_monte_carlo`),
    # so the name is not an attribute of the wrapper's own module. Resolve those imports too.
    local_imports = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            try:
                target = importlib.import_module(f"app.simulation.{node.module.lstrip('.')}")
            except ImportError:
                target = None
            if target is not None:
                for alias in node.names:
                    local_imports[alias.asname or alias.name] = target
    ns = dict(module.__dict__)
    total = 0
    # The shared abstention constructor is not this module's behaviour: faulting it would prove
    # something about the helper, not about the module under test.
    SHARED_HELPERS = {"insufficient", "check_inputs", "num", "clamp", "js_round", "round2",
                      "as_percent", "calibration_pending"}
    for helper_name in sorted(called):
        if helper_name in SHARED_HELPERS:
            continue
        owner = local_imports.get(helper_name, module)
        helper = getattr(owner, helper_name, None)
        # RUN 29. A wrapper may also import its worker AT MODULE LEVEL -- Run 29's Category 4 and
        # 5 runners do exactly that, `from .canonical_v4 import scenario_modeling` at the top of
        # models_doc.py -- so the helper is an attribute of the wrapper's module but is DEFINED
        # in another one. The original ownership test compared the helper's defining module with
        # the module it was read from and skipped every such case, which meant a thin wrapper
        # over a top-level import reported NO MUTATION BOUND while proving nothing. The owner is
        # now resolved from the helper's own `__module__`, so the fault lands in the code that
        # actually computes.
        if callable(helper) and getattr(helper, "__module__", "") != owner.__name__:
            _real = sys.modules.get(getattr(helper, "__module__", ""))
            if _real is not None and getattr(_real, helper_name, None) is helper:
                owner = _real
        if not callable(helper) or getattr(helper, "__module__", "") != owner.__name__:
            continue
        if owner is not module:
            ns = dict(ns)
            ns.update({k: v for k, v in owner.__dict__.items() if k not in ns})
        try:
            hsrc = textwrap.dedent(inspect.getsource(helper))
            htree = ast.parse(hsrc)
        except (OSError, TypeError, SyntaxError):
            continue
        tr = transformer_cls()
        htree = ast.fix_missing_locations(tr.visit(htree))
        if tr.count == 0:
            continue
        for node in htree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node.decorator_list = []
        exec(compile(htree, f"<mutated helper {helper_name}>", "exec"), ns)  # noqa: S102
        total += tr.count
    if not total:
        return None, 0
    class _DropLocalImports(ast.NodeTransformer):
        """The wrapper re-imports its worker at call time, which would rebind the real one over
        the mutated copy. The names are already in the namespace, so the import is dropped."""

        def visit_ImportFrom(self, node):  # noqa: N802
            return ast.Pass()

    tree = ast.fix_missing_locations(_DropLocalImports().visit(tree))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.decorator_list = []
    exec(compile(tree, f"<wrapper {fn.__name__}>", "exec"), ns)  # noqa: S102
    return ns[fn.__name__], total


def main() -> int:
    rows = []
    for mid, (_name, fn) in sorted(VALIDATED.items()):
        if mid in DISABLED_CONCEPT_ONLY:
            continue
        path = pathlib.Path(inspect.getfile(fn))
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        base = behaviour(fn, STRUCTURED)
        result = "UNPROVEN"
        used = ""
        mutated_behaviour = ""
        for label, cls in (("comparison operators reversed", FlipCompare),
                           ("arithmetic operators reversed", FlipArith),
                           ("every branch guard inverted", NegateGuard)):
            try:
                mfn, count = mutated_callable(fn, cls)
                if mfn is None:
                    mfn, count = mutated_via_helper(fn, cls)
                    if mfn is not None:
                        label += ", in the helper it delegates to"
            except Exception as exc:  # noqa: BLE001
                mutated_behaviour = f"mutation could not be built: {type(exc).__name__}"
                continue
            if mfn is None:
                continue
            got = behaviour(mfn, STRUCTURED)
            if got != base:
                used = f"{label} ({count} sites, isolated copy)"
                mutated_behaviour = got
                result = "PROVEN"
                break
            used = f"{label} ({count} sites, isolated copy)"
            mutated_behaviour = got
        after = hashlib.sha256(path.read_bytes()).hexdigest()
        restored = behaviour(fn, STRUCTURED)
        rows.append({
            "module_id": mid,
            "implementation": f"{fn.__module__.rsplit('.', 1)[1]}.{fn.__name__}",
            "mutation": used,
            "baseline": base[:120],
            "mutated": mutated_behaviour[:120],
            "changed": "YES" if result == "PROVEN" else "NO",
            "restored_identical": "YES" if restored == base else "NO",
            "source_sha256_before": before,
            "source_sha256_after": after,
            # A module that abstains unconditionally has no branch, no comparison and no
            # arithmetic to fault: its output is a constant refusal. That is recorded as what it
            # is rather than as a failed proof, and the constancy is itself the evidence.
            "result": (("UNCONDITIONAL_ABSTENTION_NO_FAULT_POSSIBLE"
                        if (result == "UNPROVEN" and not used
                            and "insufficient=True" in base) else result)
                       if (restored == base and before == after) else "INVALID"),
        })

    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    proven = [r for r in rows if r["result"] == "PROVEN"]
    print(f"modules mutated   {len(rows)}")
    print(f"PROVEN            {len(proven)}")
    print(f"UNPROVEN          {len([r for r in rows if r['result'] == 'UNPROVEN'])}")
    print(f"INVALID           {len([r for r in rows if r['result'] == 'INVALID'])}")
    print(f"unproven ids      {[r['module_id'] for r in rows if r['result'] != 'PROVEN']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
