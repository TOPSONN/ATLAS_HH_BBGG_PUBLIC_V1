"""Offline checks of the new MC identity pins and cumulative budget gate."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fetch_phase4_samples as mc


class SelectionBudget(unittest.TestCase):
    def fixture(self):
        files=[]
        for dsid,(name,size,checksum) in mc.PINNED.items():
            key=f'ODEO_FEB2025_v0_GamGam_mc_{dsid}.{name}.GamGam.root'
            files.append({'key':key,'size':size,'checksum':checksum,'uri':'root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/'+key})
        return {'recid':'93922','doi':'10.7483/OPENDATA.ATLAS.IMZO.7U52','_files':files}

    def test_pins_and_roles(self):
        samples=mc.select(self.fixture())
        self.assertEqual([s['dsid'] for s in samples],[343981,346214,423103])
        self.assertNotIn(302520,mc.SELECTED)

    def test_changed_record(self):
        d=self.fixture(); d['recid']='93915'
        with self.assertRaises(ValueError): mc.select(d)

    def test_changed_checksum_size_and_duplicate(self):
        for field,value in [('checksum','adler32:00000000'),('size',1)]:
            d=self.fixture(); d['_files'][0][field]=value
            with self.assertRaises(ValueError): mc.select(d)
        d=self.fixture(); d['_files'].append(d['_files'][0])
        with self.assertRaises(ValueError): mc.select(d)

    def test_wrong_uri(self):
        d=self.fixture(); d['_files'][0]['uri']=d['_files'][0]['uri'].replace('eospublic.cern.ch','elsewhere.example')
        with self.assertRaises(ValueError): mc.select(d)

    def test_new_and_historical_limits(self):
        self.assertEqual(mc.available_budget(18883874),134217728)
        self.assertEqual(mc.available_budget(268435456-7),7)
        for invalid in [-1,268435456,268435457,1.5]:
            with self.assertRaises(ValueError): mc.available_budget(invalid)

    def test_continuum_does_not_fit_remaining(self):
        self.assertGreater(110755804+58714370,mc.NEW_LIMIT)

    def test_redirect_userinfo_and_fragment_rejected_before_logging(self):
        redirect=mc.CheckedRedirect()
        for url in ['http://user:password@st-test.cern.ch:8443/file', 'https://st-test.cern.ch:8443/file#fragment']:
            with self.assertRaises(ValueError): redirect.redirect_request(None,None,307,'',{},url)

    def test_public_redirect_requires_explicit_inspection(self):
        with self.assertRaises(urllib.error.HTTPError):
            mc.CheckedRedirect().redirect_request(mc.urllib.request.Request('https://eospublic.cern.ch/file'),None,307,'',{},'http://st-test.cern.ch:8443/file?opaque=ephemeral')


if __name__=='__main__': unittest.main()
