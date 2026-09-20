"""Exposed development expectations authored in a separate source-only review."""
from copy import deepcopy
from itertools import combinations
from pathlib import Path
from argparse import Namespace
from decimal import Decimal
import tempfile
import unittest
from unittest.mock import patch

from helpers import ROOT, selection, ir_selection
from hkex_audit.artifacts import read, sha, identity, write_new
from hkex_audit.semantic import project, validate_answer, verify_query, validate_query_binding
from hkex_audit.header_support import required_support, validate_summary_selection
from hkex_audit.semantic_attempt import dispatch, request, Store

PACKET=ROOT/'eval/semantic-citation-implementation/1.1.0'
OLD=ROOT/'eval/semantic-citation-investigation/2026-09-19'


def reviewed_case(prefix):
    path=next(p for p in (PACKET/'fixtures').iterdir() if p.name.startswith(prefix+'_'))
    ir=read(path/'evidence.json');spec=read(path/'selection.json');expected=read(path/'expectation.json')
    return ir,project(ir,spec),expected


def authored_answer(query, expected):
    return {'target_id':query['selection']['target_id'],'state':'selected',
            'contributor_ids':expected['independent_contributor_expectation'],
            'support_refs':expected['required_support']}


class HeaderSupportTests(unittest.TestCase):
    def test_independent_packet_hashes_and_all_boundaries(self):
        freeze=read(PACKET/'fixture-freeze.json')
        for path,checksum in freeze['files'].items():
            self.assertEqual(sha((PACKET/path).read_bytes()),checksum,path)
        for name in freeze['cases']:
            with self.subTest(case=name):
                ir,q,expected=reviewed_case(name.split('_')[0]);validate_query_binding(q)
                self.assertEqual(q['gate'],expected['eligibility'])
                codes={r['code'] for r in q['host_analysis']['reasons']}
                for reason in expected['blocker_reason_classes']:
                    alternatives=freeze['reason_mapping'].get(reason,reason)
                    self.assertTrue(codes & set(alternatives if isinstance(alternatives,list) else [alternatives]))
                expected_scopes={r['subtotal_id']:{k:v for k,v in r.items() if k!='subtotal_id'}
                                 for r in expected['summary_relationships']}
                self.assertEqual(q['host_analysis']['summary_scopes'],expected_scopes)
                if q['gate']=='eligible':
                    a=authored_answer(q,expected);validate_answer(q,a)
                    self.assertEqual(required_support(q['host_analysis'],a['target_id'],a['contributor_ids']),set(a['support_refs']))
                    for ref in expected['required_support']:
                        with self.assertRaises(ValueError):
                            validate_answer(q,{**a,'support_refs':[i for i in a['support_refs'] if i!=ref]})
                    validate_answer(q,{**a,'support_refs':a['support_refs']+expected['optional_support']})
                else:
                    a={'target_id':q['selection']['target_id'],'state':'ambiguous','contributor_ids':[],
                       'support_refs':[q['selection']['target_id']]}
                    with self.assertRaisesRegex(ValueError,'source prerequisite'):validate_answer(q,a)
                    for role in ('primary','research'):
                        with tempfile.TemporaryDirectory() as tmp:
                            result=dispatch(q,request(q,role,'authored-block'),lambda _:self.fail('blocked transport called'),Store(tmp))
                            self.assertEqual(result['model_calls'],0)
                            self.assertEqual(result['validation']['state'],'blocked_scope')

    def test_actual_siblings_overlap_and_exhaustive_reference(self):
        ir,q,e=reviewed_case('S01');a=authored_answer(q,e)
        scope=next(iter(q['host_analysis']['summary_scopes'].values()))
        subtotal=next(iter(q['host_analysis']['summary_scopes']))
        nodes={n['id']:n for n in ir['nodes']}
        for component in scope['component_ids']:
            self.assertEqual(nodes[subtotal]['row'],nodes[component]['row'])
            self.assertEqual(nodes[subtotal]['parent_id'],nodes[component]['parent_id'])
        # Exhaustive small-set oracle from independently specified relation, not runtime graph.
        relation=e['summary_relationships'][0];members=[subtotal,*relation['component_ids'],a['contributor_ids'][1]]
        for size in range(len(members)+1):
            for chosen in combinations(members,size):
                overlap=subtotal in chosen and bool(set(chosen)&set(relation['component_ids']))
                if overlap:
                    with self.assertRaisesRegex(ValueError,'overlapping_summary_selection'):
                        validate_summary_selection(q['host_analysis'],chosen)
                else:validate_summary_selection(q['host_analysis'],chosen)
        for extra in ([scope['component_ids'][0]],[scope['component_ids'][1]],scope['component_ids']):
            with self.assertRaisesRegex(ValueError,'overlapping_summary_selection'):
                validate_answer(q,{**a,'contributor_ids':a['contributor_ids']+extra,'support_refs':a['support_refs']+extra})

    def test_group_omission_wrong_branch_and_nonselected_contributors(self):
        _,q,e=reviewed_case('S13');a=authored_answer(q,e)
        wrong=[n['id'] for n in q['context']['items'] if n['kind']=='cell' and n['row']==1 and n['column'] in (5,6,7)]
        wrong_group=next(n['id'] for n in q['context']['items'] if n['text']=='2024')
        with self.assertRaisesRegex(ValueError,'incompatible header context'):
            validate_answer(q,{**a,'contributor_ids':wrong,'support_refs':list(set(a['support_refs']+wrong+[wrong_group]))})
        for state in ('ambiguous','missing_evidence','incompatible_context','not_a_total'):
            with self.assertRaises(ValueError):validate_answer(q,{**a,'state':state})
            validate_answer(q,{**a,'state':state,'contributor_ids':[]})

    def test_query_edits_and_policy_metadata_fail_closed(self):
        ir,q,e=reviewed_case('S01')
        for field,value in [('gate','blocked_scope'),('version','direct-contributor-headers-1.0.0'),('host_analysis',{})]:
            changed={**q,field:value}
            with self.assertRaises((ValueError,KeyError)):validate_query_binding(changed)
        for mutate in ('analysis','projection'):
            changed=deepcopy(q)
            if mutate=='analysis':changed['host_analysis']['summary_scopes']={}
            else:changed['context']['items'].pop()
            changed['query_id']=identity('query',{k:v for k,v in changed.items() if k!='query_id'})
            with self.assertRaises(ValueError):verify_query(ir,changed)
        changed=deepcopy(q);changed['host_analysis']['summary_scopes']={}
        changed['query_id']=identity('query',{k:v for k,v in changed.items() if k!='query_id'})
        with self.assertRaisesRegex(ValueError,'changed host analysis'):validate_query_binding(changed)

    def test_missing_group_diagnostic_is_persisted(self):
        from test_semantic_integration import response
        from hkex_audit.semantic_attempt import replay
        _,q,e=reviewed_case('S01');a=authored_answer(q,e)
        group=e['summary_relationships'][0]['group_id']
        a['support_refs']=[i for i in a['support_refs'] if i!=group]
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);result=dispatch(q,request(q,'primary','diagnostic'),lambda _:response(a),store)
            self.assertEqual(result['validation']['state'],'invalid_output')
            self.assertIn(group,result['validation']['diagnostic']['reason'])
            self.assertEqual(replay(store,q,'primary','diagnostic')['validation'],result['validation'])

    def test_amount_mask_variation_and_distinct_source_identity(self):
        ir,q,e=reviewed_case('S01');other=project(ir,{**q['selection'],'transform':'vary_body_amounts_v1'})
        self.assertEqual(q['host_analysis'],other['host_analysis']);validate_answer(other,authored_answer(q,e))
        for prefix in ('S03','S04'):
            ir2,q2,e2=reviewed_case(prefix)
            self.assertNotEqual(ir['id'],ir2['id'])
            self.assertEqual(q2['gate'],'eligible')
            def labels(query,ids):return {n['text'] for n in query['context']['items'] if n['id'] in ids}
            self.assertEqual(labels(q,e['independent_contributor_expectation']),labels(q2,e2['independent_contributor_expectation']))

    def test_crossing_groups_and_branch_local_unit_block(self):
        from helpers import native, evidence
        cases=[(
            '<table><tr><td colspan="3">來自與客戶合約之收入</td><td colspan="2">Continued</td></tr>'
            '<tr><td colspan="2">Continued</td><td colspan="3">2025</td></tr>'
            '<tr><td>甲</td><td>乙</td><td>丙</td><td>丁</td><td>總額</td></tr></table>',
            'non_laminar_or_incomplete_hierarchy'),(
            '<table><tr><td colspan="3">港幣百萬元</td><td rowspan="2">總額</td></tr>'
            '<tr><td>甲</td><td>乙</td><td>小計</td></tr></table>', 'unsupported_header_group')]
        for html,reason in cases:
            value=native();value['pdf_info']=value['pdf_info'][:1]
            value['pdf_info'][0]['preproc_blocks']=[{'type':'table','blocks':[{'type':'table_body','html':html}]}]
            ir=evidence(value);target=next(n for n in ir['nodes'] if n['kind']=='cell' and n['text']=='總額')
            q=project(ir,{'name':'structural_negative','table_id':target['parent_id'],'target_id':target['id'],'transform':'mask_body_amounts_v1'})
            self.assertEqual(q['gate'],'blocked_scope')
            self.assertIn(reason,{r['code'] for r in q['host_analysis']['reasons']})

    def test_summary_cycles_and_schema_identity(self):
        from hkex_audit.semantic import SCHEMA
        from hkex_audit.artifacts import fingerprint
        self.assertEqual(fingerprint(SCHEMA),read(PACKET/'baseline.json')['response_schema_fingerprint'])
        with self.assertRaisesRegex(ValueError,'cyclic summary scope'):
            validate_summary_selection({'summary_scopes':{'a':{'component_ids':['b']},'b':{'component_ids':['a']}}},['a'])

    def test_g_sources_keep_semantics_separate_from_operational_block(self):
        expectations={e['fixture']:e for e in read(OLD/'fixture-expectations.json')['fixtures']}
        for name in ('G1','G2','G2_variation','G3','G4_revision2','G5'):
            with self.subTest(case=name):
                source=OLD/'sources'/name;ir=read(source/'evidence.json');old=read(source/'query-v1.json')
                q=project(ir,old['selection']);validate_query_binding(q)
                self.assertEqual(q['gate'],'eligible' if name in ('G1','G2','G2_variation') else 'blocked_scope')
                if q['gate']=='blocked_scope':
                    self.assertIn('associated_prose_uninterpreted',{r['code'] for r in q['host_analysis']['reasons']})
                else:
                    expected=expectations[name]
                    a={'target_id':q['selection']['target_id'],'state':'selected',
                       'contributor_ids':expected['allowed_contributor_set'],
                       'support_refs':[s['id'] for s in expected['required_support']]}
                    validate_answer(q,a)
                    if name in ('G2','G2_variation'):
                        target_groups=q['host_analysis']['paths'][a['target_id']]
                        for group in target_groups:
                            with self.assertRaisesRegex(ValueError,'required header context support absent'):
                                validate_answer(q,{**a,'support_refs':[i for i in a['support_refs'] if i!=group]})
                        other=next(g for g in q['host_analysis']['groups'] if g not in target_groups)
                        wrong=[i for i in q['host_analysis']['groups'][other]['members']
                               if next(n['text'] for n in q['context']['items'] if n['id']==i)!='合計']
                        with self.assertRaisesRegex(ValueError,'incompatible header context'):
                            validate_answer(q,{**a,'contributor_ids':wrong,'support_refs':list(set(a['support_refs']+wrong+[other]))})

    def test_all_blocked_batch_has_no_credentials_metadata_or_annotations(self):
        from hkex_audit.cli import launch
        from hkex_audit.semantic_cli import run, replay_batch
        source=PACKET/'fixtures/S17_caption_appended_restriction/source.json'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            # Export only the authored literal source; evaluator expectations are never runtime inputs.
            (root/'authored-source.json').write_bytes(source.read_bytes())
            write_new(root/'native-selection.json',selection(root/'authored-source.json'))
            self.assertEqual(launch('ingest',root/'native-selection.json',root/'ir'),0)
            ir=read(root/'ir/evidence.json');write_new(root/'selection.json',ir_selection(root/'ir'))
            target=next(n for n in ir['nodes'] if n['kind']=='cell' and n['text']=='總額')
            spec={'name':'blocked','table_id':target['parent_id'],'target_id':target['id'],'transform':'mask_body_amounts_v1'}
            write_new(root/'queries.json',[spec])
            args=Namespace(selection=root/'selection.json',queries=root/'queries.json',output=root/'batch',
                           max_http_calls=0,max_role_calls=0,max_seconds=30,max_cost=Decimal('1'),env_root=root/'forbidden')
            with patch('hkex_audit.semantic_cli.transport',side_effect=AssertionError('transport forbidden')), \
                 patch('hkex_audit.semantic_cli.bootstrap_key',side_effect=AssertionError('credentials forbidden')):
                self.assertEqual(run(args),0)
            summary=read(root/'batch/summary.json')
            self.assertEqual(summary['http_calls_reserved'],0)
            self.assertEqual(summary['completion_calls_reserved'],{'primary':0,'research':0})
            self.assertEqual(read(root/'batch/operational/blocked/annotations.json'),[])
            self.assertEqual(read(root/'batch/operational/blocked/provenance.json')['outcome'],'blocked_scope')
            replay_batch(Namespace(command='replay',selection=root/'selection.json',batch=root/'batch',output=root/'replay'))
            for name in ('annotations','provenance'):
                self.assertEqual((root/f'batch/operational/blocked/{name}.json').read_bytes(),
                                 (root/f'replay/blocked/{name}.json').read_bytes())


if __name__=='__main__':unittest.main()
