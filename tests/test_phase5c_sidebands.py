"""Independent synthetic-cache contracts; no physical ROOT reads or model fits."""
import csv
import hashlib
import io
import json
import math
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

EXECUTABLE=Path(sys.argv[1]).resolve()
SELECTION=Path(sys.argv[2]).resolve()
PROTOCOL=Path(sys.argv[3]).resolve()
sys.argv=[sys.argv[0]]
EXPECTED_PROTOCOL="e9916da8772902c5464ea141397340a5230cb1733bb05e7c86800d9681295f66"
HEADER="entry,run,event,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,deltaEta_gg,deltaPhi_gg,deltaEta_jj,deltaPhi_jj,p1_tight_id,p2_tight_id,p1_tight_iso,p2_tight_iso,roundoff_objects,issue".split(",")
BINS=[(105,110),(110,115),(115,120),(130,135),(135,140),(140,145),(145,150),(150,155),(155,160)]
INVOCATIONS={"accepted":0,"rejected":0}


def row(i,mass,deta,run=276336,event=None):
    return dict(entry=str(100+i),run=str(run),event=str(9000+i if event is None else event),valid="1",photon_n="2",jet_n="2",
                photon1_pt="50",photon2_pt="30",photon1_eta=str(deta/2),photon2_eta=str(-deta/2),
                jet1_pt="45",jet2_pt="35",jet1_eta=".2",jet2_eta="-.2",m_gg=str(mass),m_jj="90",
                deltaR_gg="2",deltaR_jj="2.5",deltaEta_gg=str(deta),deltaPhi_gg="1.5",deltaEta_jj=".4",deltaPhi_jj="2",
                p1_tight_id="0",p2_tight_id="0",p1_tight_iso="0",p2_tight_iso="0",roundoff_objects="0",issue="")


def fixtures():
    data=[]
    for low,_ in BINS:
        for offset,deta in ((.25,.3),(.25,-.6),(1.25,.8),(2.25,-.5),(.25,1),(1.25,-1.2),(2.25,1.5),(3.25,-1.8)):
            data.append(row(len(data),low+offset,deta))
    for mass,deta in ((104.99,.5),(105,.8),(120,.4),(125,1.5),(129.999,.8),(130,1.2),(160,.5),(160.01,.8)):
        data.append(row(len(data),mass,deta))
    return data


def serialize(rows,header=HEADER):
    return ",".join(header)+"\n"+"".join(",".join(str(r.get(k,"")) for k in header)+"\n" for r in rows)


def digest(run,event):
    canonical=f"ATLAS_HH_BBGG_PUBLIC_V1|DATA93915|run={int(run)}|event={int(event)}"
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def ranks(v):
    return [Fraction(2+2*sum(b<a for b in v)+sum(b==a for b in v)-1,2) for a in v]


def pearson(x,y):
    with localcontext() as c:
        c.prec=70
        def decimal(v):
            return Decimal(v.numerator)/Decimal(v.denominator) if isinstance(v,Fraction) else Decimal(str(v))
        x=list(map(decimal,x));y=list(map(decimal,y));mx=sum(x)/len(x);my=sum(y)/len(y)
        xx=sum((v-mx)**2 for v in x);yy=sum((v-my)**2 for v in y)
        if len(x)<2 or xx==0 or yy==0:return None
        return float(sum((a-mx)*(b-my) for a,b in zip(x,y))/(xx*yy).sqrt())


def ks(a,b):
    if not a or not b:return None
    return max(abs(Fraction(sum(v<=x for v in a),len(a))-Fraction(sum(v<=x for v in b),len(b))) for x in set(a+b))


def cramers(a,b):
    na=sum(a);nb=sum(b);n=na+nb
    if not na or not nb or sum(x+y>0 for x,y in zip(a,b))<2:return None
    chi2=Fraction(0)
    for x,y in zip(a,b):
        if x+y:
            for observed,total in ((x,na),(y,nb)):
                expected=Fraction(total*(x+y),n);chi2+=(observed-expected)**2/expected
    return math.sqrt(float(chi2/n))


