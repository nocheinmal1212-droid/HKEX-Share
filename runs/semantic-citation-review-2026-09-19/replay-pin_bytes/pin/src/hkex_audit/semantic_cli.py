"""Single-batch selected-IR semantic integration and zero-call operational replay."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from audit_inputs import descriptors, selected_files, safe_path
from audit_inputs.guard import install
from .artifacts import read, read_bytes, loads, encode, sha, fingerprint, require, write_new
from .contracts import preload, HASHES
from .consumer import inspect
from .semantic import project, verify_query, annotation
from .semantic_attempt import CONFIGS, FILES, Store, request, dispatch, replay


def isolated(function, payload, timeout=180):
    bootstrap = 'import sys,json;sys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_cli import '+function+';'+function+'(json.load(sys.stdin))'
    proc = subprocess.run([sys.executable, '-I', '-B', '-c', bootstrap, str(Path(__file__).resolve().parents[1])],
                          input=json.dumps(payload), text=True, capture_output=True, timeout=timeout, close_fds=True,
                          env={k:v for k,v in os.environ.items() if k != 'OPENROUTER_API_KEY'})
    require(proc.returncode == 0, 'isolated semantic worker failed: ' + proc.stderr[-1200:])
    return loads(proc.stdout)


def load_evidence(selection):
    paths = selected_files(selection)
    raw = [read_bytes(p) for p in paths]
    require(all(sha(b) == d['sha256'] for b,d in zip(raw, descriptors(selection))), 'selected hash mismatch')
    require(all(not b.lstrip().startswith(b'%PDF') for b in raw), 'PDF content forbidden')
    evidence, manifest = map(loads, raw)
    require(manifest['document'] == selection['document'] and manifest['schema_hashes'] == HASHES, 'IR contract mismatch')
    inspect(evidence, manifest)
    return evidence


def prepare_worker(payload):
    preload(); selection = payload['selection']; paths = selected_files(selection)
    attempts = install(paths)
    evidence = load_evidence(selection)
    queries = [project(evidence, spec) for spec in payload['specs']]
    print(encode({'queries': queries, 'access_attempts': attempts}).decode())


def consume_worker(payload):
    preload(); selection = payload['selection']; paths = selected_files(selection)
    directory = Path(payload['batch']) / 'primary' / payload['spec']['name']
    output = Path(payload['output'])
    attempts = install([*paths, *(directory / n for n in FILES)],
                       [output / n for n in ('annotations.json','provenance.json','consumption.json')])
    evidence = load_evidence(selection); query = project(evidence, payload['spec'])
    result = replay(Store(directory), query, 'primary', payload['nonce'])
    records = []
    if result.get('validation', {}).get('state') in {'accepted', 'abstained'}:
        records = [annotation(evidence, query, result['attempt_id'], result['validation']['answer'])]
    provenance = {'version': 'semantic-provenance-1.0.0', 'query_id': query['query_id'], 'query_sha256': fingerprint(query),
                  'source_sha256': query['source_sha256'], 'selection': query['selection'],
                  'primary_attempt_id': request(query, 'primary', payload['nonce'])['attempt_id'],
                  'primary_completion_sha256': sha(read_bytes(directory / 'completion.json')) if records else None,
                  'annotation_ids': [a['annotation_id'] for a in records], 'annotations_sha256': fingerprint(records),
                  'outcome': result.get('validation', {}).get('state', result.get('state'))}
    write_new(output / 'annotations.json', records); write_new(output / 'provenance.json', provenance)
    write_new(output / 'consumption.json', {'outcome': provenance['outcome'], 'access_attempts': attempts.copy(),
                                         'adapter_imported': any(k.startswith('hkex_audit.adapters') for k in sys.modules),
                                         'model_calls': 0})
    print(encode(provenance).decode())


def research_replay_worker(payload):
    preload(); selection=payload['selection']; paths=selected_files(selection)
    directory=Path(payload['batch'])/'research'/payload['spec']['name']
    attempts=install([*paths,*(directory/n for n in FILES)])
    evidence=load_evidence(selection);query=project(evidence,payload['spec'])
    result=replay(Store(directory),query,'research',payload['nonce'])
    print(encode({'query_id':query['query_id'],'result':result,'access_attempts':attempts}).decode())


def transport(job):
    bootstrap = 'import sys;sys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_transport import main;main()'
    try:
        proc = subprocess.run([sys.executable,'-I','-B','-c',bootstrap,str(Path(__file__).resolve().parents[1])],
                              input=json.dumps(job), text=True, capture_output=True, timeout=60, close_fds=True)
        return loads(proc.stdout) if proc.returncode == 0 else {'transport_status':'transport_error'}
    except subprocess.TimeoutExpired:
        return {'transport_status':'timeout'}


def bootstrap_key(root):
    """Optional explicit owner-approved root bootstrap. Never forwarded as argv/artifact."""
    if os.environ.get('OPENROUTER_API_KEY'):
        return
    path = Path(root) / '.env'
    require(not path.is_symlink(), 'credential symlink forbidden')
    if not path.is_file(): return
    for line in path.read_text().splitlines():
        if line.startswith('OPENROUTER_API_KEY='):
            value = line.split('=',1)[1].strip().strip('"\'')
            if value: os.environ['OPENROUTER_API_KEY'] = value


def paired(query, nonce, primary_store, research_store, primary_transport, research_transport, consume):
    """Primary consumption happens before waiting on the research future. Two slots maximum."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        primary = pool.submit(dispatch, query, request(query,'primary',nonce), primary_transport, primary_store)
        research = pool.submit(dispatch, query, request(query,'research',nonce), research_transport, research_store)
        p = primary.result()
        try:
            consumed = consume()  # reads committed primary only, even on commit_unknown
        except (OSError, ValueError):
            consumed = {'outcome':'persistence_failure','reason':'operational_consumption_failed'}
        r = research.result()
    return {'primary': p, 'research': r, 'consumption': consumed}


