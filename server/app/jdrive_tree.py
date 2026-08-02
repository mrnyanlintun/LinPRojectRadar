"""
The Arora project directory template, and the rules that file a document into it.

SOURCE. `JDrive_Project_Directory_Structure_NEW_v202604.pdf`, version 2026-04, transcribed
column by column from the source table (FOLDER / SUB FOLDER / SUB SUB FOLDER / DESCRIPTION FOR
USE). Folder names are VERBATIM, including the template's own inconsistencies: `C. PHOTOS`
uses a period where every other lettered folder uses an underscore, `YYYY_MM_DD XX% INFO`
uses underscores in the date where every other dated folder uses hyphens, and
`1_ACTIVE CONSTR. SET` carries an abbreviating period. Those are not typos to fix here. This
module reproduces a template that exists outside the platform, and a PM matching this tree
against the J drive must see the same strings.

NOTHING HERE IS MATERIALISED PER PROJECT, AND THAT IS THE CENTRAL DECISION.

The source document is explicit that the tree is a template a PM prunes: it says to delete
disciplines outside Arora's scope, to delete either the CAD or the REVIT folder depending on
the project, and that the PM creates the room-by-room photo folders by hand. Materialising all
of it per project would mean creating roughly sixty folders for every project and then asking
someone to delete most of them.

So no folder is ever created as a row. A project's tree is computed as:

    the template below  +  the distinct folder paths that actually hold a filed document

An empty discipline folder therefore never exists to be deleted, the CAD/REVIT choice resolves
itself (whichever one receives a file is the one that appears), and the room-by-room photo
folders the PM would have created by hand come into being when a photo is filed into them.
Pruning becomes something the platform never asks for rather than something it asks for and
then has to undo. `occupied` on each node says which is which, so the tree can be shown either
as the full template (what could exist) or as the project (what does).

PLACEHOLDER SEGMENTS. Several branches end in a segment that is a pattern rather than a name:
`YYYY-MM-DD`, `CLAIM #`, `YYYY-MM-DD SITE OBS #`, `CREDIT NAME`. `PLACEHOLDER` marks them, and
`resolve_destination` instantiates them from the document's own date and identifier. Two of
them must not be flattened into a plain type-then-date rule, and the source says so explicitly:

  * `8_CLAIMS / CLAIM # / YYYY-MM-DD`   — two levels, identifier ABOVE date. The source note:
    "alteration of standard file naming convention to be either by claim number or contractor
    first, then standard date convention".
  * `7_FIELD-SITE VISITS / YYYY-MM-DD SITE OBS #` — ONE level, identifier INSIDE the dated
    name, after the date.

They are different shapes, and `resolve_destination` builds each one separately rather than
through a shared date rule.
"""

from __future__ import annotations

from datetime import date
from typing import Any

# --------------------------------------------------------------------------- placeholders
#
# A segment whose name is a pattern the filing step fills in, not a literal folder.
PLACEHOLDER_DATE = "date"                    # YYYY-MM-DD
PLACEHOLDER_DATE_PCT = "date_pct"            # YYYY-MM-DD_XX%  /  YYYY_MM_DD XX% INFO
PLACEHOLDER_DATE_INFO = "date_info"          # YYYY-MM-DD INFO / YYYY-MM-DD_INFO
PLACEHOLDER_CLAIM = "claim"                  # CLAIM #
PLACEHOLDER_SITE_OBS = "site_obs"            # YYYY-MM-DD SITE OBS #
PLACEHOLDER_CREDIT = "credit"                # CREDIT NAME
PLACEHOLDER_ROOM = "room"                    # PM-created room/area folders under C. PHOTOS

#: Marks a node whose `name` is a pattern rather than a literal folder name.
PLACEHOLDER = "placeholder"

# The three discipline working folders, repeated verbatim under every discipline branch.
_DISCIPLINE_SUBS: tuple[dict, ...] = (
    {"name": "A_CALCS"},
    {"name": "B_EQUIP CUTS"},
    {"name": "C_PROG PRINTS"},
)

# Disciplines, in source order. The source: "Project Manager to eliminate any Disciplines not
# included in Arora's scope of service". Nothing is eliminated here because nothing is created
# here; a discipline appears for a project only once something is filed under it.
_DISCIPLINES: tuple[str, ...] = (
    "6_MECH", "7_PLUMB", "8_ELECT", "9_FIRE AL", "10_FIRE PROT", "11_SPEC SYS",
)


