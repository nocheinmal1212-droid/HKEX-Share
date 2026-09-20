"""Development-only HTML review packet with immutable source-page images."""
import html
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from .common import digest, require, write_once, within, fingerprint


def packet(root, records, manifest, locations, splits, selection, output):
    output=Path(output); selected=set(selection['error_ids'])
    require(selected and len(selected)==len(selection['error_ids']), 'packet needs unique, nonempty development selection')
    chosen=[r for r in records if r['error_id'] in selected]
    require(len(chosen)==len(selected) and all(r['split']=='dev' for r in chosen),'development packet cannot expose test or unassigned sites')
    require(selection['split_sha256']==fingerprint(splits),'selection binds a different split')
    renderer=shutil.which('pdftoppm'); require(renderer, 'pdftoppm required for visual review packet')
    pdfs={f['variant_id']:within(root,f['path']) for f in manifest['files'] if f['role']=='supplied_pdf'}
    require(len(pdfs)==2,'review requires paired supplied PDFs')
    output.mkdir(parents=True,exist_ok=True)
    cards=[]; image_inventory=[]
    esc=html.escape
    with tempfile.TemporaryDirectory() as temp:
        rendered={}
        def render(variant,page,rectangle=None):
            key=(variant,page,tuple(rectangle) if rectangle else None)
            if key in rendered:return rendered[key]
            name=f'{variant}-p{page+1}-'+fingerprint(key)[:10]+'.png'
            prefix=Path(temp)/name[:-4]
            command=[renderer,'-f',str(page+1),'-l',str(page+1),'-singlefile','-r','120','-png']
            if rectangle:
                factor=120/72
                x0,y0,x1,y1=rectangle
                x=max(0,int((x0-45)*factor)); y=max(0,int((y0-30)*factor))
                command += ['-x',str(x),'-y',str(y),'-W',str(int((x1+70)*factor)-x),'-H',str(int((y1+30)*factor)-y)]
            command += [str(pdfs[variant]),str(prefix)]
            subprocess.run(command,check=True,capture_output=True,timeout=60)
            p=prefix.with_suffix('.png');write_once(output/name,p.read_bytes())
            image_inventory.append({'path':name,'sha256':digest(p),'pdf_sha256':digest(pdfs[variant]),'page_index':page,'source_rectangle_pt':rectangle,'renderer':'pdftoppm','dpi':120})
            rendered[key]=name;return name
        for r in chosen:
            require(r['location'] is not None,'selection requires proposed source location')
            loc=r['location']; rect=loc['source_anchors'][0]['rectangle']; page=loc['page_index']
            images=[]
            for variant in sorted(pdfs):
                crop=render(variant,page,rect);full=render(variant,page)
                images.append(f'<figure><figcaption>{esc(variant)} — physical page {page+1}</figcaption><a href="{full}"><img src="{crop}" alt="Source crop"></a><p><a href="{full}">Full page and context</a></p></figure>')
            related_pages={l['page_index'] for l in r['secondary_locations']}
            if r['relation']:
                related_pages.update(op['location']['page_index'] for op in r['relation']['operands'])
            related_pages.update(selection.get('supporting_page_indices', []))
            links=[]
            for related in sorted(related_pages-{page}):
                for variant in sorted(pdfs):
                    full=render(variant,related)
                    links.append(f'<a href="{full}">{esc(variant)} physical page {related+1}</a>')
            calculations=''
            if r['relation']:
                rel=r['relation']
                rows=''.join('<tr>'+''.join(f'<td>{esc(op[k])}</td>' for k in ['operand_id','coefficient','original_text','injected_text','rounding_step'])+'</tr>' for op in rel['operands'])
                calculations=f'<h3>Proposed calculation</h3><table><tr><th>Operand</th><th>Sign</th><th>Original</th><th>Injected</th><th>Rounding step</th></tr>{rows}</table><p>Original residual: {esc(rel["original_residual"])}; injected residual: {esc(rel["injected_residual"])}; change: {esc(rel["residual_change"])}; conservative bound: {esc(rel["tolerance_bound"])}. Proposed band: {esc(r["detectability_band"])}.</p>'
            source=esc(r['original_text'] or '')+' → '+esc(r['injected_text'] or '')
            details=esc(json.dumps(r,ensure_ascii=False,indent=2))
            cards.append(f'<article><h2>{esc(r["error_id"])} — {esc(r["category_code"])}</h2><p>{esc(r["description"])}</p><p class="token">{source}</p><div class="pair">'+''.join(images)+f'</div><p>Related source pages: {" · ".join(links) or "same page"}</p>{calculations}<details><summary>Proposed record, evidence pointers and calculations</summary><pre>{details}</pre></details><p>Review: container and endpoints; visual replacement artifacts; complete contributors/context; rounding; detectability; propagation. No approval has been recorded.</p></article>')
    intro=esc(selection['rationale'])
    observations=esc(selection.get('observations', 'No visual-review observations supplied.'))
    body='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Development intake review</title><style>body{font:16px system-ui;max-width:1180px;margin:36px auto;padding:0 24px;color:#182632;background:#f4f6f7}article{padding:24px;background:white;margin:24px 0;border:1px solid #ccd5da;border-radius:8px}h1{font-size:32px}h2{font-size:20px}.pair{display:flex;gap:16px;flex-wrap:wrap}figure{margin:8px 0;flex:1;min-width:320px}img{max-width:100%;border:1px solid #bbb}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}.token{font-family:monospace}a{color:#075c92}table{border-collapse:collapse}td,th{border:1px solid #ccd5da;padding:8px;text-align:left}</style><h1>Development intake review</h1><p><strong>Pending your review · No scored results · UNGATED</strong></p>'''
    body+=f'<p>{intro}</p><p><strong>Observed source artifacts:</strong> {observations}</p><p>Source images are evidence; proposed mappings and numeric assessments are not approved. Click a crop for the full source page. All record details shown here belong to development sites.</p>'+''.join(cards)+'</html>'
    write_once(output/'index.html',body.encode())
    write_once(output/'images.json',image_inventory)
