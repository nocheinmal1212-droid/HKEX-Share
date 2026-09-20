"""Bounded source interpretation; context containment is NOT subtotal contribution.

No amounts, evaluator imports, extractor-specific fields, or transport. Unknown scopes block.
The policy resource is preloaded before worker guards and bound into each query.
"""
from copy import deepcopy
from pathlib import Path
import re
from .artifacts import loads, sha, require

VERSION = 'header-source-analysis-1.0.1'
_POLICY = None
_HASH = None


def load_policy():
    global _POLICY, _HASH
    if _POLICY is None:
        raw = Path(__file__).with_name('header_support_policy.json').read_bytes()
        _POLICY, _HASH = loads(raw), sha(raw)
    return deepcopy(_POLICY), _HASH


def policy_identity():
    policy, checksum = load_policy()
    return {'version': policy['version'], 'sha256': checksum, 'analysis_version': VERSION}


def normalize(text):
    return ' '.join(text.strip().translate(str.maketrans({'（':'(', '）':')'})).split())


def classify_label(text, policy):
    text = normalize(text or '')
    if text in policy['total_markers']:
        return ('total', text)
    if re.fullmatch(policy['period_pattern'], text):
        return ('period', text.removesuffix('年'))
    if text in policy['groups']:
        return tuple(policy['groups'][text])
    if text in policy['continuation_markers']:
        return ('presentation', 'continuation')
    if text in policy['common_display_labels']:
        return ('presentation', 'common_display')
    return ('unknown', text)


def interval(node):
    return node['column'], node['column'] + node['column_span']


def contains(group, node):
    a, b = interval(group); c, d = interval(node)
    return a <= c and d <= b


def above(group, node):
    return group['row'] + group['row_span'] <= node['row'] and contains(group, node)


def _reason(reasons, code, refs):
    value = {'code':code, 'source_refs':sorted(set(refs))}
    if value not in reasons:
        reasons.append(value)


def analyze_prose(nodes, table_id, policy):
    """Validated-IR text occurrences only. ordinal is not a reading-order capability."""
    by_id = {n['id']:n for n in nodes}
    reasons, subtrees = [], {}
    for node in nodes:
        if node['kind'] in ('table', 'cell'):
            continue
        if node['kind'] in ('description','formula','figure') or node['content_state'] == 'unsupported':
            _reason(reasons, 'nonliteral_associated_context', [node['id']])
            continue
        if not node['text'] or not node['text'].strip():
            continue
        top = node
        while top['parent_id'] != table_id:
            require(top['parent_id'] in by_id, 'broken selected prose ancestry')
            top = by_id[top['parent_id']]
        subtrees.setdefault(top['id'], []).append(node)
    for members in subtrees.values():
        if len(members) != 1:
            _reason(reasons, 'unestablished_text_order', [n['id'] for n in members])
            continue
        node = members[0]; text = node['text'].strip()
        if not (re.fullmatch(policy['caption_pattern'], text) or
                normalize(text) in policy['continuation_markers']):
            _reason(reasons, 'associated_prose_uninterpreted', [node['id']])
    return reasons


