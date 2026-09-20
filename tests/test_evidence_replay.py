import copy
from pathlib import Path
import tempfile
import unittest
from helpers import native, selection, ir_selection
from hkex_audit.artifacts import write_new, read, sha
from hkex_audit.cli import launch

class ReplayTests(unittest.TestCase):
    def test_frozen_replay_relocation_and_no_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'native.json';write_new(p,native());sel=root/'selection.json';write_new(sel,selection(p))
            self.assertEqual(launch('ingest',sel,root/'a'),0)
            self.assertEqual(launch('ingest',sel,root/'b'),0)
            self.assertEqual((root/'a/evidence.json').read_bytes(),(root/'b/evidence.json').read_bytes())
            self.assertEqual((root/'a/manifest.json').read_bytes(),(root/'b/manifest.json').read_bytes())
            moved=root/'renamed.json';p.rename(moved);sel2=root/'selection2.json';write_new(sel2,selection(moved))
            self.assertEqual(launch('ingest',sel2,root/'c'),0)
            self.assertEqual((root/'a/evidence.json').read_bytes(),(root/'c/evidence.json').read_bytes())
            moved.unlink();ir=root/'ir.json';write_new(ir,ir_selection(root/'a'))
            self.assertEqual(launch('inspect',ir,root/'replay'),0)
            self.assertEqual((root/'a/context.json').read_bytes(),(root/'replay/context.json').read_bytes())
            run=read(root/'replay/run.json');self.assertFalse(run['adapter_imported'])
            allowed={str(root/'a/evidence.json'),str(root/'a/manifest.json')}
            self.assertEqual({x['path'] for x in run['access_attempts'] if x.get('access')=='read'},allowed)
            with self.assertRaises(ValueError):launch('inspect',ir,root/'replay')

    def test_tampered_truncated_and_renamed_pdf_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            for i,data in enumerate([b'{',b'%PDF-1.7\n',b'{"_backend":"future"}']):
                p=root/f'n{i}.json';p.write_bytes(data);s=root/f's{i}.json';write_new(s,selection(p))
                self.assertEqual(launch('ingest',s,root/f'o{i}'),2)
                self.assertTrue((root/f'o{i}/stage-failure.json').exists())
                self.assertFalse((root/f'o{i}/evidence.json').exists())
            p=root/'n.json';write_new(p,native());s=selection(p);s['artifacts'][0]['sha256']='0'*64
            write_new(root/'bad-hash.json',s)
            self.assertEqual(launch('ingest',root/'bad-hash.json',root/'bad-hash'),2)

    def test_ir_version_and_variant_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'native.json';write_new(p,native());sel=root/'selection.json';write_new(sel,selection(p))
            self.assertEqual(launch('ingest',sel,root/'source'),0)
            wrong=ir_selection(root/'source');wrong['document']['variant_id']='other'
            write_new(root/'wrong-variant.json',wrong)
            self.assertEqual(launch('inspect',root/'wrong-variant.json',root/'wrong-variant'),2)
            version=read(root/'source/evidence.json');version['schema_version']='9.0.0'
            write_new(root/'incompatible-evidence.json',version)
            from hkex_audit.artifacts import fingerprint
            manifest=read(root/'source/manifest.json');manifest['evidence_sha256']=fingerprint(version)
            write_new(root/'incompatible-manifest.json',manifest)
            bad=ir_selection(root/'source')
            for name in ['evidence','manifest']:
                path=root/('incompatible-'+name+'.json');bad[name]={'path':str(path),'sha256':sha(path.read_bytes())}
            write_new(root/'wrong-version.json',bad)
            self.assertEqual(launch('inspect',root/'wrong-version.json',root/'wrong-version'),2)
