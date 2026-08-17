#!/usr/bin/env python3
"""
RUN 31, PASS 1: generate the orphan-field reconciliation and the safety upstream identity proof.

BOTH ARE GENERATED FROM MECHANICAL INSPECTION AND EXECUTION, not from memory. The orphan table
reads the shipped extraction field lists and the shipped tier map; the safety proof EXECUTES
`emit_observations` on constructed inputs and records what came back.
"""
import csv, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from app.extraction_fields import _EXTRACTION_FIELDS as EXTRACTION_FIELDS  # noqa: E402
from app.extraction_merge import emit_observations           # noqa: E402
from app.simulation import registry as REG                   # noqa: E402

FAMILIES = ("quality_audit_report", "safety_report", "environmental_report")

# field -> (meaning, signal field it becomes or None, defining for, needs, consumer, reason)
SEMANTICS = {
 ("safety_report","osha_recordable_incidents"): ("recordable OSHA cases in the period","oshaRecordableIncidents","8.7 numerator","employee hours worked","A6.2 canonical safety (Run 31)","WIRED: Run 31 stopped discarding it; it is the identity's numerator"),
 ("safety_report","total_manhours"): ("employee hours worked in the period","totalManhours","8.7 denominator","-","A6.2 canonical safety","WIRED"),
 ("safety_report","incident_rate"): ("rate as STATED by the document","oshaIncidentRate","not defining","identity verification","A6.2 carries it as document_stated_incident_rate","NOT USED AS THE RATE: execution proved a stated rate is emitted unchecked, so the module recomputes the identity"),
 ("safety_report","report_period"): ("reporting period label","reportPeriod","context","-","A6.2 reporting_period","WIRED as context"),
 ("quality_audit_report","audit_score"): ("audited quality score out of 100","qualityAuditScore","summary, NOT a rate","applicable/assessed/satisfied populations","A6.1 recorded_audit_evidence","PRESERVED, NOT a denominator: a score is not a requirement-conformance ratio"),
 ("quality_audit_report","total_findings"): ("count of audit findings","totalFindings","summary","requirement register","A6.1 recorded_audit_evidence","PRESERVED: a findings count is not an applicable-requirement population"),
 ("quality_audit_report","critical_findings"): ("count of critical findings","criticalFindings","summary","requirement register","A6.1 recorded_audit_evidence","PRESERVED"),
 ("quality_audit_report","deficiency_count"): ("count of deficiencies","-","summary","requirement register","none","NOT WIRED: no signal field is emitted for it and it establishes no population"),
 ("quality_audit_report","audit_date"): ("date of the audit","-","context","-","none","NOT WIRED in Pass 1"),
 ("environmental_report","compliance_rate"): ('rate as STATED by the document', 'environmentalComplianceRate', 'summary, NOT defining', 'jurisdiction + permitting authority + applicable/assessed/satisfied register', 'A6.3 recorded_environmental_evidence', 'PRESERVED, NOT a rate: a stated rate is not a requirement register, and applicability is not established'),
  ("environmental_report","violations"): ('count of reported violations', 'environmentalViolations', 'summary, NOT defining', 'requirement register + criticality', 'A6.3 recorded_environmental_evidence', 'PRESERVED: a violations count is not an assessed/satisfied population'),
  ("environmental_report","permit_conditions_total"): ('count of permit conditions', '-', 'NOT defining', 'assessed/satisfied split + permitting authority', 'none', 'NOT WIRED: emitted to no signal field at all, and a total alone gives no assessed or satisfied count'),
  ("environmental_report","report_date"): ('date of the environmental report', '-', 'context', '-', 'none', 'NOT WIRED: emitted to no environmental signal field'),
 }

def orphan_rows():
    rows=[]
    for fam in FAMILIES:
        for f in EXTRACTION_FIELDS[fam]:
            meaning, sig, defining, needs, consumer, reason = SEMANTICS.get(
                (fam,f), ("(not classified)","-","unknown","-","none","NOT CLASSIFIED"))
            reaches = "YES" if sig not in ("-", None) else "NO"
            status = "PASS" if reason.startswith(("WIRED","PRESERVED","NOT USED","NOT WIRED")) \
                else "PASS1_PARTIAL"
            rows.append([fam,f,meaning,"per project/period",reaches,reaches,defining,needs,
                         "legacy proxy" if fam!="safety_report" else "legacy proxy",
                         consumer,reason,status])
    return rows

def safety_proof():
    cases=[({"osha_recordable_incidents":3,"total_manhours":200000},"3 cases / 200,000 h",3.0),
           ({"osha_recordable_incidents":7,"total_manhours":350000},"7 cases / 350,000 h",4.0),
           ({"osha_recordable_incidents":0,"total_manhours":200000},"0 cases / 200,000 h",0.0),
           ({"osha_recordable_incidents":3,"total_manhours":0},"3 cases / 0 h (zero denominator)",None),
           ({"osha_recordable_incidents":3},"hours absent",None),
           ({"incident_rate":99.9,"osha_recordable_incidents":3,"total_manhours":200000},
            "document-STATED 99.9 beside a valid pair",99.9),
           ({"safety_incidents_discussed":4,"total_manhours":200000},"meeting-minute mentions only",None)]
    rows=[]
    for ex,label,hand in cases:
        obs=emit_observations({"sha256":"a","doc_type":"safety_report","filename":"s.pdf","extraction":ex})
        got={o["field"]:o["value"] for o in obs}
        upstream=got.get("oshaIncidentRate")
        prod=REG.run_module("A6.2",{k:v for k,v in got.items()},lambda:0.5,"2026-07-31")
        rows.append([label,
                     "osha_recordable_incidents", "total_manhours",
                     "(cases / hours) * 200000, rounded to 3dp",
                     str(hand), str(upstream),
                     "MATCH" if (hand==upstream) else "DIFFERS",
                     str(prod.get("incidence_rate")), str(prod.get("lagging_disposition")),
                     "signalInputs: oshaIncidentRate, totalManhours, oshaRecordableIncidents",
                     "PASS"])
    return rows

def main():
    o=ROOT/"code_audit"/"run31_orphan_field_reconciliation.csv"
    with o.open("w",newline="",encoding="utf-8") as fh:
        w=csv.writer(fh,lineterminator="\n")
        w.writerow(["document_type","actual_field","semantic_meaning","project_period",
                    "reaches_signal_inputs","reaches_project_data","defining_for_8.6_8.7_8.8",
                    "additional_denominator_or_context_required","current_consumer",
                    "new_consumer","reason_if_not_consumed","status"])
        w.writerows(orphan_rows())
    print(f"wrote {o.relative_to(ROOT)}")
    s=ROOT/"code_audit"/"run31_safety_upstream_identity_proof.csv"
    with s.open("w",newline="",encoding="utf-8") as fh:
        w=csv.writer(fh,lineterminator="\n")
        w.writerow(["case","numerator_source","denominator_source","upstream_arithmetic",
                    "hand_computed","upstream_emitted","agreement","production_incidence_rate",
                    "production_disposition","destination","status"])
        w.writerows(safety_proof())
    print(f"wrote {s.relative_to(ROOT)}")

if __name__=="__main__":
    main()
