"""Evaluation-owned forbidden-population probes; runtime never reads this inventory."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from audit_inputs import selected_files, descriptors
from .common import read, require, within


def check(root, selection_path, manifest):
    root=Path(root).resolve()
    selection=read(selection_path)
    allowed=selected_files(selection, Path(selection_path).resolve().parent)
    files={str(within(root,f['path'])):f for f in manifest['files']}
    variant=selection['document']['variant_id']
    if selection['mode']=='native':
        for path, desc in zip(allowed, descriptors(selection)):
            f=files.get(str(path))
            require(f and f['role']=='native_export' and f['variant_id']==variant and f['sha256']==desc['sha256'], 'unselected counterpart/unknown native artifact')
    else:
        from hkex_audit.artifacts import read as read_runtime, sha
        selected_manifest=read_runtime(allowed[1])
        require(selected_manifest['document']==selection['document'],'IR selection identity mismatch')
        require(sha(allowed[0].read_bytes())==selected_manifest['evidence_sha256'],'IR manifest hash mismatch')
    forbidden=[str(within(root,f['path'])) for f in manifest['files'] if str(within(root,f['path'])) not in {str(p) for p in allowed}]
    forbidden += [str(p.resolve()) for p in (root/'eval').rglob('*') if p.is_file()]
    require(forbidden,'nonempty forbidden population required')
    with tempfile.TemporaryDirectory() as temp:
        link=Path(temp).resolve()/'innocent.json';link.symlink_to(forbidden[0])
        probes=[str(p) for p in allowed]+forbidden+[str(link)]
        package_root=Path(__file__).resolve().parents[3]/'src'
        bootstrap='import sys;sys.path.insert(0,sys.argv[1]);from audit_inputs.probe import main;main()'
        run=subprocess.run([sys.executable,'-I','-B','-c',bootstrap,str(package_root)],input=json.dumps({'allowed':[str(p) for p in allowed],'probes':probes}),text=True,capture_output=True,timeout=60,check=True)
        for result in json.loads(run.stdout):
            expected='allowed' if result['path'] in {str(p) for p in allowed} else 'denied'
            require(all(v==expected for v in result['methods'].values()),'isolation probe failed')
    return {'status':'passed','scope':'runtime_guard_read_methods','allowed_files':len(allowed),'forbidden_files_and_symlink':len(forbidden)+1,
            'methods':['open','pathlib','io.open','os.open'],'limitations':['Actual adapter/consumer access traces are checked by evidence-local-check.','Not hostile-code or preloaded native-library containment.']}
