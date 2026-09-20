import copy
import unittest
from helpers import evidence
from hkex_audit.pipeline_contracts import validate_bundle

class PipelineTests(unittest.TestCase):
    def records(self):
        e=evidence();cells=[n for n in e['nodes'] if n['kind']=='cell'];refs=[c['id'] for c in cells[:2]]
        base={'schema_version':'1.0.0','doc_id':e['document']['doc_id'],'variant_id':e['document']['variant_id']}
        a={**base,'annotation_id':'a','evidence_refs':refs,'method':'model','labels':[{'dimension':'role','label':'total','support_refs':refs}], 'links':[], 'state':'resolved'}
        p={**base,'plan_id':'p','evidence_refs':refs,'annotation_refs':['a'],'operation':'equality','operands':[{'evidence_id':refs[0],'coefficient':'1'},{'evidence_id':refs[1],'coefficient':'-1'}], 'context_requirements':['same_period'],'justification_refs':refs,'completeness':'unknown','tolerance_policy':'independent_nearest'}
        loc={'page_index':0,'table_id':cells[0]['parent_id'],'section_id':None,'row_key':None,'column_key':None}
        c={**base,'check_id':'c','opportunity_id':'o','category_code':'document_wide_consistency','location':loc,'plan_id':'p','state':'failed','reason':'Synthetic contract example only.','evidence_refs':refs,'finding_ids':['f']}
        f={**base,'finding_id':'f','check_id':'c','plan_id':'p','category_code':c['category_code'],'location':loc,'evidence_refs':refs,'claim':{'kind':'numerical','operand_refs':refs,'span_refs':[]},'calculation':{'residual':'1','tolerance':'0.5','policy':'independent_nearest'}}
        return e,[a],[p],[c],[f]

    def test_linked_examples_and_faults(self):
        kwargs={'category_codes':{'document_wide_consistency'},'permitted_labels':{'role':{'total'}}}
        records=self.records();self.assertTrue(validate_bundle(*records,**kwargs))
        for index,key,value in [(1,'amount','123'),(1,'variant_id','foreign'),(2,'annotation_refs',['missing']),
                                (3,'state','passed'),(4,'plan_id',None),(4,'evidence_refs',['missing'])]:
            data=copy.deepcopy(records);data[index][0][key]=value
            with self.assertRaises(ValueError):validate_bundle(*data,**kwargs)
        with self.assertRaises(ValueError):validate_bundle(*records,category_codes=kwargs['category_codes'])
