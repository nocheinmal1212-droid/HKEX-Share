from pathlib import Path
from copy import deepcopy
import json, sys
sys.path.insert(0,str(Path.cwd()/'src'))
from hkex_audit.adapters.mineru import adapt
from hkex_audit.artifacts import encode, sha
from hkex_audit.semantic import project, validate_answer
from hkex_audit.header_support import analyze_source
root=Path('runs/semantic-citation-review-2026-09-19')
p=Path('eval/semantic-citation-implementation/1.1.0/fixtures/S01_actual_sibling_outer')
base=json.loads((p/'source.json').read_text())
records={'exposure':'post-exposure contract diagnostics; no model or provider calls','base_sha256':sha((p/'source.json').read_bytes()),'expectation_sha256':sha((root/'probe-plan.md').read_bytes()),'probes':[]}
for name in ['control','p1_continued']:
 source=deepcopy(base)
 if name!='control':
  block=source['pdf_info'][0]['preproc_blocks'][0]['blocks'][0]
  block['html']=block['html'].replace('rowspan="2"','rowspan="3"').replace('</tr><tr><td>於某一時點','</tr><tr><td colspan="3">Continued</td></tr><tr><td>於某一時點')
 document={'doc_id':'review-'+name,'variant_id':'authored','source_document_sha256':None,'source_provenance':'synthetic'}
 raw=encode(source); ir=adapt(source,document,sha(raw))
 cells=[n for n in ir['nodes'] if n['kind']=='cell'];by_text={n['text']:n['id'] for n in cells}
 spec={'name':name,'table_id':next(n['id'] for n in ir['nodes'] if n['kind']=='table'),'target_id':by_text['總額'],'transform':'mask_body_amounts_v1'}
 q=project(ir,spec)
 out=root/name;out.mkdir()
 for f,value in [('source',source),('evidence',ir),('selection',spec),('query',q)]: (out/(f+'.json')).write_bytes(encode(value))
 records['probes'].append({'name':name,'source_sha256':sha(raw),'ir_sha256':sha(encode(ir)),'query_id':q['query_id'],'gate':q['gate'],'analysis':q['host_analysis']})
 if name=='control':
  answer={'target_id':by_text['總額'],'state':'selected','contributor_ids':[by_text['港幣百萬元'],by_text['租賃(HKFRS 16)']],'support_refs':[by_text[t] for t in ['港幣百萬元','租賃(HKFRS 16)','總額']]}
  try:validate_answer(q,answer); outcome='accepted'
  except Exception as e:outcome=repr(e)
  records['probes'].append({'name':'p2_presentation_contributor','answer':answer,'host_outcome':outcome,'expected_semantics':'wrong; scope question, not by itself a host correctness bug'})
  changed=deepcopy(ir['nodes']);leaf=next(n for n in changed if n['text']=='於某一時點確認收入');leaf['column_span']=5
  a=analyze_source([n for n in changed if n['kind'] in ('cell','table')],spec['table_id'],spec['target_id'])
  records['probes'].append({'name':'p3_crossing_interval','analysis':a,'crossing_leaf_in_category_path':bool(a['paths'][leaf['id']])})
(root/'header-probes.json').write_bytes(encode(records))
print([(r['name'],r.get('gate',r.get('host_outcome',r.get('crossing_leaf_in_category_path')))) for r in records['probes']])
