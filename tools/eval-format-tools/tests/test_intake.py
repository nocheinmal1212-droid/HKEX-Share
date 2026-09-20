import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from eval_intake.common import digest, encoded, fingerprint, read, require, write_once, loads
from eval_intake.importer import import_records, note
from eval_intake.numeric import calculate, parse_token
from eval_intake.splits import assign
from eval_intake.validation import authorities, schema, validate_records
from eval_intake.inventory import header, verify_sources
from eval_intake.isolation import check
from audit_inputs import selected_files

ROOT=Path(__file__).resolve().parents[3]


def relation(values=('8','2','10'), injected=('8','2','13'), steps=('1','1','1')):
    operands=[]
    for i,(a,b,u) in enumerate(zip(values,injected,steps)):
        operands.append({'operand_id':f'o{i}','role':'total' if i==2 else 'contributor','location':{},'coefficient':'-1' if i==2 else '1','scale':'1','original_text':a,'injected_text':b,'original_value':a,'injected_value':b,'rounding_step':u})
    return {'relation_id':'rel','operation':'signed_sum','complete':True,'context':dict(concept='profit',entity='group',period='2025',unit='HKD',presentation_basis='reported'),'operands':operands,'rounding_policy':'independent_nearest'}


class ArithmeticTests(unittest.TestCase):
    def test_total_and_exact_boundaries(self):
        # Independent reference: three unit-rounded operands give 1.5 uncertainty.
        for delta,band in [('0','within_tolerance'),('1.5','within_tolerance'),('1.5001','boundary'),('3','boundary'),('3.0001','above_tolerance')]:
            from decimal import Decimal
            r=relation(injected=('8','2',str(Decimal(10)+Decimal(delta))))
            out=calculate(r)
            self.assertEqual(out['tolerance_bound'],'1.5');self.assertEqual(out['detectability_band'],band)

    def test_propagation_cancels_and_zero_tolerance(self):
        r=relation(injected=('11','2','13'))
        self.assertEqual(calculate(r)['residual_change'],'0')
        r=relation(steps=('0','0','0'))
        self.assertEqual(calculate(r)['detectability_band'],'above_tolerance')
        r=relation(injected=('8','2','10'),steps=('0','0','0'))
        self.assertEqual(calculate(r)['detectability_band'],'within_tolerance')

    def test_conversion_and_signed_coefficients(self):
        r=relation(values=('2','1','1000'),injected=('2','1','1100'),steps=('0.1','0.1','100'))
        r['operands'][0].update(scale='1000')
        r['operands'][1].update(scale='1000',coefficient='-1')
        out=calculate(r)
        self.assertEqual(out['original_residual'],'0');self.assertEqual(out['residual_change'],'-100');self.assertEqual(out['tolerance_bound'],'150.0')

    def test_invalid_and_incomplete(self):
        for key,value in [('complete',False),('rounding_policy','unknown'),('operation','divide')]:
            r=relation();r[key]=value
            with self.assertRaises(ValueError):calculate(r)
        for key,value in [('rounding_step','-1'),('scale','0'),('original_value',1.0),('coefficient','NaN')]:
            r=relation();r['operands'][0][key]=value
            with self.assertRaises(ValueError):calculate(r)

    def test_tokens_preserve_distinctions(self):
        for raw,status,value in [(None,'missing',None),(' ','blank',None),('—','dash',None),('0','parsed','0'),('(1,234.50)','parsed','-1234.50'),('-1,234.50','parsed','-1234.50'),('1,23','unrecognized',None),('15%','unrecognized',None),('920)','unrecognized',None)]:
            self.assertEqual(parse_token(raw),dict(raw=raw,status=status,value=value))


