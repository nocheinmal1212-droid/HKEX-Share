from pathlib import Path
from copy import deepcopy
import sys,json
sys.path.insert(0,str(Path.cwd()/'src'))
from hkex_audit.adapters.mineru import adapt
from hkex_audit.semantic import project,annotation,verify_query,validate_query_binding
from hkex_audit.header_support import analyze_source
from hkex_audit.artifacts import encode,sha,identity
root=Path('runs/semantic-citation-review-2026-09-19');packet=Path('eval/semantic-citation-implementation/1.1.0/fixtures')
p=packet/'S14_single_caption_null_ordinal/source.json';source=json.loads(p.read_text());source['pdf_info'][0]['preproc_blocks'][0]['blocks'][1]['blocks'][0]['type']='interline_equation'
doc={'doc_id':'review-nonliteral-caption','variant_id':'authored','source_document_sha256':None,'source_provenance':'synthetic'}
ir=adapt(source,doc,sha(encode(source)));target=next(n for n in ir['nodes'] if n['text']=='總額');spec={'name':'unsupported','table_id':target['parent_id'],'target_id':target['id'],'transform':'mask_body_amounts_v1'}
q=project(ir,spec);validate_query_binding(q)
result={'source_parent_sha256':sha(p.read_bytes()),'source_sha256':sha(encode(source)),'gate':q['gate'],'reasons':q['host_analysis']['reasons'],'annotations':{}}
for state in ['selected','ambiguous','missing_evidence','incompatible_context','not_a_total']:
 try:annotation(ir,q,'authored',{'target_id':target['id'],'state':state,'contributor_ids':[],'support_refs':[target['id']]});result['annotations'][state]='accepted'
 except ValueError as e:result['annotations'][state]=str(e)
for name,value in [('source',source),('evidence',ir),('query',q)]: (root/('prose-'+name+'.json')).write_bytes(encode(value))
p=packet/'S18_caption_and_separate_note';ir=json.loads((p/'evidence.json').read_text());q=project(ir,json.loads((p/'selection.json').read_text()));changed=deepcopy(q)
changed['context']['items']=[n for n in changed['context']['items'] if n['text']!='總額不包括租賃']
c=changed['context'];changed['host_analysis']=analyze_source(c['items'],c['table_id'],c['target_id']);changed['gate']='eligible';changed['query_id']=identity('query',{k:v for k,v in changed.items() if k!='query_id'})
for name,func in [('verify_query',lambda:verify_query(ir,changed)),('annotation',lambda:annotation(ir,changed,'authored',{'target_id':q['selection']['target_id'],'state':'ambiguous','contributor_ids':[],'support_refs':[q['selection']['target_id']]}))]:
 try:func();result['edited_projection_'+name]='accepted'
 except ValueError as e:result['edited_projection_'+name]=str(e)
(root/'prose-probes.json').write_bytes(encode(result));print(result)
