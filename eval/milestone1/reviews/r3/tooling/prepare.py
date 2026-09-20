"""Build an evaluator-only M1 packet with captured inputs and an outer report binding."""
import argparse
import re
from html import escape
from pathlib import Path
from hkex_audit.artifacts import read, loads, encode, fingerprint, sha, require
from hkex_audit.adapters.mineru import adapt
from hkex_audit.evidence import validate_evidence
from hkex_audit.evidence_context import build_context
from packet import seal, verify

ROOT = Path(__file__).resolve().parents[2]


def source_comparison(source_text, native_text):
    """Evaluator diagnostic only; never change persisted source/IR text."""
    def diagnostic(text):
        return re.sub(r'\s+', '', text).translate(str.maketrans('（）', '()'))
    return {'literal_equal': source_text == native_text,
            'diagnostic_equal': diagnostic(source_text) == diagnostic(native_text),
            'method': 'Ignore whitespace and equate fullwidth/ASCII parentheses in memory only.'}


def node_selection(evidence, case):
    prefix = f"/pdf_info/{case['page_index']}/preproc_blocks/{case['block_index']}/"
    return [n for n in evidence['nodes'] if n['native_pointer'].startswith(prefix)
            and ((case['row'] is None and n['kind'] == 'block' and n['text'] is not None)
                 or (case['row'] is not None and n['kind'] == 'cell'
                     and n['row'] == case['row'] and n['column'] == case['column']))]


def excerpt(evidence, page, block):
    """A source-linked excerpt, deliberately not a standalone document evidence IR."""
    prefix = f'/pdf_info/{page}/preproc_blocks/{block}'
    nodes = [n for n in evidence['nodes'] if n['native_pointer'] == prefix
             or n['native_pointer'].startswith(prefix + '/')]
    scopes = {n['id'] for n in nodes} | {evidence['id']}
    scopes.update(p['id'] for p in evidence['pages'] if p['page_index'] == page)
    return {'kind': 'evaluator_excerpt', 'evidence_id': evidence['id'], 'nodes': nodes,
            'sources': [s for s in evidence['sources'] if s['pointer'].startswith(prefix + '/')
                        or s['pointer'] == prefix],
            'capabilities': [c for c in evidence['capabilities'] if c['scope_id'] in scopes],
            'limitations': [x for x in evidence['limitations'] if x['region_id'] in scopes]}


def details(title, value):
    text = value if isinstance(value, str) else encode(value).decode('utf-8')
    return '<details><summary>' + escape(title) + '</summary><pre>' + escape(text) + '</pre></details>'


def table_view(evidence, page, block):
    region = excerpt(evidence, page, block)
    tables = [n for n in region['nodes'] if n['kind'] == 'table']
    if not tables:
        return '<p>No table recovered; review required.</p>' + details('Source-linked region', region)
    t = tables[0]
    rows = {}
    for n in region['nodes']:
        if n['parent_id'] == t['id'] and n['kind'] == 'cell':
            rows.setdefault(n['row'], []).append(n)
    body = ''
    for _, row in sorted(rows.items()):
        body += '<tr>'
        for n in sorted(row, key=lambda n: n['column']):
            body += (f'<td rowspan="{n["row_span"]}" colspan="{n["column_span"]}">'
                     + escape(n['text'] or '') + '<small>'
                     + escape(f"r{n['row']} c{n['column']} · {n['content_state']}") + '</small></td>')
        body += '</tr>'
    view = (f'<p><strong>Grid: {escape(t["grid_state"])}</strong>. Page index: {page}. '
            'Rows and columns are zero-based. Cell geometry unavailable.</p>'
            + '<div class="scroll"><table>' + body + '</table></div>')
    if t['grid_state'] != 'resolved':
        view += ('<p class="banner">Partial evidence: keep unsupported content unresolved. '
                 'Any future comparison requiring it must abstain; no replacement value or complete '
                 'accounting relationship is established. No detector ran.</p>')
    # Keep limitations visible, including the failing cell ID and exact source markup.
    for issue in region['limitations']:
        view += '<p><strong>' + escape(issue['code']) + '</strong>: ' + escape(issue['reason']) + '</p>'
    for s in region['sources']:
        view += details('Literal native source: ' + s['pointer'], s['text'])
    return view + details('IR nodes, spans, capabilities and limitations', region)


