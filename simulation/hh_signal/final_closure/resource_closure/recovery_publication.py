"""PR33 stacked source policy: exclude raw mount evidence and all physics."""
from __future__ import annotations
import json, re
from unittest.mock import patch
from . import publication as original

BASE = 'b8ae4cc03c0ac408577909847e56f417fc28eba8'
PREFIX = 'simulation/hh_signal/final_closure/resource_closure/'
REPORTS = 'reports/phase7i_namespace_storage_recovery/'
EXACT = {PREFIX + name for name in (
    'full_controller.py', 'mount_attestation.py', 'namespace_attestation.py',
    'recovery_publication.py', 'NAMESPACE_STORAGE_RECOVERY_ZH_TW.md',
    'tests/test_full_controller.py', 'tests/test_mount_attestation.py',
    'tests/test_namespace_attestation.py', 'tests/test_controller_recovery.py',
    'tests/test_recovery_publication.py')}
EXACT |= original.WORKFLOWS
BASE_ALLOWED = original.allowed_path
BASE_VALIDATE = original.validate_payload


def allowed(name):
    translated = name.replace(REPORTS, 'reports/phase7i_resource_closure/', 1)
    return BASE_ALLOWED(translated) and (name in EXACT or name.startswith(REPORTS))


PRIVATE_FRAME = re.compile(r'"kind"\s*:\s*"(?:PRIVATE_MOUNTINFO_RAW|PRIVATE_CHILD_STDERR)"')
RAW_MOUNT_LINE = re.compile(r'(?m)^\s*\d+ \d+ \d+:\d+ /')


def normalized_ascii_json_escapes(text):
    # Detection only: never use this normalization to interpret evidence or
    # grant permission. It also catches inline Markdown-wrapped JSON frames.
    for _ in range(16):
        revised = text.replace('\\\\', '\\').replace('\\"', '"')
        revised = re.sub(r'\\u00([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), revised)
        if revised == text:
            return text
        text = revised
    return text


def reject_private_mount_capture(value, depth=0):
    original.require(depth <= 32, 'PUBLIC_REPORT_RECURSION_BOUND')
    if isinstance(value, dict):
        original.require(value.get('kind') not in ('PRIVATE_MOUNTINFO_RAW', 'PRIVATE_CHILD_STDERR'),
                         'PRIVATE_RAW_MOUNTINFO_CAPTURE_FORBIDDEN')
        original.require(not any(k in value for k in ('raw_mountinfo', 'mountinfo_bytes_base64')),
                         'PRIVATE_RAW_MOUNTINFO_FIELD_FORBIDDEN')
        for item in value.values():
            reject_private_mount_capture(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            reject_private_mount_capture(item, depth + 1)
    elif isinstance(value, str):
        normalized = normalized_ascii_json_escapes(value)
        original.require(not PRIVATE_FRAME.search(normalized), 'PRIVATE_SERIALIZED_FRAME_FORBIDDEN')
        original.require(not RAW_MOUNT_LINE.search(value), 'PRIVATE_SERIALIZED_MOUNTINFO_FORBIDDEN')
        # Strings and JSONL wrappers cannot launder private protocol frames.
        for line in dict.fromkeys([value, *value.splitlines()]):
            try:
                decoded = json.loads(line)
            except (ValueError, TypeError):
                continue
            if decoded != value:
                reject_private_mount_capture(decoded, depth + 1)


def validate(name, raw, mode='100644'):
    row = BASE_VALIDATE(name, raw, mode)
    if name.startswith(REPORTS):
        original.require(not re.search(rb'(?m)^\d+ \d+ \d+:\d+ /', raw),
                         'RAW_MOUNTINFO_LINE_FORBIDDEN')
        text = raw.decode('utf-8')
        # Apply to every report format, including uppercase JSON and Markdown
        # JSONL/code-fence bodies. Prose labels without actual frames are safe.
        reject_private_mount_capture(text)
        if name.lower().endswith('.json'):
            reject_private_mount_capture(json.loads(raw))
    return row


def audit(repo=original.REPO):
    with patch.object(original, 'allowed_path', allowed), \
         patch.object(original, 'validate_payload', validate):
        return original.audit(repo, base=BASE)


def main():
    try:
        result = audit()
    except (ValueError, OSError) as error:
        print(json.dumps({'status': 'FAIL_RECOVERY_PUBLICATION', 'reason': str(error)[:1024]}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
