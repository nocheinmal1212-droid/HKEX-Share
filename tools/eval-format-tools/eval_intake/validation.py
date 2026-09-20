"""Schema, reference, numeric and readiness checks are distinct from formatting."""
import re
from pathlib import Path
from decimal import localcontext
from jsonschema import Draft202012Validator, FormatChecker
from ruamel.yaml import YAML
from .common import digest, finite, fingerprint, lines, read, require, within
from .numeric import calculate, decimal, parse_token
from .splits import assign, ALGORITHM


def schema(root, name, data):
    spec = read(Path(root)/'schemas'/f'{name}.schema.json')
    Draft202012Validator.check_schema(spec)
    validator = Draft202012Validator(spec, format_checker=FormatChecker())
    finite(data)
    errors = sorted(validator.iter_errors(data), key=lambda e:str(list(e.path)))
    require(not errors, '\n'.join(f'{name} {list(e.path)}: {e.message}' for e in errors))


def authorities(root):
    taxonomy = YAML(typ='safe').load((Path(root)/'spec/taxonomy.yaml').read_text())
    schema(root,'taxonomy',taxonomy)
    # The scoring contract owns scope; no second editable six-category vocabulary.
    scoring = (Path(root)/'eval/SCORING.md').read_text()
    block = scoring.split('Scored codes:\n',1)[1].split('Descoped codes',1)[0]
    scored = set(re.findall(r'^- ([a-z_]+)$',block,re.M))
    require(len(scored)==6 and scored <= {c['code'] for c in taxonomy['categories']}, 'unrecognized scoring contract scope')
    return taxonomy, scored


def check_location(loc, files, root):
    require(loc['source_anchors'], 'location needs source evidence')
    for anchor in loc['source_anchors']:
        require(anchor['artifact_path'] in files and files[anchor['artifact_path']]['sha256']==anchor['sha256'], 'unknown anchor artifact or hash')
        p = within(root, anchor['artifact_path'])
        pointer = anchor['pointer']
        if p.suffix=='.json':
            require(pointer.startswith('/'), 'JSON source requires JSON pointer')
            # Validate actual native pointers, not merely their syntax.
            obj = read(p)
            try:
                for token in pointer[1:].split('/'):
                    key = token.replace('~1','/').replace('~0','~')
                    obj = obj[int(key)] if isinstance(obj,list) else obj[key]
            except (IndexError, KeyError, ValueError, TypeError) as exc:
                raise ValueError(f'unresolved source pointer: {pointer}') from exc
        elif p.suffix=='.pdf':
            require(pointer==f"page:{loc['page_index']}", 'PDF pointer/page mismatch')
        rect = anchor['rectangle']
        if rect:
            require(0 <= rect[0] < rect[2] and 0 <= rect[1] < rect[3], 'invalid rectangle')