def fixture_material(fixture, raw):
    native = loads(raw)
    evidence = adapt(native, {'doc_id': fixture['fixture_id'], 'variant_id': 'synthetic',
                             'source_document_sha256': None, 'source_provenance': 'synthetic'}, sha(raw))
    validate_evidence(evidence, native)
    item = {**fixture, 'input_sha256': sha(raw), 'generated_ir_sha256': sha(encode(evidence)),
            'native_snapshot': 'fixtures/' + fixture['fixture_id'] + '.native.json',
            'ir_snapshot': 'fixtures/' + fixture['fixture_id'] + '.evidence.json'}
    view = '<h2 id="fixture-' + escape(fixture['fixture_id']) + '">Fixture: ' + escape(fixture['fixture_id']) + '</h2>'
    view += '<p><strong>Proposed expectation:</strong> ' + escape(fixture['expected_behavior']) + '</p>'
    view += '<p><strong>Qualification:</strong> ' + escape(fixture['qualification']) + '</p>'
    view += '<p>Evaluator annotation only; no detector executed. Input and expectation remain separate.</p>'
    view += '<p><a href="' + item['native_snapshot'] + '">Complete native input</a> · <a href="' + item['ir_snapshot'] + '">Validated fixture IR</a></p>'
    for n in evidence['nodes']:
        if n['kind'] == 'table':
            block = int(n['native_pointer'].split('/')[4])
            view += table_view(evidence, n['page_index'], block)
    # Show every non-table literal, especially the supporting note in the reference fixture.
    for s in evidence['sources']:
        if s['format'] != 'html':
            view += '<p><strong>Supporting native text</strong></p><pre>' + escape(s['text']) + '</pre>'
            view += '<code>' + escape(s['pointer']) + '</code>'
            linked = [n for n in evidence['nodes'] if any(f['source_id'] == s['id'] for f in n['fragments'])]
            view += details('Supporting text IR IDs and spans', {'source': s, 'nodes': linked})
    return item, evidence, view


