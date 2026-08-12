"""
Run 17 findings, keyed by v0.5 Module_ID_Text_Key.

EVERY ENTRY HERE IS BACKED BY AN EXECUTED TEST in test_run17_scientific_methods.py. A module with
no entry is written to the results matrix as NOT_REACHED_IN_THIS_RUN by build_artifacts.py. That
separation is deliberate: nothing in this file may be added on the strength of reading the code
alone without the corresponding named test having run.

The vocabulary is the owner specification's. In particular "validated" appears nowhere as a
verdict; empirical_validation_status is its own column and is NOT_DONE almost everywhere, which
is the honest answer for a controlled research instrument with no labelled outcome corpus.
"""

from __future__ import annotations

METHOD_CARD_DEFAULTS: dict[str, object] = {
    "module_id": "",
    "module_name": "",
    "category": "",
    "code_id": "",
    "basis_class": "",
    "canonical_or_declared_method": "",
    "primary_source": "",
    "supporting_sources": [],
    "formal_definition": "",
    "required_structure": "",
    "required_inputs": [],
    "input_units": "",
    "minimum_cardinality": "",
    "valid_domain": "",
    "parameters": [],
    "parameter_provenance_requirement": "",
    "stochastic_or_deterministic": "deterministic",
    "output_definition": "",
    "known_answer_oracle": "",
    "invariants": [],
    "metamorphic_properties": [],
    "missing_input_behavior": "",
    "invalid_input_behavior": "",
    "calibration_requirement": "",
    "threshold_status": "",
    "empirical_validation_requirement": "",
    "lineage_notes": "",
    "permitted_claim": "",
    "prohibited_claim": "",
    "current_code_location": "",
    "current_implementation_summary": "",
    "scientific_disposition": "",
    "evidence": "",
}

#: The literature and authority ledger. `retrieved` records honestly whether the primary source
#: itself was read in this container: Run 15 established that several publisher PDFs are refused
#: by the egress proxy. NOT_RETRIEVED_IN_CONTAINER means the identifier is carried from the
#: supervisory specification and the theory used is the supervisory specification's own
#: statement of it, which section 7 of the owner prompt makes the controlling authority.
SOURCE_LEDGER: list[dict[str, str]] = []

#: Findings, keyed by Module_ID_Text_Key. Populated by the run as each module is executed.
FINDINGS: dict[str, dict[str, object]] = {}
