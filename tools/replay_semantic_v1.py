"""Offline, role-scoped replay of the retained Task B batch in a pinned v1 export.

No current runtime imports, provider access, dispatch command, or automatic version fallback.
Manifests are trusted, separately reviewed replay inputs, not evaluator expectations.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

MANIFESTS = Path(__file__).with_name('replay-semantic-v1')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def verify_environment(shared, pin):
    require(sys.version == shared['python_version'], 'pinned Python version mismatch')
    require(digest(Path(sys.executable).resolve()) == shared['python_binary_sha256'], 'pinned Python binary mismatch')
    for name, expected in shared['dependencies'].items():
        dist = importlib.metadata.distribution(name)
        require(dist.version == expected['version'], 'pinned dependency version mismatch: ' + name)
        for file, checksum in expected['files'].items():
            require(digest(dist.locate_file(file)) == checksum, 'pinned dependency bytes mismatch: ' + name)
    inventory={str(p.relative_to(pin)) for p in pin.rglob('*') if p.is_file() or p.is_symlink()}
    require(inventory == set(shared['runtime_files']), 'pinned source inventory mismatch')
    for file, checksum in shared['runtime_files'].items():
        path = pin / file
        require(not any(p.is_symlink() for p in (path, *path.parents)), 'pinned source symlink')
        require(digest(path) == checksum, 'pinned source bytes mismatch: ' + file)


# Each worker receives socket denial before importing the pinned package. The package's own
# selected-file guard remains responsible for operational file isolation after schema preload.
BOOTSTRAP = r'''
import sys, json, subprocess, os
def offline(event, args):
    if event.startswith('socket.'): raise PermissionError('historical replay is offline')
sys.addaudithook(offline)
pin, payload = sys.argv[1], json.load(sys.stdin)
sys.path.insert(0, pin + '/src')
from hkex_audit import semantic_cli as c
assert c.__file__.startswith(pin + '/src/')
def isolated(function, value, timeout=180):
    bootstrap = ''' + repr("import sys,json\ndef offline(event,args):\n if event.startswith('socket.'):raise PermissionError('historical replay is offline')\nsys.addaudithook(offline)\nsys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_cli import ") + r''' + function + ';' + function + '(json.load(sys.stdin))'
    proc = subprocess.run([sys.executable, '-I', '-B', '-c', bootstrap, pin + '/src'],
        input=json.dumps(value), text=True, capture_output=True, timeout=timeout,
        env={k:v for k,v in os.environ.items() if k not in ('OPENROUTER_API_KEY','PYTHONPATH')})
    if proc.returncode: raise ValueError(proc.stderr[-1200:])
    return json.loads(proc.stdout)
c.isolated = isolated
from argparse import Namespace
c.replay_batch(Namespace(**payload))
'''


def run(args):
    role = 'primary' if args.command == 'replay' else 'research'
    pin, batch, output = args.pin.resolve(), args.batch.resolve(), args.output.absolute()
    accesses = []
    def audit(event, values):
        if event.startswith('socket.'):
            raise PermissionError('historical replay is offline')
        if event == 'open' and isinstance(values[0], (str, bytes)):
            path = os.fsdecode(values[0])
            if path.startswith(str(batch) + os.sep):
                accesses.append(path)
    sys.addaudithook(audit)
    shared_path = args.manifests / 'shared.json'
    shared = read(shared_path)
    # Never load, stat or enumerate the unselected role's manifest/directory.
    selected = read(args.manifests / (role + '.json'))
    require(shared['version'] == 'pinned-semantic-replay-1.0.0', 'unsupported pin manifest')
    require(selected['role'] == role and selected['shared_sha256'] == digest(shared_path), 'role/shared manifest mismatch')
    verify_environment(shared, pin)
    require(digest(batch / 'batch.json') == shared['batch_sha256'], 'historical batch mismatch')
    selection = read(args.selection)
    require(selection == shared['selection'], 'historical selection mismatch')
    for field in ('evidence', 'manifest'):
        require(digest(selection[field]['path']) == selection[field]['sha256'], 'historical selected input mismatch')
    config = read(batch / 'batch.json')
    require([s['name'] for s in config['specs']] == shared['names'], 'historical query inventory mismatch')
    expected_files = {f'{role}/{name}/{stem}.json' for name in shared['names']
                      for stem in ('query','request','started','response','result','completion')}
    require(set(selected['files']) == expected_files, 'role artifact inventory mismatch')
    for file, checksum in selected['files'].items():
        require(digest(batch / file) == checksum, 'historical role artifact mismatch: ' + file)
    require(not output.exists(), 'historical replay output already exists')
    env = {k:v for k,v in os.environ.items() if k not in ('OPENROUTER_API_KEY', 'PYTHONPATH')}
    proc = subprocess.run([sys.executable, '-I', '-B', '-c', BOOTSTRAP, str(pin)],
                          input=json.dumps({'command':args.command, 'selection':str(args.selection.resolve()),
                                            'batch':str(batch), 'output':str(output)}),
                          text=True, capture_output=True, env=env, timeout=180)
    require(proc.returncode == 0, 'pinned consumer failed: ' + proc.stderr[-1500:])
    summary = read(output / 'summary.json')
    require(summary['model_calls'] == 0, 'replay unexpectedly called a model')
    if role == 'primary':
        for file, checksum in selected['expected_outputs'].items():
            require(digest(output / file) == checksum, 'historical output bytes differ: ' + file)
        for name in shared['names']:
            consumed = read(output / name / 'consumption.json')
            require(consumed['model_calls'] == 0 and not consumed['adapter_imported'], 'invalid replay boundary')
            require(not any('/research/' in x.get('path','') for x in consumed['access_attempts']), 'research read in primary worker')
    else:
        for name, item in zip(shared['names'], summary['results']):
            require(item['result'].get('validation') == selected['expected_validation'][name], 'historical research outcome differs')
    excluded = 'research' if role == 'primary' else 'primary'
    require(not any(str(batch / excluded) + os.sep in p for p in accesses), 'unselected role read by launcher')
    verification = {'version':shared['version'], 'role':role, 'pinned_commit':shared['commit'],
                    'shared_manifest_sha256':digest(shared_path), 'selected_manifest_sha256':digest(args.manifests / (role+'.json')),
                    'model_calls':0, 'network_calls':0, 'launcher_batch_reads':accesses,
                    'primary_byte_identity_verified':role=='primary', 'unselected_role_verified':False}
    (output / 'pinned-verification.json').write_text(json.dumps(verification, indent=2, sort_keys=True)+'\n')
    return verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('replay', 'research-replay'))
    for name in ('pin', 'batch', 'selection', 'output'):
        parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--manifests', type=Path, default=MANIFESTS)
    args = parser.parse_args()
    try:
        result = run(args)
        print(json.dumps({k:result[k] for k in ('role','model_calls','network_calls','primary_byte_identity_verified')}))
    except (ValueError, OSError, KeyError, importlib.metadata.PackageNotFoundError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, 'pinned replay failed: '+str(exc)+'\n')


if __name__ == '__main__':
    main()
