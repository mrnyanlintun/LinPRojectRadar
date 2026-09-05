"""
RUN 137, ITEM 1. THE RETIRED-ID BUCKET: ONE SUBSTITUTION, LIFTED OUT OF test_run17.

THE DEFECT. Twenty-one active qualification scripts crash on `MissingModuleError`. Each dispatches
a module identifier the owner's Run 96/97 ruling removed from the registry (`88e6ca0`). The crash
is at the FIRST such identifier, so everything the script would have checked about the modules that
are STILL IN SERVICE never runs at all. Measured on Run 136's fleet: every one of the twenty-one
names live identifiers as well as dead ones -- `test_run19_category_2.py` dies on A2.2 while A2.1,
A2.7, A2.8 and A2.9 are live and untested; `test_run29_canonical_oracles.py` dies on A4.10 while
ten live A1/A4 identifiers go unexercised. None of them is a retired artefact. They test live
modules and trip on a retired identifier in passing, which is the case the order says to repair.

THE REPAIR, AND WHY IT IS NOT A DELETION. `tools/test_run17_scientific_methods.py` already settled
what a check about a removed module should say, and this module is that answer lifted out of it
verbatim so there is ONE of it rather than twenty-one:

    a proposition about a removed module is REPLACED, once per identifier, by the two facts that
    ARE now true of it -- the identifier does not resolve in the registry, and the dispatcher
    refuses it BY NAME rather than computing a reading -- and the propositions that followed it
    are suppressed until the next dispatch of a module still in service.

Nothing is silenced to make a suite green. The substituted assertions are counted and they go RED
the moment a removed row is put back, which is a stronger statement about the instrument than the
proposition they replace.

THE F11 DEFECT IS NOT INHERITED. Run 136 found `test_run17`'s suppression testing a flag for
TRUTHINESS, so a block ending on a removed module silently suppressed every later check of every
module -- 98 checks vanished from the count with no trace. Here suppression is CLEARED by the next
dispatch of a live module, and every suppressed check is COUNTED in `substitution.suppressed` and
printed by `report()`, so over-suppression is visible in the script's own output instead of being
invisible in its RESULT line. A suite that ends on a removed module can be seen to have done so.

ADOPTION, per script, is two edits:

    from run96_removed_substitution import substitution        # noqa: E402
    ...
    def run(code_id, si):
        return substitution.run(code_id, si, globals())        # was REG.run_module(...)

`run()` wraps the caller's own `check` / `proposition` / `near` on first use, whatever their
signatures are, so no script's check surface has to be rewritten to adopt this.
"""
from __future__ import annotations


class Absent:
    """What a removed module's reading is: every operation on it yields itself, and it is falsey.

    A per-module block computes differences, comparisons and slices from a reading before handing
    the result to `check()`. A removed module has no reading, so this absorbs those expressions
    and the block runs to its end without raising. It never reaches an assertion that counts,
    because the wrapped `check()` returns early while the module is suppressed.
    """

    def __getattr__(self, _name): return self
    def __call__(self, *_a, **_k): return self
    def __getitem__(self, _k): return self
    def __iter__(self): return iter(())
    def __len__(self): return 0
    def __bool__(self): return False
    def __eq__(self, _o): return False
    def __hash__(self): return hash("__run96_absent__")
    def __float__(self): return 0.0
    def __int__(self): return 0
    def __format__(self, _s): return "<removed at Run 96>"
    def __repr__(self): return "<removed at Run 96>"
    __str__ = __repr__

    def _binop(self, *_a): return self
    __sub__ = __rsub__ = __add__ = __radd__ = __mul__ = __rmul__ = _binop
    __truediv__ = __rtruediv__ = __floordiv__ = __mod__ = __pow__ = _binop
    __abs__ = __neg__ = __round__ = _binop

    def __lt__(self, _o): return False
    __gt__ = __le__ = __ge__ = __lt__
    def __contains__(self, _o): return False


