"""Offline JSON policy review only. No live inventory or privileged operations."""
import argparse
import json
from pathlib import Path
from .device_policy import review_device, review_mount, MAX_BYTES
from .instance_binding import review_transaction
from .boundary_contract import review_architecture


def load(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('INPUT_BOUND')
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('DUPLICATE_INPUT_KEY')
            value[key] = item
        return value
    def nonfinite(value):
        raise ValueError('NONFINITE_INPUT')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--kind', required=True, choices=('device', 'mount', 'transaction', 'architecture'))
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        value = load(args.input)
        if args.kind == 'architecture':
            result = review_architecture(value)
        else:
            if type(value) is not dict:
                raise ValueError('OBJECT_REQUIRED')
            if args.kind == 'transaction':
                result = review_transaction(value.get('records'), value.get('plan'))
            else:
                result = {'device': review_device, 'mount': review_mount}[args.kind](
                    value.get('snapshot'), value.get('contract'))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, OSError, RecursionError):
        # Never echo raw administrator host identity/private mount capture.
        print(json.dumps({'status': 'REJECTED_OR_UNKNOWN', 'operation_authorized': False,
                          'FULL_LAUNCH_ENVELOPE_VERIFIED': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
