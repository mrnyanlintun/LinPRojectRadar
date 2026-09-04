"""
RUN 135. ONE RULE FOR PRINTING A FIGURE BESIDE THE BOUNDARY IT WAS BANDED AGAINST.

THE DEFECT THIS EXISTS TO END, found in six places by two independent hunts (H6, H7, S1, S5,
M1, M2). A module bands on a full-precision quantity -- correctly -- and then renders that
quantity through a fixed presentation helper, `round1`, `round2`, `_round3` or `round(x, 1)`.
Where the quantity sits within half a rounding step of one of its own boundaries, the printed
figure lands ON the boundary while the band came from the other side of it, and the row
contradicts itself in the reader's hands:

    A1.7  TCPI 1.0004      Yellow, printed "TCPI: 1"     beside "Green at or below 1.00"
    A1.8  VAC%  -0.0100    Yellow, printed "(0%)"        beside "Green at or above zero"
    A2.8  899/1000         Yellow, printed "0.9"         beside "at or above 0.9 is Green"
    A3.3  9499/10000       Yellow, STORED  0.95          beside "at or above 0.95 is Green"
    A3.5  variance 5.04%   Yellow, printed "5.0 per cent" inside the boundary sentence itself
    A4.3  249/2500         Green,  printed "10.0 per cent" beside "at or above 10 is Yellow"
    A4.4  49/2500          Green,  printed "2.0 per cent"  beside "at or above 2 is Yellow"
    A6.3  94.95%           rounded BEFORE banding, which made 94.95 Green outright
    C1.3  0.7975           rounded BEFORE banding, which made 0.7975 Green outright

Two distinct faults are in that list and BOTH are fixed by separating the two concerns, which is
what this module is for. The first is rounding before the band -- the band then rests on a
presentation value, and the answer itself is wrong (A6.3, C1.3, and finding H1 upstream in
`extraction_merge`). The second is rounding after a correct band -- the answer is right and the
sentence beside it says otherwise.

THE RULE, stated once so the six sites cannot drift apart: print the figure at the FEWEST
decimals that keep it on the SAME SIDE of every boundary of its own ladder as the canonical
value is. Precision is added only where a boundary is close enough to need it, so an ordinary
reading renders exactly as it always did and only a reading genuinely near an edge grows a
digit. Nothing here rounds the band, nothing here moves a boundary, and nothing here introduces
a tolerance: the band is decided by the caller from the canonical value before this is ever
called.

A figure that IS exactly on a boundary still prints as that boundary. That is not the defect --
the row and the sentence agree in that case, because the value really is the boundary.
"""
from __future__ import annotations

import math
from typing import Iterable

#: How far precision may be grown before the figure is printed at full precision instead. Ten
#: decimals is past the point where a double carries meaning for the quantities in this layer,
#: so reaching it means the value differs from a boundary only in representation error, and
#: printing it whole is the honest answer.
MAX_DISPLAY_DECIMALS = 10


def _round_half_up(value: float, decimals: int) -> float:
    """`js_round` at a given number of decimals: ties go toward positive infinity.

    The same rule `round1`, `round2` and `_round3` already use, kept identical so this changes
    WHICH decimal a figure is shown to and never HOW that decimal is arrived at.
    """
    if math.isnan(value) or math.isinf(value):
        return value
    scale = 10 ** decimals
    return math.floor(value * scale + 0.5) / scale


def _same_side(value: float, shown: float, boundary: float) -> bool:
    """Is `shown` on the same side of `boundary` as `value`?

    Exactly on the boundary is its own side: a value that IS the boundary must print as the
    boundary, and a value that is not must not.
    """
    if value == boundary:
        return shown == boundary
    return shown != boundary and (value > boundary) == (shown > boundary)


def band_figure(value: float, boundaries: Iterable[float], decimals: int) -> float:
    """The figure to PRINT for `value`, given the ladder edges it was banded against.

    `decimals` is the presentation precision the site already used -- what it prints when no
    boundary is near. The returned figure is at that precision or finer, never coarser, and it
    is a number so that callers keep rendering it exactly as they did before.
    """
    if value is None:
        return value
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return value
    edges = [float(b) for b in boundaries if b is not None]
    for d in range(int(decimals), MAX_DISPLAY_DECIMALS + 1):
        shown = _round_half_up(float(value), d)
        if all(_same_side(float(value), shown, b) for b in edges):
            return shown
    return float(value)
