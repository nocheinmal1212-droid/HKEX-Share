"""Render completed interface experiment observations without modifying raw evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path


def render(run, report):
    rows=report['rows']; plan=json.loads((run/'execution-plan.json').read_text())
    offline=json.loads((run/'offline-boundaries.json').read_text())
    names={'pro':'V4 Pro (baseline)','flash':'V4 Flash (primary subject)','v41':'V4.1 Flash (extension)'}
    def table(headers,data):return ['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(row)+' |' for row in data]
    def link(row):
        name=row['status']
        if name=='http_error':name='HTTP '+str(row['http_status'])
        return f"[{name}](../runs/milestone2/interface-boundaries-2026-09-16/responses/{row['id']}.json)"
    out=['# Interface-boundary experiment — 2026-09-16','',
      'The approved experiment separates deterministic request/output consistency from model interpretation. Pro is a baseline, existing V4 Flash is the primary subject, and V4.1 Flash is a distinct extension. Reviewed fixture expectations are the authority. All routes were pinned to Fireworks; no fallback, prompt repair or retries were used.','',
      f"Executed {report['completed']}/{report['planned']} planned calls: 120 base-comparison calls and 60 extension calls. API-reported cost across available usage records: USD {report['reported_cost_usd']}; {report['records_without_reported_cost']} records have no reported cost.",'',
      '[Approved fixture proposal](interface-boundary-fixture-proposal.md) · [Frozen plan](../runs/milestone2/interface-boundaries-2026-09-16/execution-plan.json) · [Evaluation](../runs/milestone2/interface-boundaries-2026-09-16/evaluation.json)','',
      '## Per-model prompt results','',
      'B0 is the existing explicit P11 wording. B1 is the approved concise equivalent. Each model/prompt has ten cases, repeated three times. A service failure is not a semantic wrong answer, but it prevents acceptance for that planned observation.','']
    data=[]
    for route in names:
        for prompt in plan['prompt_arms']:
            subset=[r for r in rows if r['route']==route and r['prompt']==prompt]
            counts=Counter(r['status'] for r in subset)
            data.append([names[route],prompt.split('_')[0],str(len(subset)),str(counts['passed']),', '.join(f'{k}: {v}' for k,v in counts.items() if k!='passed') or 'none'])
    out+=table(['Model','Prompt','Calls','Passed','Other outcomes'],data)
    out+=['','## Deterministic fixtures','',
      'These are offline tests with response stubs and a call spy; no live model call is credited as saved or passed by these fixtures. The guard inspects structure and IDs only.','']
    out+=table(['Fixture','Fixture passed','Calls to stub','Actual boundary result','Semantic check'],[
      [r['id'],str(r['fixture_passed']),str(r['transport_spy_calls']),r['actual']['stage']+': '+r['actual']['state'],r['semantic_evaluation']] for r in offline['fixtures']])
    out+=['', 'D09 deliberately remains a semantic error even though output consistency is accepted. D01/D03/D10 retain precondition abstentions; duplicate/malformed input is rejected. Wrong IDs and inconsistent outputs are rejected, never repaired.','',
      '## Paired prompt observations','',
      'Efficiency figures use only pairs where both arms passed for the same model/case/repetition. Negative differences mean B1 used less time or fewer tokens. These are small observed samples with provider caching and scheduling outside our control, not performance guarantees.','']
    out+=table(['Model','Matched pairs','Both passed','Median prompt-token delta','Median completion-token delta','Median latency delta (s)'],[
      [names[r['route']],str(r['matched_pairs']),str(r['both_pass_pairs']),str(r['median_prompt_tokens_difference_concise_minus_baseline']),
       str(r['median_completion_tokens_difference_concise_minus_baseline']),str(r['median_latency_difference_concise_minus_baseline'])] for r in report['paired_comparisons']])
    out+=['','## Exact case outcomes','']
    for route in names:
        out+=['### '+names[route],'']
        subset=[r for r in rows if r['route']==route]
        cases=list(dict.fromkeys(r['case'] for r in subset))
        data=[]
        for case in cases:
            arms=[]
            for prompt in plan['prompt_arms']:
                group=sorted([r for r in subset if r['case']==case and r['prompt']==prompt],key=lambda r:r['repetition'])
                assert len(group)==3 and len({r['request_sha256'] for r in group})==1
                arms.append(', '.join(link(r) for r in group))
            data.append([case]+arms)
        out+=table(['Case','B0 repeats 1–3','B1 repeats 1–3'],data)+['']
    out+=['## Isolation and verification boundaries','',
      '- The experimental typed boundary validates C requests and renders the user payload during offline preparation. Every C case is eligible in both prompt arms, so the comparison does not improve scores by dropping difficult cases. The frozen request hashes protect the exact bytes sent.',
      '- Model responses are evaluated against the original schema and reviewed expected outputs, then against the typed output postconditions. Raw model failure and guard rejection are reported separately; no response is repaired. The guard is not integrated into production semantic dispatch.',
      '- The transport worker is the previously verified worker with only its accepted manifest version changed. Its OS sandbox denies project-file data; a Python audit allowlist restricts other reads after imports. Writes are limited to new response files and standard device output. Bootstrap injects the credential into a minimal environment; the worker cannot read .env, source fixtures or evaluator answers.',
      '- Twenty protected-read checks use pathlib and os.open against the evaluator key, fixture source, .env, README and six synthetic sentinels. No supplied PDF, native extractor output, evidence IR or benchmark data is used.',
      '- All comparisons use fresh two-message conversations, strict JSON schema, 512 output tokens, temperature zero, a 30-second deadline, sequential calls, and zero retries/fallback. First V4.1 calls also check observed access/model/provider and output shape within its planned 60 calls.',
      '- Metadata advertises structured outputs on the selected Fireworks endpoints. Requests pin the endpoint tag and returned provider names are checked; backend revision/weights and hidden provider preprocessing remain unknown. Same provider does not make different models identical serving environments.',
      '- IDs are sorted independently of evidence order in the schema enum. Prompt arms differ only in the system prompt; case data, schema and request settings are identical within each pair.',
      '- Unexpected abstention, wrong selection, malformed output, truncation, timeout and service errors remain separate outcomes. No intrinsic-capability conclusion follows from service or budget failures. This is synthetic interface testing, not full audit-pipeline validation.', '']
    return '\n'.join(out)


def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    report=json.loads((a.run/'evaluation.json').read_text())
    with a.out.open('x') as f:f.write(render(a.run,report))


if __name__=='__main__':main()