def _disciplines() -> list[dict]:
    return [{"name": n, "children": list(_DISCIPLINE_SUBS)} for n in _DISCIPLINES]


# --------------------------------------------------------------------------- the template
#
# Transcribed from the source table. `note` carries the source's own DESCRIPTION FOR USE where
# it governs behaviour (the CAD/REVIT choice, the room-by-room rule, the claims naming
# alteration); it is not a full transcription of the description column.
TEMPLATE: tuple[dict, ...] = (
    {"name": "0_PROJ-MGMNT", "children": [
        {"name": "1_RFP"},
        {"name": "2_FEE"},
        {"name": "3_PROP"},
    ]},
    {"name": "1_PROJ INFO", "children": [
        {"name": "1_WORK-PLAN"},
        {"name": "2_PROJ-SCHED"},
        {"name": "3_MEETINGS", "children": [
            {"name": "YYYY-MM-DD INFO", PLACEHOLDER: PLACEHOLDER_DATE_INFO},
        ]},
    ]},
    {"name": "2_DELIVERABLES", "children": [
        {"name": "1_ACTIVE CONSTR. SET"},
        {"name": "YYYY_MM_DD XX% INFO", PLACEHOLDER: PLACEHOLDER_DATE_PCT, "children": [
            {"name": "A_DRAWINGS"},
            {"name": "B_SPECS"},
            {"name": "C_CALCS"},
            {"name": "D_NARRATIVES"},
        ]},
    ]},
    {"name": "3_DESIGN", "children": [
        {"name": "1_EXISTING CONDS", "children": [
            {"name": "A_AS BUILT DWGS"},
            {"name": "B_SURVEY INFO"},
            # Verbatim: a period, where every other lettered folder uses an underscore.
            {"name": "C. PHOTOS", "note": (
                "Photos are sorted by building room or area, never by discipline and never by "
                "date of survey. The project manager creates the room by room folders."),
             "children": [
                {"name": "ROOM OR AREA", PLACEHOLDER: PLACEHOLDER_ROOM},
             ]},
        ]},
        {"name": "2_CODE & STANDARDS", "children": [
            {"name": "A_CODE REVIEW"},
            # The reference corpus lands here. See FILING_RULES.
            {"name": "B_CODE - CLIENT STANDARDS", "note": (
                "Copies of referenced building codes, standards and client standards.")},
        ]},
        {"name": "3_DESIGN NARRATIVES"},
        {"name": "4_COST ESTIMATE", "children": [
            {"name": "YYYY-MM-DD", PLACEHOLDER: PLACEHOLDER_DATE},
        ]},
        {"name": "5_BIM-CAD", "note": (
            "One of these two is kept per project, whichever the project actually uses."),
         "children": [
            {"name": "CAD (Delete if REVIT)"},
            {"name": "REVIT_HOST NAME_VERSION (Delete if CAD)"},
        ]},
        *_disciplines(),
        {"name": "12_LEED", "children": [
            {"name": "CREDIT NAME", PLACEHOLDER: PLACEHOLDER_CREDIT},
        ]},
    ]},
    {"name": "4_QC", "children": [
        {"name": "YYYY-MM-DD_XX%", PLACEHOLDER: PLACEHOLDER_DATE_PCT, "children": [
            {"name": "A_CALCS"},
            {"name": "B_DESIGN CHECKLISTS"},
            {"name": "C_DRAWINGS"},
            # The reference corpus lands here too. See FILING_RULES.
            {"name": "D_SPECIFICATIONS", "note": "Specifications held for review."},
            {"name": "E_CLIENT COMMENTS"},
            {"name": "F_QC REVIEW FORMS"},
            {"name": "G_FINAL QC RECORD"},
        ]},
    ]},
    {"name": "5_CONST ADMIN", "children": [
        {"name": "0_PERMIT"},
        {"name": "1_BID INFO"},
        {"name": "2_CONST-SCHED"},
        {"name": "3_CONST-MTGS"},
        {"name": "4_CONT-AGMTS"},
        {"name": "5_CONT-PAYMENTS"},
        {"name": "6_CONST-PHOTOS", "children": [
            {"name": "YYYY-MM-DD", PLACEHOLDER: PLACEHOLDER_DATE},
        ]},
        # ONE level: the identifier sits INSIDE the dated folder name, after the date.
        {"name": "7_FIELD-SITE VISITS", "children": [
            {"name": "YYYY-MM-DD SITE OBS #", PLACEHOLDER: PLACEHOLDER_SITE_OBS},
        ]},
        # TWO levels: the identifier sits ABOVE the date.
        {"name": "8_CLAIMS", "note": (
            "One folder per claim or change order, by claim number, and the standard date "
            "convention beneath it."),
         "children": [
            {"name": "CLAIM #", PLACEHOLDER: PLACEHOLDER_CLAIM, "children": [
                {"name": "YYYY-MM-DD", PLACEHOLDER: PLACEHOLDER_DATE},
            ]},
        ]},
        {"name": "9_CLOSE-OUT", "children": [
            {"name": "A_CERTIFICATES"},
            {"name": "B_LIEN-WAIVER"},
            {"name": "C_REPORTS-MANUALS"},
        ]},
        {"name": "10_LESSONS LEARNED"},
    ]},
    {"name": "6_RECEIVED", "children": [
        {"name": "YYYY-MM-DD_INFO", PLACEHOLDER: PLACEHOLDER_DATE_INFO},
    ]},
    # In the source, and deliberately carried: "This is a secured folder for use by the
    # Newforma software program. There is no need for anyone to access this folder." Nothing
    # is ever filed here by this platform; it appears so the tree matches the J drive.
    {"name": "NEWFORMA", "note": (
        "Secured folder used by the Newforma software. Nothing is filed here."),
     "readonly": True},
)


