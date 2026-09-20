"""One-off staged screen. No implicit retry, route or prompt tuning."""
import json,subprocess,sys
from prepare_model_selection import RUN,ROOT,MODELS,batch,save
from evaluate_model_selection import evaluate

def launch(name):
 for extra in [['--preflight'],[]]:
  subprocess.run([sys.executable,str(ROOT/'tools/experiments/launch_model_selection.py'),name,*extra],check=True)

def main():
 rows=evaluate('availability');assert len(rows)==9
 save(RUN/'availability-evaluation.json',{'rows':rows})
 routes={r['model_key']:0 for r in rows if r['category'] not in ('service_error','timeout')}
 if any(r['http_status'] in (401,402,403) for r in rows):raise SystemExit('Account/access failure; stopped')
 alternate=[{'model':r['model_key'],'case':'S03','route':1} for r in rows if r['category'] in ('service_error','timeout')]
 if alternate:
  batch('alternate',alternate);launch('alternate');alt=evaluate('alternate');save(RUN/'alternate-evaluation.json',{'rows':alt})
  routes.update({r['model_key']:1 for r in alt if r['category'] not in ('service_error','timeout')})
  rows+=alt
 for round_id,case in enumerate(['S04','S08','S11','S09','S10'],1):
  order=[m[0] for m in MODELS];shift=2*round_id%len(order);order=order[shift:]+order[:shift]
  if round_id%2:order.reverse()
  specs=[{'model':k,'case':case,'route':routes[k]} for k in order if k in routes]
  if not specs:break
  name='screen-'+case.lower();batch(name,specs);launch(name);rs=evaluate(name);save(RUN/(name+'-evaluation.json'),{'rows':rs});rows+=rs
  for r in rs:
   if r['category'] in ('service_error','timeout'):routes.pop(r['model_key'],None)
  if any(r['http_status'] in (401,402,403) for r in rs):raise SystemExit('Account/access failure; stopped')
  print('Completed',case,'active',list(routes),flush=True)
 tuning=[]
 for k,route in routes.items():
  r=next((r for r in rows if r['model_key']==k and r['category']=='truncation'),None)
  if r:tuning.append({'model':k,'case':r['case'],'route':route,'tokens':8192,'parent_attempt':r['attempt']})
 if tuning:
  batch('budget',tuning);launch('budget');rs=evaluate('budget');save(RUN/'budget-evaluation.json',{'rows':rs});rows+=rs
 save(RUN/'screen-complete.json',{'rows':rows,'active_routes':routes})
 print('Screen complete',len(rows),'attempts',flush=True)
if __name__=='__main__':main()
