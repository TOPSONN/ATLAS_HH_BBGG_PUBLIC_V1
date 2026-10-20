"""Fixed-base source/evidence publication gate; no physical dispatch.

Only changed payloads are inspected, preserving previously published baseline
figures without reinterpreting them. Every intermediate outgoing commit AND the
complete changed index are checked. CLI cannot override the reviewed base.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, stat, subprocess
from pathlib import Path, PurePosixPath

BASE = 'b80e16775bf141e45f4048c7197a8a99befaed51'
REPO = Path(__file__).resolve().parents[4]
PREFIX = 'simulation/hh_signal/final_closure/resource_closure/'
RUNTIME = 'simulation/hh_signal/final_closure/integration_runtime/'
ADAPTERS = {RUNTIME+name+'.py' for name in ('build', 'build_process', 'containment', 'route_a', 'approval', 'run')}
WORKFLOWS = {'.github/workflows/'+name+'.yml' for name in
             ('hh_signal_final_closure', 'hh_signal_readiness', 'hh_signal_resource_closure')}
FILE_BYTES = 131072
AGGREGATE_BYTES = 2*1024**2
PRIVATE_PARTS = {'.git', '.local', '__pycache__', 'private', 'private_inputs', 'private_payload',
                 'raw', 'raw_events', 'raw_archive', 'artifacts', 'build_artifacts', 'node_modules'}
PRIVATE_RAW_SHA256 = {'5e8460eee42abcf08840b5a9d7666c1d9ae6abf92c4692abbee6428f7945b08e',
                      'e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1'}
MAGIC = (b'\x7fELF', b'MZ', b'%PDF-', b'\x89PNG\r\n\x1a\n', b'root', b'\x1f\x8b',
         b'PK\x03\x04', b'PK\x05\x06', b'\x7fHDF', b'\x89HDF', b'Rar!', b'7z\xbc\xaf\x27\x1c')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def allowed_path(name):
    if not isinstance(name, str) or len(name) > 512 or not re.fullmatch(r'[A-Za-z0-9_./-]+', name):
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or path.as_posix() != name:
        return False
    if any(part.lower() in PRIVATE_PARTS or part.lower().startswith('private_') for part in path.parts):
        return False
    if re.search(r'(?:^|/)chunk_[0-9]+(?:[./]|$)', name):
        return False
    suffix = path.suffix.lower()
    if name in ADAPTERS or name in WORKFLOWS:
        return True
    if name.startswith(PREFIX):
        return suffix in ('.py', '.json', '.md')
    if name.startswith('reports/phase7i_resource_closure/') or name.startswith('reports/phase7i_resource_closure_'):
        return suffix in ('.json', '.txt', '.md')
    return False


def _json_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'JSON_DUPLICATE_KEY')
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError('NONFINITE_JSON_CONSTANT:'+value)


def validate_payload(name, raw, mode='100644'):
    require(mode == '100644', 'NONREGULAR_OR_EXECUTABLE_MODE:'+name)
    require(allowed_path(name), 'OUTSIDE_PUBLICATION_SCOPE_OR_PRIVATE_PATH:'+name)
    require(isinstance(raw, bytes) and len(raw) <= FILE_BYTES, 'PUBLICATION_FILE_CAP:'+name)
    require(not any(raw.startswith(magic) for magic in MAGIC) and raw[257:262] != b'ustar',
            'BINARY_MAGIC_OR_ARCHIVE:'+name)
    require(b'\0' not in raw and not any(ch < 32 and ch not in (9, 10, 13) for ch in raw),
            'BINARY_OR_CONTROL_BYTES:'+name)
    require(sha(raw) not in PRIVATE_RAW_SHA256, 'PRIVATE_CONFIGURATION_RAW_PAYLOAD:'+name)
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('NON_UTF8_PAYLOAD:'+name) from exc
    require(re.search(r'(?m)^\s*<(?:LesHouchesEvents|event)(?:\s[^>]*)?>\s*$', text) is None,
            'RAW_EVENT_PAYLOAD:'+name)
    require(re.search(r'(?m)^\s*(?:HepMC::|E\s+[0-9]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+)', text) is None,
            'RAW_EVENT_PAYLOAD:'+name)
    require(re.search(r'(?m)^\s*-----BEGIN(?: RSA| EC| OPENSSH)? PRIVATE KEY-----\s*$', text) is None and
            re.search(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b', text) is None,
            'SECRET_LIKE_PAYLOAD:'+name)
    if PurePosixPath(name).suffix.lower() == '.json':
        try:
            value = json.loads(text, parse_constant=_nonfinite, object_pairs_hook=_json_no_duplicates)
            json.dumps(value, allow_nan=False)
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError('INVALID_OR_NONFINITE_JSON:'+name) from exc
    return {'path': name, 'bytes': len(raw), 'sha256': sha(raw), 'mode': mode}


def git(repo, *args):
    environment = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1', LC_ALL='C')
    forbidden = ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR',
                 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_NAMESPACE')
    require(not any(os.environ.get(key) for key in forbidden), 'UNSAFE_GIT_ENVIRONMENT')
    done = subprocess.run(['git', '-C', str(repo), *args], env=environment,
                          capture_output=True, timeout=30)
    require(len(done.stdout) <= 4*1024**2 and len(done.stderr) <= 4096, 'GIT_AUDIT_OUTPUT_BOUND')
    require(done.returncode == 0, 'GIT_AUDIT_FAILED:'+args[0]+':'+str(done.returncode))
    return done.stdout


def changes(repo, *args):
    raw = git(repo, *args); pieces = raw.split(b'\0'); result = []; i = 0
    while i < len(pieces) and pieces[i]:
        fields = pieces[i].split(); i += 1
        require(len(fields) == 5 and fields[0].startswith(b':') and i < len(pieces), 'INVALID_RAW_GIT_DIFF')
        oldmode, newmode, oldoid, newoid, status = fields
        path = pieces[i].decode('utf-8'); i += 1
        require(status in (b'A', b'M'), 'DELETION_RENAME_OR_TYPE_CHANGE_FORBIDDEN:'+path)
        require(newmode == b'100644' and re.fullmatch(b'[0-9a-f]{40}', newoid) is not None,
                'NONREGULAR_OR_EXECUTABLE_MODE:'+path)
        result.append((path, newmode.decode(), newoid.decode()))
    require(all(not value for value in pieces[i:]), 'TRAILING_RAW_GIT_DIFF_DATA')
    return result


def audit(repo=REPO, base=BASE):
    # A caller-supplied base exists solely for isolated temporary-Git tests.
    # The publication CLI always uses BASE and has no base override switch.
    repo = Path(repo).resolve()
    require(re.fullmatch(r'[0-9a-f]{40}', base or '') is not None, 'EXACT_PUBLICATION_BASE_REQUIRED')
    git(repo, 'merge-base', '--is-ancestor', base, 'HEAD')
    commits = git(repo, 'rev-list', '--reverse', base+'..HEAD').decode().splitlines()
    rows = []; total = 0; staged = []; observed = set()
    def inspect(revision, path, mode, oid, index=False):
        nonlocal total
        size = int(git(repo, 'cat-file', '-s', oid).strip())
        require(0 <= size <= FILE_BYTES, 'PUBLICATION_FILE_CAP:'+path)
        raw = git(repo, 'cat-file', 'blob', oid)
        require(len(raw) == size, 'GIT_BLOB_SIZE_CHANGED:'+path)
        row = validate_payload(path, raw, mode)
        total += len(raw); require(total <= AGGREGATE_BYTES, 'PUBLICATION_AGGREGATE_CAP')
        if index:
            p = repo/path
            require(p.is_file() and not any(q.is_symlink() for q in (p, *p.parents)) and
                    stat.S_ISREG(p.lstat().st_mode), 'INDEX_WORKTREE_NOT_REGULAR:'+path)
            require(p.read_bytes() == raw, 'INDEX_WORKTREE_RAW_BYTE_MISMATCH:'+path)
        rows.append({'revision': revision, **row}); observed.add((path, oid))
    for commit in commits:
        parents = git(repo, 'rev-list', '--parents', '-n', '1', commit).decode().split()
        require(len(parents) == 2, 'OUTGOING_MERGE_COMMIT_FORBIDDEN')
        for path, mode, oid in changes(repo, 'diff-tree', '--raw', '-z', '--no-commit-id',
                                      '--no-abbrev', '--no-renames', '-r', parents[1], commit, '--'):
            inspect(commit, path, mode, oid)
    for path, mode, oid in changes(repo, 'diff', '--cached', '--raw', '--no-abbrev', '--no-renames',
                                  '--no-ext-diff', '--no-textconv', '-z', base, '--'):
        inspect('INDEX', path, mode, oid, index=True); staged.append(path)
    summary = {'status': 'PASS_BOUNDED_SOURCE_ONLY_PUBLICATION', 'base_revision': base,
        'head_revision': git(repo, 'rev-parse', 'HEAD').decode().strip(),
        'outgoing_commits': len(commits), 'outgoing_commit_payloads': sum(r['revision'] != 'INDEX' for r in rows),
        'changed_index_payloads': len(staged), 'distinct_path_blob_pairs': len(observed),
        'observed_snapshot_bytes': total, 'per_blob_cap_bytes': FILE_BYTES,
        'aggregate_cap_bytes': AGGREGATE_BYTES, 'snapshot_manifest_sha256': canonical(rows),
        'every_outgoing_intermediate_commit_and_changed_index_inspected': True,
        'baseline_artifacts_reinterpreted': False, 'figures_events_binaries_private_payloads_allowed': False,
        'payload_sample_first_12': rows[:12]}
    require(len(json.dumps(summary, sort_keys=True, allow_nan=False).encode()) <= 65536,
            'PUBLICATION_SUMMARY_BOUND')
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default=str(REPO))
    args = parser.parse_args(argv)
    try:
        result = audit(args.repo, base=BASE)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'FAIL_PUBLICATION_AUDIT', 'reason': str(exc)[:1024], 'base_revision': BASE}))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