# --------------------------------------------------------------------------- filing classes
#
# PART 3, the explicit distinction. Before this, an upload was something to extract from, so a
# stored-but-never-analysed document read as a failed extraction. These three states say what a
# document IS, so a Revit file and a broken pay application are never the same thing on screen.
CLASS_ANALYSED = "analysed"    # a mapped doc type; its figures reach the analytical path
CLASS_REFERENCE = "reference"  # specifications, codes of practice, user requirements
CLASS_FILED = "filed"          # stored and never analysed, and that is the expected outcome

FILING_CLASSES: tuple[str, ...] = (CLASS_ANALYSED, CLASS_REFERENCE, CLASS_FILED)

FILING_CLASS_LABELS: dict[str, str] = {
    CLASS_ANALYSED: "Filed and analysed",
    CLASS_REFERENCE: "Filed as reference",
    CLASS_FILED: "Filed",
}

# --------------------------------------------------------------------------- reference corpus
#
# THE SEPARATION THE APPS SCRIPT KEPT WITH A `_corpus` FOLDER, PRESERVED WITHOUT ONE.
#
# The old chain put specifications and codes in a `_corpus` folder so signal extraction could
# not read them. The separation is what matters, not the folder name, and inventing a `_corpus`
# folder here would put a directory in the tree that the Arora template does not have. The
# Arora template already has the right homes for these documents, named for exactly what they
# are, so the corpus lands in them and the separation is carried by the CLASS instead:
#
#   * a reference document is never a mapped doc type, so `is_mapped()` is false for it and
#     `assemble_signal_inputs` skips it. That is structural and predates this module.
#   * it is classed CLASS_REFERENCE, so it does not read as an unmapped or failed extraction.
#
# Both halves hold with the technical reviewer switched off. Filing is not conditional on the
# flag; only reading the corpus is.
REFERENCE_KINDS: dict[str, str] = {
    # kind -> the folder it belongs in, by the template's own description of that folder
    "specification": "4_QC/YYYY-MM-DD_XX%/D_SPECIFICATIONS",
    "code_of_practice": "3_DESIGN/2_CODE & STANDARDS/B_CODE - CLIENT STANDARDS",
    "client_standard": "3_DESIGN/2_CODE & STANDARDS/B_CODE - CLIENT STANDARDS",
    "user_requirement": "3_DESIGN/2_CODE & STANDARDS/B_CODE - CLIENT STANDARDS",
}