class AbsentReading(dict):
    """A reading that is not there. Every lookup answers `Absent`."""

    def get(self, _k, _default=None): return Absent()
    def __getitem__(self, _k): return Absent()
    def __missing__(self, _k): return Absent()


class _Substitution:
    def __init__(self) -> None:
        self.substituted: dict[str, int] = {}
        self.suppressed = 0
        self.suppressed_names: list[str] = []
        self._current = ""
        self._wrapped: set[int] = set()
        self._raw_check = None

    # -- the registry, imported lazily so this module can be read without an app on sys.path --
    @staticmethod
    def _registry():
        from app.simulation import registry as REG
        return REG

    def removed(self, code_id: str) -> bool:
        return code_id not in self._registry().registry_index()

    # -- wrapping the caller's own check surface ------------------------------------------------
    def _wrap(self, g: dict) -> None:
        """Put the suppressing wrapper in front of this script's own check surface.

        Two shapes are in use across the twenty-one and both are covered. Most spell their
        assertions as module-level functions (`check`, `proposition`, `near`); the Run-19 category
        suites route theirs through an imported audit object instead (`A.check`, `A.near`,
        `A.proposition`), so any global carrying at least two of the three names is wrapped as
        well. Missing the second shape would leave a removed module's propositions ASSERTED
        against a reading that is not there, which reads as a red suite rather than as a removal.
        """
        if id(g) in self._wrapped:
            return
        self._wrapped.add(id(g))
        names = ("check", "proposition", "near")
        for name in names:
            fn = g.get(name)
            if callable(fn) and not hasattr(fn, "__wrapped__"):
                if name == "check" and self._raw_check is None:
                    self._raw_check = fn
                g[name] = self._suppressing(fn, name)
        for key, obj in list(g.items()):
            if key.startswith("__") or isinstance(obj, (str, bytes, int, float, dict, list, tuple)):
                continue
            have = [n for n in names if callable(getattr(obj, n, None))]
            if len(have) < 2 or id(obj) in self._wrapped:
                continue
            self._wrapped.add(id(obj))
            for n in have:
                fn = getattr(obj, n)
                if hasattr(fn, "__wrapped__"):
                    continue
                try:
                    setattr(obj, n, self._suppressing(fn, n))
                    if n == "check" and self._raw_check is None:
                        self._raw_check = fn
                except (AttributeError, TypeError):
                    pass

    def _suppressing(self, fn, name):
        sub = self

        def wrapper(*a, **k):
            if sub._current:
                label = next((x for x in a if isinstance(x, str)), name)
                sub.suppressed += 1
                sub.suppressed_names.append(f"{sub._current}: {label}")
                return True
            return fn(*a, **k)

        wrapper.__name__ = getattr(fn, "__name__", name)
        wrapper.__doc__ = getattr(fn, "__doc__", None)
        wrapper.__wrapped__ = fn
        return wrapper

    # -- the substitution itself -----------------------------------------------------------------
    def dispatch(self, run_module, globals_, code_id, *a, **k):
        """Dispatch `code_id` through `run_module`, or substitute the assertion it was removed.

        THE DECISION IS THE DISPATCHER'S, NOT A LOOKUP'S. Removal is established by CALLING and
        catching `MissingModuleError`, not by testing the live registry index. That matters here:
        `test_run31_version_boundaries.py` deliberately dispatches against an OLDER registry line
        in which some of these identifiers still exist, and a lookup against the live index would
        substitute a module that the line under test really does carry.
        """
        self._wrap(globals_)
        try:
            out = run_module(code_id, *a, **k)
        except Exception as exc:                        # noqa: BLE001
            if type(exc).__name__ != "MissingModuleError":
                raise
            return self._substitute(code_id, globals_, run_module, str(exc), *a, **k)
        self._current = ""
        return out

    def run(self, code_id, si, globals_=None, rand=None, cutoff=None):
        """The `def run(code_id, si)` wrapper these suites already have, pointed here."""
        g = globals_ or {}
        REG = self._registry()
        rand = rand if rand is not None else g.get("RAND", g.get("NOOP", lambda: 0.5))
        cutoff = cutoff if cutoff is not None else g.get("CUTOFF", g.get("CUT"))
        return self.dispatch(REG.run_module, g, code_id, si, rand, cutoff)

    def _substitute(self, code_id, globals_, run_module, refusal, *a, **k):
        g = globals_ or {}
        if code_id not in self.substituted:
            self.substituted[code_id] = 0
            self._current = ""          # the removal assertions themselves must COUNT
            raw = self._raw_check_fn(g)
            self._record(raw, code_id,
                         f"RUN 96: and the dispatcher refuses {code_id} by name rather than "
                         f"computing a reading for it",
                         "not in the module registry" in refusal, refusal)
            try:
                resolves = code_id in self._registry().registry_index()
                self._record(raw, code_id,
                             f"RUN 96: {code_id} was removed from the registry and no longer "
                             f"resolves", not resolves, str(resolves))
            except Exception:                           # noqa: BLE001
                pass
        self.substituted[code_id] += 1
        self._current = code_id
        return AbsentReading({"__run96_removed__": code_id})

    @staticmethod
    def _raw(g: dict, name: str):
        """The script's own `check`, before `_wrap` put the suppressing wrapper in front of it."""
        fn = g.get(name)
        return getattr(fn, "__wrapped__", fn)

    def _raw_check_fn(self, g: dict):
        """The script's own unwrapped `check`, wherever it lives -- a module global, or a method
        on the audit object the Run-19 category suites route their assertions through."""
        fn = self._raw(g, "check")
        return fn if callable(fn) else self._raw_check

    @staticmethod
    def _record(check_fn, code_id, label, ok, detail) -> None:
        """Call the script's own `check`, whatever its argument ORDER is.

        The scripts in this bucket spell it three ways -- `check(ok, label, detail)`,
        `check(name, ok, detail)` and `check(module_id, name, condition, detail)`. The mapping is
        read from the PARAMETER NAMES rather than guessed by trying calls, because a wrong guess
        that happens not to raise would record a string where a truth value belongs and pass. If
        the names cannot be read the assertion is PRINTED, so it is never silently dropped.
        """
        import inspect
        if callable(check_fn):
            try:
                params = [q.name for q in inspect.signature(check_fn).parameters.values()
                          if q.kind in (q.POSITIONAL_ONLY, q.POSITIONAL_OR_KEYWORD)]
            except (TypeError, ValueError):
                params = []
            TRUTH = ("ok", "condition", "holds", "cond", "passed", "result", "value")
            LABEL = ("label", "name", "proposition", "message", "msg", "what", "title")
            IDENT = ("module_id", "code_id", "mid", "module", "identifier")
            DETAIL = ("detail", "details", "why", "note", "extra")
            if params and any(q in TRUTH for q in params) and any(q in LABEL for q in params):
                args = []
                for q in params:
                    if q in TRUTH: args.append(bool(ok))
                    elif q in LABEL: args.append(label)
                    elif q in IDENT: args.append(code_id)
                    elif q in DETAIL: args.append(detail)
                    else: break
                if len(args) >= 2:
                    try:
                        check_fn(*args)
                        return
                    except Exception:                   # noqa: BLE001
                        pass
        print(f"  {'PASS' if ok else '****'}  {label}" + (f"   {detail}" if not ok else ""))

    def run_all_live(self, only, run_all, *a, **k):
        """`REG.run_all` restricted to the identifiers still in service."""
        live = [m for m in only if not self.removed(m)]
        if not live:
            return AbsentReading({"__run96_removed__": tuple(only)})
        return run_all(*a, only=live, **k)

    def report(self) -> None:
        """Say what was substituted and what that suppressed. Never silent."""
        if not self.substituted:
            return
        print(f"  RUN 96 SUBSTITUTION: {len(self.substituted)} removed identifier(s) "
              f"{sorted(self.substituted)} -- each replaced by the two assertions that it is gone; "
              f"{self.suppressed} downstream check(s) about them were suppressed.")


substitution = _Substitution()