class SplitTests(unittest.TestCase):
    def test_transitive_group_and_order_invariance(self):
        edges=[{'sites':['a','b'],'reason':'same container'},{'sites':['c','b'],'reason':'paired endpoint'}]
        a=assign(['a','b','c','d'],edges,'salt')
        self.assertEqual(len({x['split_group_id'] for x in a}),2)
        self.assertEqual(a,assign(['d','c','a','b'],list(reversed(edges)),'salt'))
        for x in a:
            expected='test' if int(hashlib.sha256(('salt:'+x['split_group_id']).encode()).hexdigest(),16)%3==0 else 'dev'
            self.assertEqual(x['split'],expected)
        with self.assertRaises(ValueError):assign(['a'],[{'sites':['a','z'],'reason':'missing'}],'salt')

    def test_immutable_reroll_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frozen.json';obj=assign(['a','b'],[],'first')
            write_once(p,obj);write_once(p,obj)
            with self.assertRaises(ValueError):write_once(p,{'salt':'second','assignments':obj})


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        for directory in ['schemas','spec','eval']:
            (self.root/directory).mkdir()
        import shutil
        for path in (ROOT/'schemas').glob('*.json'):shutil.copyfile(path,self.root/'schemas'/path.name)
        for name in ['spec/taxonomy.yaml','eval/SCORING.md','eval/eval_format_spec.md']:shutil.copyfile(ROOT/name,self.root/name)
        (self.root/'corpus').mkdir()
        raw={'error_id':'fixture-1','taxonomy_version':'1','taxonomy_revision':1,'taxonomy_scope':'global','category_code':'document_wide_consistency','mutated_pdf':'bad.pdf','original_value':'報告','mutated_value':'改動','message':'Synthetic context discrepancy'}
        self.raw=self.root/'corpus/error_detail.jsonl';self.raw.write_text(json.dumps(raw,ensure_ascii=False)+'\n')
        for name in ['clean.pdf','bad.pdf','native.json']:(self.root/'corpus'/name).write_text('{}')
        self.config=dict(bundle_id='fixture',doc_id='doc',owner='Reviewer',raw_records='corpus/error_detail.jsonl',documents=[dict(path='corpus/clean.pdf',variant_id='clean'),dict(path='corpus/bad.pdf',variant_id='corrupted')],lifecycle='active',lifecycle_reason='Explicitly retain pending.')
        files=[]
        for name,role,variant in [('error_detail.jsonl','ground_truth',None),('clean.pdf','supplied_pdf','clean'),('bad.pdf','supplied_pdf','corrupted'),('native.json','native_export','corrupted')]:
            p=self.root/'corpus'/name;files.append(dict(path='corpus/'+name,sha256=digest(p),size_bytes=p.stat().st_size,role=role,variant_id=variant))
        self.manifest={**header('fixture','Synthetic test'),'source_config_sha256':'0'*64,'files':files,'exports':[],'owner':'Reviewer','limitations':['Synthetic']}
        taxonomy,scored=authorities(self.root)
        self.records=import_records(self.root,self.config,self.manifest,taxonomy,scored)

    def validate(self,records=None):return validate_records(self.root,records or self.records,self.manifest)

    def test_pending_valid_and_lossless_deterministic(self):
        report=self.validate();self.assertEqual((report['records'],report['pending'],report['ready']),(1,1,0))
        self.assertEqual(report['publication_status'],'UNGATED')
        self.assertEqual(self.records[0]['original_text'],'報告')
        taxonomy,scored=authorities(self.root)
        self.assertEqual(self.records,import_records(self.root,self.config,self.manifest,taxonomy,scored))
        verify_sources(self.root,self.manifest)

    def test_bad_records_fail(self):
        for key,value in [('category_revision',1),('category_code','invented'),('scoring_status','descoped'),('ingestion_status','ready'),('original_text','changed'),('seed',1.5),('value_delta',1.0),('expected_detectable',False),('detectability_band','above_tolerance')]:
            r=copy.deepcopy(self.records);r[0][key]=value
            if key=='expected_detectable':r[0]['review_notes']=[n for n in r[0]['review_notes'] if n['field']!='expected_detectable']
            with self.subTest(key=key), self.assertRaises(ValueError):self.validate(r)
        r=copy.deepcopy(self.records);r[0]['review_notes']=[]
        with self.assertRaises(ValueError):self.validate(r)
        with self.assertRaises(ValueError):self.validate(self.records*2)

    def test_tampered_sources_fail(self):
        self.raw.write_text(self.raw.read_text()+'\n')
        with self.assertRaises(ValueError):verify_sources(self.root,self.manifest)

    def test_strict_json(self):
        for value in ['{"x":1,"x":2}','{"x":NaN}','{"x":1e999}']:
            with self.assertRaises(ValueError):loads(value)

    def test_real_file_access_and_counterpart_selection(self):
        from eval_intake.runtime_selection import project
        selection=project(self.root,self.manifest,'doc','corrupted','corpus/native.json')
        p=self.root/'selection.json';p.write_text(json.dumps(selection))
        result=check(self.root,p,self.manifest)
        self.assertEqual(result['status'],'passed')
        selection['document']['variant_id']='clean'
        p.write_text(json.dumps(selection))
        with self.assertRaises(ValueError):check(self.root,p,self.manifest)
        with self.assertRaises(ValueError):selected_files({'pdf':str(self.raw),'native_artifacts':[],'configuration':{}})

    def test_record_schema_allows_deep_relationship_geometry(self):
        r=copy.deepcopy(self.records[0])
        r['location']={'page_index':0,'table_id':'table','section_id':None,'row_key':None,'column_key':None,'source_anchors':[{'artifact_path':'corpus/bad.pdf','sha256':'0'*64,'pointer':'page:0','rectangle':[0.1,0.2,10.3,20.4]}],'corrupted_endpoint':True}
        rel=relation();calc=calculate(rel)
        for op in rel['operands']:op['location']=copy.deepcopy(r['location'])
        rel.update({k:v for k,v in calc.items() if k!='detectability_band'})
        r['relation']=rel;r['detectability_band']=calc['detectability_band']
        schema(self.root,'error_record',r)


