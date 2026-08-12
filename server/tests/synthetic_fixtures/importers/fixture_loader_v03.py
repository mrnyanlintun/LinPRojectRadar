"""Test-only, read-only importer for the v0.3 synthetic research fixtures.

This module is the v0.2 importer, loaded a second time as an independent instance and
pointed at OG-SYNTH-0.3. Reusing the source rather than copying it means the read-only
rules, the frozen records, the origin enforcement and the identifier-only module
resolution are the same code in both versions, and the v0.2 instance the Run 9 suite uses
is not disturbed.

Two deliberate differences from the v0.2 instance:

* PACKAGE_ROOT is the v0.3 programme.
* The Run 9 alias overlay is switched off. v0.3 carries Monte Carlo EAC and Scenario
  Modeling as permanent rows in the package's own alias table, so a module that still
  needed the overlay to resolve would fail here rather than pass on an overlay's word.

Nothing loaded through this importer activates a module, makes a module voting, validates a
status band, or constitutes empirical validation of anything.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).with_name("fixture_loader.py")
_spec = importlib.util.spec_from_file_location("synthetic_fixture_loader_v03_impl", _SOURCE)
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

PROGRAMME_VERSION = "OG-SYNTH-0.3"
_impl.PACKAGE_ROOT = (
    _impl.FIXTURE_ROOT / "OG-SYNTH-0.3" / "Opus_Gubernatio_Synthetic_Programme_v0.3"
)
_impl.OVERLAY_PATH = _impl.PACKAGE_ROOT / "no_overlay_is_used_in_v0_3"
_impl.load_alias_overlay = lambda: ()

globals().update({name: value for name, value in vars(_impl).items()
                  if not name.startswith("_")})

SOURCE_PATH = _SOURCE
