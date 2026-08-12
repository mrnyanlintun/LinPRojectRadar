"""
Isolation Forest, as defined by Liu, Ting and Zhou.

CANONICAL SOURCE
    F. T. Liu, K. M. Ting and Z.-H. Zhou, "Isolation Forest", Proceedings of the 2008 Eighth
    IEEE International Conference on Data Mining (ICDM), Pisa, pp. 413-422,
    doi:10.1109/ICDM.2008.17; extended as "Isolation-Based Anomaly Detection", ACM TKDD 6(1),
    2012, doi:10.1145/2133360.2133363.

THE DEFINITION IMPLEMENTED HERE, PIECE BY PIECE
    iTree(X, e, l)      a proper binary tree. If e >= l or |X| <= 1 the node is external and
                        stores |X|. Otherwise select an attribute q uniformly at random from
                        the attributes of X, select a split point p uniformly at random
                        between min and max of q over X, and recurse on the two sides.
    iForest(X, t, psi)  t trees, each grown on an independent subsample of size psi drawn
                        without replacement from X, with height limit l = ceil(log2(psi)).
    PathLength(x, T, e) the number of edges x traverses, plus c(size) at an external node
                        holding more than one point, where c is the adjustment below.
    c(n)                2 * H(n-1) - 2 * (n-1) / n, with H the harmonic number. This is the
                        average path length of an unsuccessful search in a binary search
                        tree and is used to normalise h(x).
    s(x, n)             2 ** (-E(h(x)) / c(psi)). The paper's stated properties hold: as
                        E(h(x)) -> 0 the score -> 1; as E(h(x)) -> n-1 it -> 0; as
                        E(h(x)) -> c(n) it -> 0.5.

    Paper defaults: t = 100 trees, psi = 256. Both are defaults of the algorithm as published,
    not of any library.

DETERMINISM
    Every draw comes from a seeded random.Random. A given (data, seed, t, psi) returns the same
    score every time, which is what this platform requires of every module. The randomisation
    is real: a different seed builds different trees.

NO FALLBACK
    Isolation is the only mechanism in this file. If the reference population is too small to
    build a forest, the caller is told so; nothing silently substitutes another method.
"""

from __future__ import annotations

import math
import random
from typing import Any

EULER_GAMMA = 0.5772156649015329
DEFAULT_TREES = 100
DEFAULT_SUBSAMPLE = 256


def harmonic(i: int) -> float:
    """
    H(i), by the paper's stated estimate ln(i) + Euler's constant.

    This is the estimate the paper itself gives and the one the reference implementations use.
    It is known to sit below the exact harmonic sum for small i (at i = 9 it is low by about
    0.05) and to converge as i grows. The subsample sizes this platform uses are small, so the
    deviation is real and is recorded rather than hidden; it shifts every score by the same
    monotone factor and so does not change the ordering the method depends on.
    """
    if i <= 0:
        return 0.0
    return math.log(i) + EULER_GAMMA


def c_factor(n: int) -> float:
    """c(n) = 2H(n-1) - 2(n-1)/n. The average unsuccessful-search path length in a BST."""
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    return 2.0 * harmonic(n - 1) - 2.0 * (n - 1) / n


class _Node:
    __slots__ = ("attribute", "split", "left", "right", "size", "external")

    def __init__(self, external, size=0, attribute=None, split=None, left=None, right=None):
        self.external = external
        self.size = size
        self.attribute = attribute
        self.split = split
        self.left = left
        self.right = right


def _grow(points: list[list[float]], depth: int, height_limit: int, rng: random.Random) -> _Node:
    if depth >= height_limit or len(points) <= 1:
        return _Node(True, size=len(points))
    dims = len(points[0])
    # A random attribute, restricted to those that can actually be split: an attribute whose
    # values are all equal admits no split point and choosing it would waste the node.
    splittable = [q for q in range(dims)
                  if max(p[q] for p in points) > min(p[q] for p in points)]
    if not splittable:
        return _Node(True, size=len(points))
    q = rng.choice(splittable)
    lo = min(p[q] for p in points)
    hi = max(p[q] for p in points)
    p_split = rng.uniform(lo, hi)
    left = [p for p in points if p[q] < p_split]
    right = [p for p in points if p[q] >= p_split]
    if not left or not right:
        return _Node(True, size=len(points))
    return _Node(False, attribute=q, split=p_split,
                 left=_grow(left, depth + 1, height_limit, rng),
                 right=_grow(right, depth + 1, height_limit, rng))


def _path_length(x: list[float], node: _Node, depth: int) -> float:
    if node.external:
        return depth + c_factor(node.size)
    if x[node.attribute] < node.split:
        return _path_length(x, node.left, depth + 1)
    return _path_length(x, node.right, depth + 1)


class IsolationForest:
    """An ensemble of isolation trees over a fixed reference population."""

    def __init__(self, training: list[list[float]], n_trees: int = DEFAULT_TREES,
                 subsample: int = DEFAULT_SUBSAMPLE, seed: int = 0):
        if len(training) < 2:
            raise ValueError("an isolation forest needs at least two reference observations")
        self.n_trees = n_trees
        self.subsample = max(2, min(subsample, len(training)))
        self.seed = seed
        self.height_limit = max(1, math.ceil(math.log2(self.subsample)))
        self.normaliser = c_factor(self.subsample)
        rng = random.Random(seed)
        self.trees: list[_Node] = []
        for _ in range(n_trees):
            sample = rng.sample(training, self.subsample)
            self.trees.append(_grow(sample, 0, self.height_limit, random.Random(rng.random())))

    def path_lengths(self, x: list[float]) -> list[float]:
        return [_path_length(x, t, 0) for t in self.trees]

    def mean_path_length(self, x: list[float]) -> float:
        pl = self.path_lengths(x)
        return sum(pl) / len(pl)

    def anomaly_score(self, x: list[float]) -> float:
        """s(x, psi) = 2 ** (-E(h(x)) / c(psi)). Higher is more anomalous. In (0, 1]."""
        if self.normaliser <= 0:
            return 0.5
        return 2.0 ** (-self.mean_path_length(x) / self.normaliser)


def describe() -> dict[str, Any]:
    return {"source": "Liu, Ting and Zhou, Isolation Forest, ICDM 2008, "
                      "doi:10.1109/ICDM.2008.17",
            "default_trees": DEFAULT_TREES, "default_subsample": DEFAULT_SUBSAMPLE}
