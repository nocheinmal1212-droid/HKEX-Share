"""Lossless raw-to-canonical interpretation; no automatic approval."""
from .common import VERSION, digest, lines, require, within


def note(field, reason, reviewer='Codex intake', evidence_refs=None):
    return dict(field=field, reason=reason, reviewer=reviewer, reviewed_at=None, evidence_refs=evidence_refs or [])


def import_records(root, config, manifest, taxonomy, scored):
    raw_path = within(root, config['raw_records'])
    raw_hash = digest(raw_path)
    require(any(f['path']==config['raw_records'] and f['sha256']==raw_hash and f['role']=='ground_truth' for f in manifest['files']), 'raw source differs from inventory')
    revisions = {c['code']:c['revision'] for c in taxonomy['categories']}
    variants = {d['path'].split('/')[-1]:d['variant_id'] for d in config['documents']}
    require(len(variants)==len(config['documents']), 'ambiguous source PDF basename')
    records = []
    seen = set()
    for line, raw in enumerate(lines(raw_path), 1):
        eid = raw['error_id']
        require(eid not in seen, f'duplicate raw ID: {eid}')
        seen.add(eid)
        code = raw['category_code']
        require(code in revisions, f'unknown category: {code}')
        variant = variants.get(raw['mutated_pdf'].split('/')[-1])
        require(variant is not None, f'unmapped injected PDF: {eid}')
        r = dict(schema_version=VERSION,error_id=eid,bundle_id=config['bundle_id'],variant_id=variant,doc_id=config['doc_id'],source_ref={'path':config['raw_records'],'sha256':raw_hash,'original_record_id':eid,'line_number':line,'original_taxonomy':{'version':raw['taxonomy_version'],'revision':raw['taxonomy_revision'],'scope':raw['taxonomy_scope']}},status=config['lifecycle'],ingestion_status='pending',category_code=code,category_revision=revisions[code],scoring_status='scored' if code in scored else 'descoped',site_id=None,split_group_id=None,split=None,location=None,secondary_locations=[],original_text=raw.get('original_value'),injected_text=raw.get('mutated_value'),original_value=None,injected_value=None,value_delta=None,relation=None,detectability_band='unknown',expected_detectable=None,injection_stage='unknown',injector_version=None,seed=None,propagated=None,propagation_sites=None,description=raw.get('message',''),review_notes=[],created_at=None,updated_at=None)
        reasons = {
            'site_id':'Site identity requires source mapping.', 'split_group_id':'Grouping not attached to this intake revision.', 'split':'Frozen assignment not attached to this intake revision.',
            'location':'Page indexing, container and coordinates require source review.',
            'original_value':'Raw text retained; financial normalization not yet reviewed.', 'injected_value':'Raw text retained; financial normalization not yet reviewed.', 'value_delta':'Financial normalization not yet reviewed.',
            'relation':'Arithmetic applicability, complete operands, context and rounding require review.', 'expected_detectable':'Raw expected/actual prose and confidence are not eligibility decisions.',
            'injection_stage':'Raw redaction method is evidence to investigate, not a source attestation.',
            'injector_version':'Not supplied.', 'seed':'Not supplied; exact regeneration unavailable.', 'propagated':'Linked changes require review.', 'propagation_sites':'Unknown, not reviewed none.',
            'created_at':'Source timestamp lacks a timezone; cannot assert UTC.', 'updated_at':'No canonical human review has occurred.', 'detectability_band':'Numeric/non-numeric applicability and tolerance require review.'}
        r['review_notes']=[note(k,v) for k,v in reasons.items()]
        r['review_notes'].append(note('status',config['lifecycle_reason'],config['owner']))
        r['review_notes'].append(note('secondary_locations','Other endpoints have not yet been reviewed.'))
        if config['lifecycle']=='retired':
            r['review_notes'].append(note('retirement',config['lifecycle_reason'],config['owner']))
        records.append(r)
    require(records, 'no raw records')
    return sorted(records,key=lambda r:r['error_id'])