def validate_records(root, records, manifest, locations=None, splits=None, review=None,
                     manifest_path=None, locations_path=None, split_path=None):
    taxonomy, scored = authorities(root)
    revisions = {c['code']:c['revision'] for c in taxonomy['categories']}
    require(records, 'no canonical records')
    require(len({r.get('doc_id') for r in records})==1, 'bundle must use one consistent document identity')
    schema(root,'intake_manifest',manifest)
    files = {f['path']:f for f in manifest['files']}
    require(len(files)==len(manifest['files']), 'duplicate manifest path')
    entries = {}
    if locations is not None:
        schema(root,'intake_locations',locations)
        require(locations['bundle_id']==manifest['bundle_id'], 'location bundle mismatch')
        require(manifest_path and locations['manifest_sha256']==digest(manifest_path), 'location manifest hash mismatch')
        entries = {e['error_id']:e for e in locations['entries']}
        require(len(entries)==len(locations['entries']), 'duplicate mapping record')
        require(set(entries)=={r['error_id'] for r in records}, 'mapping inventory differs from records')
        coordinates = {(c['artifact_path'],c['page_index']):c for c in locations['coordinates']}
        require(len(coordinates)==len(locations['coordinates']), 'duplicate page coordinate definition')
        for e in entries.values():
            for loc in [e['location'],*e['secondary_locations']]:
                if loc:
                    check_location(loc,files,root)
                    for a in loc['source_anchors']:
                        if a['rectangle']:
                            c=coordinates.get((a['artifact_path'],loc['page_index']))
                            require(c is not None and a['rectangle'][2]<=c['width'] and a['rectangle'][3]<=c['height'], 'missing coordinate definition or rectangle outside page')
    assignments = {}
    if splits is not None:
        schema(root,'intake_split',splits)
        require(splits['bundle_id']==manifest['bundle_id'], 'split bundle mismatch')
        require(locations_path and splits['locations_sha256']==digest(locations_path), 'split mapping hash mismatch')
        require(manifest_path and splits['manifest_sha256']==digest(manifest_path), 'split source manifest mismatch')
        grouping=splits['grouping']; schema(root,'intake_grouping',grouping)
        from .common import encoded
        import hashlib
        require(splits['grouping_sha256']==hashlib.sha256(encoded(grouping)).hexdigest(), 'embedded grouping hash mismatch')
        require(not grouping['unresolved'], 'frozen grouping has unresolved links')
        require(set(grouping['sites'])=={e['site_id'] for e in entries.values()}, 'split sites differ from mappings')
        require(splits['algorithm']==ALGORITHM and splits['assignments']==assign(grouping['sites'],grouping['edges'],splits['salt']), 'split assignment differs from exact algorithm')
        for k,p in [('scoring','eval/SCORING.md'),('format','eval/eval_format_spec.md'),('taxonomy','spec/taxonomy.yaml')]:
            require(splits['contract_hashes'][k]==digest(Path(root)/p), 'frozen contract differs; preserve historical run and migrate explicitly')
        assignments={a['site_id']:a for a in splits['assignments']}
    decisions={}
    if review is not None:
        schema(root,'intake_review',review)
        require(review['owner']==manifest['owner'], 'review owner differs from appointed manifest owner')
        require(manifest_path and locations_path and split_path,'review needs frozen source, mapping and split paths')
        require(review['manifest_sha256']==digest(manifest_path) and review['locations_sha256']==digest(locations_path) and review['split_sha256']==digest(split_path),'stale review provenance')
        decisions={d['error_id']:d for d in review['decisions']}
        require(len(decisions)==len(review['decisions']), 'duplicate review decision')
        require(set(decisions)<={r['error_id'] for r in records},'review refers to unknown record')
    seen=set(); raw_cache={}
    for r in records:
        schema(root,'error_record',r)
        eid=r['error_id']; require(eid not in seen,f'duplicate record ID: {eid}'); seen.add(eid)
        require(r['bundle_id']==manifest['bundle_id'],'record bundle mismatch')
        require(r['category_code'] in revisions and r['category_revision']==revisions[r['category_code']],'invalid category revision')
        require(r['scoring_status']==('scored' if r['category_code'] in scored else 'descoped'),'invalid scoring scope')
        ref=r['source_ref']; require(ref['path'] in files and files[ref['path']]['role']=='ground_truth' and ref['sha256']==files[ref['path']]['sha256'],'invalid raw source reference')
        if ref['path'] not in raw_cache:
            require(digest(within(root,ref['path']))==ref['sha256'], 'raw file hash differs from source reference')
            raw_cache[ref['path']]=lines(within(root,ref['path']))
        raw=raw_cache[ref['path']]; require(ref['line_number']<=len(raw),'source line out of range'); source=raw[ref['line_number']-1]
        require(eid==ref['original_record_id']==source['error_id'],'source ID mismatch')
        require(r['category_code']==source['category_code'], 'raw category differs; an explicit category migration is required')
        require(ref['original_taxonomy']=={'version':source['taxonomy_version'],'revision':source['taxonomy_revision'],'scope':source['taxonomy_scope']}, 'original taxonomy metadata differs')
        require(r['original_text']==source.get('original_value') and r['injected_text']==source.get('mutated_value'),'source text changed')
        require(any(f['role']=='supplied_pdf' and f['variant_id']==r['variant_id'] and Path(f['path']).name==Path(source['mutated_pdf']).name for f in files.values()),'document variant does not match mutated source')
        notes={n['field'] for n in r['review_notes'] if n['reason'].strip()}
        for field,value in r.items():
            if value is None: require(field in notes,f'{eid}: unexplained null {field}')
        for field in ['detectability_band','injection_stage']:
            if r[field]=='unknown': require(field in notes,f'{eid}: unexplained {field}')
        require('status' in notes,'lifecycle requires an explicit disposition')
        if r['status']=='retired': require('retirement' in notes,'retirement reason required')
        require((r['propagated'] is None)==(r['propagation_sites'] is None),'unknown propagation sites must remain null')
        if r['propagated'] is False: require(r['propagation_sites']==[], 'reviewed no propagation requires empty sites')
        if r['propagated'] is True: require(bool(r['propagation_sites']), 'propagation requires linked sites')
        if r['original_value'] is not None or r['injected_value'] is not None:
            require(all(r[k] is not None for k in ['original_value','injected_value','value_delta']),'partial normalized values')
            for raw_key,value_key in [('original_text','original_value'),('injected_text','injected_value')]:
                require(parse_token(r[raw_key])['value'] is not None and decimal(parse_token(r[raw_key])['value'])==decimal(r[value_key]),'normalization disagrees with raw text')
            with localcontext() as ctx:
                ctx.prec=8000
                require(decimal(r['injected_value'])-decimal(r['original_value'])==decimal(r['value_delta']),'incorrect value delta')
        if r['relation'] is not None:
            computed=calculate(r['relation'])
            for k in ['original_residual','injected_residual','residual_change','tolerance_bound']:
                require(decimal(r['relation'][k])==decimal(computed[k]),f'incorrect {k}')
            require(r['detectability_band']==computed['detectability_band'],'incorrect band')
            for op in r['relation']['operands']:
                check_location(op['location'],files,root)
                for prefix in ['original','injected']:
                    parsed=parse_token(op[prefix+'_text'])['value']
                    require(parsed is not None and decimal(parsed)==decimal(op[prefix+'_value']), 'operand raw/normalized mismatch')
        elif r['detectability_band'] not in {'unknown','not_applicable'}:
            raise ValueError('numeric band requires complete reviewed relation')
        if r['detectability_band']=='not_applicable': require('relation' in notes, 'non-numeric rationale required')
        if r['expected_detectable'] is not None: require('expected_detectable' in notes,'detectability rationale required')
        for loc in [r['location'],*r['secondary_locations'],*(r['propagation_sites'] or [])]:
            if loc: check_location(loc,files,root)
        if r['site_id'] is not None:
            require(eid in entries and entries[eid]['site_id']==r['site_id'],'site not mapped')
            require(r['location']==entries[eid]['location'] and r['secondary_locations']==entries[eid]['secondary_locations'],'record endpoints differ from mapping')
        if r['split'] is not None or r['split_group_id'] is not None:
            a=assignments.get(r['site_id']); require(a and r['split']==a['split'] and r['split_group_id']==a['split_group_id'],'record split mismatch')
        if r['ingestion_status']=='ready':
            require(r['location'] is not None and r['site_id'] and r['split'] and r['split_group_id'],'ready record missing location/split')
            require(entries[eid]['status']=='reviewed','ready mapping not reviewed')
            require(r['expected_detectable'] is not None and r['detectability_band']!='unknown' and r['injection_stage']!='unknown' and r['propagated'] is not None,'ready record has unresolved eligibility/provenance')
            d=decisions.get(eid); require(d and d['decision']=='approve' and d['reviewer']==review['owner'],'ready record lacks owner approval')
            proposal=dict(r,ingestion_status='pending')
            require(d['record_sha256']==fingerprint(proposal),'approval does not bind this record')
    require(sum(len(v) for v in raw_cache.values())==len(records),'raw records omitted or canonical records duplicated')
    from collections import Counter
    return {'structural_validity':'valid','records':len(records),
            'ready':sum(r['ingestion_status']=='ready' for r in records),
            'pending':sum(r['ingestion_status']=='pending' for r in records),
            'category_counts':dict(sorted(Counter(r['category_code'] for r in records).items())),
            'band_counts':dict(sorted(Counter(r['detectability_band'] for r in records).items())),
            'null_or_unknown_field_counts':dict(sorted(Counter(k for r in records for k,v in r.items() if v is None or (k in {'detectability_band','injection_stage'} and v=='unknown')).items())),
            'mapping_counts':dict(sorted(Counter(e['status'] for e in entries.values()).items())),
            'publication_status':'UNGATED','headline':None,
            'limitations':['Intake validation alone does not establish publication gates or source fidelity.']}