def prepare(runs, output):
    from validate import verified_intake
    cfg, ready, records = verified_intake()
    runs = Path(runs).resolve()
    output = Path(output).resolve()
    require(not output.exists(), 'review path exists; choose a new review revision')
    inputs, files = [], {}

    def capture(path, snapshot=None, expected=None):
        path = Path(path).resolve()
        raw = path.read_bytes()
        digest = sha(raw)
        require(expected is None or digest == expected, 'source hash mismatch: ' + str(path))
        label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        inputs.append({'path': label, 'sha256': digest, 'snapshot': snapshot})
        if snapshot:
            require(snapshot not in files, 'duplicate snapshot')
            files[snapshot] = raw
        return raw

    capture(ROOT/'eval/milestone1/selection.json', 'inputs/selection.json')
    capture(ROOT/cfg['ready_selector'], 'inputs/ready-development.json')
    for key in ['records', 'locations', 'splits', 'review']:
        # Bind authorities, but do not duplicate the 44 pending answers into this packet.
        capture(ROOT/ready[key+'_path'], expected=ready[key+'_sha256'])
    for key in ['source_config', 'source_manifest']:
        capture(ROOT/cfg[key])
    verification = loads(capture(runs/'verification.json', 'inputs/verification.json'))
    require(verification['structural_status'] == 'passed', 'native checks did not pass')
    require(set(verification['variants']) == {'clean', 'corrupted'}, 'incomplete variant set')
    evidence = {}
    for variant, entry in verification['variants'].items():
        e = loads(capture(Path(entry['run_dir'])/'evidence.json', expected=entry['evidence_sha256']))
        capture(Path(entry['run_dir'])/'manifest.json', expected=entry['manifest_sha256'])
        selection = loads(capture(entry['selection'], 'inputs/'+variant+'-selection.json'))
        require(selection['document'] == e['document'] and e['document']['variant_id'] == variant,
                'variant/document mismatch')
        require(len(selection['artifacts']) == 1 and selection['artifacts'][0]['role'] == 'middle_json',
                'unsupported selection')
        artifact = selection['artifacts'][0]
        native = loads(capture(artifact['path'], expected=artifact['sha256']))
        require(e['artifact_ids'] == ['sha256-'+artifact['sha256']], 'native/IR identity mismatch')
        validate_evidence(e, native)
        evidence[variant] = e
    guidance = loads(capture(ROOT/'eval/milestone1/review-guidance.json', 'inputs/review-guidance.json'))
    for name in ['review-guide.md', 'audit-verification.md', 'audit-reproduction.json',
                 'audit-mapping-verification.json', 'audit-checks.json', 'audit-test-output.txt',
                 'audit-round2-claims.json', 'audit-intake-output.txt', 'audit-native-output.txt']:
        capture(ROOT/'eval/milestone1'/name, name)
    original_review = capture(ROOT/'eval/milestone1/reviews/independent-2026-09-10.md',
                              'inputs/independent-review.original.md').decode('utf-8')
    # Preserve source bytes separately; adjust only links in the convenient reading copy.
    files['independent-review.md'] = ('**Historical first review: its source-wording/paraphrase claim is withdrawn. See the [erratum](source-wording-erratum.md).**\n\nNavigation-adjusted copy; [original bytes](inputs/independent-review.original.md).\n\n'
                                    + original_review.replace('](r1/', '](original-r1/')
                                    .replace('](../prepare.py)', '](tooling/prepare-r1.py)')).encode('utf-8')
    for name in ['index.html', 'review.json', 'verification-summary.json']:
        capture(ROOT/'eval/milestone1/reviews/r1'/name, 'original-r1/'+name)
    capture(ROOT/'eval/milestone1/review-support/prepare-r1.py', 'tooling/prepare-r1.py')
    capture(ROOT/'eval/milestone1/reviews/r1/verification-summary.json', 'historical-verification-summary.json')
    for name in ['prepare.py', 'packet.py']:
        capture(ROOT/'eval/milestone1'/name, 'tooling/'+name)
    capture(ROOT/'tests/test_review_packet.py', 'tooling/test_review_packet.py')

    # Preserve the sealed second packet, and bind its explicit correction separately.
    previous = ROOT/'eval/milestone1/reviews/r2'
    prior_manifest = loads(capture(previous/'packet-manifest.json', 'original-r2/packet-manifest.json'))
    for name, digest in prior_manifest['files'].items():
        capture(previous/name, 'original-r2/'+name, digest)
    second_review = capture(ROOT/'eval/milestone1/reviews/independent-r2-2026-09-10.md',
                            'inputs/independent-review-r2.original.md').decode('utf-8')
    files['independent-review-r2.md'] = ('Navigation-adjusted copy; [original bytes](inputs/independent-review-r2.original.md).\n\n'
                                       + second_review.replace('](r2/', '](original-r2/')
                                       .replace('](../../../runs/milestone1-independent-r2/inspection-result.json)',
                                                '](source-inspection/inspection-result.json)')).encode('utf-8')
    capture(ROOT/'eval/milestone1/reviews/erratum-source-wording-2026-09-10.md', 'source-wording-erratum.md')
    inspection_root = ROOT/'runs/milestone1-independent-r2'
    inspection = loads(capture(inspection_root/'inspection-result.json', 'source-inspection/inspection-result.json'))
    require(inspection['input_sha256'] == evidence['clean']['document']['source_document_sha256'],
            'inspection source identity differs from clean IR')
    for item in inspection['artifacts']:
        capture(ROOT/item['path'], 'source-inspection/'+Path(item['path']).name, item['sha256'])
    source_text = files['source-inspection/source-paragraph.txt'].decode('utf-8')
    source_case = next(c for c in cfg['cases'] if c['error_id'] == 'HL-ERR-0006')
    source_nodes = node_selection(evidence['clean'], source_case)
    require(len(source_nodes) == 1, 'source inspection needs a unique clean paragraph')
    comparison = source_comparison(source_text, source_nodes[0]['text'])
    require(comparison['diagnostic_equal'] and inspection['diagnostic_comparison']['equal'],
            'saved source text does not support the claimed diagnostic agreement')
    source_review = {'inspection': inspection, 'comparison': comparison,
                     'clean_evidence_id': source_nodes[0]['id'],
                     'scope': 'Existing targeted clean paragraph inspection only; no new PDF read.'}

    candidates, sections, regions = [], [], []
    for case in cfg['cases']:
        record = records[case['error_id']]
        variants = {}
        content = '<h2 id="' + case['error_id'] + '">' + escape(case['error_id']) + '</h2>'
        content += '<p>' + escape(guidance['cases'][case['error_id']]) + '</p>'
        for variant, e in evidence.items():
            nodes = node_selection(e, case)
            expected = record['original_text'] if variant == 'clean' else record['injected_text']
            matches = []
            for n in nodes:
                offsets, start = [], 0
                while expected and (pos := n['text'].find(expected, start)) != -1:
                    offsets.append([pos, pos+len(expected)])
                    start = pos+len(expected)
                if offsets:
                    matches.append({'evidence_id': n['id'], 'native_pointer': n['native_pointer'],
                                    'text': n['text'], 'source_span': n['source_span'],
                                    'fragments': n['fragments'], 'token_offsets': offsets})
            status = 'proposed' if len(nodes) == len(matches) == 1 and len(matches[0]['token_offsets']) == 1 else 'ambiguous_or_unmapped'
            region = excerpt(e, case['page_index'], case['block_index'])
            variants[variant] = {'status': status, 'expected_source_text': expected, 'candidates': matches,
                                 'generated_ir_sha256': verification['variants'][variant]['evidence_sha256'],
                                 'region': region}
            content += '<h3>' + variant + ' — ' + status + '</h3><p>Source token: <code>' + escape(expected) + '</code></p>'
            for n in matches:
                content += '<pre>' + escape(n['native_pointer']+'\n'+n['evidence_id']+'\n'+n['text']) + '</pre>'
                content += details('Token offsets and complete source spans', n)
            if case['row'] is not None:
                content += table_view(e, case['page_index'], case['block_index'])
            else:
                content += details('Literal source and IR region', region)
        candidates.append({'error_id': case['error_id'], 'evaluation_location': record['location'],
                           'secondary_locations': record['secondary_locations'], 'variants': variants,
                           'review_status': 'pending', 'secondary_ir_mapping_status': 'not_proposed'})
        sections.append(content)
    for region in cfg['additional_evidence']:
        content = f'<h2 id="region-{region["page_index"]}-{region["block_index"]}">Additional evidence: ' + escape(region['purpose']) + '</h2>'
        content += '<p>Independent runs, presented together for evaluator review only. No runtime counterpart access.</p>'
        variants = {}
        for variant, e in evidence.items():
            extracted = excerpt(e, region['page_index'], region['block_index'])
            probes = []
            for n in extracted['nodes']:
                if n['kind'] == 'cell' and n['content_state'] == 'unsupported':
                    try:
                        build_context(e, [n['id']])
                    except ValueError as exc:
                        probes.append({'evidence_id': n['id'], 'state': 'rejected', 'reason': str(exc)})
                    else:
                        raise ValueError('unsupported cell entered context')
            variants[variant] = {'region': extracted, 'context_probes': probes}
            content += '<h3>' + variant + '</h3>' + table_view(e, region['page_index'], region['block_index'])
            if probes:
                content += details('Executed context rejection probe (not a detector result)', probes)
        regions.append({**region, 'variants': variants})
        sections.append(content)
    benign = loads(capture(ROOT/'eval/negatives/milestone1-proposals.json', 'inputs/fixture-proposals.json'))
    fixtures = []
    for fixture in benign['fixtures']:
        snapshot = 'fixtures/'+fixture['fixture_id']+'.native.json'
        raw = capture(ROOT/fixture['input_path'], snapshot)
        item, e, view = fixture_material({**fixture, 'qualification': guidance['fixtures'][fixture['fixture_id']]}, raw)
        fixtures.append(item)
        files[item['ir_snapshot']] = encode(e)
        sections.append(view)
    image_root = ROOT/'eval/reviews/hkex-2025-48/packet-r2'
    image_inventory = loads(capture(image_root/'images.json', 'inputs/source-image-inventory.json'))
    images = []
    view = '<h2 id="source-images">Existing reviewed source images</h2><p>Previously rendered full pages; no PDF was read or rendered for this review. Click an image to inspect at full size. Primary pages: 159, 180, 185. Reference target: 179.</p>'
    for item in image_inventory:
        if item['source_rectangle_pt'] is not None or item['page_index'] not in {158, 178, 179, 184}:
            continue
        snapshot = 'images/'+item['path']
        capture(image_root/item['path'], snapshot, item['sha256'])
        images.append({**item, 'snapshot': snapshot})
        view += '<details><summary>' + escape(item['path']) + '</summary><a href="' + snapshot + '"><img loading="lazy" src="' + snapshot + '" alt="' + escape(item['path']) + '"></a></details>'
    require(len(images) == 8, 'required source image inventory is incomplete')
    sections.append(view)
    packet = {'schema_version': '2.0.0', 'mode': 'fixture', 'review_status': 'pending',
              'reviewer': None, 'reviewed_at': None, 'inputs': inputs, 'candidates': candidates,
              'additional_evidence': regions, 'fixtures': fixtures, 'source_images': images,
              'guidance': guidance, 'source_review': source_review, 'publication_status': 'UNGATED', 'headline': None,
              'acceptance_scope': ['Eight primary native-to-IR occurrence mappings.',
                                   'Displayed evidence limitations and unsupported-content handling.',
                                   'Six qualified fixture expectations; no detector result.']}
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Milestone 1 corrected evidence review</title><style>body{font:16px/1.55 system-ui;max-width:1120px;margin:32px auto;padding:0 24px;color:#18202a}h1,h2{line-height:1.2}h2{border-top:2px solid #dbe2e8;padding-top:24px;margin-top:40px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:16px;font-size:13px}.scroll{overflow:auto}table{border-collapse:collapse;font-size:13px;width:100%}td{border:1px solid #cbd3dc;padding:6px;vertical-align:top}small{display:block;color:#555;font-size:10px}.banner{background:#fff3cd;padding:18px}details{margin:12px 0}img{max-width:100%;height:auto}code{overflow-wrap:anywhere}</style><h1>Milestone 1: corrected review packet</h1><p class="banner">Pending owner acceptance. No detector performance or whole-document PDF fidelity is established. Headline status remains UNGATED.</p><p><a href="review-guide.md">Review guide and decision template</a> · <a href="audit-verification.md">Claim-by-claim verification</a> · <a href="independent-review.md">First audit (historical)</a> · <a href="packet-manifest.json">Approval fingerprint and all file hashes</a> · <a href="review.json">Complete review data</a></p>'''
    html += '<p>Content fingerprint: <code>' + fingerprint(packet) + '</code>. The approval identifier is the <strong>approval_fingerprint in packet-manifest.json</strong>, which also binds this HTML and every bundled file. Record that exact value with your decisions.</p>'
    html += '<p class="banner">' + escape(guidance['fidelity_statement']) + '</p>'
    html += '<p><a href="source-wording-erratum.md">Explicit erratum</a> · <a href="independent-review-r2.md">Second independent audit</a> · <a href="#source-inspection">High-resolution source evidence</a></p>'
    html += '<nav>Review: ' + ' · '.join('<a href="#'+c['error_id']+'">'+c['error_id']+'</a>' for c in cfg['cases'])
    html += ' · <a href="#region-123-0">Partial table</a> · ' + ' · '.join('<a href="#fixture-'+f['fixture_id']+'">'+f['fixture_id']+'</a>' for f in fixtures) + ' · <a href="#source-images">Source images</a></nav>'
    sections.append('<h2 id="source-inspection">Targeted source evidence from the second audit</h2>'
                    '<p>The second auditor read and rendered only the clean page-185 paragraph after recording a rationale. '
                    'This revision reuses those hash-verified artifacts; it reads no PDF. The image shows 採用 and 雙重機制. '
                    'Diagnostic agreement ignores whitespace and fullwidth/ASCII parentheses; literal formatting and whole-document fidelity are not certified.</p>'
                    '<a href="source-inspection/source-paragraph.png"><img src="source-inspection/source-paragraph.png" alt="Previously rendered clean page-185 paragraph; source wording 採用"></a>'
                    '<p><a href="source-inspection/source-paragraph.txt">Saved source text</a> · '
                    '<a href="source-inspection/inspection-plan.json">Pre-inspection rationale</a> · '
                    '<a href="source-inspection/inspection-result.json">Scope, identity and artifact hashes</a></p>'
                    + details('Source comparison and provenance', source_review))
    files['index.html'] = (html + ''.join(sections) + '</html>\n').encode('utf-8')
    manifest = seal(output, packet, files)
    verify(output, manifest['approval_fingerprint'], ROOT)
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    result = prepare(a.runs, a.output)
    print('Review packet pending owner acceptance:', result['approval_fingerprint'])
