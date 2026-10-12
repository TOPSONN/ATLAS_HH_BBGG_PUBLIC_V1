"""Independent local-cache fixtures; no network, native DATA ROOT or fit."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal, localcontext

EXECUTABLE=Path(sys.argv[1]).resolve()
SELECTION=Path(sys.argv[2]).resolve()
sys.argv=[sys.argv[0]]
HEADER="entry,run,event,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,deltaEta_gg,deltaPhi_gg,deltaEta_jj,deltaPhi_jj,p1_tight_id,p2_tight_id,p1_tight_iso,p2_tight_iso,roundoff_objects,issue".split(",")


def fixtures():
    masses=[104.99,105,110,119.999,120,125,129.999,130,140,145,155,160,160.01]
    eta=[.5,.8,1,1.2,.5,1.5,.5,.4,-1,-1.2,.8,-.4,.5]
    return [dict(entry=str(100+i),run="276336",event=str(9000+i),valid="1",photon_n="2",jet_n="2",
                 photon1_pt="50",photon2_pt="30",photon1_eta=str(d/2),photon2_eta=str(-d/2),
                 jet1_pt="45",jet2_pt="35",jet1_eta=".2",jet2_eta="-.2",m_gg=str(m),m_jj="90",
                 deltaR_gg="2",deltaR_jj="2.5",deltaEta_gg=str(d),deltaPhi_gg="1.5",deltaEta_jj=".4",deltaPhi_jj="2",
                 p1_tight_id="0",p2_tight_id="0",p1_tight_iso="0",p2_tight_iso="0",roundoff_objects="0",issue="")
            for i,(m,d) in enumerate(zip(masses,eta))]


def serialized(rows,header=HEADER):
    return ",".join(header)+"\n"+"".join(",".join(str(r.get(k,"")) for k in header)+"\n" for r in rows)


def pearson(x,y):
    with localcontext() as context:
        context.prec=60
        x=list(map(lambda v:Decimal(str(v)),x));y=list(map(lambda v:Decimal(str(v)),y))
        mx=sum(x)/len(x);my=sum(y)/len(y)
        return float(sum((a-mx)*(b-my) for a,b in zip(x,y))/(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y)).sqrt())


def ranks(values):
    return [1+sum(b<a for b in values)+(sum(b==a for b in values)-1)/2 for a in values]


def fnv_fold(run,event):
    value=14695981039346656037
    for byte in f"DATA:{run}:{event}".encode("ascii"):
        value=((value^byte)*1099511628211)&((1<<64)-1)
    return value&1


class Contract(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(prefix="phase5b_sidebands_",dir=Path.cwd())
        self.addCleanup(self.directory.cleanup)
        self.base=Path(self.directory.name);self.case=0

    def run_case(self,rows=None,text=None,config=None,end=None,start="100",units="PROVISIONAL",existing=False,ok=True):
        self.case+=1;rows=fixtures() if rows is None else rows
        cache=self.base/f"cache{self.case}.csv";cache.write_text(text if text is not None else serialized(rows),encoding="utf-8",newline="")
        output=self.base/f"out{self.case}";cfg=SELECTION
        if isinstance(config,Path):cfg=config
        elif config is not None:
            cfg=self.base/f"config{self.case}.ini";cfg.write_text(config,encoding="utf-8",newline="")
        if existing:
            output.mkdir();(output/"preserve.txt").write_text("original user work")
        expected_hash=hashlib.sha256(cache.read_bytes()).hexdigest();selection_hash=hashlib.sha256(cfg.read_bytes()).hexdigest()
        result=subprocess.run([str(EXECUTABLE),str(cache),str(cfg),str(output),str(start),str(end or (100+len(rows))),units],capture_output=True,text=True,timeout=30)
        self.assertEqual(hashlib.sha256(cache.read_bytes()).hexdigest(),expected_hash)
        self.assertEqual(hashlib.sha256(cfg.read_bytes()).hexdigest(),selection_hash)
        if not ok:
            self.assertNotEqual(result.returncode,0,"Invalid fixture accepted")
            self.assertIn("FAIL DATA sidebands",result.stderr)
            if existing:
                self.assertEqual((output/"preserve.txt").read_text(),"original user work");self.assertEqual(len(list(output.iterdir())),1)
            else:self.assertFalse(output.exists(),"Invalid input left scientific output")
            return
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual({p.name for p in output.iterdir()},{"sideband_events.csv","region_diagnostics.csv","mass_histograms.csv","summary.json"})
        summary=json.loads((output/"summary.json").read_text())
        self.assertEqual(summary["input_cache_sha256"],expected_hash);self.assertEqual(summary["selection_sha256"],selection_hash)
        for key in ("native_ROOT_read","source_ROOT_identity_verified_by_app","normalization_applied","scale_factors_applied","physical_transfer_factor_applied","physical_closure_executed","blinded_analysis"):
            self.assertFalse(summary[key])
        self.assertEqual(summary["figures_generated"],0);self.assertEqual(summary["background_dominance"],"UNKNOWN");self.assertEqual(summary["single_H_contamination"],"UNKNOWN")
        def read(name):return list(csv.DictReader(io.StringIO((output/name).read_text())))
        return summary,read("sideband_events.csv"),read("region_diagnostics.csv"),read("mass_histograms.csv")

    def test_exact_boundaries_and_c9_preservation(self):
        summary,events,metrics,hist=self.run_case()
        self.assertEqual(summary["entries"],13);self.assertEqual(summary["C9"],11);self.assertEqual(summary["sideband_entries"],8);self.assertEqual(summary["outside_study_domain"],2)
        self.assertEqual([float(e["m_gg"]) for e in events],[105,110,119.999,130,140,145,155,160])
        self.assertEqual([e["baseline_partition"] for e in events],["A","B","B","A","B","B","A","A"])
        for split in (.8,1.,1.2):
            for partition in ("A","B"):
                expected=sum((abs(float(e["deltaEta_gg"]))<split)==(partition=="A") for e in events)
                selected=[r for r in metrics if r["diagnostic"]=="occupancy" and r["population"]=="SIDEBANDS" and r["partition"]==partition and float(r["split_abs_delta_eta"])==split]
                self.assertEqual(len(selected),1);self.assertEqual(int(selected[0]["n"]),expected)

    def test_independent_pearson_and_tied_spearman(self):
        _,events,metrics,_=self.run_case()
        for partition in ("ALL","A","B"):
            chosen=[e for e in events if partition=="ALL" or e["baseline_partition"]==partition]
            x=[float(e["m_gg"]) for e in chosen]
            for absolute in (False,True):
                y=[float(e["abs_deltaEta_gg"] if absolute else e["deltaEta_gg"]) for e in chosen]
                for kind in ("pearson","spearman"):
                    label=f"{kind}_mass_{'absDeltaEta' if absolute else 'deltaEta'}"
                    value=next(r for r in metrics if r["diagnostic"]==label and r["partition"]==partition and r["population"]=="SIDEBANDS")
                    expected=pearson(ranks(x),ranks(y)) if kind=="spearman" else pearson(x,y)
                    self.assertAlmostEqual(float(value["value"]),expected,places=12)

    def test_central_population_cannot_tune_diagnostics(self):
        old=self.run_case();rows=fixtures()
        for row in rows:
            if 120<=float(row["m_gg"])<130:
                row.update(photon1_eta=".7",photon2_eta="-.7",deltaEta_gg="1.4",m_gg="127")
        new=self.run_case(rows=rows)
        self.assertEqual(old[1:],new[1:]);self.assertEqual(old[0]["C9"],new[0]["C9"])

    def test_root_histogram_counts_and_explicit_edge_flow(self):
        _,events,_,hist=self.run_case()
        for partition in ("A","B"):
            rows=[r for r in hist if r["partition"]==partition]
            self.assertEqual(len(rows),13);self.assertEqual(sum(float(r["raw_count"]) for r in rows),sum(e["baseline_partition"]==partition for e in events))
            for r in rows:self.assertAlmostEqual(float(r["raw_count"]),float(r["sumw2"]),places=12)
            self.assertEqual(sum(float(r["raw_count"]) for r in rows if 120<=float(r["mass_low"])<130),0)
        self.assertEqual(next(r for r in hist if r["partition"]=="A" and r["root_bin"]=="12")["raw_count"],"1")

    def test_holdout_identity_and_fixed_pseudo_window_counts(self):
        _,events,metrics,_=self.run_case()
        for e in events:self.assertEqual(int(e["holdout_fold"]),fnv_fold(e["run"],e["event"]))
        self.assertEqual(sum(int(r["n"]) for r in metrics if r["diagnostic"]=="holdout_occupancy"),len(events))
        for r in metrics:
            if r["diagnostic"]=="pseudo_window_occupancy":
                expected=sum(float(r["mass_low"])<=float(e["m_gg"])<float(r["mass_high"]) and e["baseline_partition"]==r["partition"] for e in events)
                self.assertEqual(int(r["n"]),expected)

    def test_fraction_interval_and_fixed_sensitivity(self):
        _,events,metrics,_=self.run_case()
        for r in metrics:
            if r["diagnostic"]!="A_fraction" or r["state"]=="UNDEFINED":continue
            self.assertTrue(0<=float(r["interval_low"])<=float(r["value"])<=float(r["interval_high"])<=1+1e-15)
            if r["population"]=="FIXED_OUTER_BOUNDARY":
                chosen=[e for e in events if float(r["mass_low"])<=float(e["m_gg"])<=float(r["mass_high"])]
                successes=sum(float(e["abs_deltaEta_gg"])<float(r["split_abs_delta_eta"]) for e in chosen)
                n=len(chosen);p=successes/n;z=1.959963984540054
                centre=(p+z*z/(2*n))/(1+z*z/n);half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
                self.assertAlmostEqual(float(r["interval_low"]),centre-half,places=13);self.assertAlmostEqual(float(r["interval_high"]),centre+half,places=13)

    def test_sideband_balance_accounts_for_unequal_widths(self):
        _,events,metrics,_=self.run_case()
        for partition in ("A","B"):
            lower=sum(e["baseline_partition"]==partition and float(e["m_gg"])<120 for e in events)
            upper=sum(e["baseline_partition"]==partition and float(e["m_gg"])>=130 for e in events)
            for population,count,width in (("LOWER",lower,15),("UPPER",upper,30)):
                r=next(r for r in metrics if r["diagnostic"]=="raw_count_per_GeV" and r["population"]==population and r["partition"]==partition and float(r["split_abs_delta_eta"])==1)
                self.assertAlmostEqual(float(r["value"]),count/width,places=13)
            r=next(r for r in metrics if r["diagnostic"]=="upper_over_lower_density_ratio" and r["partition"]==partition and float(r["split_abs_delta_eta"])==1)
            self.assertAlmostEqual(float(r["value"]),upper/(2*lower),places=13)

    def test_sparse_empty_and_constant_correlations_stay_undefined(self):
        rows=fixtures()[:1];rows[0]["m_gg"]="125"
        summary,events,metrics,_=self.run_case(rows=rows)
        self.assertEqual(summary["sideband_entries"],0);self.assertFalse(events)
        self.assertTrue(all(r["state"]=="UNDEFINED" and not r["value"] for r in metrics if "pearson" in r["diagnostic"] or "spearman" in r["diagnostic"] or "fraction" in r["diagnostic"]))
        rows=fixtures()[:3]
        for row in rows:row.update(m_gg="110",photon1_eta=".25",photon2_eta="-.25",deltaEta_gg=".5")
        _,_,metrics,_=self.run_case(rows=rows)
        self.assertTrue(all(r["state"]=="UNDEFINED" for r in metrics if "pearson" in r["diagnostic"] or "spearman" in r["diagnostic"]))

    def test_selection_before_mass_and_individual_jets(self):
        rows=fixtures()
        rows[1]["jet2_pt"]="25";rows[2]["photon1_pt"]="35";rows[3]["jet1_eta"]="2.5"
        summary,events,_,_=self.run_case(rows=rows)
        self.assertEqual(summary["sideband_entries"],5);self.assertEqual(summary["C9"],8)
        self.assertFalse({101,102,103}&{int(e["entry"]) for e in events})

    def test_input_hashes_multiblock_and_crlf(self):
        for padding in (0,1,55,56,63,64,65,127,128,513):
            with self.subTest(padding=padding):
                rows=fixtures();rows[0]["issue"]="a"*padding
                self.run_case(rows=rows,text=serialized(rows).replace("\n","\r\n"),config=SELECTION.read_text().replace("\n","\r\n"))

    def test_strict_header_width_and_unsigned_guards(self):
        for text in (serialized(fixtures(),HEADER+['extra']),serialized(fixtures(),HEADER[:-1]),serialized(fixtures()).replace("entry,run","entry,entry",1),serialized(fixtures()).replace("100,276336","100,276336,extra",1),serialized(fixtures())+"\n",serialized(fixtures()).replace("100,276336","+100,276336",1),serialized(fixtures()).replace("100,276336","100,4294967296",1),serialized(fixtures()).replace("100,276336","100,18446744073709551616",1)):
            with self.subTest(text=text[:40]):self.run_case(text=text,ok=False)

    def test_semantic_and_duplicate_negative_cases(self):
        for field,value in (("valid","2"),("photon_n","100001"),("photon_n","-1"),("roundoff_objects","5"),("photon1_pt","nan"),("m_gg","inf"),("m_gg","-1"),("photon2_pt","60"),("photon1_pt",""),("deltaEta_gg","2"),("p1_tight_id","-1"),("issue","\"quoted\"")):
            with self.subTest(field=field,value=value):
                rows=fixtures();rows[1][field]=value;self.run_case(rows=rows,ok=False)
        rows=fixtures();rows[1].update(run=rows[0]['run'],event=rows[0]['event']);self.run_case(rows=rows,ok=False)
        rows=fixtures();rows[1]['entry']='102';self.run_case(rows=rows,ok=False)
        rows=fixtures();rows[1]['valid']='0';self.run_case(rows=rows,ok=False)

    def test_output_preservation_and_range_unit_configuration_guards(self):
        self.run_case(existing=True,ok=False)
        for kwargs in ({"start":"101"},{"end":"112"},{"end":"114"},{"end":"100"},{"end":"64101"},{"units":"VERIFIED"}):
            with self.subTest(kwargs=kwargs):self.run_case(ok=False,**kwargs)
        self.run_case(config=SELECTION.read_text().replace("diphoton_mass_low_gev=105","diphoton_mass_low_gev=100"),ok=False)

    def test_hash_rejects_oversized_selection_before_output(self):
        config=self.base/"oversized_sparse.ini"
        with config.open("wb") as handle:
            handle.seek(64*1024*1024);handle.write(b"x")
        self.run_case(config=config,ok=False)


if __name__=="__main__":unittest.main(verbosity=2)
