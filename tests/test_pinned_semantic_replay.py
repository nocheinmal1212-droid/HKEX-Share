"""Offline historical replay; no current operation is used to consume v1."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from helpers import ROOT
from hkex_audit.artifacts import read

BASE=ROOT/'runs/paired-semantic-integration-2026-09-18'
COMMIT='e8000e2c001983f1f65fac75de97945c628a2287'


class PinnedReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (BASE/'live-v1/batch.json').exists():
            raise unittest.SkipTest('retained local Task B artifacts unavailable; historical replay unverified')
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name).resolve();cls.pin=cls.root/'pin';cls.pin.mkdir()
        archive=subprocess.run(['git','archive',COMMIT,'src','schemas','pyproject.toml'],cwd=ROOT,capture_output=True,check=True)
        subprocess.run(['tar','-x','-C',str(cls.pin)],input=archive.stdout,check=True)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def prepare(self,root):
        batch=root/'batch';batch.mkdir()
        shutil.copy2(BASE/'live-v1/batch.json',batch/'batch.json')
        shutil.copytree(BASE/'live-v1/primary',batch/'primary')
        manifests=root/'manifests';manifests.mkdir()
        for name in ('shared','primary'):
            shutil.copy2(ROOT/'tools/replay-semantic-v1'/(name+'.json'),manifests/(name+'.json'))
        return batch,manifests

    def replay(self,batch,manifests,out,command='replay',selection=None,pin=None):
        return subprocess.run([sys.executable,'-B',str(ROOT/'tools/replay_semantic_v1.py'),command,
            '--pin',str(pin or self.pin),'--batch',str(batch),'--manifests',str(manifests),
            '--selection',str(selection or BASE/'selection.json'),'--output',str(out)],
            capture_output=True,text=True,timeout=180)

    def test_primary_ignores_deleted_and_corrupted_research_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();batch,manifests=self.prepare(root)
            for state in ('missing','corrupted'):
                if state=='corrupted':
                    shutil.copytree(BASE/'live-v1/research',batch/'research')
                    for path in (batch/'research').rglob('*.json'):path.write_text('{broken')
                    (manifests/'research.json').write_text('{broken')
                out=root/state;result=self.replay(batch,manifests,out)
                self.assertEqual(result.returncode,0,result.stderr)
                verification=read(out/'pinned-verification.json')
                self.assertTrue(verification['primary_byte_identity_verified'])
                self.assertFalse(any('/research/' in p for p in verification['launcher_batch_reads']))
                self.assertFalse(verification['unselected_role_verified'])
            # The same corrupted research input fails its separate verification.
            self.assertNotEqual(self.replay(batch,manifests,root/'research-fail','research-replay').returncode,0)

    def test_primary_shared_pin_and_role_bindings_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();batch,manifests=self.prepare(root)
            files=list((batch/'primary/total').glob('*.json'))+[batch/'batch.json']
            for file in files:
                original=file.read_bytes()
                for action in ('missing','corrupt'):
                    with self.subTest(file=file.name,action=action):
                        if action=='missing':file.unlink()
                        else:file.write_bytes(b'{broken')
                        out=root/'failed-output';result=self.replay(batch,manifests,out)
                        self.assertNotEqual(result.returncode,0,result.stdout)
                        self.assertFalse(out.exists())
                        file.write_bytes(original)
            selection=read(BASE/'selection.json');selection['evidence']['sha256']='0'*64
            changed=root/'selection.json';changed.write_text(json.dumps(selection))
            self.assertNotEqual(self.replay(batch,manifests,root/'bad-selection',selection=changed).returncode,0)
            (self.pin/'injected.pyc').write_bytes(b'not permitted')
            try:self.assertNotEqual(self.replay(batch,manifests,root/'bad-pin').returncode,0)
            finally:(self.pin/'injected.pyc').unlink()

    def test_new_runtime_rejects_old_batch_without_output(self):
        from argparse import Namespace
        from hkex_audit.semantic_cli import replay_batch
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'unsupported batch version'):
                replay_batch(Namespace(batch=BASE/'live-v1',selection=BASE/'selection.json',output=Path(tmp)/'out',command='replay'))
            self.assertFalse((Path(tmp)/'out').exists())


if __name__=='__main__':unittest.main()
