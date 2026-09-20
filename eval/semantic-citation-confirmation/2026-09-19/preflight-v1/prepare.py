"""One-shot OFFLINE preparation. No dispatch, transport, credential or model access."""
import os
os.environ = {}  # Do not inspect or forward the host environment.
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import sys
import sysconfig
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from hkex_audit import semantic, semantic_attempt, semantic_cli, header_support, contracts
from hkex_audit.artifacts import read, encode, sha, fingerprint, write_new

PACKET = Path(__file__).resolve().parent
PREP = ROOT / 'runs/semantic-citation-confirmation-2026-09-19/prepared-v1'
LIVE = ROOT / 'runs/semantic-citation-confirmation-2026-09-19/live-v1'


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    write_new(path, data)


def inventory():
    return {str(p.relative_to(ROOT)): sha(p.read_bytes())
            for base in ('src', 'schemas') for p in sorted((ROOT/base).rglob('*'))
            if p.is_file() and p.suffix in ('.py', '.json')}


def environment():
    distributions = {}
    for name in ('attrs', 'jsonschema', 'jsonschema-specifications', 'referencing', 'rpds-py'):
        d = metadata.distribution(name)
        files = {str(d.locate_file(f).absolute()): sha(d.locate_file(f).read_bytes())
                 for f in d.files if str(f).endswith(('.py', '.json', '.so', '.dylib', '.txt'))
                 or Path(str(f)).name in ('METADATA', 'WHEEL', 'RECORD', 'INSTALLER')}
        distributions[name] = {'version': d.version, 'requires': d.requires, 'files': files}
    return {'executable': sys.executable, 'executable_realpath': str(Path(sys.executable).resolve()),
            'executable_sha256': sha(Path(sys.executable).read_bytes()), 'version': sys.version,
            'prefix': sys.prefix, 'base_prefix': sys.base_prefix, 'soabi': sysconfig.get_config_var('SOABI'),
            'pyvenv_cfg_sha256': sha((Path(sys.prefix)/'pyvenv.cfg').read_bytes()),
            'distributions': distributions}


