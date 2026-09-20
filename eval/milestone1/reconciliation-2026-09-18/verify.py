"""Read-only Task A verification; no PDF, image, OCR, model or credential reads.

Run with PYTHONPATH=src and the installed project Python. --check-inputs additionally
requires the original local native inputs and saved IR. Tooling drift is reported,
never substituted into the approved packet. Historical image archival is separate.
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'eval/milestone1'))
from packet import verify, review_read, review_bytes
from hkex_audit.artifacts import fingerprint, sha, require


def check(local=False):
    approval = review_read(ROOT/'eval/milestone1/approvals/r4.owner-2026-09-11.json')
    directory = ROOT/approval['packet_path']
    result = verify(directory, approval['approval_fingerprint'])
    review = review_read(directory/'review.json')
    require(fingerprint({k: v for k, v in approval.items() if k != 'record_fingerprint'})
            == approval['record_fingerprint'], 'approval record fingerprint mismatch')
    require(sha(review_bytes(directory/'packet-manifest.json')) == approval['packet_manifest_sha256'],
            'approved manifest hash mismatch')
    require(review['content_fingerprint'] == approval['review_content_fingerprint'],
            'approved review content mismatch')
    require(review['acceptance_scope'] == approval['accepted_scope'], 'accepted scope mismatch')
    mappings = [{'error_id': c['error_id'], 'variants': {
        v: [n['evidence_id'] for n in d['candidates']] for v, d in c['variants'].items()
    }} for c in review['candidates']]
    require(mappings == approval['primary_mappings'], 'approved mappings mismatch')
    fields = ['fixture_id', 'expected_behavior', 'qualification', 'input_sha256', 'generated_ir_sha256']
    require([{k: f[k] for k in fields} for f in review['fixtures']] == approval['fixture_acceptances'],
            'approved fixture qualifications mismatch')
    result['approval_record'] = 'exact_bindings_verified; existing_owner_decision_only'
    result['primary_mappings'] = sum(len(v) for m in mappings for v in m['variants'].values())
    result['qualified_fixtures'] = len(review['fixtures'])
    result['publication_status'] = approval['publication_status']
    result['exclusions'] = approval['exclusions']
    if local:
        permitted_drift = {'eval/milestone1/prepare.py', 'eval/milestone1/packet.py',
                           'eval/milestone1/native-review-guide.md', 'tests/test_review_packet.py'}
        unchanged, drift = [], []
        for item in review['inputs']:
            if sha(review_bytes(ROOT/item['path'])) == item['sha256']:
                unchanged.append(item['path'])
            else:
                require(item['path'] in permitted_drift and item['snapshot'], 'unexpected original-input drift')
                require(sha(review_bytes(directory/item['snapshot'])) == item['sha256'], 'original snapshot mismatch')
                drift.append(item['path'])
        result['original_inputs'] = {'unchanged': len(unchanged), 'active_tooling_or_guide_drift': drift,
                                     'approved_snapshots_preserved': True}
    inventories = {}
    for name in ['model-selection-2026-09-17', 'flash-context-check-2026-09-17-r2']:
        manifest = review_read(ROOT/'runs/milestone2'/name/'final-hashes.json')
        for path, digest in manifest.items():
            require(not path.lower().endswith('.pdf'), 'PDF inventory entry forbidden')
            require(sha((ROOT/path).read_bytes()) == digest, 'frozen experiment changed: ' + path)
        inventories[name] = len(manifest)
    result['frozen_experiment_inventory_hashes'] = inventories
    return result


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-inputs', action='store_true')
    args = parser.parse_args()
    print(json.dumps(check(args.check_inputs), indent=2))