# Filename evidence for a reference document. Deliberately SEPARATE from the analytical
# classifier: extending `DOC_TYPES` with a "specification" type would put specifications inside
# the vocabulary the analytical classifier chooses from, and the one thing this separation
# exists to guarantee is that they are never chosen from it.
_REFERENCE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("code_of_practice", "code of practice"),
    ("code_of_practice", "building code"),
    ("client_standard", "client standard"),
    ("client_standard", "design standard"),
    ("user_requirement", "user requirement"),
    ("user_requirement", "owner's project requirement"),
    ("user_requirement", "owners project requirement"),
    ("user_requirement", "employer's requirement"),
    ("specification", "specification"),
    ("specification", "spec section"),
    ("specification", "masterformat"),
)


def reference_kind(filename: str) -> str | None:
    """The reference-corpus kind this filename declares, or None.

    Filename evidence only, and that is a stated limitation rather than a hidden one: nothing
    reads the CONTENT of a reference document to decide it is one, because the only content
    reader on the platform is the analytical extractor and routing a specification through it
    is precisely what must not happen.
    """
    lowered = f" {str(filename or '').lower()} "
    for kind, needle in _REFERENCE_PATTERNS:
        if needle in lowered:
            return kind
    return None


# --------------------------------------------------------------------------- filing rules
#
# doc_type -> destination, for the analytical document vocabulary.
#
# THE TEMPLATE AND THE ANALYTICAL VOCABULARY OVERLAP ONLY PARTLY, and this table is where that
# becomes visible. The Arora tree was written for what a design and construction-administration
# project produces; it has folders named for payment applications, claims, site observations,
# construction schedules and closeout reports. It has NO folder for an RFI log, a submittal
# register, a safety report or an NCR log, because those arrive from the contractor rather than
# being produced by the design team.
#
# Those types are therefore filed to `6_RECEIVED`, whose own description is "All received
# documents are saved into individual folders following Arora's naming convention" — the
# template's own answer for a document that arrives without a designated home. That is a
# reading of the template, not a gap in it, and it is flagged here so it can be overridden with
# one line if a real project files them elsewhere.
_RECEIVED = ("6_RECEIVED", PLACEHOLDER_DATE_INFO)

FILING_RULES: dict[str, tuple] = {
    # --- named by the template's own description of the destination folder ---------------
    # "Documents include Payment Log, Schedule of Values, Payment Applications/Certifications"
    "pay_application": ("5_CONST ADMIN/5_CONT-PAYMENTS",),
    "schedule_of_values": ("5_CONST ADMIN/5_CONT-PAYMENTS",),
    # "Documents include Agreements, Payment Bonds, Certificates of Insurance"
    "contract_value": ("5_CONST ADMIN/4_CONT-AGMTS",),
    # "Add folders per claim/change order by Contractor" — identifier ABOVE date.
    "change_order": ("5_CONST ADMIN/8_CLAIMS", PLACEHOLDER_CLAIM),
    # "Field/Site Observation Reports" — identifier INSIDE the dated name.
    "field_report": ("5_CONST ADMIN/7_FIELD-SITE VISITS", PLACEHOLDER_SITE_OBS),
    "inspection_report": ("5_CONST ADMIN/7_FIELD-SITE VISITS", PLACEHOLDER_SITE_OBS),
    # "Meeting minutes, Agenda, Notes" under construction administration.
    "oac_minutes": ("5_CONST ADMIN/3_CONST-MTGS",),
    # "Construction schedules"
    "schedule_update": ("5_CONST ADMIN/2_CONST-SCHED",),
    "time_phased_schedule": ("5_CONST ADMIN/2_CONST-SCHED",),
    "lookahead_schedule": ("5_CONST ADMIN/2_CONST-SCHED",),
    # "Documents include ... Commissioning Reports"
    "commissioning_report": ("5_CONST ADMIN/9_CLOSE-OUT/C_REPORTS-MANUALS",),
    # The design branch's own dated cost-estimate folder.
    "cost_report": ("3_DESIGN/4_COST ESTIMATE", PLACEHOLDER_DATE),

    # --- no folder of their own in the template; see the note above -----------------------
    "monthly_report": _RECEIVED,
    "rfi_log": _RECEIVED,
    "rfa_log": _RECEIVED,
    "submittal_register": _RECEIVED,
    "ncr_log": _RECEIVED,
    "safety_report": _RECEIVED,
    "environmental_report": _RECEIVED,
    "quality_audit_report": _RECEIVED,
    "risk_register": _RECEIVED,
    "correspondence_notice": _RECEIVED,
    "procurement_log": _RECEIVED,
    "resource_report": _RECEIVED,
    "subcontractor_report": _RECEIVED,
    "past_performance_report": _RECEIVED,
    "historical_data": _RECEIVED,
}

