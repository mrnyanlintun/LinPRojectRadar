"""RUN 132. Actual cost is what the work cost; a figure net of retainage is not.

A pay application (G702) states amount_paid_to_date -- completed-to-date LESS RETAINAGE. Until
Run 132 that figure was emitted to the ``ac`` signal key AND ranked above the monthly report's
stated actual_cost by a WRITER_TIERS entry that carried no recorded reason. On PRJ-002 period 1
that made CPI read 1.111 (under cost) where the stated actual cost gives 0.955 (over), which
moved A1 Cost and EVM Performance from Yellow to Green. Every project in the corpus files a pay
application, so the defect was systematic.

Run as a script with cwd = server/. No model call, no database: select_signal_inputs is pure.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.extraction_merge import assemble_signal_inputs
from app.field_registry import WRITER_TIERS
from app.simulation.models_evm import check_inputs


def doc(sha, dt, ex):
    return {"sha256": sha, "doc_type": dt, "filename": sha + ".pdf", "extraction": ex}


# PRJ-002 period 1, as the documents state it.
MONTHLY_REPORT = doc("mr1", "monthly_report", {
    "actual_cost": 1900000, "earned_value": 1815000, "planned_value": 1900000,
    "actual_percent_complete": 60.5, "planned_percent_complete": 63.3,
    "budget_at_completion": 3000000, "report_period": "2025-01-31"})
PAY_APPLICATION = doc("pa1", "pay_application", {
    "amount_paid_to_date": 1633500,      # = 1,815,000 less ten per cent retainage
    "completed_to_date": 1815000, "percent_complete_verified": 60.5,
    "original_contract_sum": 3000000,
    "original_contingency": 150000, "remaining_contingency": 90000,
    "period_to_date": "2025-01-31"})

# Every other figure on the path, which this change must leave exactly alone.
UNMOVED = ("ev", "pv", "bac", "baselineContractSum", "actualPctComplete",
           "plannedPctComplete", "originalContingency", "remainingContingency", "spi")
UNMOVED_BOTH = {"ev": 1815000, "pv": 1900000, "bac": 3000000,
                "baselineContractSum": None, "actualPctComplete": 60.5,
                "plannedPctComplete": 63.3, "originalContingency": 150000,
                "remainingContingency": 90000, "spi": 0.955}
UNMOVED_PAY_ONLY = {"ev": 1815000, "pv": None, "bac": 3000000,
                    "baselineContractSum": None, "actualPctComplete": 60.5,
                    "plannedPctComplete": None, "originalContingency": 150000,
                    "remainingContingency": 90000, "spi": None}

ok = fail = 0


def check(label, got, want):
    global ok, fail
    if got == want:
        ok += 1
        print(f"  PASS  {label}: {got!r}")
    else:
        fail += 1
        print(f"  FAIL  {label}: got {got!r}, expected {want!r}")


print("1. Both documents present -- the stated actual cost must win.")
both = assemble_signal_inputs([MONTHLY_REPORT, PAY_APPLICATION])
check("ac", both["ac"], 1900000)
check("ac source docType", (both["sources"] or {}).get("ac", {}).get("docType"),
      "monthly_report")
check("cpi", both["cpi"], 0.955)
check("ac is NOT the retainage-net figure", both["ac"] == 1633500, False)

print("2. Pay application only -- ac is absent and the EVM modules abstain.")
pay_only = assemble_signal_inputs([PAY_APPLICATION])
check("ac", pay_only["ac"], None)
check("no ac source entry", "ac" in (pay_only["sources"] or {}), False)
check("cpi", pay_only["cpi"], None)
check("check_inputs(bac, ev, ac)", check_inputs(pay_only, ("bac", "ev", "ac")), False)
check("check_inputs(ac)", check_inputs(pay_only, ("ac",)), False)

print("3. The pay application emits no ac under any arrangement of the evidence.")
for label, docs in (("reversed", [PAY_APPLICATION, MONTHLY_REPORT]),
                    ("pay app twice", [PAY_APPLICATION, PAY_APPLICATION])):
    got = assemble_signal_inputs(docs)
    src = (got["sources"] or {}).get("ac", {}).get("docType")
    check(f"{label}: ac never sourced from pay_application", src == "pay_application", False)

print("4. ac has no writer tier, and must not regain one.")
check("WRITER_TIERS has no 'ac' entry", "ac" in WRITER_TIERS, False)
print("   actualPctComplete KEEPS its pay-application preference deliberately: "
      "percent_complete_verified is certified before retainage is withheld, so it is the "
      "same quantity as actual_percent_complete, independently verified.")
check("actualPctComplete tiers", WRITER_TIERS.get("actualPctComplete"),
      {"pay_application": 0, "monthly_report": 1})

print("5. Nothing else on the path moved.")
for field, want in UNMOVED_BOTH.items():
    check(f"both/{field}", both[field], want)
for field, want in UNMOVED_PAY_ONLY.items():
    check(f"pay-only/{field}", pay_only[field], want)

print(f"\n{ok} passed, {fail} failed")
raise SystemExit(1 if fail else 0)
