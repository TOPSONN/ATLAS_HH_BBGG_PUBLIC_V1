"""Explicit independent DATA-derived-cache audit; never a CTest physical read.

Usage: python -B tests/audit_phase5c_sidebands.py REPO OUTPUT_DIRECTORY NEW_JSON
Reuses the independent rational/Decimal reference functions from the synthetic
contract tests, not the C++ implementation. Does not modify any scientific input.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import runpy
import sys


def main():
    if not __debug__:
        raise RuntimeError("Independent assertions require normal Python execution")
    repo=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();destination=Path(sys.argv[3]).resolve()
    if destination.exists():raise FileExistsError("Audit JSON must be new")
    original=sys.argv[:]
    sys.argv=[str(repo/"tests/test_phase5c_sidebands.py"),"unused",str(repo/"metadata/phase3_selection_config.ini"),str(repo/"metadata/phase5c_sideband_protocol.json")]
    try:reference=runpy.run_path(str(repo/"tests/test_phase5c_sidebands.py"))
    finally:sys.argv=original
    source=repo/"outputs/phase4_numerical_v2_20261012/DATA93915/phase2/events.csv"
    selection=repo/"metadata/phase3_selection_config.ini";protocol=repo/"metadata/phase5c_sideband_protocol.json"
    tracked=[source,selection,protocol]+sorted(out.iterdir())
    hashes={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
    assert hashes[str(source.relative_to(repo))]=="c242e256d76d6832031b2e4b2dfeeb342b5b05885c2a6bdf53d2d5eab71201c7"
    assert hashes[str(selection.relative_to(repo))]=="77d57cd6fa204aad5a24031ac925c4e20e121b8aee35148cc29b522b39cf5751"
    assert hashes[str(protocol.relative_to(repo))]==reference["EXPECTED_PROTOCOL"]
    summary=json.loads((out/"summary.json").read_text())
    def read(path):
        with path.open(newline="") as f:return list(csv.DictReader(f))
    raw=read(source);events=read(out/"sideband_events.csv");audit=read(out/"sideband_audit.csv");hist=read(out/"root_mass_counts.csv")
    cfg=dict(line.split("=",1) for line in selection.read_text().splitlines() if line and not line.startswith("#"))
    assert list(raw[0])==reference["HEADER"]
    unique=set();expected=[];valid=c5=jets=c9=central=outside=0
    for entry,r in enumerate(raw,100):
        assert int(r["entry"])==entry
        identity=(int(r["run"]),int(r["event"]));assert identity not in unique;unique.add(identity)
        if r["valid"]!="1":continue
        valid+=1
        if int(r["photon_n"])<2:continue
        eta=[float(r[f"photon{i}_eta"]) for i in (1,2)]
        photon=(float(r["photon1_pt"])>float(cfg["photon_leading_pt_min_gev"]) and
                float(r["photon2_pt"])>float(cfg["photon_subleading_pt_min_gev"]) and
                all(abs(e)<float(cfg["photon_abs_eta_max"]) and not float(cfg["photon_crack_low"])<abs(e)<float(cfg["photon_crack_high"]) for e in eta))
        if not photon:continue
        c5+=1
        accepted_jets=int(r["jet_n"])>=2 and all(float(r[f"jet{i}_pt"])>float(cfg["jet_pt_min_gev"]) and abs(float(r[f"jet{i}_eta"]))<float(cfg["jet_abs_eta_max"]) for i in (1,2))
        if not accepted_jets:continue
        jets+=1;m=float(r["m_gg"]);d=float(r["deltaEta_gg"])
        if not 105<=m<=160:outside+=1;continue
        c9+=1
        if 120<=m<130:central+=1;continue
        categories=[i for i,(lo,hi) in enumerate(reference["BINS"]) if lo<=m<hi or (i==8 and m==160)]
        assert len(categories)==1
        h=reference["digest"](*identity);fold=int(h[:2],16)&1
        expected.append((entry,*identity,m,d,abs(d),categories[0],"A" if abs(d)<1 else "B","LOWER" if m<120 else "UPPER",fold,"CALIBRATION" if fold==0 else "VALIDATION",h))
    assert len(raw)==63095 and valid==63058 and c5==51136 and jets==9037 and c9==1689 and central==315 and outside==7348
    assert len(expected)==len(events)==1374
    for e,x in zip(events,expected):
        actual=(int(e["entry"]),int(e["run"]),int(e["event"]),float(e["m_gg"]),float(e["deltaEta_gg"]),float(e["abs_deltaEta_gg"]),int(e["mass_category"]),e["baseline_partition"],e["sideband"],int(e["fold"]),e["role"],e["identity_sha256"])
        assert actual==x and e["scope"]=="RETROSPECTIVE_DATA_ONLY_DESCRIPTIVE"
    assert summary["fold_identity_intersection"]==0
    folds=[{(e["run"],e["event"]) for e in events if int(e["fold"])==f} for f in (0,1)]
    assert not folds[0]&folds[1] and len(folds[0])==724 and len(folds[1])==650
    for key,value in (("entries",len(raw)),("cache_valid",valid),("C5",c5),("C5_plus_jets",jets),("C9",c9),("outside_study_domain",outside),("central_window_rows_excluded_from_statistics",central),("sideband_entries",len(events))):assert summary[key]==value
    maxima={"ks":0.,"cramers_v":0.,"correlations":0.,"shape_fraction":0.,"shape_covariance":0.,"wilson":0.}
    checked={k:0 for k in maxima};z=1.959963984540054
    cache={}
    def subset(pop,partition,split,low,high):
        key=(pop,partition,split,low,high)
        if key not in cache:cache[key]=reference["selected"](events,pop,partition,split,low,high)
        return cache[key]
    for r in audit:
        name=r["diagnostic"];pop=r["population"];partition=r["partition"];split=float(r["split_abs_delta_eta"]);low=float(r["mass_low"]);high=float(r["mass_high"])
        assert r["scope"]=="RETROSPECTIVE_DATA_ONLY_DESCRIPTIVE"
        if name in ("empirical_ks_mass_A_vs_B","cramers_v_mass_category_partition"):
            a=subset(pop,"A",split,low,high);b=subset(pop,"B",split,low,high)
            assert int(r["n"])==len(a) and int(r["n_other"])==len(b)
            if name.startswith("empirical"):
                expected_value=reference["ks"]([float(e["m_gg"]) for e in a],[float(e["m_gg"]) for e in b]);kind="ks"
            else:
                c=[[sum(int(e["mass_category"])==i for e in points) for i in range(9)] for points in (a,b)]
                expected_value=reference["cramers"](*c);kind="cramers_v"
        elif name=="empirical_ks_mass_fold0_vs_fold1":
            a=subset("FOLD0",partition,split,low,high);b=subset("FOLD1",partition,split,low,high)
            assert int(r["n"])==len(a) and int(r["n_other"])==len(b)
            expected_value=reference["ks"]([float(e["m_gg"]) for e in a],[float(e["m_gg"]) for e in b]);kind="ks"
        elif name in ("pearson_mass_absDeltaEta","spearman_mass_absDeltaEta"):
            p=subset(pop,partition,split,low,high);assert int(r["n"])==len(p)
            x=[float(e["m_gg"]) for e in p];y=[float(e["abs_deltaEta_gg"]) for e in p]
            if name.startswith("spearman"):x=reference["ranks"](x);y=reference["ranks"](y)
            expected_value=reference["pearson"](x,y);kind="correlations"
        elif name in ("conditional_mass_fraction","conditional_multinomial_covariance"):
            p=subset(pop,partition,split,105,160);n=len(p);i=int(r["category"]);j=int(r["other_category"])
            count=[sum(int(e["mass_category"])==bin_id for e in p) for bin_id in range(9)];assert int(r["n"])==n
            if name=="conditional_mass_fraction":expected_value=count[i]/n if n else None;kind="shape_fraction"
            else:expected_value=((count[i]/n if i==j else 0)-count[i]*count[j]/(n*n))/n if n else None;kind="shape_covariance"
        elif name=="mass_conditional_A_fraction_Wilson95":
            p=[e for e in subset(pop,"ALL",split,105,160) if int(e["mass_category"])==int(r["category"])];n=len(p);a=sum(float(e["abs_deltaEta_gg"])<split for e in p);assert int(r["n"])==n
            if n:
                fraction=a/n;den=1+z*z/n;centre=(fraction+z*z/(2*n))/den;half=z*math.sqrt(fraction*(1-fraction)/n+z*z/(4*n*n))/den
                error=max(abs(float(r["interval_low"])-max(0,centre-half)),abs(float(r["interval_high"])-min(1,centre+half)))
                maxima["wilson"]=max(maxima["wilson"],error);checked["wilson"]+=1;assert error<1e-14
            continue
        else:continue
        if expected_value is None:assert r["state"]=="UNDEFINED" and r["value"]==""
        else:
            error=abs(float(r["value"])-float(expected_value));maxima[kind]=max(maxima[kind],error);checked[kind]+=1;assert error<1e-14,(name,pop,error)
    for partition in ("A","B"):
        p=[e for e in events if e["baseline_partition"]==partition]
        h=[r for r in hist if r["partition"]==partition];assert len(h)==13
        for r in h:
            bin_id=int(r["root_bin"])
            count=sum((float(e["m_gg"])<105 if bin_id==0 else float(e["m_gg"])>=160 if bin_id==12 else 105+5*(bin_id-1)<=float(e["m_gg"])<105+5*bin_id) for e in p)
            assert float(r["raw_count"])==count and abs(float(r["sumw2"])-count)<1e-12
    assert len(audit)==summary["audit_rows"]==1962
    assert hashes=={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
    result={"status":"PASS_INDEPENDENT_RAW_CACHE_IDENTITY_AND_ARITHMETIC_AUDIT","scope":"RETROSPECTIVE_DATA_ONLY_DESCRIPTIVE_NO_PHYSICAL_TF_OR_FIT","input_events":len(raw),"sideband_events":len(events),"identity_overlap":0,"fold0":724,"fold1":650,"audit_rows":len(audit),"reference_cells_checked":checked,"maximum_absolute_reference_residuals":maxima,"file_sha256":hashes,"native_ROOT_event_reads":0,"pvalues":False,"physical_closure":False}
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("x",encoding="utf-8",newline="\n") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps({k:result[k] for k in ("status","input_events","sideband_events","reference_cells_checked","maximum_absolute_reference_residuals")},sort_keys=True))


if __name__=="__main__":main()
