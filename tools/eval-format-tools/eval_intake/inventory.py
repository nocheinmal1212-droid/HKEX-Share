"""Evaluation-only explicit source inventory."""
from pathlib import Path
from .common import VERSION, digest, fingerprint, read, relative, require, within


def header(bundle_id, reason, revision=1, predecessor=None):
    return dict(schema_version=VERSION, bundle_id=bundle_id, revision=revision,
                predecessor=predecessor, revision_reason=reason)


def inventory(root, config_path):
    root = Path(root).resolve()
    config = read(config_path)
    require(set(config) == {'bundle_id', 'doc_id', 'owner', 'raw_records', 'documents', 'exports', 'lifecycle', 'lifecycle_reason'}, 'invalid source configuration keys')
    require(config['lifecycle'] in {'active', 'retired'} and config['lifecycle_reason'], 'explicit lifecycle decision required')
    require(len({d['variant_id'] for d in config['documents']}) == len(config['documents']), 'duplicate document variant')
    files = {}
    def add(path, role, variant):
        p = within(root, path)
        require(p.is_file() and not p.is_symlink(), f'missing source: {path}')
        name = relative(root, p)
        require(name not in files, f'duplicate source registration: {name}')
        files[name] = dict(path=name, sha256=digest(p), size_bytes=p.stat().st_size, role=role, variant_id=variant)
    add(config['raw_records'], 'ground_truth', None)
    docs = {d['variant_id']:d['path'] for d in config['documents']}
    for variant, path in docs.items():
        add(path, 'supplied_pdf', variant)
    exports = []
    for e in config['exports']:
        directory = within(root, e['root'])
        require(directory.is_dir(), f'missing export: {directory}')
        tree = []
        for p in sorted(directory.rglob('*')):
            require(not p.is_symlink(), f'export symlink unsupported: {p}')
            if p.is_file() and p.name not in {'.DS_Store', '.gitkeep'}:
                path = relative(root, p)
                add(path, 'native_export', e['variant_id'])
                tree.append({'path':p.relative_to(directory).as_posix(), 'sha256':files[path]['sha256'], 'size_bytes':files[path]['size_bytes']})
        require(tree, 'empty native export')
        middle = read(within(root, e['middle_json']))
        require(e['origin_pdf'] in files and e['middle_json'] in files, 'export anchor not inventoried')
        exports.append(dict(variant_id=e['variant_id'],root=e['root'],tree_sha256=fingerprint(tree),engine='MinerU',backend=middle.get('_backend'),version=middle.get('_version_name'),checkpoint=None,settings=None,page_count=len(middle['pdf_info']),supplied_pdf=docs[e['variant_id']],origin_pdf=e['origin_pdf'],correspondence={'status':'pending','reason':'Page/content/render correspondence review recorded separately; byte hashes alone are insufficient.'}))
    return {**header(config['bundle_id'],'Initial immutable source inventory.'), 'source_config_sha256':digest(config_path),'files':sorted(files.values(),key=lambda f:f['path']),'exports':exports,'owner':config['owner'],'limitations':['Checkpoint, extraction settings and their equivalence are unavailable in supplied metadata.','Hash inventory is not a PDF correspondence attestation.']}


def verify_sources(root, manifest):
    hashes = {}
    for f in manifest['files']:
        p = within(root, f['path'])
        require(p.is_file() and p.stat().st_size == f['size_bytes'] and digest(p) == f['sha256'], f"source changed: {f['path']}")

        hashes[f['path']] = f['sha256']
    for export in manifest['exports']:
        directory = within(root, export['root'])
        tree = []
        for p in sorted(directory.rglob('*')):
            require(not p.is_symlink(), f'unexpected export symlink: {p}')
            if p.is_file() and p.name not in {'.DS_Store', '.gitkeep'}:
                name = relative(root, p)
                require(name in hashes, f'uninventoried export file: {name}')
                tree.append({'path':p.relative_to(directory).as_posix(), 'sha256':hashes[name], 'size_bytes':p.stat().st_size})
        require(fingerprint(tree)==export['tree_sha256'], 'native export tree differs from inventory')
