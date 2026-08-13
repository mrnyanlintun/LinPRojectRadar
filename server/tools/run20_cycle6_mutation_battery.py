import subprocess, shutil, os, re, sys
L='app/simulation/lineage.py'; F='app/simulation/fusion.py'
orig={p:open(p).read() for p in (L,F)}
SUITES=['test_run20_primitive_lineage.py','test_run20_lineage_model.py',
        'test_run20_lineage_declaration_truth.py','test_run20_advisory_lineage_disclosure.py',
        'test_run20_voting_lineage.py','test_run20_lineage_reproduction.py']

MUTS=[
 ('M1 restore transitive closure over the selected bodies', L,
  '''    selected = sorted(best, key=lambda i: (records[i]["module_id"], i))''',
  '''    selected = sorted(best, key=lambda i: (records[i]["module_id"], i))
    selected = selected[:1] if len(records) > 1 else selected'''),
 ('M2 merge A and C whenever a bridging signal touches both', L,
  '''    if prim_a & prim_b:
        return True''',
  '''    if prim_a & prim_b:
        return True
    if prim_a and prim_b:
        return True'''),
 ('M3 count the bridging signal as its own independent body', L,
  '''        for slot, rep in enumerate(selected):
            if dep[i][rep]:
                bodies[slot].append(i)
                break''',
  '''        for slot, rep in enumerate(selected):
            if False and dep[i][rep]:
                bodies[slot].append(i)
                break'''),
 ('M4 strip primitive_source_ids from the lineage record', L,
  '''        "primitive_source_ids": prim,\n''', ''),
 ('M5 strip parent_signal_ids from the lineage record', L,
  '''        "parent_signal_ids": tuple(sorted(set(parent_signal_ids))),\n''', ''),
 ('M6 promote derived evidence to a primitive source of its own', L,
  '''                if j is not None and not prim[j] <= prim[i]:''',
  '''                if False and j is not None and not prim[j] <= prim[i]:'''),
 ('M7 revert A1.3 to the false reporting-history declaration', L,
  '''        "A1.3", source_fact_ids=("ac", "bac", "ev"),
        lineage_group_ids=(EARNED_VALUE_BODY,),''',
  '''        "A1.3", source_fact_ids=("ev", "pv", "reporting_history"),
        lineage_group_ids=(EARNED_VALUE_BODY, REPORTING_HISTORY_BODY),'''),
 ('M8 revert A1.5 to the false planned-value declaration', L,
  '''        "A1.5", source_fact_ids=("ac", "ev", "reporting_history"),''',
  '''        "A1.5", source_fact_ids=("ev", "pv", "reporting_history"),'''),
 ('M9 revert the synthesis declaration to the unreachable audit id', L,
  '''    "D1.5": lineage_record(  # Anomaly Score, a mean over portfolio-outlier constituents
        "D1.5", source_fact_ids=(),
        dependency_ids=("D1.2",),''',
  '''    "PH.5": lineage_record(
        "PH.5", source_fact_ids=(),
        dependency_ids=("A1.7", "A1.8"),'''),
 ('M10 revert A3.5 into the earned-value body (cycle 5 regression)', L,
  '''        lineage_group_ids=(INDIRECT_COST_BODY,),''',
  '''        lineage_group_ids=(EARNED_VALUE_BODY,),'''),
 ('M11 admit quality metadata as project-condition evidence', L,
  '''NON_PROJECT_EVIDENCE: frozenset[str] = frozenset({
    QUALITY_METADATA, GOVERNANCE_OUTPUT, DECISION_OUTPUT,
})''',
  '''NON_PROJECT_EVIDENCE: frozenset[str] = frozenset({
    GOVERNANCE_OUTPUT, DECISION_OUTPUT,
})'''),
 ('M12 admit decision output as project-condition evidence', L,
  '''NON_PROJECT_EVIDENCE: frozenset[str] = frozenset({
    QUALITY_METADATA, GOVERNANCE_OUTPUT, DECISION_OUTPUT,
})''',
  '''NON_PROJECT_EVIDENCE: frozenset[str] = frozenset({
    QUALITY_METADATA, GOVERNANCE_OUTPUT,
})'''),
 ('M13 replace the exact selection with a greedy pass in arrival order', L,
  '''        search(0, [], frozenset())''',
  '''        c_best = []
        for _i in range(n):
            if all(not dep[_i][_j] for _j in c_best):
                c_best.append(_i)
        c_best_key = tuple(sorted(records[i]["module_id"] for i in c_best))'''),
 ('M13b greedy pass in reverse arrival order', L,
  '''        search(0, [], frozenset())''',
  '''        c_best = []
        for _i in reversed(range(n)):
            if all(not dep[_i][_j] for _j in c_best):
                c_best.append(_i)
        c_best_key = tuple(sorted(records[i]["module_id"] for i in c_best))'''),
 ('M19 return the connected components themselves as the bodies (the closure by another name)', L,
  '''        best.extend(c_best)''',
  '''        best.extend(c_best[:1])'''),
 ('M14 absorb a bridging signal into EVERY body it touches', L,
  '''                bodies[slot].append(i)
                break''',
  '''                bodies[slot].append(i)'''),
 ('M15 ignore declared lineage group ids in the dependence predicate', L,
  '''    if set(a["lineage_group_ids"]) & set(b["lineage_group_ids"]):
        return True
    if (b["module_id"] in a["dependency_ids"]''',
  '''    if False:
        return True
    if (b["module_id"] in a["dependency_ids"]'''),
 ('M16 give an undeclared primitive set the empty set instead of the facts', L,
  '''    prim = (tuple(sorted(set(primitive_source_ids))) if primitive_source_ids is not None
            else tuple(sorted(set(facts) | set(docs))))''',
  '''    prim = tuple(sorted(set(primitive_source_ids or ())))'''),
 ('M17 apply Dempster within a body instead of the idempotent reading', F,
  '''        rep = worst_band(bands_in)''',
  '''        rep = bands_in[0]'''),
 ('M18 stop reporting whether the separation was solved exactly', F,
  '''        "body_selection_exact": separation["selection_exact"],\n''', ''),
]

results=[]
for name, path, old, new in MUTS:
    src=orig[path]
    if old not in src:
        results.append((name,'NOT-APPLIED','old text absent')); continue
    mutated=src.replace(old,new,1)
    if mutated==src:
        results.append((name,'NO-BYTES-CHANGED','')); continue
    open(path,'w').write(mutated)
    caught=[]
    try:
        for s in SUITES:
            r=subprocess.run([sys.executable,s],cwd='tools',capture_output=True,text=True,
                             env={**os.environ,'PYTHONIOENCODING':'utf-8'})
            out=r.stdout+r.stderr
            ok = r.returncode==0 and re.search(r'^RESULT: (\d+)/\1( checks passed)?$',out,re.M)
            if not ok:
                first=[l.strip(' -') for l in out.splitlines() if l.strip().startswith('- ')]
                caught.append((s, first[0][:110] if first else out.strip().splitlines()[-1][:110]))
    finally:
        open(path,'w').write(src)
    results.append((name,'CAUGHT' if caught else 'SURVIVED',
                    caught[0][0]+' :: '+caught[0][1] if caught else ''))
for n,st,d in results:
    print(f'{st:16} | {n}\n                 | {d}')
print('SURVIVORS:',sum(1 for _,s,_ in results if s!='CAUGHT'))
