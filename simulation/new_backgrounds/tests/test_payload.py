"""Failure-only publication controls; no fabricated Monte Carlo references."""
import importlib.util
from pathlib import Path
import sys
import unittest
REPO=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('background_payload_audit',REPO/'simulation/new_backgrounds/scripts/audit_payload.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class PayloadRejections(unittest.TestCase):
    def test_figures_reject_even_if_a_binary_allowlist_is_claimed(self):
        for extension in ('.pdf','.png'):
            path='reference_samples/new_backgrounds/B04_ZH/final'+extension
            with self.assertRaisesRegex(ValueError,'figure'):audit.inspect(path,b'invalid',{path})
    def test_unbound_physics_binary_and_source_cache_reject(self):
        for path in ('reference_samples/new_backgrounds/B04_ZH/detector.root',
                     'simulation/new_backgrounds/build/tmp.txt','simulation/new_backgrounds/__pycache__/a.pyc'):
            with self.assertRaises(ValueError):audit.inspect(path,b'invalid',set())
    def test_private_credential_and_historical_path_reject(self):
        with self.assertRaisesRegex(ValueError,'private'):
            audit.inspect('metadata/phase6g_bad.json',b'{"token":"github_pat_'+b'a'*24+b'"}',set())
        with self.assertRaisesRegex(ValueError,'historical'):
            audit.inspect('reports/phase6f_final_decision.md',b'changed',set())

if __name__=='__main__':unittest.main()