def main():
    assert not LIVE.exists()
    corrected = read(ROOT/'eval/semantic-citation-implementation/1.1.1/implementation-bindings.json')
    assert all(sha((ROOT/p).read_bytes()) == h for p,h in corrected['files'].items())
    assert semantic.VERSION == corrected['operation_version']
    assert semantic_attempt.VERSION == corrected['attempt_version']
    assert sha(semantic.PROMPT.encode()) == corrected['prompt_sha256']
    assert fingerprint(semantic.SCHEMA) == corrected['schema_sha256']
    assert header_support.policy_identity() == corrected['policy']
    assert semantic_cli.runtime_identity() == corrected['runtime_sha256']
    assert semantic_attempt.CONFIGS == corrected['configurations']
    selection = semantic_cli.normalized_selection(ROOT/'runs/paired-semantic-integration-2026-09-18/selection.json')
    retained = read(ROOT/'runs/paired-semantic-integration-2026-09-18/queries.json')
    specs = [next(s for s in retained if s['name'] == n) for n in ('total', 'period_groups')]
    put(PREP/'selection.json', selection)
    put(PREP/'queries.json', specs)
    prepared = semantic_cli.isolated('prepare_worker', {'selection':selection, 'specs':specs})
    put(PREP/'preparation.json', prepared)
    evidence = read(selection['evidence']['path'])
    nodes = {n['id']: n for n in evidence['nodes']}
    source_packet_path = ROOT/'eval/semantic-integration/2026-09-18/source-review-packet.json'
    source_packet = read(source_packet_path)
    assert all(n == nodes[n['id']] for n in source_packet['nodes'])
    review_path = ROOT/'eval/semantic-citation-investigation/2026-09-19/independent-source-review.json'
    review = read(review_path)
    expectations = []
    query_bindings = []
    for q in prepared['queries']:
        semantic.verify_query(evidence, q)
        assert q['gate'] == 'eligible'
        name = q['selection']['name']
        ex = next(c for c in review['original_cases'] if c['case'] == name)
        assert ex['freeze_ready'] and ex['adjudicated_state'] == 'selected'
        assert q['selection']['target_id'] == ex['target_id']
        assert all(i in {n['id'] for n in q['context']['items']}
                   for i in ex['required_support_ids'] + ex['optional_support_ids'])
        for citation in ex['source_citations']:
            n = nodes[citation['node_id']]
            assert n['text'] == citation['literal_text']
            for key in ('parent_id','page_index','row','column','row_span','column_span','fragments','native_pointer','source_span'):
                assert n[key] == citation[key]
        expectations.append({'name': name, 'query_id':q['query_id'], 'target_id':ex['target_id'],
            'expected_status':'selected', 'expected_contributor_header_ids':ex['contributor_ids'],
            'required_support_ids':ex['required_support_ids'], 'optional_support_ids':ex['optional_support_ids'],
            'review_rationale_verbatim':ex['reason'], 'source_citations':ex['source_citations'],
            'required_support_reasons':ex['required_support'], 'optional_support_reasons':ex['optional_support']})
        put(PREP/name/'query.json', q)
        reqs = {r:semantic_attempt.request(q,r,LIVE.name) for r in semantic_attempt.CONFIGS}
        assert reqs['primary']['semantic_payload_sha256'] == reqs['research']['semantic_payload_sha256']
        assert reqs['primary']['attempt_id'] != reqs['research']['attempt_id']
        for r,req in reqs.items():
            put(PREP/name/(r+'-request.json'), req)
        query_bindings.append({'name':name, 'query_id':q['query_id'], 'query_sha256':fingerprint(q),
            'gate':q['gate'], 'projection_items':len(q['context']['items']),
            'role_attempt_ids':{r:v['attempt_id'] for r,v in reqs.items()},
            'semantic_payload_sha256':reqs['primary']['semantic_payload_sha256'],
            'conservative_reservations_usd':{r:str(Decimal(len(encode(v['payload']))+4096)*Decimal('.000010')+Decimal(4096)*Decimal('.000020')) for r,v in reqs.items()}})
    put(PACKET/'expectations.json', {'version':'confirmation-conditional-citation-expectations-1.0.0',
        'evaluator_only':True, 'model_results':False,
        'migration':'Same-agent, post-exposure migration of existing source-only judgments to operation 1.1; no new independent/blind/domain approval. Common display units are optional by operation scope, never because of old pass counts.',
        'terminology':'In the total review rationale, descendants describes semantic summary components, not physical containment: 合計 and the two timing headers are siblings under the revenue group. The finite summary rule establishes their relationship.',
        'source_review':str(review_path.relative_to(ROOT)), 'source_review_sha256':sha(review_path.read_bytes()),
        'source_packet':str(source_packet_path.relative_to(ROOT)), 'source_packet_sha256':sha(source_packet_path.read_bytes()),
        'queries':expectations})
    put(PACKET/'query-bindings.json', query_bindings)
    put(PACKET/'source-verification.json', {'selection':selection,
        'source_packet_nodes_identical':len(source_packet['nodes']), 'projections_reconstructed':True,
        'literal_2026_caption_preserved':any(n['text']=='截至2026年12月31日止年度' for n in prepared['queries'][0]['context']['items']),
        'units_preserved':[any(n['text']=='港幣百萬元' for n in q['context']['items']) for q in prepared['queries']],
        'new_semantic_judgment_required':False})
    runtime_files = inventory()
    runtime_files['pyproject.toml'] = sha((ROOT/'pyproject.toml').read_bytes())
    for path,h in runtime_files.items():
        dest = PREP/'runtime-snapshot'/path
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f: f.write((ROOT/path).read_bytes())
        assert sha(dest.read_bytes()) == h
    with (PREP/'prompt.txt').open('xb') as f: f.write(semantic.PROMPT.encode('utf-8'))
    put(PREP/'response-schema.json', semantic.SCHEMA)
    put(PREP/'configurations.json', semantic_attempt.CONFIGS)
    put(PACKET/'execution-identity.json', {'runtime_files':runtime_files, 'environment':environment(),
        'modules':{m.__name__:str(Path(m.__file__).resolve()) for m in (semantic,semantic_attempt,semantic_cli,header_support,contracts)},
        'operation':semantic.VERSION,'attempt':semantic_attempt.VERSION,'batch':semantic_cli.BATCH_VERSION,
        'policy':header_support.policy_identity(),'runtime_identity':semantic_cli.runtime_identity(),
        'prompt_sha256':sha(semantic.PROMPT.encode()),'schema_sha256':fingerprint(semantic.SCHEMA),
        'schema_fields':semantic.SCHEMA['required'],'snapshot':str((PREP/'runtime-snapshot').relative_to(ROOT)),
        'launch_source_path':str(ROOT/'src'),'installed_wheel_used':False})
    bootstrap = 'import sys;sys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_cli import main;raise SystemExit(main(sys.argv[2:]))'
    argv = [sys.executable,'-I','-B','-c',bootstrap,str(ROOT/'src'),'run',
        '--selection',str(PREP/'selection.json'),'--queries',str(PREP/'queries.json'),
        '--output',str(LIVE),'--max-http-calls','6','--max-role-calls','2',
        '--max-seconds','600','--max-cost','8']
    put(PACKET/'launch-proposal.json', {'authorization':'NONE; preparation only', 'argv':argv,
        'cwd':str(ROOT),'nonce':LIVE.name,'live_output':str(LIVE),'live_output_exists':False,
        'bootstrap_credentials':False, 'ceilings':{'http_calls':6,'metadata_gets':2,'primary_completions':2,
        'research_completions':2,'seconds_total':600,'seconds_per_attempt':60,'reservation_usd':'8',
        'output_tokens_per_completion':4096,'retries':0,'fallbacks':0},
        'prelaunch_binding_requirement':'Offline check must pass against approved freeze before any credential/provider activity; any drift stops, no silent regeneration.',
        'provider_availability_and_price':'Unknown; no metadata calls made.'})
    print(json.dumps({'prepared':query_bindings, 'snapshot_files':len(runtime_files), 'live_exists':LIVE.exists()}))


if __name__ == '__main__': main()
