"""SYNTHETIC_METHOD_TEST: strict aggregate units and correlated object errors."""
from decimal import Decimal
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from validate_photon_evidence import partition_rows, clustered_object_moments, close

EVENT='SOURCE_EVENT_INDICATOR_NONEXCLUSIVE_ORIGIN_FLAGS'
OBJECT='SOURCE_EVENT_HAS_MATCHING_PHOTON_ORIGIN_OBJECT'
def rows(ne=150,no=600):return [{'classification_unit':EVENT} for _ in range(ne)]+[{'classification_unit':OBJECT} for _ in range(no)]

class IndependentPhotonEvidenceTests(unittest.TestCase):
    def test_all_750_rows_required(self):
        a,b=partition_rows(rows());self.assertEqual((len(a),len(b)),(150,600))
    def test_old_event_only_shape_rejected(self):
        with self.assertRaisesRegex(ValueError,'unit/cardinality'):partition_rows(rows(no=0))
    def test_missing_object_row_rejected(self):
        with self.assertRaisesRegex(ValueError,'unit/cardinality'):partition_rows(rows(no=599))
    def test_missing_event_row_rejected(self):
        with self.assertRaisesRegex(ValueError,'unit/cardinality'):partition_rows(rows(ne=149))
    def test_unknown_unit_rejected(self):
        x=rows();x[-1]['classification_unit']='INDEPENDENT_PHOTONS'
        with self.assertRaisesRegex(ValueError,'unit/cardinality'):partition_rows(x)
    def test_retyped_object_rows_rejected(self):
        with self.assertRaisesRegex(ValueError,'unit/cardinality'):partition_rows(rows(ne=750,no=0))
    def test_event_clustered_variance(self):
        total,var=clustered_object_moments([0,2],[Decimal('.2'),Decimal('.2')])
        self.assertEqual(total,Decimal('.4'));self.assertEqual(var,Decimal('.16'))
        # Treating two photons as independent weighted counts gives .08, wrong.
        with self.assertRaisesRegex(ValueError,'mismatch'):close('.08',var,'correlated variance')
    def test_constant_multiplicity_has_zero_sampling_variance(self):
        total,var=clustered_object_moments([2,2],[Decimal('.2'),Decimal('.2')])
        self.assertEqual(total,Decimal('.8'));self.assertEqual(var,0)
    def test_signed_cluster_preserved(self):
        total,var=clustered_object_moments([2,2],[Decimal('.2'),Decimal('-.2')])
        self.assertEqual(total,0);self.assertEqual(var,Decimal('.64'))
    def test_invalid_counts_rejected(self):
        for counts in ([0,-1],[0,True],[0,.5]):
            with self.assertRaisesRegex(ValueError,'invalid object'):clustered_object_moments(counts,[.2,.2])
    def test_partial_cohort_rejected(self):
        with self.assertRaisesRegex(ValueError,'incomplete'):clustered_object_moments([1],[.2])
    def test_undefined_not_zero(self):
        close('',None,'undefined')
        with self.assertRaisesRegex(ValueError,'undefined became'):close('0',None,'undefined')
if __name__=='__main__':unittest.main()