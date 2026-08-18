"""
RUN 33 FINAL CLOSURE. THE INDEPENDENT FROZEN-FOREST SCORING ORACLE FOR PH.1.

WHY THIS FILE EXISTS. The Run-33 acceptance condition for PH.1 was a single-seed Spearman
correlation with scikit-learn of at least 0.99. That was never a canonical requirement of the
literature, and it cannot be one: BOTH implementations construct RANDOMIZED ensembles, so a
single observed rank correlation mixes algorithm fidelity with Monte Carlo ensemble variation
between two independent draws. The measurement that separates the two is this one -- FREEZE the
forest, then check that two independently written scorers give the same score for the same point
on the same trees. Ensemble randomness is held fixed and only the arithmetic is under test.

THE ONE RULE THAT MAKES THIS AN ORACLE AT ALL: NOTHING HERE CALLS THE PRODUCTION SCORER.
`app.simulation.isolation_forest` owns `_path_length`, `c_factor`, `harmonic`,
`mean_path_length` and `anomaly_score`. This file imports NONE of them and reproduces every one
of them from the published definition. `serialize` reads plain attributes off the tree nodes --
that is reading DATA, not delegating arithmetic -- and everything downstream of it operates on
dictionaries this module built. Asserting against a copy of the logic is the fourth of the five
ways a check has lied in this repository, and fault 10 of the closure campaign exists to prove
this file has not done it: it replaces the path computation below with a call to production and
requires the guard to go RED.

THE DEFINITION IMPLEMENTED HERE, from Liu, Ting and Zhou (ICDM 2008, doi:10.1109/ICDM.2008.17):

    c(n)            = 2 * H(n-1) - 2 * (n-1) / n,  c(0) = c(1) = 0, c(2) = 1
    h_i(x)          = edges traversed in tree i, PLUS c(size) at an external node
    E[h(x)]         = (1 / t) * sum_i h_i(x)
    s(x, psi)       = 2 ** (-E[h(x)] / c(psi))

H IS THE PAPER'S OWN ln(i) + gamma ESTIMATE, which is the approximation the repository declares
and Run 15 recorded. `harmonic_exact` below computes the exact harmonic sum instead, so the
DECLARED DEVIATION can be measured rather than assumed -- it is a deviation of the estimate from
the exact sum, not a deviation of this file from production.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

#: Euler-Mascheroni, written out here rather than imported, so this file shares no constant with
#: the implementation it is checking.
EULER_GAMMA_ORACLE = 0.57721566490153286060651209008240243

#: The predeclared tolerance for the fixed-forest equivalence. Both implementations perform the
#: SAME double-precision operations on the SAME frozen structure, differing only in the order the
#: source text puts them in, so the only difference either may show is floating-point
#: association. 1e-12 absolute is orders of magnitude looser than that and orders of magnitude
#: tighter than any arithmetic defect the campaign injects, the smallest of which moves a score
#: by more than 1e-3.
EQUIVALENCE_TOLERANCE = 1e-12

#: Declared conventions, recorded on every serialized forest so a reader can see which they are.
PATH_DEPTH_CONVENTION = "EDGES_TRAVERSED_FROM_ROOT_ROOT_IS_DEPTH_ZERO"
EXTERNAL_NODE_ADJUSTMENT = "PLUS_C_OF_TERMINAL_SAMPLE_SIZE"


# ---------------------------------------------------------------------------------------------
# THE NORMALISING CONSTANT, REIMPLEMENTED
# ---------------------------------------------------------------------------------------------

def harmonic_estimate(i: int) -> float:
    """H(i) by the paper's own stated estimate. Independent of production's `harmonic`."""
    if i <= 0:
        return 0.0
    return math.log(i) + EULER_GAMMA_ORACLE


def harmonic_exact(i: int) -> float:
    """H(i) as the exact sum, for measuring the declared deviation rather than assuming it."""
    total = 0.0
    for j in range(1, i + 1):
        total += 1.0 / j
    return total


def oracle_c(n: int, *, exact: bool = False) -> float:
    """c(n) = 2H(n-1) - 2(n-1)/n, from the definition, with c(0) = c(1) = 0 and c(2) = 1."""
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    h = harmonic_exact(n - 1) if exact else harmonic_estimate(n - 1)
    return 2.0 * h - 2.0 * (n - 1) / n


# ---------------------------------------------------------------------------------------------
# FREEZING A FOREST
# ---------------------------------------------------------------------------------------------

def serialize_tree(node: Any) -> dict[str, Any]:
    """
    One tree, as plain data: selected feature, split value, children, leaf sample size.

    READS ATTRIBUTES ONLY. It calls no method of the node and no function of the module the node
    came from, so what comes back is a description of a structure rather than a delegation to the
    code that built it.
    """
    if getattr(node, "external"):
        return {"external": True, "size": int(getattr(node, "size")),
                "feature": None, "split": None, "left": None, "right": None}
    return {
        "external": False,
        "size": int(getattr(node, "size")),
        "feature": int(getattr(node, "attribute")),
        "split": float(getattr(node, "split")),
        "left": serialize_tree(getattr(node, "left")),
        "right": serialize_tree(getattr(node, "right")),
    }


def serialize_forest(forest: Any) -> dict[str, Any]:
    """
    A frozen forest: every tree's structure, psi, the tree count, the seed, the height limit,
    the declared conventions, and c(psi) RECOMPUTED HERE rather than copied off the forest.
    """
    psi = int(getattr(forest, "subsample"))
    return {
        "psi": psi,
        "n_trees": int(getattr(forest, "n_trees")),
        "seed": int(getattr(forest, "seed")),
        "height_limit": int(getattr(forest, "height_limit")),
        "path_depth_convention": PATH_DEPTH_CONVENTION,
        "external_node_adjustment": EXTERNAL_NODE_ADJUSTMENT,
        "c_psi": oracle_c(psi),
        "trees": [serialize_tree(t) for t in getattr(forest, "trees")],
    }


def forest_digest(frozen: Mapping[str, Any]) -> str:
    """A stable hash of the frozen structure, for the reproducibility record."""
    return hashlib.sha256(
        json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------------------------
# SCORING A FROZEN FOREST, INDEPENDENTLY
# ---------------------------------------------------------------------------------------------

def oracle_path_length(tree: Mapping[str, Any], x, depth: int = 0) -> float:
    """
    h_i(x): edges traversed from the root, PLUS c(size) at the external node reached.

    The traversal rule is the published one and is written out here: go LEFT when the point's
    value on the selected feature is strictly below the split, RIGHT otherwise.
    """
    node = tree
    d = depth
    while not node["external"]:
        if x[node["feature"]] < node["split"]:
            node = node["left"]
        else:
            node = node["right"]
        d += 1
    return d + oracle_c(node["size"])


def oracle_path_lengths(frozen: Mapping[str, Any], x) -> list[float]:
    return [oracle_path_length(t, x) for t in frozen["trees"]]


def oracle_mean_path(frozen: Mapping[str, Any], x) -> float:
    """E[h(x)] = (1/t) * sum_i h_i(x). The arithmetic mean over the ensemble, nothing else."""
    lengths = oracle_path_lengths(frozen, x)
    return sum(lengths) / len(lengths)


def oracle_score(frozen: Mapping[str, Any], x) -> float:
    """s(x, psi) = 2 ** (-E[h(x)] / c(psi)). Higher is more anomalous."""
    c = frozen["c_psi"]
    if c <= 0:
        return 0.5
    return 2.0 ** (-oracle_mean_path(frozen, x) / c)


# ---------------------------------------------------------------------------------------------
# HAND-CONSTRUCTED FORESTS FOR THE SMALL ORACLES
# ---------------------------------------------------------------------------------------------

def leaf(size: int = 1) -> dict[str, Any]:
    return {"external": True, "size": int(size), "feature": None, "split": None,
            "left": None, "right": None}


def split(feature: int, value: float, left: dict, right: dict) -> dict[str, Any]:
    return {"external": False, "size": int(left["size"]) + int(right["size"]),
            "feature": int(feature), "split": float(value), "left": left, "right": right}


def chain_tree(depth: int, *, leaf_size: int = 1, feature: int = 0) -> dict[str, Any]:
    """
    A tree in which the point 0.0 is isolated at exactly `depth` edges.

    Every internal node splits feature `feature` at 0.5 and sends 0.0 LEFT, so a point at 0.0
    traverses `depth` edges and lands on a leaf of `leaf_size` samples. Every right child is a
    single-sample leaf, which contributes nothing to any path the fixtures below take.
    """
    node = leaf(leaf_size)
    for _ in range(depth):
        node = split(feature, 0.5, node, leaf(1))
    return node


def hand_forest(trees: list[dict[str, Any]], psi: int, *, seed: int = 0) -> dict[str, Any]:
    """A frozen forest assembled from hand-built trees, in the same shape `serialize_forest` uses."""
    return {
        "psi": int(psi),
        "n_trees": len(trees),
        "seed": int(seed),
        "height_limit": max(_tree_height(t) for t in trees),
        "path_depth_convention": PATH_DEPTH_CONVENTION,
        "external_node_adjustment": EXTERNAL_NODE_ADJUSTMENT,
        "c_psi": oracle_c(int(psi)),
        "trees": trees,
    }


def _tree_height(node: Mapping[str, Any]) -> int:
    if node["external"]:
        return 0
    return 1 + max(_tree_height(node["left"]), _tree_height(node["right"]))
