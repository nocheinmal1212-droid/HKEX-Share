"""Build an evaluator-only, hash-bound M1 review packet from independently generated IR."""
import argparse
from html import escape
from pathlib import Path
from hkex_audit.artifacts import read, write_new, fingerprint, sha, require
from validate import ROOT, verified_intake


def node_selection(evidence, case):
    prefix=f"/pdf_info/{case['page_index']}/preproc_blocks/{case['block_index']}"
    if case['row'] is None:
        candidates=[n for n in evidence['nodes'] if n['native_pointer'].startswith(prefix+'/') and n['kind']=='block' and n['text'] is not None]
    else:
        candidates=[n for n in evidence['nodes'] if n['native_pointer'].startswith(prefix+'/') and n['kind']=='cell' and n['row']==case['row'] and n['column']==case['column']]
    return candidates


def table_view(evidence,page,block):
    prefix=f'/pdf_info/{page}/preproc_blocks/{block}'
    tables=[n for n in evidence['nodes'] if n['native_pointer']==prefix and n['kind']=='table']
    if not tables:return '<p>No table recovered; review required.</p>'
    t=tables[0];rows={};cells=[n for n in evidence['nodes'] if n['parent_id']==t['id'] and n['kind']=='cell']
    for n in cells:rows.setdefault(n['row'],[]).append(n)
    body=''.join('<tr>'+''.join(f'<td rowspan="{n["row_span"]}" colspan="{n["column_span"]}" title="{escape(n["id"],quote=True)}">{escape(n["text"] or "")}</td>' for n in sorted(row,key=lambda n:n['column']))+'</tr>' for _,row in sorted(rows.items()))
    sources=[s for s in evidence['sources'] if s['pointer'].startswith(prefix+'/') and s['format']=='html']
    return f'<p>Grid: {escape(t["grid_state"])}. Page index: {page}. Cell geometry unavailable.</p><div class="scroll"><table>{body}</table></div>'+''.join('<details><summary>Literal native HTML and pointer</summary><pre>'+escape(s['pointer']+'\n'+s['text'])+'</pre></details>' for s in sources)


def prepare(runs, output):
    cfg,ready,records=verified_intake();runs=Path(runs).resolve();output=Path(output).resolve()
    require(not output.exists(),'review path exists; choose a new review revision')
    verification=read(runs/'verification.json');evidence={v:read(Path(d['run_dir'])/'evidence.json') for v,d in verification['variants'].items()}
    candidates=[];sections=[]
    for case in cfg['cases']:
        record=records[case['error_id']];variants={}
        for variant,e in evidence.items():
            nodes=node_selection(e,case);expected=record['original_text'] if variant=='clean' else record['injected_text']
            matches=[]
            for n in nodes:
                offsets=[];start=0
                while expected and (pos:=n['text'].find(expected,start))!=-1:
                    offsets.append([pos,pos+len(expected)]);start=pos+len(expected)
                if offsets:matches.append({'evidence_id':n['id'],'native_pointer':n['native_pointer'],'text':n['text'],
                                           'source_span':n['source_span'],'fragments':n['fragments'],'token_offsets':offsets})
            status='proposed' if len(nodes)==1 and len(matches)==1 and len(matches[0]['token_offsets'])==1 else 'ambiguous_or_unmapped'
            variants[variant]={'status':status,'expected_source_text':expected,'candidates':matches,'generated_ir_sha256':verification['variants'][variant]['evidence_sha256']}
        candidate={'error_id':case['error_id'],'evaluation_location':record['location'],'secondary_locations':record['secondary_locations'],
                   'variants':variants,'review_status':'pending','reviewer':None,'reviewed_at':None,
                   'fidelity_basis':'Existing owner-reviewed source case plus new native/IR correspondence; no new PDF inspection.'}
        candidates.append(candidate)
        content='<h2>'+escape(case['error_id'])+'</h2><p>New correspondence: pending owner review. These are evaluator-authored locations, not runtime operand selection.</p>'
        for variant,data in variants.items():
            content+='<h3>'+escape(variant)+' — '+escape(data['status'])+'</h3>'
            content+='<p>Approved source token: <code>'+escape(data['expected_source_text'])+'</code></p>'
            for n in data['candidates']:
                content+='<pre>'+escape(n['native_pointer']+'\n'+n['evidence_id']+'\n'+n['text'])+'</pre>'
            if case['row'] is not None:content+=table_view(evidence[variant],case['page_index'],case['block_index'])
        sections.append(content)
    for region in cfg['additional_evidence']:
        sections.append('<h2>Additional evidence: '+escape(region['purpose'])+'</h2><p>Fidelity/relationship interpretation unreviewed.</p>'+table_view(evidence['clean'],region['page_index'],region['block_index']))
    benign=read(ROOT/'eval/negatives/milestone1-proposals.json')
    for fixture in benign['fixtures']:
        native=read(ROOT/fixture['input_path']);html=native['pdf_info'][0]['preproc_blocks'][0]['blocks'][0]['lines'][0]['spans'][0]['html']
        sections.append('<h2>Synthetic fixture: '+escape(fixture['fixture_id'])+'</h2><p>'+escape(fixture['expected_behavior'])+'</p><pre>'+escape(html)+'</pre><p>Proposed label; no detector executed.</p>')
    packet={'schema_version':'1.0.0','mode':'fixture','review_status':'pending','reviewer':None,'reviewed_at':None,
            'ready_selector_sha256':sha((ROOT/cfg['ready_selector']).read_bytes()),'selection_sha256':sha((ROOT/'eval/milestone1/selection.json').read_bytes()),
            'verification_sha256':sha((runs/'verification.json').read_bytes()),'verification_path':str(runs/'verification.json'),
            'candidates':candidates,'additional_evidence':cfg['additional_evidence'],'benign_fixture_proposals_sha256':sha((ROOT/'eval/negatives/milestone1-proposals.json').read_bytes()),
            'acceptance_scope':['Native-to-IR correspondence for the four ready development cases.','Evidence limitations and incomplete/ambiguous table handling.','Six proposed benign/ambiguous fixture labels.'],
            'publication_status':'UNGATED','headline':None}
    packet['content_fingerprint']=fingerprint(packet)
    output.mkdir(parents=True)
    write_new(output/'review.json',packet)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Milestone 1 evidence review</title><style>body{font:16px/1.55 system-ui;max-width:1120px;margin:32px auto;padding:0 24px;color:#18202a}h1,h2{line-height:1.2}h2{border-top:2px solid #dbe2e8;padding-top:24px;margin-top:40px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:16px;font-size:13px}.scroll{overflow:auto}table{border-collapse:collapse;font-size:13px;width:100%}td{border:1px solid #cbd3dc;padding:6px;vertical-align:top}.banner{background:#fff3cd;padding:18px}details{margin:12px 0}</style><h1>Milestone 1: evidence handoff</h1><p class="banner">Pending owner acceptance. Structural validation and replay passed; this packet does not establish detector performance or new PDF fidelity. Headline status remains UNGATED.</p>'''
    html+='<p>Review fingerprint: <code>'+packet['content_fingerprint']+'</code></p><p>Review the literal text, logical cells, source traces and limitations below. Approvals must bind this fingerprint; prior intake approvals do not approve these generated mappings.</p>'
    html+=''.join(sections)+'</html>\n';(output/'index.html').write_text(html)
    return packet

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    result=prepare(a.runs,a.output);print('Review packet pending owner acceptance:',result['content_fingerprint'])