if __name__=='__main__':unittest.main()

class ReviewApprovalTests(unittest.TestCase):
    setUp = IntakeTests.setUp
    def approved_fixture(self):
        from eval_intake.splits import freeze
        manifest_path=self.root/'manifest.json';write_once(manifest_path,self.manifest)
        record=copy.deepcopy(self.records[0])
        anchor={'artifact_path':'corpus/bad.pdf','sha256':digest(self.root/'corpus/bad.pdf'),'pointer':'page:0','rectangle':None}
        location=dict(page_index=0,table_id=None,section_id='section',row_key=None,column_key=None,source_anchors=[anchor],corrupted_endpoint=True)
        record.update(site_id='site',location=location,expected_detectable=True,detectability_band='not_applicable',injection_stage='pre_ocr_pdf',propagated=False,propagation_sites=[])
        locations={**header('fixture','Synthetic reviewed mapping'),'manifest_sha256':digest(manifest_path),'coordinates':[],'entries':[dict(error_id=record['error_id'],site_id='site',status='reviewed',location=location,secondary_locations=[],native_candidates=[],reason='Synthetic reviewer approved mapping')]}
        loc_path=self.root/'locations.json';write_once(loc_path,locations)
        grouping={**header('fixture','Synthetic grouping'),'manifest_sha256':digest(manifest_path),'locations_sha256':digest(loc_path),'sites':['site'],'edges':[],'unresolved':[],'reviewer':'Reviewer','reviewed_at':'2026-09-09T12:00:00Z','prior_exposure':'synthetic','strategy':'reviewed_connections','rationale':'single site'}
        group_path=self.root/'grouping.json';write_once(group_path,grouping)
        split=freeze(self.root,grouping,group_path,manifest_path,loc_path,locations)
        split_path=self.root/'split.json';write_once(split_path,split)
        record.update(split=split['assignments'][0]['split'],split_group_id=split['assignments'][0]['split_group_id'])
        approval={**header('fixture','Synthetic owner approval'),'manifest_sha256':digest(manifest_path),'locations_sha256':digest(loc_path),'split_sha256':digest(split_path),'owner':'Reviewer','decisions':[dict(error_id=record['error_id'],decision='approve',reviewer='Reviewer',reviewed_at='2026-09-09T12:00:00Z',rationale='Synthetic approval only',record_sha256=fingerprint(record))]}
        record['ingestion_status']='ready'
        return [record],locations,split,approval,manifest_path,loc_path,split_path

    def test_valid_owner_review_and_stale_record_denied(self):
        records,loc,splits,review,mp,lp,sp=self.approved_fixture()
        result=validate_records(self.root,records,self.manifest,loc,splits,review,mp,lp,sp)
        self.assertEqual(result['ready'],1)
        records[0]['description']='Changed after review'
        with self.assertRaisesRegex(ValueError,'approval does not bind'):validate_records(self.root,records,self.manifest,loc,splits,review,mp,lp,sp)

    def test_unreviewed_mapping_wrong_owner_and_rerolled_split_denied(self):
        records,loc,splits,review,mp,lp,sp=self.approved_fixture()
        for which in ['mapping','owner','split']:
            l,s,r=copy.deepcopy(loc),copy.deepcopy(splits),copy.deepcopy(review)
            if which=='mapping':l['entries'][0]['status']='proposed'
            if which=='owner':r['owner']='Not appointed'
            if which=='split':s['assignments'][0]['split']='dev' if s['assignments'][0]['split']=='test' else 'test'
            with self.subTest(which=which),self.assertRaises(ValueError):validate_records(self.root,records,self.manifest,l,s,r,mp,lp,sp)

    def test_unknown_grouping_refuses_freeze(self):
        from eval_intake.splits import freeze
        records,loc,split,review,mp,lp,sp=self.approved_fixture()
        grouping=copy.deepcopy(split['grouping']);grouping['unresolved']=['Unknown paired endpoint may cross splits']
        with self.assertRaisesRegex(ValueError,'unresolved grouping'):freeze(self.root,grouping,self.root/'grouping.json',mp,lp,loc)

    def test_development_packet_rejects_test_selection_before_render(self):
        from eval_intake.packet import packet
        r=copy.deepcopy(self.records[0]);r['split']='test'
        with self.assertRaisesRegex(ValueError,'cannot expose test'):
            packet(self.root,[r],self.manifest,{}, {}, {'error_ids':[r['error_id']],'split_sha256':'0'*64,'rationale':'synthetic'},self.root/'packet')

