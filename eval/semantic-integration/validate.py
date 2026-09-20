"""Evaluator-only source review comparison. Never imported by runtime; makes zero API calls."""
import argparse
from pathlib import Path
from hkex_audit.artifacts import read, write_new, sha, fingerprint
from hkex_audit.semantic_cli import normalized_selection, isolated
from hkex_audit.semantic import project
from hkex_audit.semantic_attempt import Store, replay


def review_decision(gate, expected, validation):
    if gate != 'eligible':
        return (expected['expected_status']=='abstained' and
                validation.get('state')==expected['expected_abstention_reason']), None
    answer=validation.get('answer')
    if not answer:
        return None,None
    correct=(answer['state']==expected['expected_status'] and
             set(answer['contributor_ids'])==set(expected['expected_contributor_header_ids']))
    supported=set(expected['required_support_ids'])<=set(answer['support_refs'])
    return correct,supported


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selection',required=True,type=Path);p.add_argument('--batch',required=True,type=Path)
    p.add_argument('--review',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();selection=normalized_selection(args.selection);batch=read(args.batch/'batch.json');review=read(args.review)
    prepared=isolated('prepare_worker',{'selection':selection,'specs':batch['specs']})
    evidence=read(selection['evidence']['path']);nodes={n['id']:n for n in evidence['nodes']}
    assert fingerprint(evidence)==review['source_identity_as_declared_by_packet']['source_sha256']
    assert batch['selection']==selection
    by_name={q['name']:q for q in review['queries']};results=[];traces=[]
    for q in prepared['queries']:
        name=q['selection']['name'];ex=by_name[name];roles={}
        for role in ('primary','research'):
            result=replay(Store(args.batch/role/name),q,role,batch['nonce'])
            v=result.get('validation',{});a=v.get('answer') or {}
            correct,supported=review_decision(q['gate'],ex,v)
            roles[role]={'state':v.get('state',result.get('state')),'selection_matches_source_review':correct,
                         'required_support_present':supported,'attempt_id':result['attempt_id'],'model_calls_on_replay':result['model_calls'],
                         'historical_model_calls':result.get('historical_model_calls'),'cost':v.get('cost'),'cost_status':v.get('cost_status'),
                         'served':v.get('served'),'answer':a or None}
        annotations=read(args.batch/'operational'/name/'annotations.json')
        provenance=read(args.batch/'operational'/name/'provenance.json')
        assert provenance['annotations_sha256']==fingerprint(annotations)
        assert provenance['query_id']==q['query_id']
        if annotations:
            assert provenance['primary_attempt_id']==roles['primary']['attempt_id']
            assert provenance['primary_completion_sha256']==sha((args.batch/'primary'/name/'completion.json').read_bytes())
        for a in annotations:
            traces.append({'query':name,'annotation_id':a['annotation_id'],'primary_attempt_id':provenance['primary_attempt_id'],
                           'selected_target':q['selection']['target_id'],'links':a['links'],
                           'evidence':[{'id':i,'text':nodes[i]['text'],'page_index':nodes[i]['page_index'],
                                        'native_pointer':nodes[i]['native_pointer'],'fragments':nodes[i]['fragments']} for i in a['evidence_refs']]})
        same=None
        if all(roles[r]['answer'] for r in roles):
            a,b=[roles[r]['answer'] for r in roles]
            same=a['state']==b['state'] and set(a['contributor_ids'])==set(b['contributor_ids'])
        results.append({'name':name,'query_id':q['query_id'],'gate':q['gate'],'roles':roles,'agreement':same,
                        'operational_annotation_count':len(annotations)})
    args.output.mkdir(parents=True,exist_ok=False)
    write_new(args.output/'evaluation.json',{'version':'saved-ir-review-evaluation-1.0.1','correction':'Local abstentions compare the frozen expected_status plus expected_abstention_reason, not status alone; v1 retained.', 'mode':'frozen_ir_development_agent_review','review_sha256':sha(args.review.read_bytes()),
              'source_sha256':fingerprint(evidence),'model_calls':0,'results':results,
              'limitations':['Header semantics only; no numerical operands/plans/checks/findings.','Independent agent review is not human/domain approval.','Not a scored or held-out population.']})
    write_new(args.output/'primary-source-traces.json',traces)
    print([(x['name'],[(r,y['state'],y['selection_matches_source_review'],y['required_support_present']) for r,y in x['roles'].items()]) for x in results])

if __name__=='__main__':main()
