"""Offline raw-model and boundary evaluation; no model calls or response repair."""
import argparse
import base64
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from statistics import median

from evaluate_fixtures import classify
from interface_boundary import postcheck, precheck, user_payload


def sha(raw):return hashlib.sha256(raw).hexdigest()


def evaluate(run, partial=False):
    plan=json.loads((run/'execution-plan.json').read_text())
    raw=(run/'requests.json').read_bytes();assert sha(raw)==plan['manifest_sha256']
    manifest=json.loads(raw)
    key_raw=(run/'evaluator-key.json').read_bytes();assert sha(key_raw)==plan['evaluator_key_sha256']
    answers=json.loads(key_raw)['cases'];requests={r['id']:r for r in manifest['requests']}
    rows=[];missing=[];cost=Decimal('0');missing_cost=0
    for answer in answers:
        path=run/'responses'/(answer['id']+'.json')
        if not path.exists():missing.append(answer['id']);continue
        record=json.loads(path.read_text());request=requests[answer['id']]
        body_raw=base64.b64decode(request['body_base64'],validate=True)
        assert record['request_sha256']==request['sha256']==sha(body_raw)
        assert record['id']==answer['id']
        body=json.loads(body_raw)
        assert precheck(answer['typed_request'])==answer['host_precheck']
        assert json.loads(body['messages'][1]['content'])==user_payload(answer['typed_request'])
        if 'response_base64' in record:
            payload=base64.b64decode(record['response_base64'],validate=True)
            assert sha(payload)==record['response_sha256']
            try:
                response=json.loads(payload,parse_float=Decimal)
                value=response.get('usage',{}).get('cost')
                if value is None:missing_cost+=1
                else:cost+=Decimal(str(value))
            except (ValueError,AttributeError):missing_cost+=1
        else:missing_cost+=1
        raw_result=classify(record,answer)
        boundary={'state':'not_evaluated','reason':'complete_parsed_output_unavailable'}
        if raw_result['status'] in ('passed','invalid_schema','unexpected_abstention','wrong_selection','failure_to_abstain'):
            boundary=postcheck(answer['typed_request'],raw_result['observed_output'])
        rows.append({**answer,**raw_result,'boundary':boundary,'request_sha256':request['sha256'],
                     'response_record_sha256':sha(path.read_bytes()),'http_status':record.get('http_status'),
                     'elapsed_seconds':record['elapsed_seconds'],'credential_redacted':record.get('credential_redacted',False)})
    if not partial:
        assert not missing
        assert json.loads((run/'responses/completed.json').read_text())['calls']==len(requests)
    groups=defaultdict(Counter)
    for r in rows:groups[r['route']+'/'+r['prompt']][r['status']]+=1
    paired=[]
    for route in plan['routes']:
        index={(r['case'],r['repetition'],r['prompt']):r for r in rows if r['route']==route}
        values=[]
        for case,rep,prompt in list(index):
            if prompt!='B0_existing_explicit':continue
            a=index[case,rep,prompt];b=index.get((case,rep,'B1_concise_equivalent'))
            if b is None:continue
            entry={'case':case,'repetition':rep,'baseline_id':a['id'],'concise_id':b['id'],
                   'baseline_status':a['status'],'concise_status':b['status'],'both_pass':a['status']==b['status']=='passed'}
            if entry['both_pass']:
                entry['latency_difference_concise_minus_baseline']=round(b['elapsed_seconds']-a['elapsed_seconds'],6)
                for field in ['prompt_tokens','completion_tokens','total_tokens']:
                    av=(a.get('usage') or {}).get(field);bv=(b.get('usage') or {}).get(field)
                    if isinstance(av,(int,float)) and isinstance(bv,(int,float)):entry[field+'_difference_concise_minus_baseline']=bv-av
            values.append(entry)
        effects={'route':route,'matched_pairs':len(values),'both_pass_pairs':sum(v['both_pass'] for v in values),'pairs':values}
        for field in ['latency','prompt_tokens','completion_tokens','total_tokens']:
            suffix='latency_difference_concise_minus_baseline' if field=='latency' else field+'_difference_concise_minus_baseline'
            vals=[v[suffix] for v in values if suffix in v]
            effects['median_'+suffix]=median(vals) if vals else None
        paired.append(effects)
    return {'planned':len(requests),'completed':len(rows),'missing':missing,'reported_cost_usd':str(cost),
            'records_without_reported_cost':missing_cost,'counts':{k:dict(v) for k,v in groups.items()},
            'paired_comparisons':paired,'rows':rows,'interpretation':'Raw model results and guard acceptance are distinct. Pro is a baseline, not an oracle. Efficiency summaries use both-pass pairs only; service failures and truncation remain visible.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--partial',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    result=evaluate(a.run,a.partial)
    if a.out:
        with a.out.open('x') as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','missing','paired_comparisons')},indent=2))
    for r in result['rows']:
        if r['status']!='passed':print(r['id'],r['route'],r['case'],r['prompt'],r['repetition'],r['status'],r['observed_output'])


if __name__=='__main__':main()
