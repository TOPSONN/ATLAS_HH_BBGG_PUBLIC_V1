"""PR35 stacked delta gate; every intermediate blob and index remains bounded."""
from __future__ import annotations
import json
from unittest.mock import patch
from . import publication as original
from . import autonomous_publication as prior
from . import recovery_publication as privacy
BASE_VALIDATE = original.validate_payload

BASE = 'cd6b43202318560492491104f994312133e8e436'
PREFIX = 'simulation/hh_signal/final_closure/resource_closure/'
REPORTS = 'reports/phase7i_s4_persistent_capacity_closure/'
EXACT = {PREFIX+n for n in (
    'full_controller.py', 'job_envelope.py', 'storage_capacity.py',
    'offline_regression.py', 'capacity_publication.py',
    'tests/test_full_controller.py', 'tests/test_job_envelope.py',
    'tests/test_storage_capacity.py', 'tests/test_capacity_publication.py',
    'tests/test_s4_controller_wiring.py', 'tests/test_git_envelope.py')}
EXACT |= {'simulation/hh_signal/final_closure/integration_runtime/git_precheck.py',
          'simulation/hh_signal/final_closure/integration_runtime/contract.py'}
EXACT |= original.WORKFLOWS


def allowed(name):
    return name in EXACT or (name.startswith(REPORTS) and
        prior.allowed(name.replace(REPORTS, prior.REPORTS, 1)))


def validate(name, raw, mode='100644'):
    row = BASE_VALIDATE(name, raw, mode)
    if name.startswith(REPORTS):
        privacy.reject_private_mount_capture(raw.decode('utf-8'))
        if name.lower().endswith('.json'):
            privacy.reject_private_mount_capture(json.loads(raw))
    return row


def audit(repo=original.REPO):
    with patch.object(original, 'allowed_path', allowed), \
         patch.object(original, 'validate_payload', validate):
        return original.audit(repo, base=BASE)


def main():
    try:
        result = audit()
    except (ValueError, OSError) as error:
        print(json.dumps({'status':'FAIL_CAPACITY_PUBLICATION', 'reason':str(error)[:1024]}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
