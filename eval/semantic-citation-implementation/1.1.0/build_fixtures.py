"""Offline authored sources -> validated IR and independently specified ID expectations.

No semantic runtime or candidate responses imported. This is evaluation preparation only.
"""
from pathlib import Path
from copy import deepcopy
import json
from hkex_audit.adapters.mineru import adapt
from hkex_audit.artifacts import read, write_new, encode, sha
from hkex_audit.evidence import node_id, validate_evidence

HERE = Path(__file__).resolve().parent


def build(case):
    blocks = [{'type':'table_body', 'html':case['html']}]
    for tree in case['associated_text_subtrees']:
        blocks.append({'type':'table_caption', 'blocks':[
            {'type':'text','content':n['text']} for n in tree['literal_occurrences']]})
    native = {'_backend':'vlm','_version_name':'3.2.2','pdf_info':[
        {'page_idx':0,'preproc_blocks':[{'type':'table','blocks':blocks}],'discarded_blocks':[]}]}
    document = {'doc_id':'authored-header-'+case['case_id'], 'variant_id':'development',
                'source_document_sha256':None, 'source_provenance':'synthetic'}
    ir = adapt(native, document, sha(encode(native)))
    # ordinal is source-authored identity metadata, NOT recovered reading order. Record the
    # deliberate producer-neutral transformation; only leaf occurrence identities change.
    transformations = []
    for index, tree in enumerate(case['associated_text_subtrees'],1):
        for leaf, occurrence in enumerate(tree['literal_occurrences']):
            ptr = f'/pdf_info/0/preproc_blocks/0/blocks/{index}/blocks/{leaf}'
            node = next(n for n in ir['nodes'] if n['native_pointer']==ptr)
            before = node['id']; node['ordinal'] = occurrence['ordinal']
            node['id'] = node_id(ir['id'],node['kind'],ptr,node['ordinal'])
            transformations.append({'source_id_before':before,'source_id_after':node['id'],
                                    'ordinal':node['ordinal'],'reason':'authored identity/order boundary contrast'})
    validate_evidence(ir, native)
    return native, ir, transformations


def resolve(ir, selector):
    matches = [n['id'] for n in ir['nodes'] if n['kind']=='cell' and
               all(n[k]==v for k,v in selector.items())]
    assert len(matches)==1, selector
    return matches[0]


def main():
    sources=read(HERE/'review/sources.json'); review=read(HERE/'review/independent-review.json')
    assert sha((HERE/'review/sources.json').read_bytes())==review['sources_file_sha256']
    index=[]
    for source, expected in zip(sources['cases'],review['cases'],strict=True):
        assert source['case_id']==expected['case_id'] and source['input_sha256']==expected['input_sha256']
        raw=json.dumps({k:v for k,v in source.items() if k!='input_sha256'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        assert sha(raw)==source['input_sha256']
        native, ir, transformations=build(source)
        dest=HERE/'fixtures'/source['case_id'];dest.mkdir(parents=True,exist_ok=True)
        table=next(n['id'] for n in ir['nodes'] if n['kind']=='table')
        spec={'name':source['case_id'].lower(),'table_id':table,'target_id':resolve(ir,source['target']),
              'transform':'mask_body_amounts_v1'}
        resolved=deepcopy(expected)
        for field in ('independent_contributor_expectation','required_support','optional_support'):
            resolved[field]=None if expected[field] is None else [resolve(ir,s) for s in expected[field]]
        resolved['summary_relationships']=[]
        for relation in expected['summary_relationships']:
            resolved['summary_relationships'].append({'rule_id':relation['rule_id'],
                'group_id':resolve(ir,relation['group']), 'subtotal_id':resolve(ir,relation['subtotal']),
                'component_ids':sorted(resolve(ir,s) for s in relation['components']),
                'support_refs':sorted(resolve(ir,s) for s in relation['support_refs'])})
        for name,value in [('source',native),('evidence',ir),('selection',spec),('expectation',resolved),
                           ('provenance',{'authorship':source['authorship'],'source_case_sha256':source['input_sha256'],
                             'operation_version':'direct-contributor-headers-1.1.0','transformations':transformations,
                             'status':'exposed authored development; no model completion'})]:
            path=dest/(name+'.json')
            if path.exists():
                assert path.read_bytes()==encode(value), 'existing fixture differs'
            else:
                write_new(path,value)
        index.append(source['case_id'])
    files={str(p.relative_to(HERE)):sha(p.read_bytes()) for base in ('review','fixtures')
           for p in sorted((HERE/base).rglob('*')) if p.is_file()}
    write_new(HERE/'fixture-freeze.json',{'version':'citation-development-freeze-1.0.0','cases':index,
        'files':files,'stage':'source-only review and ID resolution before candidate-response tests; no prospective inference',
        'reason_mapping':{'conflicting_discriminator_path':'conflicting_header_context',
                          'unsupported_header_group_or_unresolved_subtotal_scope':['unsupported_header_group','unresolved_subtotal_scope']}})


if __name__=='__main__':
    main()
