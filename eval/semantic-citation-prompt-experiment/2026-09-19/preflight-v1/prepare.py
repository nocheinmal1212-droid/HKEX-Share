"""Exclusive-write offline preparation; no credentials, transport or saved answers."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parent
RUNS = ROOT/'runs/semantic-citation-prompt-experiment-2026-09-19'
PREP = RUNS/'prepared-v1'
LIVE = RUNS/'live-v1'
PRIOR = ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v2'
OLD = ROOT/'runs/semantic-citation-confirmation-2026-09-19/prepared-v2'
CITATION = ('support_refs is the full citation list. It must contain target_id, every ID in '
            'contributor_ids, and the source-group IDs establishing their membership or hierarchy, '
            'including the group defining a selected subtotal even when the target is outside that '
            'group. Repeat target_id and every contributor_ids entry inside support_refs; appearing '
            'in another field does not satisfy this requirement. Do not put only contextual group '
            'IDs in support_refs.')
STATE = ('If the source supports a complete immediate contributor selection for this target, '
         'set state to "selected" and put exactly those contributor IDs in contributor_ids. '
         'Do not use an abstention state when returning a contributor selection. For missing_evidence, '
         'ambiguous, incompatible_context or not_a_total, set contributor_ids to []. Choose the '
         'abstention state using the existing evidence/context rules; do not convert uncertainty '
         'into selected.')

def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

def preservation():
    paths = [PRIOR/'freeze.json',
             ROOT/'runs/semantic-citation-confirmation-2026-09-19/evaluation-v2/artifact-integrity.json',
             ROOT/'runs/semantic-citation-failure-investigation-2026-09-19/v1/integrity.json']
    counts = []
    for p in paths:
        files = read(p)['files']
        for name, expected in files.items():
            assert sha(ROOT/name) == expected, 'historical drift: '+name
        counts.append({'manifest':str(p.relative_to(ROOT)), 'sha256':sha(p),'members':len(files)})
    old = ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v1/freeze.json'
    assert sha(old) == 'f98cab8947112698dc2e8d58ba30441dc6d8f40f3d1a35125994ce50a34e7643'
    assert not (ROOT/'runs/semantic-citation-confirmation-2026-09-19/live-v1').exists()
    return counts

def call(arm, function, payload):
    src = PREP/arm/'runtime-snapshot/src'
    code = 'import sys,json;sys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_cli import '+function+';'+function+'(json.load(sys.stdin))'
    p = subprocess.run([sys.executable,'-I','-B','-c',code,str(src)], input=json.dumps(payload),
                       text=True,capture_output=True,env={},timeout=180,check=True)
    return json.loads(p.stdout)

def main():
    assert not PREP.exists() and not LIVE.exists()
    put(RUNS/'checks-v1/preservation-before.json', preservation())
    identity = read(PRIOR/'execution-identity.json')
    original = (ROOT/'src/hkex_audit/semantic.py').read_text()
    tree = ast.parse(original)
    prompt = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id','')=='PROMPT' for t in n.targets))
    selection, specs = read(OLD/'selection.json'), read(OLD/'queries.json')
    assert [s['name'] for s in specs] == ['total','period_groups']
    put(PREP/'selection.json',selection); put(PREP/'queries.json',specs)
    shutil.copyfile(PRIOR/'expectations.json', PACKET/'expectations.json')
    bindings = {}
    cost = 0
    from decimal import Decimal
    cost = Decimal(0)
    for arm, blocks in {'A':[], 'B':[CITATION], 'C':[STATE], 'D':[CITATION,STATE]}.items():
        snapshot = PREP/arm/'runtime-snapshot'
        for name, expected in identity['runtime_files'].items():
            assert sha(ROOT/name) == expected
            dst = snapshot/name; dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,dst)
        new_prompt = prompt + (('\n\n'+'\n\n'.join(blocks)) if blocks else '')
        version = 'direct-contributor-headers-1.1.0' if arm=='A' else 'direct-contributor-headers-1.1.0-prompt-experiment-1-'+arm
        if arm != 'A':
            modified = original.replace("VERSION = 'direct-contributor-headers-1.1.0'",'VERSION = '+repr(version))
            modified = modified.replace('PROMPT = '+repr(prompt), 'PROMPT = '+repr(new_prompt)) if 'PROMPT = '+repr(prompt) in modified else modified.replace("PROMPT = '''"+prompt+"'''",'PROMPT = '+repr(new_prompt))
            assert modified != original
            (snapshot/'src/hkex_audit/semantic.py').write_text(modified)
        nonce = LIVE.name+'-'+arm
        queries = call(arm,'prepare_worker',{'selection':selection,'specs':specs})['queries']
        requests = []
        for q in queries:
            assert q['prompt']==new_prompt and q['version']==version
            old = read(OLD/q['selection']['name']/'query.json')
            assert {k:v for k,v in q.items() if k not in ('prompt','version','query_id')} == {k:v for k,v in old.items() if k not in ('prompt','version','query_id')}
            name=q['selection']['name']; put(PREP/arm/name/'query.json',q)
            code='import sys,json;sys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_attempt import request; p=json.load(sys.stdin);print(json.dumps({r:request(p["query"],r,p["nonce"]) for r in ("primary","research")}))'
            p=subprocess.run([sys.executable,'-I','-B','-c',code,str(snapshot/'src')],input=json.dumps({'query':q,'nonce':nonce}),text=True,capture_output=True,env={},check=True,timeout=30)
            reqs=json.loads(p.stdout)
            assert reqs['primary']['semantic_payload_sha256']==reqs['research']['semantic_payload_sha256']
            for role,req in reqs.items():
                put(PREP/arm/name/(role+'-request.json'),req)
                # Same canonical UTF-8 encoding as runtime artifacts.encode.
                payload=json.dumps(req['payload'],ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n'
                estimate=Decimal(len(payload)+4096)*Decimal('.000010')+Decimal(4096)*Decimal('.000020')
                cost+=estimate
                requests.append({'case':name,'role':role,'attempt_id':req['attempt_id'],'reservation_usd':str(estimate)})
        bindings[arm]={'nonce':nonce,'output':str(LIVE/nonce),'operation':version,'added_blocks':blocks,'requests':requests,
                       'runtime_files':{str(p.relative_to(snapshot)):sha(p) for p in snapshot.rglob('*') if p.is_file()}}
    assert cost <= Decimal('16')
    put(PACKET/'arms.json',bindings)
    put(PACKET/'environment.json',identity['environment'])
    schedule=[{'arm':a,'case':'total'} for a in 'ABDC']+[{'arm':a,'case':'period_groups'} for a in 'CDBA']
    put(PACKET/'launch-proposal.json',{'version':'prompt-factorial-1.0.0','live_authorization':False,
        'output':str(LIVE),'nonce':LIVE.name,'schedule':schedule,'ceilings':{'http_calls':18,'metadata_gets':2,
        'completions':16,'per_role':8,'seconds_total':900,'seconds_per_attempt':60,'reservation_usd':'16',
        'output_tokens':4096,'retries':0,'fallbacks':0},'full_reservation_usd':str(cost),
        'argv':[sys.executable,'-I','-B',str(PACKET/'launch.py'),'--expected-sha256','APPROVED_FREEZE_SHA256'],
        'credential_source':'OPENROUTER_API_KEY only; no dotenv or other environment entries read',
        'availability_and_pricing':'Unknown until newly authorized metadata checks'})
    print(json.dumps({'arms':4,'requests':16,'reservation_usd':str(cost),'live_output_exists':LIVE.exists()}))

if __name__=='__main__': main()