class SourceAndBoundaryRegressionTests(unittest.TestCase):
    def test_geometry_compares_numeric_zero_representations(self):
        from pypdf import PdfWriter
        from pypdf.generic import FloatObject, NumberObject, RectangleObject, NameObject
        from eval_intake.source_review import inspect_pair
        with tempfile.TemporaryDirectory() as d:
            paths=[]
            for i,zero in enumerate([FloatObject('0.0'),NumberObject(0)]):
                writer=PdfWriter();page=writer.add_blank_page(width=100,height=200)
                page[NameObject('/MediaBox')]=RectangleObject([zero,zero,100,200])
                path=Path(d)/f'{i}.pdf';writer.write(path);paths.append(path)
            result=inspect_pair(*paths)
            self.assertTrue(result['page_comparisons'][0]['geometry_equal'])

    def test_runtime_has_no_evaluation_imports_or_answer_literals(self):
        import ast
        for path in (ROOT/'src/audit_inputs').glob('*.py'):
            source=path.read_text();tree=ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    self.assertTrue(all(n.name.split('.')[0] not in {'eval_intake','eval_formatter'} for n in node.names))
                if isinstance(node,ast.ImportFrom):
                    self.assertNotIn((node.module or '').split('.')[0],{'eval_intake','eval_formatter'})
            self.assertNotIn('HL-ERR-',source)
            self.assertNotIn('hksa_2026032600825',source)

    def test_exact_arithmetic_independent_of_decimal_context(self):
        from decimal import localcontext
        r=relation(values=('12345678901234567890','2','12345678901234567892'),injected=('12345678901234567890','2','12345678901234567893'))
        with localcontext() as ctx:
            ctx.prec=3
            self.assertEqual(calculate(r)['residual_change'],'-1')
