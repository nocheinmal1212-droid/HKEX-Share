"""Bounded multi-model wrapper over the unchanged v2 attempt completion contract."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import ssl
import sys
import time
import urllib.error
import urllib.request
sys.path.insert(0, str(Path(__file__).resolve().parent))
from direct_contributor_attempt_v2 import Store, dispatch, encode, parse, precheck, replay, sha
from direct_contributor_boundary import output_schema
from direct_contributor_live_v2 import install_guard as original_guard
from direct_contributor_worker import ENDPOINT, MAX_BYTES, NoRedirect, deadline, verify_isolation


def wire_request(job, payload, prompt, settings, diagnostic=None):
    body = deepcopy(settings)
    body['messages'] = [{'role': 'system', 'content': prompt}, {'role': 'user', 'content': encode(payload).decode()}]
    schema = output_schema(job)
    if diagnostic:
        body['messages'] += [{'role': 'assistant', 'content': diagnostic['original_content']},
                             {'role': 'user', 'content': diagnostic['instruction']}]
        schema = diagnostic['schema']
    body['response_format'] = {'type':'json_schema', 'json_schema': {'name':'diagnostic' if diagnostic else 'direct_contributors', 'strict':True, 'schema':schema}}
    return body


class Transport:
    def __init__(self, entry, prompt, key, opener):
        self.entry, self.prompt, self.key, self.opener = entry, prompt, key, opener
        self.network_attempts = 0
    def __call__(self, payload):
        e = self.entry
        raw = encode(wire_request(e['job'], payload, self.prompt, e['settings'], e.get('diagnostic')))
        if sha(raw) != e['configuration']['wire_request_sha256'] or parse(raw) != e['configuration']['wire_request']:
            raise ValueError('wire binding mismatch')
        result = {'wire_request_sha256':sha(raw), 'started_at':datetime.now(timezone.utc).isoformat()}
        started = time.monotonic()
        signal.alarm(60)
        try:
            req = urllib.request.Request(ENDPOINT, data=raw, headers={'Authorization':'Bearer '+self.key, 'Content-Type':'application/json'})
            self.network_attempts += 1
            try: response = self.opener.open(req, timeout=60)
            except urllib.error.HTTPError as error: response = error
            with response:
                body = response.read(MAX_BYTES+1)
                result['http_status'] = response.code
            result['transport_status'] = 'received' if len(body)<=MAX_BYTES else 'response_too_large'
            if len(body)>MAX_BYTES:
                body=body[:MAX_BYTES]; result['response_truncated_for_storage']=True
            safe=body.replace(self.key.encode(),b'[REDACTED]')
            result.update(body=safe,credential_redacted=safe!=body)
        except TimeoutError: result['transport_status']='timeout'
        except (OSError,urllib.error.URLError): result['transport_status']='transport_error'
        finally: signal.alarm(0)
        result['elapsed_seconds']=round(time.monotonic()-started,6)
        return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--preflight',action='store_true');a=p.parse_args()
    raw=a.manifest.read_bytes();m=parse(raw);entries=m['attempts']
    assert 1<=len(entries)<=54 and len({e['id'] for e in entries})==len(entries)
    for e in entries:
        assert precheck(e['source'],e['identity'],e['job'])['state']=='eligible'
        assert e['settings']['max_tokens'] in (2048,4096,8192)
        assert e['settings']['provider']['allow_fallbacks'] is False
        assert len(e['settings']['provider']['only'])==1
        body=wire_request(e['job'],e['job']['payload'],m['prompt'],e['settings'],e.get('diagnostic'))
        assert body==e['configuration']['wire_request'] and sha(encode(body))==e['configuration']['wire_request_sha256']
        assert len(encode(body))<=32000
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    accesses=original_guard(a.manifest.parent,a.out,entries)
    checks=verify_isolation(m['protected_paths'])
    if a.preflight:
        Store(a.out).write('preflight.json',encode({'checks':checks,'network_calls':0,'manifest_sha256':sha(raw)}));print('Preflight passed; zero calls.',flush=True);return
    key=os.environ.get('OPENROUTER_API_KEY')
    if not key: raise SystemExit('Credential unavailable')
    signal.signal(signal.SIGALRM,deadline)
    observations=[]
    for e in entries:
        t=Transport(e,m['prompt'],key,opener);directory=a.out/e['id']
        result=dispatch(e['source'],e['identity'],e['job'],t,Store(directory),e['configuration'])
        rp=replay(directory)
        observation={'id':e['id'],'dispatch':result,'replay':rp,'network_attempts':t.network_attempts}
        Store(directory).write('observation.json',encode(observation))
        observations.append({'id':e['id'],'state':result['state'],'network_attempts':t.network_attempts})
        print(json.dumps(observations[-1]),flush=True)
        if result['state'] in ('persistence_failure','commit_unknown','attempt_conflict'): break
    Store(a.out).write('batch.json',encode({'checks':checks,'manifest_sha256':sha(raw),'observations':observations}))
    Store(a.out).write('access.json',encode(accesses))
if __name__=='__main__':main()