def json_input(path):
    path = safe_path(path, Path.cwd())
    require(path.suffix == '.json' and not any(p.startswith('.env') or p == 'APIKEY.txt' for p in path.parts), 'only explicit noncredential JSON inputs allowed')
    return path


def normalized_selection(path):
    path = json_input(path)
    selection = read(path); require(selection['mode']=='ir', 'semantic operation requires saved IR')
    for d,p in zip(descriptors(selection), selected_files(selection,path.parent)): d['path']=str(json_input(p))
    return selection


def new_directory(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in [path,*path.parents]), 'symlink directory forbidden')
    require(not any(p in path.parts for p in ('eval','corpus','.git')), 'protected output')
    require(not path.exists(), 'output exists; use a fresh directory')
    path.mkdir(parents=True)
    return path.resolve()


def run(args):
    selection = normalized_selection(args.selection)
    specs = read(json_input(args.queries))
    require(isinstance(specs,list) and 0 < len(specs) <= 6, 'one to six queries required')
    require(len({s['name'] for s in specs}) == len(specs), 'duplicate query name')
    prepared = isolated('prepare_worker', {'selection':selection,'specs':specs})
    output = new_directory(args.output)
    nonce = output.name
    config = {'version':'semantic-batch-1.0.0','nonce':nonce,'selection':selection,'specs':specs,
              'runtime_code_sha256': fingerprint({p:sha((Path(__file__).parent/p).read_bytes()) for p in ('semantic.py','semantic_attempt.py','semantic_cli.py','semantic_transport.py')}),
              'limits': {'max_http_calls': args.max_http_calls,'max_completion_calls_per_role':args.max_role_calls,
                         'max_seconds':args.max_seconds,'max_cost_usd':str(args.max_cost)}, 'configurations':CONFIGS}
    require(args.max_http_calls >= 2 and 0 <= args.max_role_calls <= 6 and 0 < args.max_seconds <= 900 and 0 < args.max_cost <= Decimal('20'), 'invalid investigation bounds')
    write_new(output/'batch.json',config); write_new(output/'prepared.json',prepared)
    if args.env_root: bootstrap_key(args.env_root)
    require(bool(os.environ.get('OPENROUTER_API_KEY')), 'OPENROUTER_API_KEY absent; prepared batch retained, no calls')
    start = time.monotonic(); http_calls = 0; metadata = {}; reserves = {}; role_calls = {r:0 for r in CONFIGS}
    # Metadata is part of the declared HTTP/time budget, even when it fails.
    for role, c in CONFIGS.items():
        if http_calls >= args.max_http_calls or time.monotonic()-start+60 > args.max_seconds:
            metadata[role]={'transport_status':'budget_exhausted'}; reserves[role]=None
            write_new(output/(role+'-metadata.json'),metadata[role]); continue
        http_calls += 1
        record=transport({'mode':'metadata','role':role}); metadata[role]=record; reserves[role]=None
        try:
            require(record['transport_status']=='ok','metadata unavailable')
            data=loads(base64.b64decode(record['body_base64']))['data']
            require(data['id']==c['model'], 'advertised model mismatch')
            endpoints=[e for e in data['endpoints'] if e.get('tag')==c['route'] and e.get('status')==0]
            require(len(endpoints)==1,'exact route not available')
            ep=endpoints[0]
            require(ep['provider_name']==c['served_provider'], 'advertised provider mismatch')
            require({'structured_outputs','response_format','temperature','max_tokens'} <= set(ep['supported_parameters']), 'required controls unavailable')
            prices=ep['pricing']; prompt=Decimal(prices['prompt']); completion=Decimal(prices['completion'])
            require(prompt.is_finite() and completion.is_finite() and prompt>=0 and completion>=0,'invalid advertised price')
            # UTF-8 bytes conservatively bound token count; reserve full output cap. Unknown
            # non-token charges fail closed; advertised prices/revisions are not immutable.
            require(prompt <= Decimal('0.000005') and completion <= Decimal('0.000020'), 'price exceeds frozen route cap')
            require(Decimal(str(prices.get('request',0))) == 0, 'per-request charges unsupported')
            require(Decimal(str(prices.get('internal_reasoning',completion))) <= Decimal('0.000020'), 'reasoning price exceeds cap')
            # Text-only, no search/tools/audio/images. Reserve route price ceilings,
            # not a mutable discounted quote. Cache charges conservatively doubled.
            reserves[role]=(Decimal('0.000010'),Decimal('0.000020'))
        except (KeyError,ValueError,TypeError,ArithmeticError):
            record['availability_validation']='unavailable_or_unsupported'
        write_new(output/(role+'-metadata.json'),record)
    reserved=Decimal(0); results=[]
    for query in prepared['queries']:
        decisions={}
        for role in CONFIGS:
            reason=None; estimate=Decimal(0)
            req=request(query,role,nonce)
            if query['gate']=='eligible':
                if reserves[role] is None: reason='unavailable'
                else:
                    prompt,completion=reserves[role]
                    estimate=Decimal(len(encode(req['payload']))+4096)*prompt+Decimal(4096)*completion
                    if (http_calls>=args.max_http_calls or role_calls[role]>=args.max_role_calls or
                        time.monotonic()-start+60>args.max_seconds or reserved+estimate>args.max_cost): reason='budget_exhausted'
                if reason is None:
                    http_calls+=1; role_calls[role]+=1; reserved+=estimate
            decisions[role]={'reason':reason,'reserved_cost_usd':str(estimate) if reason is None else '0'}
        for role in CONFIGS: (output/role/query['selection']['name']).mkdir(parents=True)
        dest=output/'operational'/query['selection']['name'];dest.mkdir(parents=True)
        def send(role):
            def execute(req):
                reason=decisions[role]['reason']
                if reason: return {'transport_status':reason,'reason':'pre_dispatch_availability_or_budget'}
                return transport({'mode':'completion','role':role,'payload':req['payload']})
            return execute
        result=paired(query,nonce,Store(output/'primary'/query['selection']['name']),Store(output/'research'/query['selection']['name']),
                      send('primary'),send('research'),
                      lambda:isolated('consume_worker',{'selection':selection,'spec':query['selection'],'batch':str(output),'output':str(dest),'nonce':nonce}))
        results.append({'name':query['selection']['name'],'query_id':query['query_id'],'dispatch_reservations':decisions,**result})
        write_new(output/(query['selection']['name']+'-summary.json'),results[-1])
        print(query['selection']['name']+': '+result['consumption']['outcome'],flush=True)
    write_new(output/'summary.json',{'results':results,'http_calls_reserved':http_calls,'completion_calls_reserved':role_calls,
                                   'cost_reserved_usd':str(reserved),'elapsed_seconds':time.monotonic()-start,
                                   'limits':config['limits'],'plans_checks_findings':'not_implemented'})
    return 0


