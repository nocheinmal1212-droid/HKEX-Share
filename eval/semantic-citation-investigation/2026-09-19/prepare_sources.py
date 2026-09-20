"""Offline authored investigation fixtures. Not runtime code or model results."""
from copy import deepcopy
from pathlib import Path
import json
from hkex_audit.artifacts import encode, sha
from hkex_audit.adapters.mineru import adapt
from hkex_audit.evidence import validate_evidence
from hkex_audit.semantic import project, verify_query

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
def read(p): return json.loads((ROOT / p).read_text())
def write(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f: f.write(encode(x))

packet = read('eval/semantic-integration/2026-09-18/source-review-packet.json')
ir = read('runs/milestone1-r1/corrupted/evidence.json')
assert sha((ROOT/'runs/milestone1-r1/corrupted/evidence.json').read_bytes()) == packet['source_sha256']
ns = {n['id']:n for n in packet['nodes']}
ss = {s['id']:s for s in ir['sources']}
unit = ns['cell-b52c32ff495ebd5add32f9e2f6d31a1a4625de8f528e78aa3985617119514bfa']
html = ss[unit['source_span']['source_id']]['text']
f = unit['fragments'][0]
assert html[f['start']:f['end']] == '港幣百萬元'
blank_html = html[:f['start']] + html[f['end']:]

def native(h, caption=None, note=None):
    blocks=[]
    if caption is not None: blocks.append({'type':'table_caption','lines':[{'spans':[{'type':'text','content':caption}]}]})
    blocks.append({'type':'table_body','lines':[{'spans':[{'type':'table','html':h}]}]})
    if note is not None: blocks.append({'type':'table_footnote','lines':[{'spans':[{'type':'text','content':note}]}]})
    # Profile fields select an existing parser, not an assertion of actual OCR execution.
    return {'_backend':'vlm','_version_name':'3.2.2','pdf_info':[{'page_idx':0,'preproc_blocks':[{'type':'table','blocks':blocks}]}]}

g2='<table><tr><td colspan="3">銷售額（港幣百萬元）</td><td colspan="3">銷售量（千件）</td></tr><tr><td>產品甲</td><td>產品乙</td><td>合計</td><td>產品甲</td><td>產品乙</td><td>合計</td></tr><tr><td>17</td><td>23</td><td>91</td><td>5</td><td>8</td><td>42</td></tr></table>'
g2v='<table><tr><td colspan="3">銷售量（千件）</td><td colspan="3">銷售額（港幣百萬元）</td></tr><tr><td>產品丁</td><td>產品丙</td><td>合計</td><td>產品丁</td><td>產品丙</td><td>合計</td></tr><tr><td>700</td><td>9</td><td>2</td><td>61</td><td>401</td><td>6</td></tr></table>'
g3='<table><tr><td colspan="2">銷售額（港幣百萬元）</td><td colspan="2">銷售量（千件）</td><td></td></tr><tr><td>產品甲</td><td>產品乙</td><td>產品甲</td><td>產品乙</td><td>合計</td></tr></table>'
g5='<table><tr><td colspan="2">銷售量（千件）</td><td rowspan="2">合計（港幣百萬元）</td></tr><tr><td>產品甲</td><td>產品乙</td></tr></table>'
specs = [
 ('G1',blank_html,'截至2026年12月31日止年度',None,(0,5)),
 ('G2',g2,None,None,(1,2)),
 ('G2_variation',g2v,None,None,(1,5)),
 ('G3',g3,None,'合計僅包含與其同一計量口徑的產品甲及產品乙；計量口徑見表頭。',(1,4)),
 ('G4',g2,None,'銷售額（港幣百萬元）表頭下的合計：本合計僅列銷售量（千件）。',(1,2)),
 ('G5',g5,None,'本表僅列銷售量（千件）的產品甲及產品乙作為候選類別；合計僅包含與其同一計量口徑的類別。未列其他類別或計量口徑轉換關係。',(0,2)),
]
records=[]
for name,h,caption,note,target in specs:
    d=OUT/'sources'/name
    src=native(h,caption,note); raw=encode(src)
    doc={'doc_id':'citation-policy-'+name.lower(),'variant_id':'authored-v1','source_document_sha256':None,'source_provenance':'synthetic'}
    e=adapt(src,doc,sha(raw)); validate_evidence(e,src)
    table=next(n for n in e['nodes'] if n['kind']=='table')
    cells={(n['row'],n['column']):n for n in e['nodes'] if n['kind']=='cell'}
    q=project(e,{'name':name.lower(),'table_id':table['id'],'target_id':cells[target]['id'],'transform':'mask_body_amounts_v1'})
    verify_query(e,q)
    mapping={}
    if name=='G1':
        old=[n for n in packet['nodes'] if n['parent_id']==unit['parent_id'] and n['kind']=='cell']
        for n in old:
            nn=cells[n['row'],n['column']]; mapping[n['id']]=nn['id']
            assert all(n[k]==nn[k] for k in ('row','column','row_span','column_span'))
            assert nn['text']==('' if n['id']==unit['id'] else n['text'])
        q_caption=[n['text'] for n in e['nodes'] if n['text'] and '2026' in n['text']]
        assert q_caption==['截至2026年12月31日止年度']
    record={'fixture':name,'classification':'derived_source_generalization' if name=='G1' else 'synthetic_generalization',
      'source_provenance':'Authored offline; profile envelope is parser input syntax, not a MinerU run or an actual report.',
      'operation_version_for_projection':q['version'],'proposed_policy_version':'direct-contributor-headers-1.1.0-proposal',
      'transformation': {'semantic_edits':['Replace only the common-unit literal with an explicit blank HTML cell.'] if name=='G1' else ['Author literal groups, headers, and any table-associated note.'],
        'administrative_changes':['New source/document/node identities; single logical page index 0; no physical geometry claimed; source envelope recreated for the existing adapter.'],
        'parent_packet':{'path':'eval/semantic-integration/2026-09-18/source-review-packet.json','sha256':sha((ROOT/'eval/semantic-integration/2026-09-18/source-review-packet.json').read_bytes())} if name=='G1' else None,
        'original_html_source':ss[unit['source_span']['source_id']] if name=='G1' else None,
        'original_to_derived_cell_ids':mapping},
      'target_id':q['selection']['target_id'], 'source_citations':[{'id':n['id'],'text':n['text'],'parent_id':n['parent_id'],'row':n['row'],'column':n['column'],'row_span':n['row_span'],'column_span':n['column_span'],'fragments':n['fragments']} for n in e['nodes'] if n['text'] is not None],
      'files':{}}
    for fn,value in [('source.json',src),('evidence.json',e),('query-v1.json',q)]:
        write(d/fn,value);record['files'][fn]=sha((d/fn).read_bytes())
    write(d/'manifest.json',record);records.append(record)

# Explicit occurrence mapping for amount/name/order variation, never compare opaque IDs directly.
base=json.loads((OUT/'sources/G2/evidence.json').read_text()); var=json.loads((OUT/'sources/G2_variation/evidence.json').read_text())
bc={(n['row'],n['column']):n for n in base['nodes'] if n['kind']=='cell'}
vc={(n['row'],n['column']):n for n in var['nodes'] if n['kind']=='cell'}
mapping={}
for (r,c),n in bc.items():
    group=3 if c<3 else 0; offset=c%3
    newc=group+(0 if r==0 else {0:1,1:0,2:2}[offset])
    mapping[n['id']]=vc[r,newc]['id']
write(OUT/'sources/G2-variation-map.json',{'version':'1.0.0','changes':['Swap amount/quantity group order.','Rename product 甲 to 丙 and 乙 to 丁; reverse product order within each group.','Replace all body amounts independently, without arithmetic constraints.'],'id_mapping':mapping})
write(OUT/'source-only-index.json',{'scope':'Source-only review. No answers or expected support lists.','sources':[{'fixture':r['fixture'],'manifest':str((OUT/'sources'/r['fixture']/'manifest.json').relative_to(ROOT)),'source':str((OUT/'sources'/r['fixture']/'source.json').relative_to(ROOT)),'evidence':str((OUT/'sources'/r['fixture']/'evidence.json').relative_to(ROOT)),'target_id':r['target_id']} for r in records]})
print('Prepared',len(records),'source fixtures; validated native-to-IR fragments and faithful v1 projections. No inference.')
