"""Preserve the source-only review's G4 ambiguity; author a separate corrected fixture."""
import json
from pathlib import Path
from hkex_audit.artifacts import encode,sha
from hkex_audit.adapters.mineru import adapt
from hkex_audit.evidence import validate_evidence
from hkex_audit.semantic import project,verify_query

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
old=HERE/'sources/G4'
src=json.loads((old/'source.json').read_text())
note=src['pdf_info'][0]['preproc_blocks'][0]['blocks'][1]['lines'][0]['spans'][0]
note['content']+='本表定義：同一合計不可同時歸屬銷售額及銷售量。上述表頭歸屬與本註均為有效聲明，兩者無優先或更正關係。'
doc={'doc_id':'citation-policy-g4-revision2','variant_id':'authored-v2','source_document_sha256':None,'source_provenance':'synthetic'}
e=adapt(src,doc,sha(encode(src)));validate_evidence(e,src)
table=next(n for n in e['nodes'] if n['kind']=='table')
target=next(n for n in e['nodes'] if n['kind']=='cell' and (n['row'],n['column'])==(1,2))
q=project(e,{'name':'g4_revision2','table_id':table['id'],'target_id':target['id'],'transform':'mask_body_amounts_v1'});verify_query(e,q)
d=HERE/'sources/G4_revision2';d.mkdir()
def write(p,x):
    with p.open('xb') as f:f.write(encode(x))
for fn,x in [('source.json',src),('evidence.json',e),('query-v1.json',q)]:write(d/fn,x)
old_e=json.loads((old/'evidence.json').read_text())
mapping={a['id']:b['id'] for a,b in zip(old_e['nodes'],e['nodes'])}
manifest={'fixture':'G4_revision2','classification':'synthetic_generalization','source_provenance':'Authored logical contradiction; no actual report or MinerU execution claimed.',
  'operation_version_for_projection':q['version'],'proposed_policy_version':'direct-contributor-headers-1.1.0-proposal','target_id':target['id'],
  'transformation':{'parent':'sources/G4/source.json','parent_sha256':sha((old/'source.json').read_bytes()),
    'reason':'Source-only review found a possible note-as-correction reading. Explicitly declare mutually exclusive, effective statements with no priority/correction.',
    'semantic_edits':['Append only the literal mutually-exclusive/no-priority statement to the existing table note.'],
    'administrative_changes':['New document, source and occurrence identities.'],'id_mapping':mapping},
  'source_citations':[{'id':n['id'],'text':n['text'],'parent_id':n['parent_id'],'row':n['row'],'column':n['column'],'row_span':n['row_span'],'column_span':n['column_span'],'fragments':n['fragments']} for n in e['nodes'] if n['text'] is not None],
  'files':{fn:sha((d/fn).read_bytes()) for fn in ('source.json','evidence.json','query-v1.json')}}
write(d/'manifest.json',manifest)
write(HERE/'source-only-index-revision2.json',{'adds_to':'source-only-index.json','fixture':'G4_revision2',
 'source':str((d/'source.json').relative_to(ROOT)),'evidence':str((d/'evidence.json').relative_to(ROOT)),
 'manifest':str((d/'manifest.json').relative_to(ROOT)),'target_id':target['id'],'supersedes_for_conflict_case':'G4; original source preserved, not freeze-ready'})
print('Created G4 revision 2; original G4 unchanged.')
