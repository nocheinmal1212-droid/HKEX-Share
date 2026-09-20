"""Freeze the approved typed-boundary experiment; offline preparation only."""
import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import Mock

from interface_boundary import dispatch, precheck, user_payload

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/milestone2/interface-boundaries-2026-09-16'
STAGE=Path('/private/tmp/audit-interface-2026-09-16-v1')
VERSION='interface-boundaries-2026-09-16-v1'


def encode(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def sha(data):return hashlib.sha256(data).hexdigest()


def write(path,value):
    with path.open('xb') as f:f.write(encode(value))


def main():
    source=ROOT/'spec/diagnostics/interface-boundaries-v1.json'
    fixture=json.loads(source.read_text())
    roles={'pro':('baseline',fixture['model_roles']['baseline']),
           'flash':('primary_subject',fixture['model_roles']['primary_subject']),
           'v41':('extension',fixture['model_roles']['optional_extension'])}
    routes={}
    for short,(role,model) in roles.items():
        metadata=json.loads((RUN/'metadata'/(short+'.json')).read_text())['data']
        assert metadata['id']==model
        endpoints=[e for e in metadata['endpoints'] if e.get('tag')=='fireworks' and e.get('status')==0]
        assert len(endpoints)==1
        e=endpoints[0]
        assert {'temperature','max_tokens','response_format','structured_outputs'}<=set(e['supported_parameters'])
        routes[short]={'model':model,'role':role,'tag':e['tag'],'provider_name':e['provider_name'],'metadata':e}
    offline=[]
    for case in fixture['deterministic_fixtures']:
        before=deepcopy(case)
        spy=Mock(return_value=deepcopy(case['stub_model_output']))
        result=dispatch(case['request'],spy)
        assert result['model_calls']==spy.call_count==case['expected_model_calls']
        assert result['stage']==case['expected_stage'] and result['state']==case['expected_state']
        assert case==before and result['model_output']==case['stub_model_output']
        semantic=('not_model_evaluated' if not spy.call_count else
                  'expected' if result['model_output']==case['reviewed_semantic_expected'] else 'wrong')
        if case['id']=='D09_semantic_error_survives_guards':assert semantic=='wrong'
        offline.append({'id':case['id'],'fixture_passed':True,'actual':result,'semantic_evaluation':semantic,
                        'transport_spy_calls':spy.call_count,'fixture_rationale':case['reason']})
    write(RUN/'offline-boundaries.json',{'scope':'offline_stubs_only','fixtures':offline,'all_passed':True})
    requests=[];answers=[]
    prompts=list(fixture['prompts'])
    for repetition in (1,2,3):
        order=prompts if repetition!=2 else list(reversed(prompts))
        for case in fixture['contract_fixtures']:
            gate=precheck(case['request']);assert gate['state']=='eligible'
            payload=user_payload(case['request']);assert payload==case['model_user_payload']
            schema=deepcopy(fixture['output_contract']['schema_template'])
            schema['properties']['evidence_id']['enum']=sorted(e['id'] for e in case['request']['evidence'])+[None]
            for short,route in routes.items():
                for prompt in order:
                    body={'model':route['model'],'messages':[{'role':'system','content':fixture['prompts'][prompt]},
                       {'role':'user','content':encode(payload).decode()}], 'temperature':0,'max_tokens':512,'stream':False,
                       'provider':{'only':[route['tag']],'require_parameters':True,'allow_fallbacks':False},
                       'response_format':{'type':'json_schema','json_schema':{'name':'synthetic_label','strict':True,'schema':schema}}}
                    raw=encode(body);id=f'call-{len(requests)+1:03d}'
                    requests.append({'id':id,'body_base64':base64.b64encode(raw).decode(),'sha256':sha(raw)})
                    answers.append({'id':id,'route':short,'role':route['role'],'model':route['model'],'provider_name':route['provider_name'],
                         'case':case['id'],'prompt':prompt,'repetition':repetition,'typed_request':case['request'],
                         'host_precheck':gate,'expected':case['expected_model_output'],'schema':schema})
    assert len(requests)==180
    manifest={'version':VERSION,'bounds':{'max_calls':180,'retries':0,'deadline_seconds':30,'max_response_bytes':131072},'requests':requests}
    STAGE.mkdir(exist_ok=False);(RUN/'responses').mkdir(exist_ok=False);(RUN/'sentinels').mkdir(exist_ok=False)
    write(RUN/'evaluator-key.json',{'cases':answers})
    write(STAGE/'requests.json',manifest);shutil.copyfile(STAGE/'requests.json',RUN/'requests.json')
    old_worker=Path(__file__).with_name('fixture_worker.py').read_bytes()
    new_worker=old_worker.decode().replace('approved-fixtures-2026-09-15-v1',VERSION)
    worker=Path(__file__).with_name('interface_worker.py')
    with worker.open('x') as f:f.write(new_worker)
    shutil.copyfile(worker,STAGE/'interface_worker.py')
    protected=[str(RUN/'evaluator-key.json'),str(source),str(ROOT/'.env'),str(ROOT/'README.md')]
    for name in ('corpus.pdf','native.json','evidence-ir.json','ground-truth.json','clean.json','corrupted.json'):
        path=RUN/'sentinels'/name;path.write_text('Synthetic isolation sentinel; not report evidence.\n');protected.append(str(path))
    write(STAGE/'isolation-paths.json',protected)
    profile='(version 1)\n(allow default)\n(deny file-read-data (subpath '+json.dumps(str(ROOT))+'))\n'
    profile+='(deny file-write*)\n(allow file-write* (subpath '+json.dumps(str(RUN/'responses'))+') (subpath "/dev"))\n'
    (STAGE/'sandbox.sb').write_text(profile);shutil.copyfile(STAGE/'sandbox.sb',RUN/'sandbox.sb')
    write(RUN/'execution-plan.json',{'version':VERSION,'approved_at':'2026-09-16','frozen_at':datetime.now(timezone.utc).isoformat(),
         'source_fixture_sha256':sha(source.read_bytes()),'manifest_sha256':sha(encode(manifest)),
         'evaluator_key_sha256':sha((RUN/'evaluator-key.json').read_bytes()),'worker_sha256':sha(worker.read_bytes()),
         'parent_worker_sha256':sha(old_worker),'worker_change':'Only accepted manifest version changes; historical worker stays unchanged.',
         'boundary_sha256':sha(Path(__file__).with_name('interface_boundary.py').read_bytes()),'sandbox_sha256':sha(profile.encode()),
         'routes':routes,'base_calls':120,'extension_calls':60,'planned_calls':180,'fixture_count':10,'prompt_arms':prompts,
         'setting_change':'None from approved proposal; strict schema, 512 output tokens, temperature zero, 30-second deadline.',
         'order':'Three repetitions, fixed C01-C10 order; per case Pro/Flash/V4.1 paired calls. B0 then B1 in repeats 1/3; B1 then B0 in repeat 2.',
         'isolation':'Copied verified transport-only worker; OS denies project data, Python allowlist after imports, request-only manifest, evaluator key separate, environment-only key inside worker, fixed endpoint, zero retries/fallback.',
         'typed_boundary':'All C requests are validated and rendered by experimental typed boundary during preparation; all eligible; immutable hashes protect the exact submitted payload. Postconditions applied offline without changing raw decisions. Experimental component is not wired into production semantic runtime.',
         'interpretation':'Pro baseline is not an oracle; approved expected answers are authoritative. V4.1 is a separate extension. Shared provider does not attest equal backend configuration or exact weights. Service failures remain visible, never semantic abstentions.'})
    print('All 11 D fixtures passed. Frozen 120 base + 60 extension calls on Fireworks; no inference yet.')


if __name__=='__main__':main()
