"""Read-only retrospective intake checks; evaluation use only, no PDF parsing.

Run from the repository root with PYTHONPATH=src:tools/eval-format-tools and
tools/eval-format-tools/.venv/bin/python. JSON results are written to stdout.
"""
import hashlib
import json
from decimal import Decimal as D
from pathlib import Path
import subprocess

from eval_intake.validation import validate_records

ROOT = Path.cwd()
BASE = '5e30566e939a404975d0efdfcff53c8d55745fe0'
CLOSE = '0b2a712'
P = Path('eval/reviews/hkex-2025-48')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def historical(ref, path):
    return subprocess.check_output(['git', 'show', f'{ref}:{path}'])


selector = read(P/'ready-development.json')
paths = {k: Path(selector[k+'_path']) for k in ['records', 'locations', 'splits', 'review']}
for k, path in paths.items():
    assert sha(path) == selector[k+'_sha256']
    assert path.read_bytes() == historical(CLOSE, path)
manifest_path = Path('eval/manifests/hkex-2025-48.json')
manifest = read(manifest_path)
for f in manifest['files']:
    assert sha(f['path']) == f['sha256'], f['path']
records = [json.loads(x) for x in paths['records'].read_text().splitlines()]
validated = validate_records(ROOT, records, manifest, read(paths['locations']),
    read(paths['splits']), read(paths['review']), manifest_path=manifest_path,
    locations_path=paths['locations'], split_path=paths['splits'])
assert (validated['ready'], validated['pending']) == (4, 44)

images = read(P/'packet-r2/images.json')
for item in images:
    path = P/'packet-r2'/item['path']
    assert sha(path) == item['sha256']
    assert path.read_bytes() == historical(BASE, path)
for path in [P/'packet-r2/index.html', P/'packet-r2/images.json', P/'character-probes.json', manifest_path]:
    assert path.read_bytes() == historical(BASE, path)
before_split = json.loads(historical(BASE, 'eval/splits/hkex-2025-48.r2.json'))
after_split = read(paths['splits'])
for key in ['assignments', 'salt', 'algorithm', 'bootstrap_seed']:
    assert before_split[key] == after_split[key], key

selected = {r['error_id']: r for r in records if r['ingestion_status'] == 'ready'}
arithmetic = {}
# Independently implement the contract equation; do not call intake.calculate.
for eid, record in selected.items():
    rel = record['relation']
    if rel is None:
        continue
    residuals = {v: sum(D(o['coefficient'])*D(o['scale'])*D(o[v+'_value'])
                        for o in rel['operands']) for v in ['original', 'injected']}
    bound = sum(abs(D(o['coefficient']))*D(o['scale'])*D(o['rounding_step'])/2
                for o in rel['operands'])
    change = residuals['injected'] - residuals['original']
    band = 'within_tolerance' if abs(change) <= bound else 'boundary' if abs(change) <= 2*bound else 'above_tolerance'
    for v in residuals:
        assert residuals[v] == D(rel[v+'_residual'])
    assert bound == D(rel['tolerance_bound']) and change == D(rel['residual_change'])
    assert band == record['detectability_band'] and abs(residuals['injected']) > bound
    arithmetic[eid] = {**{v+'_residual': str(n) for v, n in residuals.items()},
                       'bound': str(bound), 'change': str(change), 'band': band}

packet = read('eval/milestone1/reviews/r2/review.json')
mapping_count = 0
operand_count = 0
ir_hashes = {}
for variant in ['clean', 'corrupted']:
    path = Path('runs/milestone1-r1')/variant/'evidence.json'
    ir = read(path)
    ir_hashes[variant] = sha(path)
    nodes = {n['id']: n for n in ir['nodes']}
    for case in packet['candidates']:
        item = case['variants'][variant]
        assert item['generated_ir_sha256'] == sha(path)
        for candidate in item['candidates']:
            node = nodes[candidate['evidence_id']]
            for key in ['text', 'native_pointer', 'source_span', 'fragments']:
                assert candidate[key] == node[key]
            assert node['page_index'] == selected[case['error_id']]['location']['page_index']
            for start, end in candidate['token_offsets']:
                assert node['text'][start:end] == item['expected_source_text']
            mapping_count += 1
    # Manual structural addresses independently checked against saved page images.
    addresses = [('HL-ERR-0025', [(158, 1, 2), (158, 2, 2), (158, 3, 2)]),
                 ('HL-ERR-0041', [(158, 1, 2), (179, 5, 4)])]
    for eid, cells in addresses:
        for operand, (page, row, column) in zip(selected[eid]['relation']['operands'], cells):
            found = [n for n in nodes.values() if n['kind'] == 'cell' and
                     n['page_index'] == page and n['row'] == row and n['column'] == column]
            assert len(found) == 1
            prefix = 'original' if variant == 'clean' else 'injected'
            assert found[0]['text'] == operand[prefix+'_text']
            operand_count += 1

print(json.dumps({'status': 'passed', 'baseline': BASE, 'closure_commit': CLOSE,
    'current_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'source_files_verified': len(manifest['files']), 'packet_images_verified': len(images),
    'closure_bound_files_unchanged': {k: sha(v) for k, v in paths.items()},
    'historical_packet_and_split_preserved': True,
    'intake_validation': validated, 'independent_arithmetic': arithmetic,
    'primary_ir_candidates_verified': mapping_count, 'operand_occurrences_verified': operand_count,
    'saved_ir_sha256': ir_hashes, 'publication_status': 'UNGATED',
    'limits': ['PDF bytes hashed only; visual review uses existing packet images.',
               'No detector execution, new approval, or new pending-record label.',
               'IR occurrence verification does not approve semantic relationships.']}, indent=2)+'\n')
