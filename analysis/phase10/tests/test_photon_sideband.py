"""Independent synthetic checks; no actual event production or detector dispatch."""
import importlib.util
import math
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"source"),str(ROOT/"scripts")]
import sideband as sb
import photon_feasibility as pf

def diagonal(values):
    return [[values[i] if i==j else 0.0 for j in range(len(values))] for i in range(len(values))]

class PhotonSyntheticTests(unittest.TestCase):
    def test_regions_are_disjoint_exhaustive(self):
        self.assertEqual([sb.region(t,i) for t,i in [(True,True),(True,False),(False,True),(False,False)]],list("ABCD"))
        with self.assertRaises(ValueError):sb.region(1,True)

    def test_closure_prompt_contamination_and_correlations(self):
        r=sb.synthetic_suite()
        self.assertEqual(r["status"],"PASS_SYNTHETIC_METHOD_ONLY")
        self.assertTrue(all(r["checks"].values()))
        self.assertFalse(r["import_into_physical_results"])

    def test_zero_D_rejects_rather_than_zero_rate(self):
        r=sb.synthetic_transfer([1.,1.,1.,0.],[0.]*4,1.,diagonal([0.]*9))
        self.assertFalse(r["valid"]);self.assertNotIn("predicted_target",r)
        self.assertEqual(r["status"],"INVALID_ZERO_OR_NEGATIVE_DENOMINATOR")

    def test_zero_C_has_no_finite_precision_claim(self):
        r=sb.synthetic_transfer([1.,1.,0.,1.],[0.]*4,1.,diagonal([0.]*9))
        self.assertEqual(r["status"],"ZERO_CONTROL_SUPPORT")
        self.assertNotIn("relative_precision",r)

    def test_negative_subtraction_strict_and_diagnostic(self):
        args=([1.,2.,3.,4.],[0.,3.,0.,0.],1.,diagonal([0.]*9))
        strict=sb.synthetic_transfer(*args)
        diagnostic=sb.synthetic_transfer(*args,diagnostic_negative=True)
        self.assertFalse(strict["valid"]);self.assertNotIn("predicted_target",strict)
        self.assertFalse(diagnostic["valid"]);self.assertTrue(diagnostic["diagnostic_only"])
        self.assertLess(diagnostic["predicted_target"],0)

    def test_invalid_covariance(self):
        for matrix in [diagonal([-1.]*9),[[0.]],[[float("nan")]*9 for _ in range(9)]]:
            with self.assertRaises(ValueError):sb.synthetic_transfer([4.,2.,2.,1.],[0.]*4,1.,matrix)
        c=diagonal([1.]*9);c[1][2]=2.;c[2][1]=2.
        with self.assertRaises(ValueError):sb.validate_covariance(c,9)
        c=diagonal([1.]*9);c[1][2]=.5
        with self.assertRaises(ValueError):sb.validate_covariance(c,9)

    def test_full_jacobian_finite_difference(self):
        # Independent symmetric finite difference of the elementary ratio,
        # including random prompt subtraction and correlation kappa.
        values=[170.,110.,80.,55.,20.,10.,5.,5.,1.2]
        c=diagonal([2.]*8+[.01])
        r=sb.synthetic_transfer(values[:4],values[4:8],values[8],c)
        def formula(x):
            return x[8]*(x[1]-x[5])*(x[2]-x[6])/(x[3]-x[7])
        numeric=[]
        for i in range(9):
            lo=values[:];hi=values[:];step=1e-5
            lo[i]-=step;hi[i]+=step
            numeric.append((formula(hi)-formula(lo))/(2*step))
        for a,b in zip(numeric,r["prediction_gradient"]):self.assertAlmostEqual(a,b,places=6)
        variance=sum(numeric[i]**2*c[i][i] for i in range(9))
        self.assertAlmostEqual(variance,r["prediction_variance"],places=5)

    def test_offdiagonal_kappa_correlation_kept(self):
        c=diagonal([100.,50.,40.,30.]+[0.]*4+[.01])
        c[1][8]=c[8][1]=.25
        r=sb.synthetic_transfer([100.,50.,40.,30.],[0.]*4,1.,c)
        naive=sb.synthetic_transfer([100.,50.,40.,30.],[0.]*4,1.,diagonal([100.,50.,40.,30.]+[0.]*4+[.01]))
        expected_delta=2*r["prediction_gradient"][1]*r["prediction_gradient"][8]*.25
        self.assertAlmostEqual(r["prediction_variance"]-naive["prediction_variance"],expected_delta)

    def test_transfer_uncertainty_analytic(self):
        c=diagonal([100.,80.,60.,40.]+[0.]*5)
        r=sb.synthetic_transfer([120.,80.,60.,40.],[0.]*4,1.,c)
        self.assertAlmostEqual(r["transfer_variance"],60/40**2+60**2*40/40**4)
        self.assertAlmostEqual(r["prediction_variance"],120**2*(1/80+1/60+1/40))

    def test_shared_event_covariance_independent_categorical_enumeration(self):
        rows=[[1.,0.]]*3+[[0.,1.]]*2+[[0.,0.]]*5
        totals,c=sb.event_total_covariance(rows)
        self.assertEqual(totals,[3.,2.])
        n=10
        self.assertAlmostEqual(c[0][0],n*n/(n-1)*.3*.7)
        self.assertAlmostEqual(c[0][1],-n*n/(n-1)*.3*.2)
        self.assertLess(c[0][1],0.)

    def test_cluster_candidates_do_not_become_independent_events(self):
        # Two candidates from one event remain one row; covariance is on events.
        rows=[[2.,0.],[0.,2.],[0.,0.],[0.,0.]]
        _,c=sb.event_total_covariance(rows)
        self.assertAlmostEqual(c[0][0],4.)
        with self.assertRaises(ValueError):sb.event_total_covariance([[1.,0.]])

    def test_illconditioning_blocks_delta_interpretation(self):
        c=diagonal([1.]*9)
        r=sb.synthetic_transfer([3.,2.,1.,1.],[0.]*4,1.,c)
        self.assertFalse(r["valid"]);self.assertEqual(r["status"],"ILL_CONDITIONED_DENOMINATOR")
        self.assertFalse(r["physical_usable"])

    def test_prompt_efficiency_and_electron_transfer_rejected(self):
        for semantics in ["PROMPT_PHOTON_ID_EFFICIENCY","ELECTRON_TO_PHOTON_TRANSFER"]:
            with self.assertRaisesRegex(ValueError,"not a jet fake transfer"):
                sb.validate_physical_fake_source({"semantics":semantics,"status":"VALIDATED"})

    def test_synthetic_source_never_physical(self):
        with self.assertRaisesRegex(ValueError,"synthetic inputs forbidden"):
            sb.validate_physical_fake_source({"evidence_class":"SYNTHETIC_METHOD_ONLY","status":"VALIDATED"})

    def test_missing_control_data_rejected(self):
        with self.assertRaisesRegex(ValueError,"BLOCKED_MISSING_COMPATIBLE_OBSERVABLES"):
            sb.validate_physical_fake_source({"semantics":"JET_TO_PHOTON_TRANSFER_WITH_MATCHED_DENOMINATOR","status":"VALIDATED"})

    def test_covariance_validation_accepts_zero_modes(self):
        sb.validate_covariance([[1.,1.],[1.,1.]],2)
        with self.assertRaises(ValueError):sb.validate_covariance([[0.,1.],[1.,0.]],2)

    def test_invalid_kappa_and_input_domains(self):
        for k in [0.,-1.,float("nan")]:
            with self.assertRaises(ValueError):sb.synthetic_transfer([3.,2.,1.,1.],[0.]*4,k,diagonal([0.]*9))
        with self.assertRaises(ValueError):sb.synthetic_transfer([3.,2.,1.,-1.],[0.]*4,1.,diagonal([0.]*9))

    def test_source_join_duplicates_and_stage_mismatch_rejected(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory(prefix="phase10_photon_fixture_") as work:
            native=Path(work)/"native.jsonl";origins=Path(work)/"origins.jsonl"
            n={"dataset_id":"B06","source_event_ordinal":1,"source_event_sha256":"a"*64,
               "hepmc_event_sha256":"b"*64,"stages":[True,False,False,False,False]}
            o={"dataset_id":"B06","source_event_index":1,"source_event_sha256":"a"*64,
               "hepmc_event_sha256":"b"*64,"stages":[True,False,False,False,False]}
            native.write_text(json.dumps(n)+"\n"+json.dumps(n)+"\n")
            origins.write_text(json.dumps(o)+"\n")
            with self.assertRaisesRegex(ValueError,"duplicate source event key"):pf.load_join(native,origins)
            native.write_text(json.dumps(n)+"\n")
            o["stages"]=[True,True,False,False,False]
            origins.write_text(json.dumps(o)+"\n")
            with self.assertRaisesRegex(ValueError,"stage identity mismatch"):pf.load_join(native,origins)
            o["stages"]=n["stages"];o["source_event_sha256"]="c"*64
            origins.write_text(json.dumps(o)+"\n")
            with self.assertRaisesRegex(ValueError,"unmatched/duplicate"):pf.load_join(native,origins)

    def test_tcl_module_parser_preserves_nested_formula(self):
        text="module Isolation PhotonIsolation {\n set X { {1} }\n}\nmodule Efficiency Next {\n}\n"
        section=pf.module_block(text,"Isolation","PhotonIsolation")
        self.assertIn("{ {1} }",section);self.assertNotIn("module Efficiency",section)

    def test_public_catalog_has_explicit_denominators_and_no_transfer(self):
        catalog=pf.json_read(ROOT/"config/photon_public_calibration.json")
        self.assertFalse(catalog["compatible_calibration_imported"])
        for source in catalog["sources"]:
            for key in ("version","energy_tev","data_period","denominator","object_definition","transfer_factor_semantics","uncertainties","correlations","applicability","license"):
                self.assertTrue(source[key],key)
            self.assertFalse(source["physical_value_imported"])

if __name__=="__main__":unittest.main()