# --------------------------------------------------------------------------- format rules
#
# FILE FORMAT IS EVIDENCE THE ANALYTICAL CLASSIFIER NEVER SEES. A Revit model is not one of the
# analytical document types and never will be, so the classifier can only ever call it
# UNMAPPED — but its extension says exactly where it belongs, and the Arora tree has a folder
# named for it. Filing on the extension puts these documents in the right place instead of
# leaving them in the review queue forever.
#
# This is also what settles the template's CAD-versus-REVIT instruction ("Delete this folder if
# project is a REVIT project", and the converse). Neither folder is created for any project, so
# whichever one actually receives a file is the one that appears in that project's tree, and
# the PM never deletes anything.
#
# `review` is False for CAD and Revit because the extension is unambiguous. It is True for
# images because it is not: a photo could be a survey photo, which the template requires be
# sorted by building room into folders the PM creates by hand, and the platform cannot know the
# room. Those land in the dated construction-photos folder and are flagged so the PM can move
# them.
FORMAT_RULES: dict[str, tuple[str, str | None, bool]] = {
    ".rvt": ("3_DESIGN/5_BIM-CAD/REVIT_HOST NAME_VERSION (Delete if CAD)", None, False),
    ".rfa": ("3_DESIGN/5_BIM-CAD/REVIT_HOST NAME_VERSION (Delete if CAD)", None, False),
    ".dwg": ("3_DESIGN/5_BIM-CAD/CAD (Delete if REVIT)", None, False),
    ".dxf": ("3_DESIGN/5_BIM-CAD/CAD (Delete if REVIT)", None, False),
    ".dgn": ("3_DESIGN/5_BIM-CAD/CAD (Delete if REVIT)", None, False),
    ".jpg": ("5_CONST ADMIN/6_CONST-PHOTOS", PLACEHOLDER_DATE, True),
    ".jpeg": ("5_CONST ADMIN/6_CONST-PHOTOS", PLACEHOLDER_DATE, True),
    ".png": ("5_CONST ADMIN/6_CONST-PHOTOS", PLACEHOLDER_DATE, True),
    ".heic": ("5_CONST ADMIN/6_CONST-PHOTOS", PLACEHOLDER_DATE, True),
}


def format_rule(filename: str) -> tuple[str, str | None, bool] | None:
    """The destination this file's EXTENSION declares, or None."""
    name = str(filename or "").lower()
    dot = name.rfind(".")
    return FORMAT_RULES.get(name[dot:]) if dot > 0 else None


#: Where a document goes when its type is unknown, or known with too little confidence to file
#: it silently into a discipline folder. It is a real folder of the template, not an invented
#: one, and `needs_filing_review` is what actually makes it reviewable — see
#: `documents.py`'s filing step and the Files tab's review filter.
REVIEW_DESTINATION = _RECEIVED

# --------------------------------------------------------------------------- the threshold
#
# THE NUMBER, AND WHERE IT COMES FROM. The classifier prompt already asks the model for
# `{"docType", "confidence"}`; until this work the confidence was parsed and then dropped on
# the floor, so nothing on the platform had ever seen it (see `extraction_client.classify`).
#
# 0.70 is the legacy Apps Script's own default for a missing confidence
# (`parsed.confidence != null ? parsed.confidence : 0.7`, .gs 788), so it is the one number the
# instrument being reproduced ever committed to. It is NOT calibrated: extraction has never run
# against a real project document, so nothing here has been measured against real
# classifications, and this constant is the single place to change when it has been.
#
# The rule deliberately treats "no confidence" as reviewable rather than as confident. A
# classification that came from the filename heuristic, or one the model declined, carries no
# confidence at all, and filing those silently into a discipline folder is the exact failure
# the review destination exists to prevent.
CONFIDENCE_THRESHOLD = 0.70


