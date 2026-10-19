#!/usr/bin/env python3
"""SYNTHETIC_METHOD_TEST: boundary/partition and shape-variance fixtures only."""
from decimal import Decimal, localcontext
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('postprocess',Path(__file__).parents[1]/'scripts/postprocess.py')
post=importlib.util.module_from_spec(spec);spec.loader.exec_module(post)
class Boundaries(unittest.TestCase):
 def test_mass_endpoints(self):
  for value,expected in [(104.999,'OUTSIDE_MGG'),(105,'LOW'),(119.999,'LOW'),(120,'HIGGS'),(130,'HIGGS'),(130.001,'HIGH'),(160,'HIGH'),(160.001,'OUTSIDE_MGG'),(None,'UNDEFINED_MGG')]:
   with self.subTest(value=value):self.assertEqual(post.mass_region(value),expected)
 def test_tag_exclusivity(self):
  self.assertEqual([post.tag_region(n) for n in range(5)],['TAG_0','TAG_1','TAG_GE2','TAG_GE2','TAG_GE2'])
  with self.assertRaises(ValueError):post.tag_region(-1)
  with self.assertRaises(ValueError):post.tag_region(.5)
 def test_nonfinite_mass(self):
  with self.assertRaises(ValueError):post.mass_region(float('nan'))
 def test_signed_fixed_N(self):
  result=post.summary([1,-1],4);self.assertEqual(result['sumw'],0);self.assertAlmostEqual(result['fixed_N_variance'],8/3)
 def test_constant_full_N(self):self.assertEqual(post.summary([.1]*4,4)['fixed_N_variance'],0)
 def test_duplicate_source(self):
  events=[dict(dataset_id='TOY',N_original=2,source_event_ordinal=1)]*2
  with self.assertRaises(ValueError):post.groups(events)
 def test_dataset_key_scope(self):
  events=[dict(dataset_id=name,N_original=2,source_event_ordinal=i) for name in ('TOY_A','TOY_B') for i in (1,2)]
  self.assertEqual(set(post.groups(events)),{'TOY_A','TOY_B'})
 def test_flows_and_rightmost_edge(self):
  shape,bins=post.shape([(-1.,1.),(0.,2.),(1.,3.),(2.,4.)],[0.,1.,2.],4)
  self.assertEqual(bins,[[1.],[2.],[3.],[4.]])
  self.assertEqual(shape,[.1,.2,.3,.4])
 def test_zero_signed_normalization(self):self.assertIsNone(post.shape([(0.,1.),(1.,-1.)],[0.,1.],2)[0])
 def test_shape_covariance_not_sumw2_only(self):
  with localcontext() as context:
   context.prec=70
   raw=list(map(Decimal,('1','2','3','4')));selected=[raw[0],Decimal(0),raw[2],Decimal(0)]
   total=sum(raw);p=sum(selected)/total
   influences=[(a-p*b)/total for a,b in zip(selected,raw)]
   self.assertEqual(sum(influences),0)
   direct=Decimal(4)/3*sum(x*x for x in influences)
   algebra=Decimal(4)/3*(sum(x*x for x in selected)*(1-2*p)+p*p*sum(x*x for x in raw))/(total*total)
   self.assertEqual(direct,algebra)
   normalized,bins=post.shape([(0.,1.),(1.,2.),(0.,3.),(1.,4.)],[-.5,.5,1.5],4)
   self.assertAlmostEqual(post.shape_variance(bins,normalized,4)[1],float(direct),places=14)
   self.assertNotEqual(direct,sum(x*x for x in selected)/(total*total))
if __name__=='__main__':unittest.main()
