"""Persist exposed development diagnostics. No model/provider/network calls or old writes."""
import base64
from copy import deepcopy
from pathlib import Path
import sys
from argparse import Namespace
from decimal import Decimal
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests'))
from helpers import selection, ir_selection
from test_header_support import reviewed_case, authored_answer
from test_semantic_integration import response
from hkex_audit.artifacts import read, write_new, sha, fingerprint
from hkex_audit.cli import launch
from hkex_audit.semantic import project, validate_answer, SCHEMA
from hkex_audit.header_support import policy_identity
from hkex_audit.semantic_attempt import dispatch, request, Store
from hkex_audit.semantic_cli import isolated, run, replay_batch, runtime_identity


def offline(event,args):
    if event.startswith('socket.'):raise PermissionError('offline verification')


def source_export(source,document,out):
    out.mkdir(parents=True)
    (out/'authored-source.json').write_bytes(source.read_bytes())
    write_new(out/'native-selection.json',selection(out/'authored-source.json',document))
    assert launch('ingest',out/'native-selection.json',out/'ir')==0
    sel=ir_selection(out/'ir');write_new(out/'selection.json',sel)
    return sel,read(out/'ir/evidence.json')


def main():
    sys.addaudithook(offline)
    output=ROOT/'runs/semantic-citation-implementation-1.1.0/development'
    output.mkdir()  # deliberately no overwrite
    records={'classification':'exposed development; authored transports are not model completions',
             'provider_calls':0,'network_calls':0,'runtime_sha256':runtime_identity(),'policy':policy_identity(),
             'schema_sha256':fingerprint(SCHEMA),'reviewed_sources':[],'retained_diagnostics':[],
             'operational_blocks':[],'isolation':[]}
    for name in read(HERE/'fixture-freeze.json')['cases']:
        _,q,e=reviewed_case(name.split('_')[0])
        assert q['gate']==e['eligibility']
        if q['gate']=='eligible':validate_answer(q,authored_answer(q,e))
        records['reviewed_sources'].append({'case':name,'query_id':q['query_id'],'gate':q['gate'],
            'host_analysis':q['host_analysis'],'independent_expectation_sha256':sha((HERE/'fixtures'/name/'expectation.json').read_bytes())})
    old=ROOT/'runs/paired-semantic-integration-2026-09-18/live-v1'
    ir=read(ROOT/'runs/milestone1-r1/corrupted/evidence.json')
    for name in ('total','subtotal','period_groups','varied_total'):
        saved=read(old/'primary'/name/'query.json');q=project(ir,saved['selection'])
        answer=read(old/'primary'/name/'result.json')['validation']['answer']
        validate_answer(q,answer)
        groups=[g for g in q['host_analysis']['groups'] if g in answer['support_refs']]
        rejected=[]
        for group in groups:
            copied={**answer,'support_refs':[i for i in answer['support_refs'] if i!=group]}
            try:validate_answer(q,copied)
            except ValueError as exc:rejected.append({'omitted_id':group,'reason':str(exc)})
            else:raise AssertionError('required group omission accepted')
        overlap=[]
        if name in ('total','varied_total'):
            components=next(iter(q['host_analysis']['summary_scopes'].values()))['component_ids']
            for extra in ([components[0]],[components[1]],components):
                copied={**answer,'contributor_ids':answer['contributor_ids']+extra,'support_refs':answer['support_refs']+extra}
                try:validate_answer(q,copied)
                except ValueError as exc:
                    assert 'overlapping_summary_selection' in str(exc);overlap.append(str(exc))
                else:raise AssertionError('sibling overlap accepted')
        records['retained_diagnostics'].append({'name':name,'classification':'post-exposure diagnostic re-evaluation',
            'new_query_id':q['query_id'],'saved_answer_sha256':fingerprint(answer),
            'conditional_host_check':'accepted; not semantic acceptance','group_omission_rejections':rejected,
            'sibling_overlap_rejections':overlap,'historical_complete_support':'0/4 unchanged'})
    oldfixtures=ROOT/'eval/semantic-citation-investigation/2026-09-19/sources'
    for name,semantic_state in [('G3','missing_evidence'),('G4_revision2','ambiguous'),('G5','incompatible_context')]:
        source=oldfixtures/name;expected_ir=read(source/'evidence.json');dest=output/name
        sel,ir=source_export(source/'source.json',expected_ir['document'],dest)
        assert fingerprint(ir)==fingerprint(expected_ir), 'source export changed evidence identity'
        spec=read(source/'query-v1.json')['selection'];write_new(dest/'queries.json',[spec])
        args=Namespace(selection=dest/'selection.json',queries=dest/'queries.json',output=dest/'batch',
                       max_http_calls=0,max_role_calls=0,max_seconds=30,max_cost=Decimal('1'),env_root=None)
        with patch('hkex_audit.semantic_cli.transport',side_effect=AssertionError('transport forbidden')):
            assert run(args)==0
        produced=dest/'batch/operational'/spec['name']
        assert read(produced/'annotations.json')==[]
        prov=read(produced/'provenance.json');assert prov['outcome']=='blocked_scope'
        records['operational_blocks'].append({'fixture':name,'independent_semantic_state':semantic_state,
            'operational_outcome':prov['outcome'],'blocking_reasons':prov['blocking_reasons'],
            'annotations_sha256':sha((produced/'annotations.json').read_bytes()),'http_calls':read(dest/'batch/summary.json')['http_calls_reserved']})
    source=HERE/'fixtures/S01_actual_sibling_outer'
    sel,ir=source_export(source/'source.json',read(source/'evidence.json')['document'],output/'isolation-source')
    spec=read(source/'selection.json');q=project(ir,spec);answer=authored_answer(q,read(source/'expectation.json'))
    for mode in ('accepted','failure','abstained','invalid_support'):
        batch=output/('authored-'+mode);batch.mkdir()
        for role in ('primary','research'):(batch/role/spec['name']).mkdir(parents=True)
        a=deepcopy(answer)
        if mode=='abstained':a.update(state='ambiguous',contributor_ids=[])
        if mode=='invalid_support':a['support_refs'].remove(next(iter(q['host_analysis']['groups'])))
        raw={'transport_status':'timeout'} if mode=='failure' else response(a)
        dispatch(q,request(q,'primary','authored'),lambda _:raw,Store(batch/'primary'/spec['name']))
        dispatch(q,request(q,'research','authored'),lambda _:response(answer,'research'),Store(batch/'research'/spec['name']))
        dest=batch/'operational';dest.mkdir()
        isolated('consume_worker',{'selection':sel,'spec':spec,'batch':str(batch),'output':str(dest),'nonce':'authored'})
        annotations=read(dest/'annotations.json');provenance=read(dest/'provenance.json')
        assert (bool(annotations and annotations[0]['links']))==(mode=='accepted')
        guard=read(dest/'consumption.json')
        assert not guard['adapter_imported'] and not any('/research/' in a.get('path','') for a in guard['access_attempts'])
        records['isolation'].append({'mode':mode,'provenance':provenance,'annotations':annotations,
            'consumption':guard,'transport_origin':'authored mock; attempt model_calls counts mock dispatch, provider_calls=0'})
    write_new(HERE/'offline-results.json',records)
    print('Persisted offline development diagnostics; zero provider/network calls.')


if __name__=='__main__':main()
