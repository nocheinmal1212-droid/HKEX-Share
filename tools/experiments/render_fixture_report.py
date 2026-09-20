"""Render the completed offline evaluation into a reviewable Markdown appendix."""
import argparse
from collections import Counter
import json
from pathlib import Path


def render(report, run):
    rows = report['rows']
    routes = ['pro', 'flash', 'glm', 'gemini', 'pro_secondary']
    labels = {'pro':'DeepSeek Pro / Baidu', 'flash':'DeepSeek Flash / OpenInference',
              'glm':'GLM / DeepInfra', 'gemini':'Gemini / Google AI Studio (oracle)',
              'pro_secondary':'DeepSeek Pro / Ionstream'}
    short = {'passed':'pass','truncated':'token limit','http_error':'HTTP error',
             'access_or_parameter_unsupported':'access/parameter error','failure_to_abstain':'failed to abstain',
             'unexpected_abstention':'unexpected abstention','invalid_schema':'invalid schema',
             'wrong_selection':'wrong selection','timeout':'timeout','malformed_json':'malformed JSON'}
    def outcome(r):
        return f"[{short.get(r['status'], r['status'])}](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/{r['id']}.json)"
    def table(headers, data):
        return ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---']*len(headers))+' |'] + ['| '+' | '.join(r)+' |' for r in data]
    lines=['# Experimental fixture results — 2026-09-15','',
        'DeepSeek Pro, DeepSeek Flash and GLM are the subjects. Gemini is an independent comparison oracle. Reviewed fixture answers remain the scoring authority; Gemini does not receive subject outputs and its success alone cannot attribute a failure to model weights.','',
        f"Executed {report['completed_records']} of {report['planned']} predeclared calls sequentially, without retries. API-reported cost for records with usage: USD {report['reported_cost_usd']}; {report['records_without_reported_cost']} records have no reported cost. These are synthetic diagnostics, not financial-audit accuracy measurements.",'',
        '[Frozen plan](../runs/milestone2/hypothesis-fixtures-2026-09-15/execution-plan.json) · [Launch and isolation revision](../runs/milestone2/hypothesis-fixtures-2026-09-15/launch-attestation.json) · [Machine-readable evaluation](../runs/milestone2/hypothesis-fixtures-2026-09-15/evaluation.json)','',
        '## Shared explicit prompt: nine-case core suite','']
    cases=['zh_total','reordered','rebound_ids','renamed_ids','no_total','missing_target','ambiguous_total','english_total','simplified_total']
    core=[r for r in rows if 'core' in r['groups']]
    index={(r['route'],r['case']):r for r in core}
    lines+=table(['Case']+[labels[r] for r in routes[:4]],[[c]+[outcome(index[r,c]) for r in routes[:4]] for c in cases])
    lines+=['','## H1 / H2: vocabulary and scope factorial','',
        'P00 = original; P10 = vocabulary only; P01 = scope only; P11 = both. Each cell below is one first observation. All use the strict schema.','']
    first=[r for r in rows if 'H1' in r['groups']]
    index={(r['route'],r['case'],r['prompt']):r for r in first}
    lines+=table(['Route','Case','P00','P10','P01','P11'],[[labels[r],c]+[outcome(index[r,c,p]) for p in ['P00','P10','P01','P11']] for r in routes[:4] for c in ['zh_total','no_total','missing_target']])
    lines+=['','## H3: schema mode with identical explicit messages','', 'No output repair: both modes use the same local contract validator. One observation per mode and case.','']
    index={(r['route'],r['case'],r['strict']):r for r in rows if r['prompt']=='P11' and r['repetition']==1 and r['route']!='pro_secondary'}
    lines+=table(['Route','Case','Strict schema','No API schema'],[[labels[r],c,outcome(index[r,c,True]),outcome(index[r,c,False])] for r in routes[:4] for c in ['zh_total','no_total','missing_target']])
    lines+=['','## H4: repeated identical requests','',
        'Three observations per subject, prompt and common case. Request hashes must match within each row. The first observations also appear in the factorial/core tables. Provider tags are pinned; response provider names are verified. The API does not independently attest endpoint revision or weights.','']
    repeats=[r for r in rows if r['route']!='gemini' and (set(r['groups']) & {'H4_first','H4_repeat','H4_provider'})]
    data=[]
    for route in ['pro','flash','glm','pro_secondary']:
        for case in ['zh_total','no_total','missing_target']:
            for prompt in ['P00','P11']:
                group=sorted([r for r in repeats if (r['route'],r['case'],r['prompt'])==(route,case,prompt)],key=lambda r:r['repetition'])
                assert len(group)==3 and len({r['request_sha256'] for r in group})==1
                data.append([labels[route],case,prompt]+[outcome(r) for r in group])
    lines+=table(['Route','Case','Prompt','Repeat 1','Repeat 2','Repeat 3'],data)
    lines+=['','## H5: completion budget','', 'Original prompt without API schema; 30-second deadline unchanged. Gemini receives the same budget conditions as an oracle.','']
    budget=[r for r in rows if 'H5_budget' in r['groups']]
    index={(r['route'],r['case'],r['budget']):r for r in budget}
    lines+=table(['Route','Case','512 tokens','2,048 tokens'],[[labels[r],c,outcome(index[r,c,512]),outcome(index[r,c,2048])] for r in ['pro','gemini'] for c in ['zh_total','no_total']])
    lines+=['','## Coverage and failure ledger','', 'Counts below include exploratory configurations and repeated calls. They are workload/completion diagnostics, not an accuracy ranking.','']
    lines+=table(['Route','Calls','Outcomes'],[[labels[r],str(sum(report['counts_by_route'][r].values())),', '.join(f'{k}: {v}' for k,v in report['counts_by_route'][r].items())] for r in routes])
    lines+=['','## Isolation and interpretation boundaries','',
        '- The worker reads a request-only manifest with opaque call IDs. Evaluator answers and Gemini comparison results are absent from that manifest and unavailable to the worker.',
        '- The final macOS sandbox denies project-file contents and limits writes to the response directory and standard device output. A Python audit allowlist restricts other file reads after imports to staging, the interpreter runtime and CA certificates; process launch and foreign-code loading are denied by that hook. This is defense in depth for a trusted worker, not a claim of a general hostile-code sandbox.',
        '- Two initial broad OS allowlist profiles could not start the interpreter. No calls occurred under those profiles. The working profile and the worker were finalized before live calls; the launch attestation records their hashes without changing the frozen request manifest.',
        '- Twenty protected-read checks passed before execution: pathlib and os.open attempts against the evaluator key, fixture source, .env, README and six synthetic sentinel files. The sentinel named corpus.pdf is invented test data; no supplied PDF was opened.',
        '- Every request uses a fresh two-message conversation. No automatic retries, fallback, cache-busting text, explanations requested, extra reasoning settings or response corrections.',
        '- Responses preserve bounded bytes, with credential-only redaction if necessary. Unknown response revision and missing costs remain unknown. Provider-side caching, scheduling, preprocessing and token accounting are outside our control.',
        '- Reordering the evidence also reorders the schema ID enum under the approved fixture construction; that fixture tests combined occurrence-order portability rather than isolating those two orders.',
        '- The alternate Pro provider block occurs later than the primary block, so provider and time cannot be fully separated. Three repeats and single-observation schema comparisons are small diagnostic samples.',
        '- A subject/oracle disagreement is evidence of a differing tested model/provider path; it is not proof of an intrinsic capability failure. Oracle agreement does not replace reviewed expected answers.', '']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    report=json.loads((a.run/'evaluation.json').read_text())
    with a.out.open('x') as stream: stream.write(render(report,a.run))


if __name__=='__main__': main()
