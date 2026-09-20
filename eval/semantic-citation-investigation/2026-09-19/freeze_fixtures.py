"""Freeze independently reviewed diagnostic expectations; no runtime patch or inference."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from hkex_audit.artifacts import encode,sha
from hkex_audit.semantic import validate_answer,verify_query,SCHEMA
from hkex_audit.evidence import validate_evidence
from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def read(p):return json.loads(p.read_text())
def write(p,x):
    with p.open('xb') as f:f.write(encode(x))
def file(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())}
review=read(HERE/'independent-source-review.json')
old=read(ROOT/'eval/semantic-integration/2026-09-18/independent-review.json')
oldby={r['name']:r for r in old['queries']}
live=ROOT/'runs/paired-semantic-integration-2026-09-18/live-v1'
proposal='direct-contributor-headers-1.1.0-proposal'
expectations=[]
for r in review['original_cases']:
    name=r['fixture'];q=read(live/'primary'/name/'query.json');fr=oldby[name]
    expectations.append({'fixture':'R/'+name,'classification':'exposed_reproduction',
      'operation_version':'direct-contributor-headers-1.0.0','proposed_policy_version':proposal,
      'source_manifest':{'source_packet':file(ROOT/'eval/semantic-integration/2026-09-18/source-review-packet.json'),
        'selected_ir':file(ROOT/'runs/milestone1-r1/corrupted/evidence.json'),
        'query':file(live/'primary'/name/'query.json'),'response':file(live/'primary'/name/'response.json'),
        'frozen_review':file(ROOT/'eval/semantic-integration/2026-09-18/independent-review.json')},
      'target_id':r['target_id'],'proposed_state':r['state'],'allowed_contributor_set':r['contributor_ids'],
      'required_support':r['required_support'],'optional_support':r['optional_support'],
      'source_only_evidence':r.get('source_only_evidence',[]),
      'frozen_required_support':[{'id':i,'reason':'Frozen pre-inference v1 expectation; preserved even where new policy judges common unit optional.'} for i in fr.get('required_support_ids',[])],
      'provenance_transform':{'source_edits':[],'projection_transform':q['selection']['transform'],
        'diagnostic_responses':'R1/R4 unchanged replay; R2 adds only real unit or removes target/contributor citation; R3 removes 2025 citation or substitutes 2024 peers. No historical answer rewritten.'},
      'diagnostic_records':'diagnostics/reproductions.json','expected_v1_host':'accept eligible original answer; local missing_evidence for blank target',
      'expected_frozen_evaluator':'correct contributors but missing unit for four eligible originals; correct local abstention for blank target',
      'proposed_policy_use':'Any later old-answer evaluation is post-exposure diagnostic re-evaluation, never historical replacement.'})

gby={r['fixture']:r for r in review['generalization_cases']}
for name,r in gby.items():
    if not r['freeze_ready']:continue
    d=HERE/'sources'/name;e=read(d/'evidence.json');q=read(d/'query-v1.json')
    validate_evidence(e,read(d/'source.json'));verify_query(e,q)
    ns={n['id']:n for n in e['nodes']}
    assert all(ns[s['id']]['text'] for s in r['required_support']+r['optional_support'])
    expectations.append({'fixture':name,'classification':'derived_source_generalization' if name=='G1' else 'synthetic_generalization',
      'operation_version':proposal,'executable_projection_version':q['version'],'source_manifest':file(d/'manifest.json'),
      'source':file(d/'source.json'),'evidence':file(d/'evidence.json'),'projection':file(d/'query-v1.json'),
      'target_id':r['target_id'],'proposed_state':r['state'],'allowed_contributor_set':r['contributor_ids'],
      'required_support':r['required_support'],'optional_support':r['optional_support'],'source_only_evidence':r.get('source_only_evidence',[]),
      'rationale':r['rationale'],'provenance_transform':read(d/'manifest.json')['transformation'],
      'expected_host_positive':'v1 structurally accepts the minimal nonblank support response; does not certify source semantics',
      'expected_proposed_evaluator_positive':'state and contributor set equal review; all decision-bearing required support present',
      'negative_expectations':'Omitted required support or a different state/selection fails proposed source acceptance. v1 actual enforcement is measured separately; no upgraded validator is implemented.',
      'future_numeric_status':'No financial plan/finding authorized; unit/basis/completeness prerequisites remain separate.'})

mapping=read(HERE/'sources/G2-variation-map.json')['id_mapping']
assert {mapping[i] for i in gby['G2']['contributor_ids']}==set(gby['G2_variation']['contributor_ids'])
assert mapping[gby['G2']['target_id']]==gby['G2_variation']['target_id']
write(HERE/'fixture-expectations.json',{'version':'citation-policy-fixtures-1.0.0','operation_proposal':proposal,
  'review':file(HERE/'independent-source-review.json'),'not_runtime_input':True,'model_calls':0,
  'fixtures':expectations,'excluded_drafts':[{'fixture':'G4','reason':'Source-only review permits correction/exception reading; replaced by separately identified G4_revision2.'}],
  'invariance':{'G2_mapping':file(HERE/'sources/G2-variation-map.json'),'reviewed_membership_equal_under_mapping':True,
    'original_amount_contrast':'diagnostics/amount-contrast.json'}})

# Freeze sources/IDs/expectations first; the following responses are derived authored probes.
paths=[HERE/'fixture-expectations.json',HERE/'independent-source-review.json',HERE/'independent-source-review.md',
       HERE/'source-only-index.json',HERE/'source-only-index-revision2.json',HERE/'sources/G2-variation-map.json']
for name in gby:
    paths += [HERE/'sources'/name/fn for fn in ('source.json','evidence.json','query-v1.json','manifest.json')]
write(HERE/'fixture-freeze.json',{'version':'citation-policy-review-freeze-1.0.0','frozen_at_utc':datetime.now(timezone.utc).isoformat(),
  'operation_proposal':proposal,'status':'review-frozen proposal; no implementation, provider call, human/domain approval or acceptance closure',
  'freeze_order':'Source-only agent review and policy/wording reconciliation; sources and expectations frozen here; authored G response diagnostics generated afterward. No prospective model answers exist.',
  'source_ready_generalization':[n for n,r in gby.items() if r['freeze_ready']],
  'excluded_but_preserved':['G4'],'exposed_reproductions':['R1','R2','R3','R4'],
  'files':[file(p) for p in paths],
  'future_request_binding':'v1 projections retain literal old prompt/schema/version. Future implementation and actual 1.1 request bytes require a separate freeze; these are not new requests.',
  'inference_authorized':False})

checks=[]
for r in expectations:
    name=r['fixture']
    if name.startswith('R/'):continue
    q=read(HERE/'sources'/name/'query-v1.json');nodes={n['id']:n for n in q['context']['items']}
    answer={'target_id':r['target_id'],'state':r['proposed_state'],'contributor_ids':r['allowed_contributor_set'],
            'support_refs':[s['id'] for s in r['required_support']]}
    variants=[('positive',deepcopy(answer))]
    for ref in answer['support_refs']:
        a=deepcopy(answer);a['support_refs'].remove(ref);variants.append(('omit_'+ref,a))
    if name in ('G2','G2_variation'):
        group=next(n for n in nodes.values() if n['text']=='銷售量（千件）')
        wrong=[n['id'] for n in nodes.values() if n['kind']=='cell' and n['row']==1 and n['column'] in (group['column'],group['column']+1)]
        a=deepcopy(answer);a['contributor_ids']=wrong;a['support_refs']+=wrong;variants.append(('wrong_quantity_group',a))
    if name in ('G3','G4_revision2','G5'):
        group=next(n for n in nodes.values() if n['text']==('銷售量（千件）' if name=='G5' else '銷售額（港幣百萬元）'))
        chosen=[n['id'] for n in nodes.values() if n['kind']=='cell' and n['row']==1 and n['column'] in (group['column'],group['column']+1)]
        a=deepcopy(answer);a['contributor_ids']=chosen;a['support_refs']=list(dict.fromkeys(a['support_refs']+chosen))
        variants.append(('abstention_retains_contributors',a))
        b=deepcopy(a);b['state']='selected';variants.append(('unsupported_selected_pair',b))
    for label,a in variants:
        try:validate_answer(q,a);host={'accepted':True,'error':None}
        except ValueError as ex:host={'accepted':False,'error':str(ex)}
        semantic=(a['state']==answer['state'] and set(a['contributor_ids'])==set(answer['contributor_ids']) and set(answer['support_refs'])<=set(a['support_refs']))
        assert semantic==(label=='positive')
        if label=='positive':assert host['accepted']
        if label in ('wrong_quantity_group','abstention_retains_contributors'):assert not host['accepted']
        checks.append({'fixture':name,'variant':label,'origin':'authored_response_fixture_after_source_only_review; not model output or annotation',
          'response':a,'operation_policy':proposal,'executed_host_version':q['version'],
          'strict_schema_pass':not list(Draft202012Validator(SCHEMA).iter_errors(a)),
          'actual_v1_host':host,'proposed_review_acceptance':semantic,
          'enforcement_status':'structural host only; new semantic/citation prerequisites are not implemented'})
write(HERE/'diagnostics/generalization-response-pairs.json',{'model_calls':0,'network_calls':0,'cases':checks,
  'interpretation':'Authored response probes establish current host behavior, not model capability or implemented 1.1 acceptance.'})
print('Froze',len(expectations),'case expectations and',len(paths),'source/review files;',len(checks),'authored G response checks.')