def selected(events,population,partition="ALL",split=1,low=105,high=160):
    fold=0 if population.startswith("FOLD0") else 1 if population.startswith("FOLD1") else None
    if population.startswith("FIXED_OUTER_TRIM_"):
        trim_low,trim_high=map(int,population.removeprefix("FIXED_OUTER_TRIM_").split("_"));low=max(low,trim_low);high=min(high,trim_high)
    return [e for e in events if (fold is None or int(e["fold"])==fold) and low<=float(e["m_gg"])<=high and
            (partition=="ALL" or (float(e["abs_deltaEta_gg"])<split)==(partition=="A"))]


class Contract(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(prefix="phase5c_sidebands_",dir=Path.cwd())
        self.addCleanup(self.directory.cleanup);self.base=Path(self.directory.name);self.case=0

    def run_case(self,rows=None,text=None,selection=None,protocol=None,start="100",end=None,units="PROVISIONAL",sample="SYNTHETIC",existing=False,ok=True):
        self.case+=1;rows=fixtures() if rows is None else rows
        cache=self.base/f"cache{self.case}.csv";cache.write_text(text if text is not None else serialize(rows),encoding="utf-8",newline="")
        output=self.base/f"out{self.case}";cfg=SELECTION;pr=PROTOCOL
        for value,name in ((selection,"selection"),(protocol,"protocol")):
            if value is None:continue
            target=value if isinstance(value,Path) else self.base/f"{name}{self.case}.txt"
            if not isinstance(value,Path):target.write_text(value,encoding="utf-8",newline="")
            if name=="selection":cfg=target
            else:pr=target
        hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (cache,cfg,pr)]
        if existing:output.mkdir();(output/"preserve.txt").write_text("user work")
        result=subprocess.run([str(EXECUTABLE),str(cache),str(cfg),str(pr),str(output),str(start),str(end or (100+len(rows))),units,sample],capture_output=True,text=True,timeout=30)
        self.assertEqual([hashlib.sha256(p.read_bytes()).hexdigest() for p in (cache,cfg,pr)],hashes)
        if not ok:
            INVOCATIONS["rejected"]+=1;self.assertNotEqual(result.returncode,0,"Malformed input accepted");self.assertIn("FAIL Phase5C sidebands",result.stderr)
            if existing:self.assertEqual((output/"preserve.txt").read_text(),"user work");self.assertEqual(len(list(output.iterdir())),1)
            else:self.assertFalse(output.exists(),"Invalid input left a scientific output")
            return
        INVOCATIONS["accepted"]+=1;self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual({p.name for p in output.iterdir()},{"summary.json","sideband_events.csv","sideband_audit.csv","root_mass_counts.csv"})
        files={p.name:p.read_bytes() for p in output.iterdir()};summary=json.loads(files["summary.json"])
        self.assertEqual(summary["input_cache_sha256"],hashes[0]);self.assertEqual(summary["selection_sha256"],hashes[1]);self.assertEqual(summary["protocol_sha256"],hashes[2]);self.assertEqual(hashes[2],EXPECTED_PROTOCOL)
        self.assertEqual(summary["scope"],"SYNTHETIC_DIAGNOSTIC_VALIDATION")
        for name in ("blinded_analysis","untouched_validation","pvalues_computed","independence_claimed","best_boundary_selected","calibration_fit_performed","source_ROOT_identity_verified_by_app","normalization_applied","scale_factors_applied","physical_transfer_factor_applied","background_prediction_performed","physical_closure_executed"):
            self.assertFalse(summary[name])
        for name in ("native_ROOT_event_reads","downloaded_bytes","figures_generated","fold_identity_intersection"):self.assertEqual(summary[name],0)
        for name in ("background_dominance","single_H_contamination"):self.assertEqual(summary[name],"UNKNOWN")
        for filename in ("sideband_events.csv","sideband_audit.csv","root_mass_counts.csv"):
            self.assertEqual(summary[filename.replace(".csv","_sha256")],hashlib.sha256(files[filename]).hexdigest())
        parse=lambda name:list(csv.DictReader(io.StringIO(files[name].decode())))
        return summary,parse("sideband_events.csv"),parse("sideband_audit.csv"),parse("root_mass_counts.csv"),files

    def test_protocol_and_exact_selection_are_frozen(self):
        self.assertEqual(hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),EXPECTED_PROTOCOL)
        self.run_case(protocol=PROTOCOL.read_text()+" ",ok=False)
        self.run_case(protocol=PROTOCOL.read_text().replace("0.8,1.0,1.2","0.9,1.0,1.1"),ok=False)
        self.run_case(selection=SELECTION.read_text().replace("jet_pt_min_gev=25","jet_pt_min_gev=26"),ok=False)
        self.run_case(selection=SELECTION.read_text().replace("\n","\r\n"),ok=False)

    def test_boundary_classification_and_preserved_c9(self):
        rows=[row(i,m,d) for i,(m,d) in enumerate(zip([104.99,105,110,119.999,120,125,129.999,130,140,145,155,160,160.01],[.5,.8,1,1.2,.5,1.5,.5,.4,-1,-1.2,.8,-.4,.5]))]
        summary,events,_,hist,_=self.run_case(rows)
        self.assertEqual(summary["C9"],11);self.assertEqual(summary["sideband_entries"],8);self.assertEqual(summary["outside_study_domain"],2)
        self.assertEqual([float(e["m_gg"]) for e in events],[105,110,119.999,130,140,145,155,160])
        self.assertEqual([int(e["mass_category"]) for e in events],[0,1,2,3,5,6,8,8]);self.assertEqual(events[-1]["baseline_partition"],"A")
        self.assertEqual(next(r for r in hist if r["partition"]=="A" and r["root_bin"]=="12")["raw_count"],"1")

    def test_canonical_sha256_identity_and_fold_disjoint_union(self):
        rows=fixtures();rows[0].update(run="4294967295",event="18446744073709551615")
        summary,events,_,_,_=self.run_case(rows)
        for e in events:
            d=digest(e["run"],e["event"]);self.assertEqual(e["identity_sha256"],d);self.assertEqual(int(e["fold"]),int(d[:2],16)&1)
            self.assertEqual(e["role"],"CALIBRATION" if int(e["fold"])==0 else "VALIDATION")
        folds=[{(e["run"],e["event"]) for e in events if int(e["fold"])==f} for f in (0,1)]
        self.assertFalse(folds[0]&folds[1]);self.assertEqual(len(folds[0]|folds[1]),len(events))
        self.assertEqual(summary["fold_union_entries"],len(events));self.assertEqual(summary["whole_cache_unique_identities"],len(rows))

    def test_identity_folds_do_not_depend_on_entry_mass_or_row_order(self):
        old=self.run_case();rows=fixtures()[::-1]
        for i,r in enumerate(rows):r["entry"]=str(100+i)
        new=self.run_case(rows)
        identity=lambda e:(e["run"],e["event"])
        self.assertEqual({identity(e):e["fold"] for e in old[1]},{identity(e):e["fold"] for e in new[1]})
        self.assertEqual(len(old[2]),len(new[2]));self.assertEqual(old[3],new[3])
        for a,b in zip(old[2],new[2]):
            for key in a:
                if key in ("value","interval_low","interval_high") and a[key] and b[key]:self.assertAlmostEqual(float(a[key]),float(b[key]),places=13)
                else:self.assertEqual(a[key],b[key])

    def test_every_central_perturbation_is_excluded_from_all_statistics(self):
        old=self.run_case();rows=fixtures()
        for r in rows:
            if 120<=float(r["m_gg"])<130:r.update(m_gg="127.9",photon1_eta=".7",photon2_eta="-.7",deltaEta_gg="1.4",event=str(int(r["event"])+100000))
        new=self.run_case(rows)
        for filename in ("sideband_events.csv","sideband_audit.csv","root_mass_counts.csv"):
            self.assertEqual(old[4][filename],new[4][filename],filename)
        self.assertEqual(old[0]["C9"],new[0]["C9"])

    def test_tied_ks_independent_exact_rational_reference(self):
        _,events,audit,_,_=self.run_case()
        for r in audit:
            if r["diagnostic"] not in ("empirical_ks_mass_A_vs_B","empirical_ks_mass_fold0_vs_fold1"):continue
            split=float(r["split_abs_delta_eta"])
            if r["diagnostic"].endswith("A_vs_B"):
                a=selected(events,r["population"],"A",split,float(r["mass_low"]),float(r["mass_high"]));b=selected(events,r["population"],"B",split,float(r["mass_low"]),float(r["mass_high"]))
            else:a=selected(events,"FOLD0",r["partition"],split);b=selected(events,"FOLD1",r["partition"],split)
            reference=ks([float(e["m_gg"]) for e in a],[float(e["m_gg"]) for e in b])
            self.assertEqual(int(r["n"]),len(a));self.assertEqual(int(r["n_other"]),len(b))
            if reference is None:self.assertEqual(r["state"],"UNDEFINED");self.assertFalse(r["value"])
            else:self.assertAlmostEqual(float(r["value"]),float(reference),places=14)

    def test_cramers_v_independent_rational_contingency(self):
        _,events,audit,_,_=self.run_case()
        for r in audit:
            if r["diagnostic"]!="cramers_v_mass_category_partition":continue
            samples=[selected(events,r["population"],p,float(r["split_abs_delta_eta"]),float(r["mass_low"]),float(r["mass_high"])) for p in ("A","B")]
            c=[[sum(int(e["mass_category"])==i for e in sample) for i in range(9)] for sample in samples]
            expected=cramers(*c)
            if expected is None:self.assertEqual(r["state"],"UNDEFINED")
            else:self.assertAlmostEqual(float(r["value"]),expected,places=13)

    def test_known_perfect_association_with_empty_columns_retained(self):
        data=[row(i,106 if i<10 else 141,.5 if i<10 else 1.5) for i in range(20)]
        _,_,audit,_,_=self.run_case(data)
        r=next(r for r in audit if r["diagnostic"]=="cramers_v_mass_category_partition" and r["population"]=="POOLED_SIDEBANDS" and float(r["split_abs_delta_eta"])==1)
        self.assertEqual(float(r["value"]),1)
        shapes=[r for r in audit if r["diagnostic"]=="conditional_mass_fraction" and r["population"]=="POOLED_SIDEBANDS" and r["partition"]=="ALL"]
        self.assertEqual(len(shapes),9);self.assertEqual(sum(float(r["value"])==0 for r in shapes),7)

    def test_full_multinomial_covariance_independent_reference_and_psd(self):
        _,events,audit,_,_=self.run_case()
        rng=random.Random(5021)
        for pop in ("POOLED_SIDEBANDS","FOLD0_CALIBRATION","FOLD1_VALIDATION"):
            for partition in ("ALL","A","B"):
                sample=selected(events,pop,partition);n=len(sample);counts=[sum(int(e["mass_category"])==i for e in sample) for i in range(9)]
                ps=[Fraction(c,n) for c in counts]
                matrix=[[None]*9 for _ in range(9)]
                rows=[r for r in audit if r["diagnostic"]=="conditional_multinomial_covariance" and r["population"]==pop and r["partition"]==partition]
                self.assertEqual(len(rows),81)
                for r in rows:
                    i=int(r["category"]);j=int(r["other_category"]);expected=((ps[i] if i==j else 0)-ps[i]*ps[j])/n
                    matrix[i][j]=float(r["value"]);self.assertAlmostEqual(matrix[i][j],float(expected),places=16)
                for i in range(9):self.assertAlmostEqual(sum(matrix[i]),0,places=16)
                for _ in range(25):
                    v=[rng.uniform(-3,3) for _ in range(9)];q=sum(v[i]*matrix[i][j]*v[j] for i in range(9) for j in range(9));self.assertGreaterEqual(q,-1e-15)
                shapes=[r for r in audit if r["diagnostic"]=="conditional_mass_fraction" and r["population"]==pop and r["partition"]==partition]
                self.assertEqual(len(shapes),9)
                for r in shapes:self.assertAlmostEqual(float(r["value"]),float(ps[int(r["category"])]),places=16)

    def test_pearson_and_tied_spearman_independent_decimal_reference(self):
        _,events,audit,_,_=self.run_case()
        for r in audit:
            if r["diagnostic"] not in ("pearson_mass_absDeltaEta","spearman_mass_absDeltaEta"):continue
            points=selected(events,r["population"],r["partition"],1,float(r["mass_low"]),float(r["mass_high"]))
            x=[float(e["m_gg"]) for e in points];y=[float(e["abs_deltaEta_gg"]) for e in points]
            expected=pearson(ranks(x),ranks(y)) if r["diagnostic"].startswith("spearman") else pearson(x,y)
            if expected is None:self.assertEqual(r["state"],"UNDEFINED")
            else:self.assertAlmostEqual(float(r["value"]),expected,places=13)

    def test_mass_conditional_occupancies_and_wilson_counting_intervals(self):
        _,events,audit,_,_=self.run_case()
        for r in audit:
            if r["diagnostic"]!="mass_conditional_A_fraction_Wilson95":continue
            sample=selected(events,r["population"],"ALL",float(r["split_abs_delta_eta"]),105,160)
            sample=[e for e in sample if int(e["mass_category"])==int(r["category"])];n=len(sample);a=sum(float(e["abs_deltaEta_gg"])<float(r["split_abs_delta_eta"]) for e in sample)
            self.assertEqual(int(r["n"]),n)
            if not n:self.assertEqual(r["state"],"UNDEFINED");continue
            p=a/n;z=1.959963984540054;den=1+z*z/n;centre=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
            self.assertAlmostEqual(float(r["value"]),p,places=14);self.assertAlmostEqual(float(r["interval_low"]),max(0,centre-half),places=13);self.assertAlmostEqual(float(r["interval_high"]),min(1,centre+half),places=13)

    def test_sparse_empty_constant_and_one_fold_states_are_undefined(self):
        scenarios=[[row(0,125,.5)],[row(i,110,.5) for i in range(3)],[row(i,110,.5 if i<2 else 1.5) for i in range(4)]]
        for rows in scenarios:
            result=self.run_case(rows);audit=result[2]
            for r in audit:
                if r["diagnostic"]=="cramers_v_mass_category_partition" or r["diagnostic"] in ("pearson_mass_absDeltaEta","spearman_mass_absDeltaEta"):
                    self.assertEqual(r["state"],"UNDEFINED");self.assertFalse(r["value"])
        events=[]
        for event in range(9000,9500):
            if int(digest(276336,event)[:2],16)&1==0:
                events.append(row(len(events),106+len(events)*5,.5 if len(events)%2 else 1.5,event=event))
                if len(events)==3:break
        summary,_,audit,_,_=self.run_case(events);self.assertEqual(summary["fold1_validation_entries"],0)
        self.assertTrue(all(r["state"]=="UNDEFINED" for r in audit if r["population"]=="RETROSPECTIVE_HELDOUT"))

    def test_fixed_trim_categories_keep_unambiguous_selection_context(self):
        _,events,audit,_,_=self.run_case()
        labels={r["population"] for r in audit if r["population"].startswith("FIXED_OUTER_TRIM")}
        self.assertEqual(labels,{"FIXED_OUTER_TRIM_110_160","FIXED_OUTER_TRIM_105_155","FIXED_OUTER_TRIM_110_155"})
        for r in audit:
            if r["population"] not in labels or r["diagnostic"] not in ("mass_category_A_count","mass_category_B_count"):continue
            sample=selected(events,r["population"],r["partition"],float(r["split_abs_delta_eta"]))
            expected=sum(int(e["mass_category"])==int(r["category"]) for e in sample)
            self.assertEqual(int(r["n"]),expected);self.assertEqual(float(r["value"]),expected)

    def test_selection_before_mass_and_strict_original_object_thresholds(self):
        rows=fixtures();rows[0]["jet2_pt"]="25";rows[1]["photon1_pt"]="35";rows[2]["jet1_eta"]="2.5";rows[3].update(photon1_eta="1.4",photon2_eta="-.25",deltaEta_gg="1.65")
        summary,events,_,_,_=self.run_case(rows)
        self.assertFalse({100,101,102,103}&{int(e["entry"]) for e in events});self.assertEqual(summary["sideband_entries"],75-4)

    def test_histogram_raw_counts_sumw2_and_gap_are_explicit(self):
        _,events,_,hist,_=self.run_case()
        for partition in ("A","B"):
            rows=[r for r in hist if r["partition"]==partition];self.assertEqual(len(rows),13)
            self.assertEqual(sum(float(r["raw_count"]) for r in rows),sum(e["baseline_partition"]==partition for e in events))
            self.assertEqual(sum(float(r["raw_count"]) for r in rows if 120<=float(r["mass_low"])<130),0)
            for r in rows:self.assertAlmostEqual(float(r["sumw2"]),float(r["raw_count"]),places=12)

    def test_sha256_multiblock_inputs_and_crlf_cache(self):
        for padding in (0,1,55,56,63,64,65,127,128,513):
            rows=fixtures();rows[0]["issue"]="a"*padding;self.run_case(rows,text=serialize(rows).replace("\n","\r\n"))

    def test_whole_cache_duplicates_including_central_cannot_leak(self):
        rows=fixtures();rows[-5].update(run=rows[0]["run"],event=rows[0]["event"]);self.run_case(rows,ok=False)
        rows=fixtures();rows[1].update(run=rows[0]["run"],event=rows[0]["event"]);self.run_case(rows,ok=False)

    def test_strict_header_width_order_unsigned_and_scalar_guards(self):
        for text in (serialize(fixtures(),HEADER+['extra']),serialize(fixtures(),HEADER[:-1]),serialize(fixtures()).replace("entry,run","entry,entry",1),serialize(fixtures()).replace("100,276336","100,276336,extra",1),serialize(fixtures())+"\n"):
            self.run_case(text=text,ok=False)
        for field,value in (("entry","+100"),("run","4294967296"),("event","18446744073709551616"),("entry","101"),("valid","2"),("photon_n","100001"),("jet_n","-1"),("roundoff_objects","5"),("photon1_pt","nan"),("m_gg","inf"),("m_gg","-1"),("photon2_pt","60"),("photon1_pt",""),("deltaEta_gg","2"),("p1_tight_id","-1"),("issue","\"quoted\"")):
            rows=fixtures();rows[0][field]=value;self.run_case(rows,ok=False)

    def test_output_range_scope_unit_and_physical_pin_guards(self):
        self.run_case(existing=True,ok=False)
        for kwargs in ({"start":"101"},{"end":"100"},{"end":"179"},{"end":"181"},{"end":"64101"},{"units":"VERIFIED"},{"sample":"MC"},{"sample":"DATA93915"}):
            self.run_case(ok=False,**kwargs)

    def test_oversized_protocol_and_config_fail_before_allocation_or_output(self):
        large=self.base/"large_sparse.json"
        with large.open("wb") as f:f.seek(64*1024*1024);f.write(b"x")
        self.run_case(protocol=large,ok=False);self.run_case(selection=large,ok=False)


if __name__=="__main__":
    result=unittest.main(verbosity=2,exit=False)
    print("SYNTHETIC_CACHE_INVOCATIONS "+json.dumps(INVOCATIONS,sort_keys=True))
    sys.exit(not result.result.wasSuccessful())
