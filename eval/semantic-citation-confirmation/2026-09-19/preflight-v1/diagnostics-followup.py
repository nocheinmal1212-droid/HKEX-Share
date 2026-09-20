"""Finish reporting interrupted diagnostics without overwriting the first run.

The first harness eagerly evaluated r['result']['state'] as dict.get's default
even for a successful replay that has validation.state. Runtime was unaffected.
No expected outcome changes; keep the initial helper and all its artifacts.
"""
import os
os.environ={}
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('diagnostics_original',HERE/'diagnostics.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


def main():
    baseline=d.OUT/'batch-baseline'
    records=[]
    for variant in ('research_missing','research_corrupt','primary_corrupt'):
        dest=d.OUT/('isolation-'+variant)
        for name in d.EXPECT:
            out=dest/'checked-followup'/name;out.mkdir(parents=True)
            d.cli.isolated('consume_worker',{'selection':d.SELECTION,'spec':d.QUERIES[name]['selection'],
                'batch':str(dest),'output':str(out),'nonce':baseline.name})
            r=d.cli.isolated('research_replay_worker',{'selection':d.SELECTION,'spec':d.QUERIES[name]['selection'],
                'batch':str(dest),'nonce':baseline.name})
            d.put(dest/'research-followup'/name/'replay.json',r)
            same=all((out/f).read_bytes()==(baseline/'operational'/name/f).read_bytes()
                     for f in ('annotations.json','provenance.json'))
            if variant.startswith('research'):
                assert same and r['result']['state']=='incomplete_attempt'
            else:
                assert d.read(out/'annotations.json')==[]
                assert r['result']['validation']['state']=='accepted'
            log=d.read(out/'consumption.json')
            assert log['model_calls']==0 and not log['adapter_imported']
            assert not any('/research/' in x.get('path','') or '/eval/' in x.get('path','') for x in log['access_attempts'])
            assert r['result']['model_calls']==0
            records.append({'variant':variant,'name':name,'primary':d.read(out/'provenance.json')['outcome'],
                'research':r['result'].get('validation',{}).get('state',r['result'].get('state')),
                'primary_bytes_identical':same,'replay_model_calls':0})
        print('completed role isolation:',variant,flush=True)
    d.put(d.OUT/'role-isolation-followup.json',records)
    d.blank_control()
    d.put(d.OUT/'harness-followup.json',{'initial_failure':'Diagnostic-only KeyError while reporting successful research replay; eager dict.get default referenced absent top-level state.',
        'correction':'Use nested safe .get only in this new follow-up reporting helper.',
        'expected_outcomes_changed':False,'runtime_changed':False,'old_outputs_overwritten':False,
        'all_required_checks_completed':True,'model_calls':0,'metadata_calls':0,
        'known_execution_blocker':'Current CLI cannot enforce a hard 600-second total ceiling.'})
    assert not Path(d.read(d.PACKET/'launch-proposal.json')['live_output']).exists()
    print('Follow-up complete, blank control zero-call; no live directory.',flush=True)


if __name__=='__main__': main()
