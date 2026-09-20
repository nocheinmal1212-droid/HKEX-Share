"""Freeze authored source expectations without importing semantic/header runtime."""
from copy import deepcopy
from pathlib import Path
import subprocess, sys
sys.path.insert(0,str(Path.cwd()/'src'))
from hkex_audit.adapters.mineru import adapt
from hkex_audit.artifacts import read, encode, sha, write_new
ROOT=Path.cwd(); HERE=Path(__file__).resolve().parent
REVIEW=ROOT/'runs/semantic-citation-review-2026-09-19/p1_continued'
old=read(ROOT/'eval/semantic-citation-implementation/1.1.0/implementation-bindings.json')
assert all(sha((ROOT/p).read_bytes())==h for p,h in old['files'].items())
# Preserve the exact uncommitted pre-correction runtime, independently of HEAD.
files=subprocess.check_output(['rg','--files','src','schemas'],text=True).splitlines()+['pyproject.toml']
for p in files:
 dest=HERE/'runtime-before'/p;dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write((ROOT/p).read_bytes())
write_new(HERE/'baseline.json',{'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
 'original_bindings_sha256':sha((ROOT/'eval/semantic-citation-implementation/1.1.0/implementation-bindings.json').read_bytes()),
 'runtime_files':{p:sha((ROOT/p).read_bytes()) for p in files},'original_implementation_files':old['files'],
 'review_source_sha256':sha((REVIEW/'source.json').read_bytes()),'review_ir_sha256':sha((REVIEW/'evidence.json').read_bytes()),
 'exposure':'post-exposure regression, not independent semantic confirmation'})
base=read(REVIEW/'source.json');html=base['pdf_info'][0]['preproc_blocks'][0]['blocks'][0]['html']
variants={'nested':html,
 'repeated':html.replace('rowspan="3"','rowspan="4"').replace('<td colspan="3">Continued</td></tr>','<td colspan="3">Continued</td></tr><tr><td colspan="3">Continued</td></tr>'),
 'reordered':html.replace('<td>於某一時點確認收入</td><td>隨時間逐步確認收入</td>','<td>隨時間逐步確認收入</td><td>於某一時點確認收入</td>').replace('<td>17</td><td>3</td><td>20</td><td>4</td><td>24</td>','<td>701</td><td>9</td><td>12</td><td>803</td><td>5</td>'),
 'missing':html.replace('隨時間逐步確認收入',''),
 'duplicate':html.replace('隨時間逐步確認收入','於某一時點確認收入'),
 'extra':html.replace('colspan="3"','colspan="4"').replace('<td>合計</td>','<td>合計</td><td>備忘</td>').replace('<td>20</td>','<td>20</td><td>99</td>'),
 'unknown':html.replace('Continued','Reported scope'),
 'crossing':'<table><tr><td colspan="3">來自與客戶合約之收入</td><td colspan="2">Continued</td></tr><tr><td colspan="2">Continued</td><td colspan="3">2025</td></tr><tr><td>甲</td><td>乙</td><td>丙</td><td>丁</td><td>總額</td></tr></table>'}
for name,text in variants.items():
 dest=HERE/'fixtures'/name;dest.mkdir(parents=True)
 source=deepcopy(base);source['pdf_info'][0]['preproc_blocks'][0]['blocks'][0]['html']=text
 if name=='nested':ir=read(REVIEW/'evidence.json')
 else:ir=adapt(source,{'doc_id':'presentation-regression-'+name,'variant_id':'authored','source_document_sha256':None,'source_provenance':'synthetic'},sha(encode(source)))
 cells=[n for n in ir['nodes'] if n['kind']=='cell']
 def ref(label):
  found=[n['id'] for n in cells if n['text']==label];assert len(found)==1,(name,label);return found[0]
 positive=name in ('nested','repeated','reordered')
 target_labels=['總額','合計'] if name in ('nested','repeated','reordered','missing','unknown') else ['總額']
 expected=[];specs=[]
 for target in target_labels:
  key='outer' if target=='總額' else 'subtotal';tid=ref(target)
  specs.append({'name':key,'table_id':next(n['parent_id'] for n in cells if n['id']==tid),'target_id':tid,'transform':'mask_body_amounts_v1'})
  contributors=[ref(x) for x in (['合計','租賃(HKFRS 16)'] if key=='outer' else ['於某一時點確認收入','隨時間逐步確認收入'])] if positive else []
  expected.append({'name':key,'gate':'eligible' if positive else 'blocked_scope','contributors':contributors,
   'support':sorted(set([tid,*contributors,ref('來自與客戶合約之收入(HKFRS 15)')])) if positive else [],
   'presentation_refs':[n['id'] for n in cells if n['text']=='Continued'] if positive else []})
 write_new(dest/'source.json',source);write_new(dest/'evidence.json',ir);write_new(dest/'selections.json',specs);write_new(dest/'expectations.json',expected)
write_new(HERE/'fixture-freeze.json',{'classification':'post-exposure authored regression; no inference',
 'cases':list(variants),'files':{str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file()},
 'before_runtime_edit':True})
print('Frozen 8 authored sources, 13 target expectations and pre-correction runtime.')
