#!/usr/bin/env python3
"""User-run, explicit one-use authorization; no generator execution."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from simulation.zh_pilot.phase6g.common import bridge_identity, request, issue_ticket, ACK, CAMPAIGN
from prepare_pilot import safe_output, protected_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acknowledgement', required=True)
    parser.add_argument('--process', required=True)
    parser.add_argument('--events', required=True, type=int)
    parser.add_argument('--seed', required=True, type=int)
    parser.add_argument('--energy', required=True, type=float)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--max-hours', default=2, type=float)
    parser.add_argument('--max-disk-gb', default=5, type=float)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    args.dry_run = False
    try:
        if args.acknowledgement != ACK:
            raise ValueError('NOT_AUTHORIZED: exact acknowledgement required')
        if CAMPAIGN.exists():
            raise ValueError('PHASE6G_SINGLE_RUN_LIMIT: prior attempt reserved; retain it for separate review')
        req = request(args)
        protected = protected_paths()
        output = safe_output(req['output'], protected)
        receipt = safe_output(args.receipt, protected)
        if receipt.is_relative_to(output) or output.is_relative_to(receipt.parent):
            raise ValueError('authorization receipt and fresh run output must have separate directories')
        identity, _ = bridge_identity()
        ticket = issue_ticket(args.receipt, req, identity, args.acknowledgement)
        print(json.dumps({'status': ticket['status'], 'receipt': str(args.receipt.resolve()),
                          'ticket_id': ticket['ticket_id'], 'events_generated': 0}, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print('BLOCKED: '+str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