def is_mapped_type(doc_type: str) -> bool:
    """Whether the analytical layer recognises this type. Imported lazily to keep this module
    importable from a migration or a test without dragging in the extraction vocabulary."""
    from .extraction_fields import UNMAPPED, is_mapped
    return bool(doc_type) and doc_type != UNMAPPED and is_mapped(doc_type)


def needs_review(doc_type: str, confidence: float | None, filing_class: str,
                 filename: str | None = None) -> bool:
    """Whether this placement must be shown to the PM rather than made silently."""
    if filing_class == CLASS_REFERENCE:
        # A reference document is placed by an explicit filename declaration, not by the
        # analytical classifier, so there is no model confidence to be low.
        return False
    if not is_mapped_type(doc_type):
        rule = format_rule(filename or "")
        if rule is not None:
            # The extension decided it, so there is no low-confidence classification to review.
            # Images still return True here, from their own rule: see FORMAT_RULES.
            return rule[2]
        return True
    if confidence is None:
        return True
    return float(confidence) < CONFIDENCE_THRESHOLD


# --------------------------------------------------------------------------- destinations


#: The date segment for a document that carries no readable date of its own.
#:
#: NOT a stamped wall clock and NOT an epoch date. `1970-01-01` would look like a real date a
#: reader could act on, and today's date would assert that the document is about today. The
#: platform's standing posture on a missing document date is to mark it undated explicitly
#: rather than substitute one, and a folder name is no exception.
UNDATED = "UNDATED"


def _date_segment(kind: str, as_of: date | None, pct: str | None,
                  identifier: str | None) -> str:
    """Instantiate one placeholder segment. The two identifier-bearing shapes are built here,
    separately, because they are genuinely different shapes."""
    stamp = as_of.isoformat() if as_of else UNDATED
    if kind == PLACEHOLDER_DATE:
        return stamp
    if kind == PLACEHOLDER_DATE_INFO:
        return f"{stamp}_INFO"
    if kind == PLACEHOLDER_DATE_PCT:
        return f"{stamp}_{pct or 'XX%'}"
    if kind == PLACEHOLDER_SITE_OBS:
        # YYYY-MM-DD SITE OBS #  — the identifier follows the date, in one folder name.
        return f"{stamp} SITE OBS {identifier}" if identifier else f"{stamp} SITE OBS"
    if kind == PLACEHOLDER_CLAIM:
        return f"CLAIM {identifier}" if identifier else "CLAIM"
    if kind == PLACEHOLDER_CREDIT:
        return identifier or "CREDIT"
    if kind == PLACEHOLDER_ROOM:
        return identifier or "ROOM OR AREA"
    return stamp


def resolve_destination(doc_type: str, *, filing_class: str, as_of: date | None = None,
                        identifier: str | None = None, pct: str | None = None,
                        reference: str | None = None, filename: str | None = None,
                        confidence: float | None = None) -> str:
    """
    The folder path this document is filed into. Pure: no clock, no database.

    Returns a `/`-joined path of literal folder names, with every placeholder already
    instantiated, so what is stored is the real destination rather than a pattern.
    """
    if filing_class == CLASS_REFERENCE:
        base = REFERENCE_KINDS.get(reference or "", REFERENCE_KINDS["specification"])
        # The QC specifications folder sits under a dated submission folder; instantiate it.
        return base.replace("YYYY-MM-DD_XX%",
                            _date_segment(PLACEHOLDER_DATE_PCT, as_of, pct, None))

    # Format evidence outranks an UNMAPPED classification: the classifier can only ever call a
    # Revit model unmapped, while the extension says exactly where it belongs. It does NOT
    # outrank a confident analytical classification, so a PDF pay application is still filed as
    # a pay application rather than by being a PDF.
    if not is_mapped_type(doc_type):
        rule = format_rule(filename or "")
        if rule is not None:
            head, placeholder, _review = rule
            if placeholder is None:
                return head
            return f"{head}/{_date_segment(placeholder, as_of, pct, identifier)}"

    if needs_review(doc_type, confidence, filing_class):
        head, placeholder = REVIEW_DESTINATION
        return f"{head}/{_date_segment(placeholder, as_of, pct, identifier)}"

    rule = FILING_RULES.get(doc_type)
    if not rule:
        head, placeholder = REVIEW_DESTINATION
        return f"{head}/{_date_segment(placeholder, as_of, pct, identifier)}"

    head = rule[0]
    if len(rule) == 1:
        return head
    placeholder = rule[1]
    segment = _date_segment(placeholder, as_of, pct, identifier)
    if placeholder == PLACEHOLDER_CLAIM:
        # TWO levels: CLAIM # / YYYY-MM-DD. Not flattened into a type-then-date rule.
        return f"{head}/{segment}/{_date_segment(PLACEHOLDER_DATE, as_of, None, None)}"
    return f"{head}/{segment}"


