"""Explicitly authored offline substitutions for real cancellation tests; never live transport."""
import os
os.environ = {'OPENROUTER_API_KEY':'INERT-AUTHORED-FIXTURE'}
import base64
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit import semantic_cli as cli
from hkex_audit.artifacts import read, encode
from hkex_audit.semantic_attempt import CONFIGS, Store
PREP=ROOT/'runs/semantic-citation-confirmation-2026-09-19/prepared-v1'
EX=read(ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v1/expectations.json')
PREPARED=read(PREP/'preparation.json')

def deny_network(event,args):
    if event in {'socket.__new__','socket.connect','socket.getaddrinfo'}:
        raise AssertionError('offline fixture attempted network')
sys.addaudithook(deny_network)

def response(name,role,state='selected'):
    e=next(e for e in EX['queries'] if e['name']==name)
    a={'target_id':e['target_id'],'state':state,'contributor_ids':e['expected_contributor_header_ids'] if state=='selected' else [],'support_refs':e['required_support_ids']}
    b={'model':CONFIGS[role]['model'],'provider':CONFIGS[role]['served_provider'],'id':'AUTHORED-OFFLINE',
       'choices':[{'finish_reason':'stop','message':{'content':json.dumps(a)}}]}
    return {'transport_status':'ok','request_started':True,'body_base64':base64.b64encode(encode(b)).decode()}

def metadata(role):
    c=CONFIGS[role]
    b={'data':{'id':c['model'],'endpoints':[{'tag':c['route'],'status':0,'provider_name':c['served_provider'],
        'supported_parameters':['structured_outputs','response_format','temperature','max_tokens'],
        'pricing':{'prompt':'.000005','completion':'.000020','request':'0'}}]}}
    return {'transport_status':'ok','request_started':True,'body_base64':base64.b64encode(encode(b)).decode()}

def main(payload):
    mode=payload.pop('fixture_mode'); output=Path(payload['output'])
    original_isolated=cli.isolated; original_write=Store.write
    def marker(name,value):
        (output/name).write_text(json.dumps(value))
    def stall(stage, descendant=False):
        marker('stage.json',{'stage':stage,'pid':os.getpid(),'monotonic':time.monotonic()})
        if descendant:
            # Authored transport subprocess and its owned descendant both inherit the
            # run session. The parent deliberately waits; only the supervisor can stop it.
            child = 'import os,signal,time,pathlib;signal.signal(signal.SIGTERM,signal.SIG_IGN);pathlib.Path('+repr(str(output/('descendant-ready-'+stage)))+').write_text(str(os.getpid()));time.sleep(120)'
            code = 'import subprocess,sys,json,pathlib,time;p=subprocess.Popen([sys.executable,"-I","-B","-c",'+repr(child)+'],env={});pathlib.Path('+repr(str(output/('descendant-'+stage+'.json')))+').write_text(json.dumps({"pid":p.pid}));p.wait()'
            p=subprocess.Popen([sys.executable,'-I','-B','-c',code],env={})
            marker('transport-'+stage+'.json',{'pid':p.pid})
            p.wait()
        else:
            time.sleep(120)
    def isolated(function,data,timeout=180):
        if function=='prepare_worker':
            if mode=='preparation':stall('preparation',True)
            return PREPARED
        if mode=='consumption':
            (Path(data['output'])/'annotations.json').write_bytes(b'[')
            stall('consumption')
        return original_isolated(function,data,timeout=timeout)
    def transport(job,timeout=60):
        role=job['role']
        if job['mode']=='metadata':
            if mode=='metadata' or (mode=='between_metadata' and role=='research'):
                stall('metadata-'+role,True)
            return metadata(role)
        name=next(q['selection']['name'] for q in PREPARED['queries'] if q['context']['target_id']==json.loads(job['payload']['messages'][1]['content'])['target_id'])
        if mode=='paired':stall('paired-'+role,role=='research')
        if mode=='slow_research' and role=='research':stall('research',True)
        if mode=='between_queries' and name=='period_groups':stall('second-query-'+role)
        if mode=='primary_failure' and role=='primary':return {'transport_status':'timeout','request_started':True}
        return response(name,role,'ambiguous' if mode=='primary_abstention' and role=='primary' else 'selected')
    def write(store,name,value):
        if mode=='partial_response' and name=='response.json' and '/primary/' in str(store.directory):
            (store.directory/name).write_bytes(b'{"partial":')
            stall('response-persistence')
        original_write(store,name,value)
    cli.isolated=isolated;cli.transport=transport;Store.write=write
    cli.run_worker(payload)

if __name__=='__main__':main(json.load(sys.stdin))
