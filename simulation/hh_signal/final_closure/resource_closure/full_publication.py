"""PR32-stacked delta policy; original PR32 publication policy is immutable."""
from __future__ import annotations
import json
from unittest.mock import patch
from . import publication as old

BASE = '66663557984fcc069de600e2af07e778a4ac30ff'
ROOT = 'simulation/hh_signal/final_closure/resource_closure/'
BASE_ALLOWED = old.allowed_path
EXACT = {ROOT + name for name in ('full_controller.py', 'full_publication.py',
    'FULL_CONTROLLER_ZH_TW.md', 'tests/test_full_controller.py',
    'tests/test_full_publication.py')}
EXACT |= old.WORKFLOWS


def allowed(name):
    if not BASE_ALLOWED(name):
        return False
    return name in EXACT or (name.startswith('reports/phase7i_resource_closure/full_controller_')
                             and name.endswith(('.json', '.md', '.txt')))


def audit(repo=old.REPO):
    # Reuse unchanged byte/secret/archive/index/every-intermediate checks with
    # a narrower additive path allowlist and exact independently stacked base.
    with patch.object(old, 'allowed_path', allowed):
        return old.audit(repo, base=BASE)


def main():
    try:
        row = audit()
    except (ValueError, OSError) as error:
        print(json.dumps({'status': 'FAIL_PUBLICATION_AUDIT', 'reason': str(error)[:1024]}))
        return 2
    print(json.dumps(row, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
