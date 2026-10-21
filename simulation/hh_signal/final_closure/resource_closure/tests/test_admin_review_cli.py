import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from .. import admin_review as c
from .test_admin_security import device


class AdminReviewCliTests(unittest.TestCase):
    def run_fixture(self,raw):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.json';p.write_bytes(raw)
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                code=c.main(['--kind','device','--input',str(p)])
            return code,json.loads(output.getvalue())

    def test_consistent_offline_input_does_not_create_execution_authority(self):
        s,cx=device();code,out=self.run_fixture(json.dumps({'snapshot':s,'contract':cx}).encode())
        self.assertEqual(code,0);self.assertFalse(out['operation_authorized'])

    def test_duplicate_nonfinite_oversize_or_wrong_shape_is_rejected(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b' '*131073,b'[]'):
            code,out=self.run_fixture(raw)
            self.assertEqual(code,2);self.assertEqual(out['status'],'REJECTED_OR_UNKNOWN')

    def test_privileged_cli_action_is_not_a_supported_option(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                c.main(['--kind','format','--input','UNOPENED'])
