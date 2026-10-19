#!/usr/bin/env python3
"""SYNTHETIC_METHOD_TEST only; independent tiny analytic moment/PMF examples."""
from decimal import Decimal, localcontext
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('independent_statistics',Path(__file__).parents[1]/'scripts/independent_statistics.py')
stats=importlib.util.module_from_spec(spec);spec.loader.exec_module(stats)
class Methods(unittest.TestCase):
 def test_full_denominator(self):
  with localcontext() as context:
   context.prec=70
   m=stats.moments([1,2,3,4]);self.assertEqual(m['sumw'],10);self.assertEqual(m['fixed_N_source_sampling_variance'],Decimal(20)/3)
 def test_signed_cancellation(self):
  m=stats.moments([1,-1,0,0]);self.assertEqual(m['ESS'],0);self.assertEqual(m['cancellation_ratio'],0)
 def test_empty_support(self):self.assertIsNone(stats.moments([0,0])['ESS'])
 def test_constant_covariance(self):self.assertEqual(stats.covariance([1,2,3],[9,9,9]),0)
 def test_common_pairing(self):self.assertEqual(stats.covariance([1,2,3],[2,4,6]),6)
 def test_independent_PMF(self):
  jets=[{'flavour':0,'pt':100},{'flavour':0,'pt':100}]
  with localcontext() as context:
   context.prec=70
   p=stats.tag_probability(jets[0]);self.assertEqual(stats.conditional_probability(jets),p*p)
 def test_nonfinite(self):
  with self.assertRaises(ValueError):stats.moments([1,float('nan')])
 def test_low_support_flags(self):self.assertEqual(stats.quality(stats.moments([1,0,0,0]),1),'LOW_ESS_LT10')
if __name__=='__main__':unittest.main()