# --------------------------------------------------------------------------- the tree view


def _clone(node: dict, prefix: str, occupied: set[str]) -> dict:
    path = f"{prefix}/{node['name']}" if prefix else node["name"]
    out: dict[str, Any] = {
        "name": node["name"],
        "path": path,
        "placeholder": node.get(PLACEHOLDER),
        "occupied": path in occupied,
        "children": [],
    }
    if node.get("note"):
        out["note"] = node["note"]
    if node.get("readonly"):
        out["readonly"] = True
    for child in node.get("children", ()):
        kid = _clone(child, path, occupied)
        out["children"].append(kid)
        if kid["occupied"]:
            out["occupied"] = True
    return out


def project_tree(occupied_paths: set[str] | None = None) -> list[dict]:
    """
    The template, annotated with which folders this project actually holds documents in, plus
    any real folder that filing created and the template only describes as a pattern.

    `occupied` is true for a folder holding documents AND for every ancestor of one, so a
    viewer can collapse everything a project has never used without losing the path to what it
    has. Nothing is created and nothing is deleted: see the module docstring.
    """
    occupied = set(occupied_paths or ())
    # Every ancestor of an occupied folder is occupied too.
    expanded: set[str] = set()
    for path in occupied:
        parts = path.split("/")
        for i in range(1, len(parts) + 1):
            expanded.add("/".join(parts[:i]))

    tree = [_clone(node, "", expanded) for node in TEMPLATE]

    # Instantiated placeholder folders: real folders that exist because something was filed
    # into them (a dated submission, a claim number, a room). They are grafted onto the branch
    # whose placeholder pattern they match, so `2026-06-15 SITE OBS 3` appears under
    # `7_FIELD-SITE VISITS` beside the pattern it was built from rather than at the root.
    by_path: dict[str, dict] = {}

    def index(nodes: list[dict]) -> None:
        for n in nodes:
            by_path[n["path"]] = n
            index(n["children"])

    index(tree)
    for path in sorted(expanded):
        if path in by_path:
            continue
        parent_path, _, name = path.rpartition("/")
        parent = by_path.get(parent_path)
        if parent is None:
            continue
        node = {"name": name, "path": path, "placeholder": None, "occupied": True,
                "children": [], "instantiated": True}
        parent["children"].append(node)
        by_path[path] = node
    return tree


def is_known_path(path: str) -> bool:
    """
    Whether `path` is a folder this template can hold, template or instantiated.

    Used to refuse a move to a path that is not part of the Arora structure at all. A
    placeholder's own pattern name is NOT a valid destination: a document belongs in a real
    dated folder, never in the pattern that describes one.
    """
    if not path or path.startswith("/") or path.endswith("/") or ".." in path:
        return False
    literal: set[str] = set()
    placeholder_parents: set[str] = set()
    pattern_names: set[str] = set()

    def walk(nodes: tuple[dict, ...] | list[dict], prefix: str) -> None:
        for n in nodes:
            p = f"{prefix}/{n['name']}" if prefix else n["name"]
            if n.get(PLACEHOLDER):
                placeholder_parents.add(prefix)
                pattern_names.add(n["name"])
            else:
                literal.add(p)
            walk(n.get("children", ()), p)

    walk(TEMPLATE, "")
    if path in literal:
        return True
    # A placeholder's own PATTERN name is never a destination. `6_RECEIVED/YYYY-MM-DD_INFO`
    # describes the shape of a folder; a document belongs in the real dated folder built from
    # it, never in the pattern itself.
    if path.rpartition("/")[2] in pattern_names:
        return False
    # An instantiated placeholder: its parent must be a branch that declares a placeholder,
    # or a claim folder (whose own children are dated folders).
    parent, _, _leaf = path.rpartition("/")
    if parent in placeholder_parents:
        return True
    grandparent, _, _mid = parent.rpartition("/")
    return grandparent in placeholder_parents and parent not in literal


