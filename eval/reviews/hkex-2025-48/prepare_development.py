"""Evaluation-only proposed operand selection; never import into runtime.

Run from repository root with pdfplumber 0.11.9 available and tools/eval-format-tools
on PYTHONPATH. Geometry is manually selected review data, not detector logic.
Amounts are read from source characters and parsed by code, never authored here.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy
import json
import pdfplumber
from eval_intake.common import read, lines, digest, write_once, fingerprint
from eval_intake.numeric import calculate, parse_token, decimal, text
from eval_intake.importer import note
from decimal import localcontext

root=Path('.')
manifest=read('eval/manifests/hkex-2025-48.json'); files={f['path']:f for f in manifest['files']}
locations=read('eval/locations/hkex-2025-48.json');records=lines('eval/records/hkex-2025-48/corrupted.jsonl')
byid={r['error_id']:r for r in records}; mapping={e['error_id']:e for e in locations['entries']}
clean='corpus/hksa_2026032600825_kpmg.pdf';corrupt='corpus/hksa_2026032600825_kpmg_error_dataset_48.pdf'
existing_proposals=Path('eval/reviews/hkex-2025-48/development-proposals.jsonl')
now=lines(existing_proposals)[0]['updated_at'] if existing_proposals.exists() else datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
# All chosen y-coordinates come from the reviewed raw site rectangles or the revenue row
# aligned with its note-reference token. The 2025 HKD column is selected from the header.
revenue_box=[315.0,188.5,341.0,197.5]

def loc(page,container,rect,row=None,column=None):
    return dict(page_index=page,table_id=container,section_id=None,row_key=row,column_key=column,source_anchors=[dict(artifact_path=p,sha256=files[p]['sha256'],pointer=f'page:{page}',rectangle=rect) for p in [corrupt,clean]],corrupted_endpoint=None)

def chars(pdf,page,box):
    selected=[c for c in pdf.pages[page].chars if box[0]-.2<=(c['x0']+c['x1'])/2<=box[2]+.2 and box[1]-.2<=(c['top']+c['bottom'])/2<=box[3]+.2]
    return ''.join(c['text'] for c in sorted(selected,key=lambda c:c['x0']))

with pdfplumber.open(clean) as a,pdfplumber.open(corrupt) as b:
    def operand(oid,role,page,container,box,coefficient,row):
        original,injected=chars(a,page,box),chars(b,page,box)
        va,vb=parse_token(original)['value'],parse_token(injected)['value']
        assert va is not None and vb is not None,(oid,original,injected)
        return dict(operand_id=oid,role=role,location=loc(page,container,box,row,'2025-HKD-million'),coefficient=coefficient,scale='1',original_text=original,injected_text=injected,original_value=va,injected_value=vb,rounding_step='1')
    gross=byid['HL-ERR-0025']; gross_box=gross['location']['source_anchors'][0]['rectangle']; cost_box=byid['HL-ERR-0001']['location']['source_anchors'][0]['rectangle']
    gross_ops=[operand('revenue','contributor',158,'statement-income',revenue_box,'1','revenue'),operand('direct-costs','contributor',158,'statement-income',cost_box,'1','direct-costs'),operand('gross-profit','total',158,'statement-income',gross_box,'-1','gross-profit')]
    paired=byid['HL-ERR-0041']; pair_box=paired['location']['source_anchors'][0]['rectangle']
    pair_ops=[operand('statement-revenue','contributor',158,'statement-income',revenue_box,'1','revenue'),operand('segment-revenue-total','total',179,'note-segment-results',pair_box,'-1','revenue-total')]
    for r,ops,concept in [(gross,gross_ops,'gross profit'),(paired,pair_ops,'revenue')]:
        rel=dict(relation_id='review-'+r['error_id'],operation='signed_sum',complete=True,context=dict(concept=concept,entity='consolidated group',period='2025 annual column',unit='HKD million',presentation_basis='reported; comparative and reference RMB columns excluded'),operands=ops,rounding_policy='independent_nearest')
        computed=calculate(rel);rel.update({k:v for k,v in computed.items() if k!='detectability_band'})
        r['relation']=rel;r['detectability_band']=computed['detectability_band'];r['expected_detectable']=True
        for prefix in ['original','injected']:r[prefix+'_value']=parse_token(r[prefix+'_text'])['value']
        with localcontext() as ctx:
            ctx.prec=8000;r['value_delta']=text(decimal(r['injected_value'])-decimal(r['original_value']))
        r['location']=copy.deepcopy(ops[-1]['location']);r['location']['corrupted_endpoint']=True
        if r is paired:r['secondary_locations']=[copy.deepcopy(ops[0]['location'])];r['secondary_locations'][0]['corrupted_endpoint']=False
        r['review_notes']=[n for n in r['review_notes'] if n['field'] not in ['relation','original_value','injected_value','value_delta','detectability_band','expected_detectable','location','secondary_locations']]
        r['review_notes'] += [note('relation','Agent proposal: contributors selected from row roles and 2025 HKD column; coefficients include total. Independent nearest rounding is a conservative displayed-million assumption requiring owner confirmation.'),note('expected_detectable','Agent proposal true: corrupted residual exceeds full rounding bound. Header year is independently corrupted; 2025 column and original report context support the intended relationship. Runtime must resolve that context independently.'),note('location','Proposed logical address and source spans require owner review.')]
        if not r['secondary_locations']:r['review_notes'].append(note('secondary_locations','Single-table additive discrepancy; all operands retained in relation.'))
    for eid in ['HL-ERR-0006','HL-ERR-0017']:
        r=byid[eid];r['detectability_band']='not_applicable';r['expected_detectable']=True
        r['review_notes']=[n for n in r['review_notes'] if n['field'] not in ['relation','detectability_band','expected_detectable']]
        r['review_notes'] += [note('relation','Non-numeric token/reference discrepancy; no financial tolerance applies.'),note('expected_detectable','Agent proposal true: inspect source wording and repeated percent convention.' if eid.endswith('0006') else 'Agent proposal true: revenue reference changed to an unrelated note. Review both note subjects; do not use amount agreement to resolve it.')]
        for n in r['review_notes']:
            if n['field'] in ['original_value','injected_value','value_delta']: n['reason']='Not applicable to this token/reference assessment; literal source text retained.'
    # Reference endpoint: the intended revenue-disaggregation note. Its context heading is
    # separately corrupted, so this endpoint remains proposed, not a ready comparison.
    reference=byid['HL-ERR-0017']
    reference['secondary_locations']=[loc(178,'note-revenue-disaggregation',[77,150,530,350])]
    for path in [clean,corrupt]:
        if not any(c['artifact_path']==path and c['page_index']==178 for c in locations['coordinates']):raise AssertionError('missing page coordinates')
    selected=[byid[e] for e in ['HL-ERR-0006','HL-ERR-0017','HL-ERR-0025','HL-ERR-0041']]
    for r in selected:
        r['injection_stage']='pre_ocr_pdf'
        r['review_notes']=[n for n in r['review_notes'] if n['field'] not in ['injection_stage','updated_at']]
        r['updated_at']=now
        r['review_notes'].append(note('injection_stage','Original/injected characters verified at all 48 PDF rectangles. Native corrupted export is separately inventoried. Exact injector version and seed remain unknown.'))
        r['review_notes'].append(note('ingestion_status','Awaiting owner review of this evidence packet; no approval recorded.'))
        for n in r['review_notes']:
            if n['field'] in ['site_id','split','split_group_id']: n['reason']='Assigned under the frozen conservative single-group development split; no holdout exists.'
        m=mapping[r['error_id']];m['location']=r['location'];m['secondary_locations']=r['secondary_locations']
        m['reason']='Detailed development proposal with logical rows and related endpoints where applicable. User review outstanding.'
        for location in [r['location'],*r['secondary_locations']]:
            for anchor in location['source_anchors']:
                for coord in locations['coordinates']:
                    if coord['artifact_path']==anchor['artifact_path'] and coord['page_index']==location['page_index']:
                        coord['printed_label']=str(location['page_index']-1)
    locations.update(revision=2,predecessor=digest('eval/locations/hkex-2025-48.json'),revision_reason='Refine selected development endpoints and record printed labels; all mappings remain proposed.')
    write_once('eval/locations/hkex-2025-48.r2.json',locations)
    write_once('eval/reviews/hkex-2025-48/development-proposals.jsonl',b''.join(json.dumps(r,ensure_ascii=False,separators=(',',':')).encode()+b'\n' for r in selected))
    grouping=read('eval/reviews/hkex-2025-48/grouping.json');grouping.update(revision=2,predecessor=digest('eval/reviews/hkex-2025-48/grouping.json'),revision_reason='Mapping-only refinement; same grouping and site identities.',locations_sha256=digest('eval/locations/hkex-2025-48.r2.json'))
    write_once('eval/reviews/hkex-2025-48/grouping.r2.json',grouping)
    print('Prepared four pending development proposals; source-derived numeric relationships:',sum(r['relation'] is not None for r in selected))