def replay_batch(args):
    batch=Path(args.batch).resolve(); config=read(safe_path(batch/'batch.json'))
    require(config['configurations']==CONFIGS, 'replay configuration mismatch')
    selection=normalized_selection(args.selection)
    require(selection==config['selection'], 'replay input selection mismatch')
    # Validate caller-controlled names/IDs before constructing any output subdirectory.
    isolated('prepare_worker',{'selection':selection,'specs':config['specs']})
    output=new_directory(args.output); results=[]
    for spec in config['specs']:
        dest=output/spec['name'];dest.mkdir()
        results.append(isolated('research_replay_worker' if args.command=='research-replay' else 'consume_worker',{'selection':selection,'spec':spec,'batch':str(batch),'output':str(dest),'nonce':config['nonce']}))
    write_new(output/'summary.json',{'model_calls':0,'role':'research' if args.command=='research-replay' else 'primary','results':results})
    return 0


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    live=sub.add_parser('run'); live.add_argument('--queries',required=True,type=Path)
    live.add_argument('--max-http-calls',required=True,type=int);live.add_argument('--max-role-calls',required=True,type=int)
    live.add_argument('--max-seconds',required=True,type=int);live.add_argument('--max-cost',required=True,type=Decimal)
    live.add_argument('--env-root',type=Path)
    replay_parser=sub.add_parser('replay');replay_parser.add_argument('--batch',required=True,type=Path)
    research_parser=sub.add_parser('research-replay');research_parser.add_argument('--batch',required=True,type=Path)
    for p in (live,replay_parser,research_parser):
        p.add_argument('--selection',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv)
    try: return run(args) if args.command=='run' else replay_batch(args)
    except (ValueError,OSError) as exc:
        print('semantic failure: '+type(exc).__name__+': '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':
    raise SystemExit(main())