if __name__ == "__main__":
    # The two shapes that must not be flattened into one date rule.
    claim = resolve_destination("change_order", filing_class=CLASS_ANALYSED,
                                as_of=date(2026, 6, 15), identifier="7", confidence=0.9)
    assert claim == "5_CONST ADMIN/8_CLAIMS/CLAIM 7/2026-06-15", claim
    obs = resolve_destination("field_report", filing_class=CLASS_ANALYSED,
                              as_of=date(2026, 6, 15), identifier="3", confidence=0.9)
    assert obs == "5_CONST ADMIN/7_FIELD-SITE VISITS/2026-06-15 SITE OBS 3", obs

    pay = resolve_destination("pay_application", filing_class=CLASS_ANALYSED,
                              as_of=date(2026, 6, 15), confidence=0.95)
    assert pay == "5_CONST ADMIN/5_CONT-PAYMENTS", pay

    low = resolve_destination("pay_application", filing_class=CLASS_ANALYSED,
                              as_of=date(2026, 6, 15), confidence=0.2)
    assert low == "6_RECEIVED/2026-06-15_INFO", low

    ref = resolve_destination("", filing_class=CLASS_REFERENCE, as_of=date(2026, 6, 15),
                              reference="code_of_practice")
    assert ref == "3_DESIGN/2_CODE & STANDARDS/B_CODE - CLIENT STANDARDS", ref

    assert reference_kind("Division 23 Specification.pdf") == "specification"
    assert reference_kind("pay app 7.pdf") is None

    # A document with no readable date is marked undated, never stamped with an invented one.
    undated = resolve_destination("pay_application", filing_class=CLASS_ANALYSED, as_of=None,
                                  confidence=0.95)
    assert undated == "5_CONST ADMIN/5_CONT-PAYMENTS", undated
    undated_review = resolve_destination("", filing_class=CLASS_FILED, as_of=None,
                                         filename="mystery.bin")
    assert undated_review == "6_RECEIVED/UNDATED_INFO", undated_review
    assert "1970" not in undated_review

    # Format evidence: the CAD/REVIT choice resolves itself, and neither is reviewable.
    revit = resolve_destination("", filing_class=CLASS_FILED, filename="Tower.rvt")
    assert revit == "3_DESIGN/5_BIM-CAD/REVIT_HOST NAME_VERSION (Delete if CAD)", revit
    assert needs_review("", None, CLASS_FILED, "Tower.rvt") is False
    cad = resolve_destination("", filing_class=CLASS_FILED, filename="site.dwg")
    assert cad == "3_DESIGN/5_BIM-CAD/CAD (Delete if REVIT)", cad
    # A photo could be a survey photo, which belongs in a room folder only a PM can make.
    assert needs_review("", None, CLASS_FILED, "room101.jpg") is True
    # Format never overrides a confident analytical classification.
    assert resolve_destination("pay_application", filing_class=CLASS_ANALYSED,
                               as_of=date(2026, 6, 15), filename="payapp.jpg",
                               confidence=0.95) == "5_CONST ADMIN/5_CONT-PAYMENTS"

    assert is_known_path("5_CONST ADMIN/5_CONT-PAYMENTS")
    assert is_known_path("6_RECEIVED/2026-06-15_INFO")
    assert is_known_path("5_CONST ADMIN/8_CLAIMS/CLAIM 7/2026-06-15")
    assert not is_known_path("../etc/passwd")
    assert not is_known_path("/5_CONST ADMIN")
    assert not is_known_path("MADE UP FOLDER")
    # The pattern itself is not a destination; the folder built from it is.
    assert not is_known_path("6_RECEIVED/YYYY-MM-DD_INFO")

    t = project_tree({"5_CONST ADMIN/5_CONT-PAYMENTS"})
    const = [n for n in t if n["name"] == "5_CONST ADMIN"][0]
    assert const["occupied"] is True
    assert [n for n in t if n["name"] == "0_PROJ-MGMNT"][0]["occupied"] is False
    print("jdrive_tree self-check: OK")
