"""
One-time derivation of the Monte Carlo EAC Forecast fixture family.

Every number this writes comes from the contract document
(research_fixtures/production_contract/monte_carlo_eac_forecast/contract.json), transcribed
into closed-form arithmetic here. Nothing in this file imports, calls or reads the production
module. The output CSVs are frozen literals; the suite compares production against them.
"""
import csv, hashlib, json, math, pathlib

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = HERE / "research_fixtures" / "production_contract" / "monte_carlo_eac_forecast"

# case_id, bac, cpi, spi, doc, character
CASES = [
    ("MC-01-deterministic-collapse", 1_000_000.0, 1.00, 1.00, 0.00, "deterministic collapse"),
    ("MC-02-single-sampled-cpi",     1_000_000.0, 0.90, 1.00, 0.00, "single sampled cost index"),
    ("MC-03-cpi-driven",             2_400_000.0, 0.80, 1.00, 0.00, "cost index driven"),
    ("MC-04-cpi-and-spi-driven",     2_400_000.0, 0.90, 0.90, 0.00, "cost and schedule index driven"),
    ("MC-05-stable-performance",       750_000.0, 1.00, 1.00, 0.20, "stable performance, document risk only"),
    ("MC-06-deteriorating",          5_000_000.0, 0.70, 0.75, 0.60, "deteriorating performance"),
    ("MC-07-strong-performance",     1_250_000.0, 1.15, 1.10, 0.00, "strong performance, spread clamped at zero"),
    ("MC-08-spread-upper-region",      900_000.0, 0.10, 0.10, 1.00, "spread clamped at one"),
    ("MC-09-small-budget",              12_500.0, 0.95, 0.98, 0.05, "small budget"),
    ("MC-10-doc-risk-clamped",       1_000_000.0, 1.00, 1.00, 1.00, "document risk at the top of its domain"),
]

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

rows, truth = [], []
for cid, bac, cpi, spi, doc, character in CASES:
    m_eac = bac / cpi
    s = clamp(0.5 * (1 - cpi) + 0.3 * (1 - spi) + 0.2 * clamp(doc, 0, 1), 0, 1)
    o = m_eac * (1 - 0.10 * s)
    m = m_eac
    p = m_eac * (1 + 0.40 * s)
    degenerate = (p - o) < 1e-9
    if degenerate:
        alpha = beta = float("nan")
    else:
        alpha = 1 + 4 * (m - o) / (p - o)
        beta = 1 + 4 * (p - m) / (p - o)
    analytic_mean = m_eac * (1 + 0.05 * s)
    analytic_sd = math.sqrt(0.0075) * s * m_eac
    rows.append(dict(case_id=cid, character=character, bac=repr(bac), cpi=repr(cpi),
                     spi=repr(spi), doc_risk_score=repr(doc), iterations=5000,
                     seed=12345, data_origin="SYNTHETIC_RESEARCH_FIXTURE",
                     not_for_empirical_validation="true"))
    truth.append(dict(case_id=cid, m_eac=repr(m_eac), spread_driver=repr(s),
                      optimistic=repr(o), most_likely=repr(m), pessimistic=repr(p),
                      pert_lambda=4, alpha=repr(alpha), beta=repr(beta),
                      degenerate="true" if degenerate else "false",
                      analytic_mean=repr(analytic_mean), analytic_sd=repr(analytic_sd),
                      deterministic_p50=repr(m_eac) if degenerate else "",
                      deterministic_p80=repr(m_eac) if degenerate else ""))

def write(name, data):
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(data[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(data)
    return path

paths = [write("known_answer_cases.csv", rows), write("known_answer_ground_truth.csv", truth)]
paths.append(OUT / "contract.json")
digest = OUT / "CHECKSUMS.sha256"
lines = []
for p in sorted(paths, key=lambda x: x.name):
    lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n")
digest.write_text("".join(lines), encoding="utf-8")
print("wrote", len(rows), "cases")
