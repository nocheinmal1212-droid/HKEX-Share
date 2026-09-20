"""Frozen-rule finalist and diagnostic preparation, strictly evaluator-side."""
import argparse,json,statistics
from decimal import Decimal
from prepare_model_selection import ROOT,RUN,MODELS,read,save,batch
from evaluate_model_selection import evaluate,summarize

def confirmation():
 screen=read(RUN/'screen-complete.json');rows=screen['rows'];common=[r for r in rows if not r['attempt'].startswith('budget/')];configs=read(RUN/'configurations.json')
 eligible=[]
 for index,(k,*_) in enumerate(MODELS):
  if k=='gemini':continue
  rs=[r for r in common if r['model_key']==k]
  if (len(rs)==6 and not any(r['category']=='unsupported_selection' for r in rs) and sum(r['relation_match'] is True for r in rs)>=5 and any(r['case']=='S03' and r['category']=='correct_selection' for r in rs)):
   cost=sum(Decimal(str(r['cost_usd'])) for r in rs if r['cost_usd'] is not None)
   eligible.append((k,(-sum(r['full_pass'] for r in rs),any(r['cost_usd'] is None for r in rs),cost,statistics.median(r['elapsed_seconds'] for r in rs),index)))
 finalists=[]
 for flash in [True,False]:
  group=sorted((x for x in eligible if configs[x[0]]['flash']==flash),key=lambda x:x[1])
  if group:finalists.append(group[0][0])
 if 'gemini' in screen['active_routes']:finalists.append('gemini')
 settings={k:{'route':screen['active_routes'][k],'tokens':8192 if any(r['model_key']==k and r['attempt'].startswith('budget/') and r['full_pass'] for r in rows) else 4096} for k in finalists}
 save(RUN/'confirmation-selection.json',{'rule':'Frozen design, no weighted score','eligible_order':[{'model':k,'ranking_fields':[str(v) if isinstance(v,Decimal) else v for v in rank]} for k,rank in sorted(eligible,key=lambda x:x[1])],'finalists':settings,'screen_summary':summarize(common)})
 specs=[]
 for repeat in [1,2]:
  cases=['H01','H02','S11'];order=list(finalists)
  if repeat==2:cases.reverse();order.reverse()
  for c in cases:
   for k in order:specs.append({'model':k,'case':c,**settings[k]})
 if specs:batch('confirmation',specs)
 print('Finalists',settings,flush=True)

INSTRUCTION='''This is a diagnostic follow-up about your previous response, not a request to change it. Give a brief, source-grounded explanation of that response. Cite literal evidence IDs and short verbatim excerpts supporting the selection, abstention or refusal. Identify decisive missing evidence, conflicting context, instruction ambiguity or output-format constraint. If you now identify a specific unsupported assumption or error, state it plainly; otherwise say what remains uncertain. Name the smallest clarification or additional evidence that could resolve the issue, if applicable. Do not invent source facts, calculate financial amounts, supply a replacement answer, or provide private step-by-step reasoning. Return JSON with explanation, citations (objects with id and excerpt), uncertainty, and smallest_clarification. Keep the explanation concise.'''
SCHEMA={'type':'object','additionalProperties':False,'required':['explanation','citations','uncertainty','smallest_clarification'],'properties':{'explanation':{'type':'string'},'citations':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['id','excerpt'],'properties':{'id':{'type':'string'},'excerpt':{'type':'string'}}}},'uncertainty':{'type':'string'},'smallest_clarification':{'type':'string'}}}
def diagnostic():
 assert (RUN/'confirmation-selection.json').exists()
 rows=read(RUN/'screen-complete.json')['rows']
 cr=evaluate('confirmation') if (RUN/'confirmation').exists() else []
 save(RUN/'confirmation-initial-evaluation.json',{'summary':summarize(cr),'rows':cr})
 selected=[];omitted=[];unavailable=[]
 def qualifies(r):return r['state']=='model_refusal' or r['usable'] and (not r['full_pass'] or r['output']['action']=='abstain')
 for k,*_ in MODELS:
  rs=[r for r in rows if r['model_key']==k];cs=[r for r in cr if r['model_key']==k]
  wrong=next((r for r in rs if r['state']=='model_refusal' or r['usable'] and not r['full_pass']),None)
  abstain=next((r for r in rs if r['full_pass'] and r['output']['action']=='abstain'),None)
  cw=next((r for r in cs if r['state']=='model_refusal' or r['usable'] and not r['full_pass']),None)
  ca=next((r for r in cs if r['full_pass'] and r['output']['action']=='abstain'),None)
  for r in [wrong,abstain,cw or ca]:
   if r:selected.append(r)
  picked={r['attempt'] for r in selected}
  omitted += [r['attempt'] for r in rs+cs if qualifies(r) and r['attempt'] not in picked]
  unavailable += [r['attempt'] for r in rs+cs if not r['usable'] and r['state']!='model_refusal']
 specs=[]
 for r in selected:
  parent_name,parent_id=r['attempt'].split('/')
  e=next(e for e in read(RUN/parent_name/'manifest.json')['attempts'] if e['id']==parent_id)
  route=next(i for i,x in enumerate(read(RUN/'configurations.json')[r['model_key']]['routes']) if x['tag']==r['requested_provider'][0])
  original=r['content']
  if original is None:
   import base64
   env=json.loads(base64.b64decode(read(RUN/parent_name/'attempts'/parent_id/'response.json')['body_base64']))
   original=env['choices'][0]['message'].get('refusal')
  assert isinstance(original,str)
  specs.append({'model':r['model_key'],'case':r['case'],'route':route,'tokens':2048,'parent_attempt':r['attempt'],'diagnostic':{'original_content':original,'instruction':INSTRUCTION,'schema':SCHEMA}})
 save(RUN/'diagnostic-sampling.json',{'selected':[r['attempt'] for r in selected],'qualifying_omitted':omitted,'unavailable_decisions':unavailable,'initial_scores_frozen':True,'interpretation':'Full-contract failures include reason/support failure, reported separately from wrong relationships.'})
 if specs:batch('diagnostics',specs)
 print('Diagnostics',len(specs),'omitted qualifying',len(omitted),'unavailable',len(unavailable),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode');a=p.parse_args()
 if a.mode=='confirmation':confirmation()
 elif a.mode=='diagnostic':diagnostic()
