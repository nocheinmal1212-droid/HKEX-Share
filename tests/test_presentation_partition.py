"""Post-exposure regressions frozen before the presentation partition correction."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from helpers import ROOT, selection, ir_selection
from hkex_audit.artifacts import read, sha, write_new
from hkex_audit.semantic import project, validate_answer, validate_query_binding
from hkex_audit.semantic_attempt import Store, request, dispatch
from hkex_audit.semantic_cli import isolated
from hkex_audit.header_support import required_support

PACKET=ROOT/'eval/semantic-citation-implementation/1.1.1'


def cases(name):
    directory=PACKET/'fixtures'/name
    evidence=read(directory/'evidence.json')
    return evidence,zip(read(directory/'selections.json'),read(directory/'expectations.json'))


def answer(query, expected):
    return {'target_id':query['selection']['target_id'],'state':'selected',
            'contributor_ids':expected['contributors'],'support_refs':expected['support']}


class PresentationPartitionTests(unittest.TestCase):
    def test_frozen_source_boundaries(self):
        freeze=read(PACKET/'fixture-freeze.json')
        for path,checksum in freeze['files'].items():
            self.assertEqual(sha((PACKET/path).read_bytes()),checksum,path)
        for name in freeze['cases']:
            ir,entries=cases(name)
            for spec,expected in entries:
                with self.subTest(source=name,target=spec['name']):
                    q=project(ir,spec);validate_query_binding(q)
                    self.assertEqual(q['gate'],expected['gate'])
                    if expected['gate']=='blocked_scope':
                        self.assertFalse(q['host_analysis']['summary_scopes'])
                        with tempfile.TemporaryDirectory() as tmp:
                            result=dispatch(q,request(q,'primary','blocked'),lambda _:self.fail('blocked transport'),Store(tmp))
                            self.assertEqual(result['model_calls'],0)
                    else:
                        validate_answer(q,answer(q,expected))
                        self.assertEqual(set(q['host_analysis']['presentation_refs']),set(expected['presentation_refs']))
                        for ref in expected['presentation_refs']:
                            original=next(n for n in ir['nodes'] if n['id']==ref)
                            projected=next(n for n in q['context']['items'] if n['id']==ref)
                            for key in ('text','fragments','row','column','row_span','column_span'):
                                self.assertEqual(original[key],projected[key])

    def test_group_support_optional_wrappers_and_overlap(self):
        for name in ('nested','repeated','reordered'):
            ir,entries=cases(name)
            for spec,expected in entries:
                with self.subTest(source=name,target=spec['name']):
                    q=project(ir,spec);a=answer(q,expected);validate_answer(q,a)
                    group=next(iter(q['host_analysis']['groups']))
                    self.assertEqual(required_support(q['host_analysis'],a['target_id'],a['contributor_ids']),set(a['support_refs']))
                    with self.assertRaisesRegex(ValueError,'required header context support absent'):
                        validate_answer(q,{**a,'support_refs':[i for i in a['support_refs'] if i!=group]})
                    validate_answer(q,{**a,'support_refs':a['support_refs']+expected['presentation_refs']})
                    wrapper=expected['presentation_refs'][0]
                    with self.assertRaisesRegex(ValueError,'incompatible header context'):
                        validate_answer(q,{**a,'contributor_ids':a['contributor_ids']+[wrapper],'support_refs':a['support_refs']+[wrapper]})
                    if spec['name']=='outer':
                        scope=next(iter(q['host_analysis']['summary_scopes'].values()))
                        for extra in ([scope['component_ids'][0]],[scope['component_ids'][1]],scope['component_ids']):
                            with self.assertRaisesRegex(ValueError,'overlapping_summary_selection'):
                                validate_answer(q,{**a,'contributor_ids':a['contributor_ids']+extra,'support_refs':a['support_refs']+extra})

    def test_old_analysis_binding_requires_old_runtime(self):
        # Same logical operation, but the old host analysis must not be silently migrated.
        ir,entries=cases('nested');spec,_=next(entries);q=project(ir,spec)
        self.assertEqual(q['host_analysis']['policy']['analysis_version'],'header-source-analysis-1.0.1')
        old=deepcopy(q);old['host_analysis']['policy']['analysis_version']='header-source-analysis-1.0.0'
        with self.assertRaisesRegex(ValueError,'changed header policy binding'):validate_query_binding(old)

    def test_persisted_outer_and_subtotal_replay(self):
        from hkex_audit.cli import launch
        from test_semantic_integration import response
        ir,entries=cases('nested')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();source=PACKET/'fixtures/nested/source.json'
            (root/'source.json').write_bytes(source.read_bytes())
            write_new(root/'native-selection.json',selection(root/'source.json',ir['document']))
            self.assertEqual(launch('ingest',root/'native-selection.json',root/'ir'),0)
            self.assertEqual(read(root/'ir/evidence.json'),ir)
            sel=ir_selection(root/'ir')
            for spec,expected in entries:
                q=project(ir,spec);a=answer(q,expected)
                for role in ('primary','research'):
                    path=root/role/spec['name'];path.mkdir(parents=True)
                    result=dispatch(q,request(q,role,'authored'),lambda _,r=role:response(a,r),Store(path))
                    self.assertEqual(result['validation']['state'],'accepted')
                outputs=[]
                for step in ('consume','replay'):
                    dest=root/step/spec['name'];dest.mkdir(parents=True)
                    isolated('consume_worker',{'selection':sel,'spec':spec,'batch':str(root),'output':str(dest),'nonce':'authored'})
                    annotations=read(dest/'annotations.json');self.assertEqual(len(annotations[0]['links']),2)
                    guard=read(dest/'consumption.json')
                    self.assertFalse(guard['adapter_imported'])
                    self.assertFalse(any('/research/' in x.get('path','') for x in guard['access_attempts']))
                    outputs.append([(dest/(n+'.json')).read_bytes() for n in ('annotations','provenance')])
                self.assertEqual(*outputs)


if __name__=='__main__':unittest.main()
