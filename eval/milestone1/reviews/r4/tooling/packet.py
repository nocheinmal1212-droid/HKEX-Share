"""Evaluator-only review bindings; no runtime imports this module.

The content fingerprint binds inputs/expectations. The outer approval fingerprint
also binds rendered bytes. Neither is a signature: retain the owner's exact
approval fingerprint separately and supply it when verifying a later adoption.
"""
import argparse
from pathlib import Path
from hkex_audit.artifacts import encode, fingerprint, read, require, sha, write_new


def member(directory, name):
    path = Path(name)
    require(not path.is_absolute() and name and '..' not in path.parts,
            'invalid packet member path')
    require(path.suffix.lower() != '.pdf', 'PDF packet inputs are forbidden')
    result = directory / path
    require(all(not p.is_symlink() for p in [result, *result.parents]),
            'packet symlinks are forbidden')
    return result


def seal(output, review, files):
    """Write a new immutable revision. All bytes are captured before rendering/sealing."""
    output = Path(output).resolve()
    require(not output.exists(), 'review path exists; choose a new review revision')
    require('content_fingerprint' not in review, 'review already fingerprinted')
    review = {**review, 'content_fingerprint': fingerprint(review)}
    require('index.html' in files and 'review.json' not in files
            and 'packet-manifest.json' not in files, 'invalid packet file set')
    files = {**files, 'review.json': encode(review)}
    manifest = {'schema_version': '1.0.0', 'review_status': 'pending',
                'content_fingerprint': review['content_fingerprint'],
                'files': {name: sha(data) for name, data in sorted(files.items())}}
    manifest['approval_fingerprint'] = fingerprint(manifest)
    # Validate every member before writing any of them.
    for name in files:
        member(output, name)
    output.mkdir(parents=True)
    for name, data in files.items():
        path = member(output, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    write_new(output / 'packet-manifest.json', manifest)
    return manifest


def verify(directory, expected=None, root=None):
    """Verify bundled bytes offline; root additionally rechecks original source inputs.

    For adoption, both expected (from the owner's decision) and root are required
    by the caller. This command records integrity, never grants approval.
    """
    directory = Path(directory).resolve()
    manifest = read(member(directory, 'packet-manifest.json'))
    claimed = manifest['approval_fingerprint']
    require(fingerprint({k: v for k, v in manifest.items() if k != 'approval_fingerprint'}) == claimed,
            'packet manifest fingerprint mismatch')
    require(expected is None or expected == claimed, 'approved fingerprint differs')
    require({'index.html', 'review.json'} <= manifest['files'].keys(), 'missing core packet files')
    for name, digest in manifest['files'].items():
        require(sha(member(directory, name).read_bytes()) == digest, 'packet file changed: ' + name)
    review = read(directory / 'review.json')
    require(fingerprint({k: v for k, v in review.items() if k != 'content_fingerprint'})
            == review['content_fingerprint'] == manifest['content_fingerprint'],
            'review content fingerprint mismatch')
    for item in review['inputs']:
        if item.get('snapshot'):
            require(manifest['files'].get(item['snapshot']) == item['sha256'],
                    'input snapshot hash mismatch')
        if root is not None:
            path = Path(root) / item['path']
            require(path.suffix.lower() != '.pdf' and path.resolve().suffix.lower() != '.pdf',
                    'PDF source inputs are forbidden')
            require(sha(path.read_bytes()) == item['sha256'], 'source input changed: ' + item['path'])
    return {'status': 'passed', 'approval_fingerprint': claimed,
            'files_checked': len(manifest['files']),
            'original_inputs_checked': len(review['inputs']) if root is not None else 0,
            'owner_approval': 'not_granted_by_integrity_check'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet', required=True, type=Path)
    p.add_argument('--expected-fingerprint')
    p.add_argument('--check-inputs', action='store_true')
    a = p.parse_args()
    print(verify(a.packet, a.expected_fingerprint,
                 Path(__file__).resolve().parents[2] if a.check_inputs else None))
