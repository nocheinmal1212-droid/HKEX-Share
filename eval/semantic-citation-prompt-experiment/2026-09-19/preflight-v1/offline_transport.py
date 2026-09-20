"""Authored test transport only. Empty inherited environment; no network permitted."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time

def guard(event,args):
    if event in {'socket.__new__','socket.connect','socket.getaddrinfo'}: raise PermissionError('offline transport')
sys.addaudithook(guard)
p=json.load(sys.stdin);job=p['job'];fixture=p['fixture'];role=job['role']
assert set(os.environ)<= {'__CF_USER_TEXT_ENCODING','LC_CTYPE'}  # Interpreter-added locale only.
if time.monotonic()>=job['deadline_monotonic']:
    print(json.dumps({'transport_status':'budget_exhausted','request_started':False}));raise SystemExit()
config={'primary':('google/gemini-3.8-flash','google-ai-studio','Google AI Studio'),
        'research':('deepseek/deepseek-v4.1-flash','together','Together')}[role]
if fixture.get('stall')==job['mode']+'-'+role:
    prefix=p['prefix']
    child_code='import os,time,pathlib;pathlib.Path('+repr(prefix+'-descendant.pid')+').write_text(str(os.getpid()));time.sleep(120)'
    child=subprocess.Popen([sys.executable,'-I','-B','-c',child_code],env={},close_fds=True)
    Path(prefix+'-worker.pid').write_text(str(os.getpid()))
    child.wait()
if job['mode']=='metadata':
    body={'data':{'id':config[0],'endpoints':[{'tag':config[1],'status':0,'provider_name':config[2],
        'supported_parameters':['structured_outputs','response_format','temperature','max_tokens'],
        'pricing':{'prompt':'.000005','completion':'.000020','request':'0'}}]}}
else:
    if fixture.get('failure_role')==role:
        print(json.dumps({'transport_status':'timeout','request_started':True}));raise SystemExit()
    context=json.loads(job['payload']['messages'][1]['content'])
    target=context['target_id']
    answer=fixture.get('answers',{}).get(target,{'target_id':target,'state':'ambiguous','contributor_ids':[],'support_refs':[target]})
    if fixture.get('abstain_role')==role: answer={**answer,'state':'ambiguous','contributor_ids':[]}
    body={'id':'AUTHORED-OFFLINE','model':config[0],'provider':config[2],
          'choices':[{'finish_reason':'stop','message':{'content':json.dumps(answer)}}]}
print(json.dumps({'transport_status':'ok','request_started':True,
                  'body_base64':base64.b64encode(json.dumps(body).encode()).decode()}))
