"""Publication tests exercise actual index/intermediate-commit inspection."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from simulation.hh_signal.final_closure.resource_closure import capacity_publication as p


class CapacityPublicationTests(unittest.TestCase):
    def test_exact_delta_and_report_paths_only(self):
        for name in ('full_controller.py','job_envelope.py','storage_capacity.py'):
            self.assertTrue(p.allowed(p.PREFIX+name))
        for name in ('reports/phase7i_s4_persistent_capacity_closure/REPORT_ZH_TW.md',
                     'reports/phase7i_s4_persistent_capacity_closure/evidence.json'):
            self.assertTrue(p.allowed(name))
        for name in ('reports/phase7i_s4_persistent_capacity_closure/a.png',
                     'reports/phase7i_s4_persistent_capacity_closure/a.pdf',
                     'reports/phase7i_autonomous_controller_recovery/evidence.json',
                     'simulation/hh_signal/final_closure/config/physics_contract.json',
                     'a.lhe','MG5/bin/mg5_aMC','reports/raw_env.json'):
            self.assertFalse(p.allowed(name),name)

    def test_private_raw_report_not_publishable(self):
        name=p.REPORTS+'evidence.json'
        raw=json.dumps({'kind':'PRIVATE_MOUNTINFO_RAW','base64':'cHJpdmF0ZQ=='}).encode()
        with patch.object(p.original,'allowed_path',p.allowed):
            with self.assertRaises(ValueError):p.validate(name,raw)

    def test_disallowed_intermediate_commit_cannot_be_hidden_by_safe_head(self):
        with tempfile.TemporaryDirectory() as name:
            r=Path(name)
            def git(*args):
                return subprocess.run(['git',*args],cwd=r,check=True,
                    capture_output=True,text=True).stdout.strip()
            git('init');git('config','user.name','Inert Test')
            git('config','user.email','inert@example.invalid')
            (r/'base.txt').write_text('INERT')
            git('add','base.txt');git('commit','-m','inert base')
            base=git('rev-parse','HEAD')
            file=r/'reports/phase7i_s4_persistent_capacity_closure/evidence.json'
            file.parent.mkdir(parents=True)
            file.write_text('{"safe":true}\n')
            git('add',str(file.relative_to(r)));git('commit','-m','safe')
            image=r/'not-approved.png';image.write_bytes(b'INERT')
            git('add','not-approved.png');git('commit','-m','rejected intermediate')
            git('rm','not-approved.png');git('commit','-m','removed')
            with patch.object(p,'BASE',base):
                with self.assertRaisesRegex(ValueError,'PUBLICATION'):
                    p.audit(r)


if __name__ == '__main__':unittest.main()