def analyze_headers(nodes, target_id, policy):
    by_id = {n['id']:n for n in nodes}; target = by_id[target_id]
    cells = sorted((n for n in nodes if n['kind']=='cell' and n['row'] < target['row']+target['row_span']),
                   key=lambda n:(n['row'],n['column'],n['id']))
    reasons = []
    labels = {n['id']:classify_label(n['text'] if n['content_state']=='text' else None,policy) for n in cells}
    bounds = (min(n['column'] for n in cells), max(interval(n)[1] for n in cells))
    potential, presentation = {}, []
    for n in cells:
        if n['content_state']=='unsupported':
            _reason(reasons, 'unsupported_header_content', [n['id']])
        if n['content_state']!='text' or not n['text'] or n['column_span'] <= 1 or not any(above(n,c) for c in cells):
            continue
        role, value = labels[n['id']]
        if role=='presentation' and (value=='continuation' or interval(n)==bounds):
            presentation.append(n['id'])
        else:
            potential[n['id']] = n
    groups = list(potential.values())
    for i,g in enumerate(groups):
        for h in groups[i+1:]:
            a,b=interval(g); c,d=interval(h)
            if max(a,c)<min(b,d) and not (above(g,h) or above(h,g)):
                _reason(reasons, 'non_laminar_or_incomplete_hierarchy', [g['id'],h['id']])
    ancestors = {n['id']:[g['id'] for g in groups if above(g,n)] for n in cells}
    # A literal discriminator can expose a conflict/missing target context even when an
    # intermediate partition cannot qualify as a contributor group. Keep that diagnostic
    # distinct; it does not turn the unqualified wrapper into a citation certificate.
    for ref, chain in ancestors.items():
        for dimension in ('period', 'dimension'):
            matching = [g for g in chain if labels[g][0] == dimension]
            if len({labels[g][1] for g in matching}) > 1:
                _reason(reasons, 'conflicting_header_context', [ref, *matching])
    children = {g['id']:[] for g in groups}
    for n in cells:
        # A presentation wrapper stays in the source trace, but its wrapped headers
        # already occupy this membership partition. Do not count both layers.
        if n['id'] in presentation:
            continue
        chain = ancestors[n['id']]
        if chain:
            # Non-laminar alternatives already block; do not certify an arbitrary tie.
            parent = max(chain,key=lambda i:(potential[i]['row'], -potential[i]['column_span']))
            children[parent].append(n['id'])
    qualified = {}
    for g in reversed(groups):
        refs=children[g['id']]; members=[by_id[i] for i in refs]
        role,value=labels[g['id']]
        occupied=[]
        for n in members:
            occupied.extend(range(*interval(n)))
        complete = sorted(occupied)==list(range(*interval(g)))
        if not complete:
            _reason(reasons,'non_laminar_or_incomplete_hierarchy',[g['id'],*refs])
        lower=[n for n in cells if above(g,n)]
        total_present=any(labels[n['id']][0]=='total' for n in lower)
        branches=[n for n in members if labels[n['id']][0]!='total' and n['text'] and n['content_state']=='text']
        nested_valid=all(i not in potential or i in qualified for i in refs)
        if (role in ('category','dimension','period') and complete and total_present and len(branches)>=2
                and nested_valid and all(n['text'] and n['content_state']=='text' for n in members)):
            qualified[g['id']]={'kind':role,'value':value,'members':refs}
        else:
            _reason(reasons,'unsupported_header_group',[g['id']])
    paths={n['id']:[g for g in ancestors[n['id']] if g in qualified] for n in cells}
    for ref,chain in paths.items():
        for dimension in ('period','dimension','category'):
            matching=[g for g in chain if qualified[g]['kind']==dimension]
            if len({qualified[g]['value'] for g in matching})>1:
                _reason(reasons, 'unsupported_category_nesting' if dimension=='category' else 'conflicting_header_context', [ref,*matching])
    analysis={'groups':qualified,'paths':paths,'presentation_refs':presentation,'summary_scopes':{},'reasons':reasons}
    analysis['summary_scopes']=derive_summary_scopes(by_id,labels,qualified,policy)
    for subtotal in list(analysis['summary_scopes']):
        chain=ancestors[subtotal]
        if any(len({labels[g][1] for g in chain if labels[g][0]==kind})>1
               for kind in ('period','dimension','category')):
            del analysis['summary_scopes'][subtotal]
    for n in cells:
        if not candidate_in_branch(n,target,analysis):
            continue
        for g in ancestors[n['id']]:
            kind,_=labels[g]
            if kind in ('period','dimension') and not any(labels[t][0]==kind for t in ancestors[target_id]):
                _reason(reasons,'missing_target_discriminator',[target_id,n['id'],g])
        if labels[n['id']][0]=='total' and n['id'] not in analysis['summary_scopes']:
            _reason(reasons,'unresolved_subtotal_scope',[n['id'],*paths[n['id']]])
    return analysis


def candidate_in_branch(node, target, analysis):
    if (node['id']==target['id'] or node['kind']!='cell' or node['parent_id']!=target['parent_id']
            or not node['text'] or node['content_state']!='text' or node['column']==target['column']
            or node['row']>=target['row']+target['row_span'] or node['id'] in analysis['groups']
            or node['id'] in analysis['presentation_refs']):
        return False
    # Ancestor groups bind every selected header's full interval, not its anchor alone.
    for group in analysis['paths'][target['id']]:
        if group not in analysis['paths'].get(node['id'],[]):
            return False
    return True


def derive_summary_scopes(nodes, labels, groups, policy):
    scopes={}
    for group, item in groups.items():
        members=item['members']
        for rule in policy['summary_rules']:
            if [item['kind'],item['value']] != rule['group']:
                continue
            totals=[i for i in members if labels[i][0]=='total']
            matches={role:[i for i in members if normalize(nodes[i]['text'] or '') in names]
                     for role,names in rule['component_roles'].items()}
            if (len(totals)==1 and all(len(ids)==1 for ids in matches.values())
                    and len(members)==len(matches)+1 and not any(i in groups for i in members)):
                components=sorted(ids[0] for ids in matches.values())
                scopes[totals[0]]={'rule_id':rule['id'],'group_id':group,'component_ids':components,
                                  'support_refs':sorted([group,totals[0],*components])}
    return scopes


def analyze_source(nodes, table_id, target_id):
    policy, _ = load_policy()
    header=analyze_headers(nodes,target_id,policy)
    header['reasons']+=analyze_prose(nodes,table_id,policy)
    header['reasons']=sorted(header['reasons'],key=lambda r:(r['code'],r['source_refs']))
    if header['reasons']:
        # No certified summary witness survives a blocked source profile.
        header['summary_scopes']={}
    return {'policy':policy_identity(),**header}


def required_support(analysis, target, contributors):
    required={target,*contributors}
    for ref in (target,*contributors):
        required.update(analysis['paths'].get(ref,[]))
    return required


def validate_summary_selection(analysis, contributors):
    scopes=analysis['summary_scopes']
    def covered(ref, visiting):
        require(ref not in visiting,'cyclic summary scope')
        result=set()
        for member in scopes.get(ref,{}).get('component_ids',[]):
            result.add(member);result.update(covered(member, visiting|{ref}))
        return result
    for ref in contributors:
        require(not (covered(ref,set()) & set(contributors)), 'overlapping_summary_selection')


def validate_paths(query, answer):
    analysis=query['host_analysis']; target=answer['target_id']; chosen=answer['contributor_ids']
    missing=required_support(analysis,target,chosen)-set(answer['support_refs'])
    require(not missing, 'required header context support absent: '+','.join(sorted(missing)))
    nodes={n['id']:n for n in query['context']['items']}
    for ref in chosen:
        require(candidate_in_branch(nodes[ref],nodes[target],analysis), 'incompatible header context')
    validate_summary_selection(analysis,chosen)
