"""Evaluation-owned projection. Only safe document provenance reaches runtime."""
from pathlib import Path
from hkex_audit.artifacts import require


def project(root, manifest, doc_id, variant_id, native_path):
    root = Path(root).resolve()
    files = {f['path']: f for f in manifest['files']}
    selected = files.get(native_path)
    require(selected is not None and selected['role'] == 'native_export' and selected['variant_id'] == variant_id,
            'unselected counterpart or unknown native artifact')
    require(native_path.endswith('_middle.json') or Path(native_path).name == 'native.json', 'select the middle-JSON artifact explicitly')
    pdfs = [f for f in manifest['files'] if f['role'] == 'supplied_pdf' and f['variant_id'] == variant_id]
    require(len(pdfs) == 1, 'source document provenance missing or ambiguous')
    return {'schema_version': '1.0.0', 'mode': 'native',
            'document': {'doc_id': doc_id, 'variant_id': variant_id, 'source_document_sha256': pdfs[0]['sha256'],
                         'source_provenance': 'supplied_unverified'},
            'artifacts': [{'role': 'middle_json', 'path': str((root / native_path).absolute()), 'sha256': selected['sha256']}]}
