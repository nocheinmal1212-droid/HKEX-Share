"""Frozen evaluation-only connected-component assignment."""
import hashlib
from .common import digest, fingerprint, require
from .inventory import header

ALGORITHM = 'sha256(utf8(salt + ":" + split_group_id)) as integer mod 3; 0=test, otherwise dev'


def assign(sites, edges, salt):
    require(len(sites)==len(set(sites)) and sites and salt, 'sites and salt must be nonempty and unique')
    parent = {s:s for s in sites}
    def find(s):
        while parent[s] != s:
            parent[s] = parent[parent[s]]
            s = parent[s]
        return s
    for edge in edges:
        a,b = edge['sites']
        require(a in parent and b in parent and a != b and edge['reason'].strip(), 'invalid grouping edge')
        a,b = find(a),find(b)
        parent[max(a,b)] = min(a,b)
    components = {}
    for s in sorted(sites):
        components.setdefault(find(s),[]).append(s)
    out = []
    for members in components.values():
        gid = 'group-' + fingerprint(members)[:24]
        split = 'test' if int(hashlib.sha256((salt+':'+gid).encode('utf-8')).hexdigest(),16)%3 == 0 else 'dev'
        out.extend(dict(site_id=s,split_group_id=gid,split=split) for s in members)
    return sorted(out,key=lambda a:a['site_id'])


def freeze(root, grouping, grouping_path, manifest_path, locations_path, locations, salt='hkex-intake-v2-001', seed=0):
    require(not grouping['unresolved'], 'cannot freeze unresolved grouping')
    require(grouping['manifest_sha256']==digest(manifest_path) and grouping['locations_sha256']==digest(locations_path), 'grouping provenance mismatch')
    require(set(grouping['sites'])=={e['site_id'] for e in locations['entries']}, 'grouping must account for every mapped/intake site')
    assignments = assign(grouping['sites'],grouping['edges'],salt)
    if grouping['strategy']=='conservative_bundle':
        require(len({a['split_group_id'] for a in assignments})==1, 'conservative bundle must be one connected group')
    return {**header(grouping['bundle_id'],'First frozen assignment; never reroll.'),'manifest_sha256':digest(manifest_path),'locations_sha256':digest(locations_path),'grouping_sha256':digest(grouping_path),'contract_hashes':{k:digest(root/p) for k,p in [('scoring','eval/SCORING.md'),('format','eval/eval_format_spec.md'),('taxonomy','spec/taxonomy.yaml')]},'algorithm':ALGORITHM,'salt':salt,'bootstrap_seed':seed,'assignments':assignments,'grouping':grouping,'frozen':True}
