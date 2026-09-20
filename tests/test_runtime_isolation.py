import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from helpers import ROOT, native, selection
from audit_inputs import selected_files
from hkex_audit.artifacts import write_new

class IsolationTests(unittest.TestCase):
    def test_methods_aliases_descriptors_and_external_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();allowed=root/'allowed.json';allowed.write_text('{}')
            forbidden=root/'renamed.json';forbidden.write_text('EVALUATOR_SECRET_SENTINEL')
            link=root/'alias.json';link.symlink_to(forbidden)
            bootstrap='import sys;sys.path.insert(0,sys.argv[1]);from audit_inputs.probe import main;main()'
            run=subprocess.run([sys.executable,'-I','-B','-c',bootstrap,str(ROOT/'src')],
                input=json.dumps({'allowed':[str(allowed)],'probes':[str(allowed),str(forbidden),str(link)]}),text=True,capture_output=True,check=True)
            results=json.loads(run.stdout)
            self.assertTrue(all(v=='allowed' for v in results[0]['methods'].values()))
            self.assertTrue(all(v=='denied' for r in results[1:] for v in r['methods'].values()))
            code='''import sys,os,socket,subprocess,ctypes
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from audit_inputs.guard import install
install([])
ops=[lambda:open(0),lambda:os.listdir('.'),lambda:os.scandir('.'),lambda:socket.socket(),lambda:subprocess.run(['true']),lambda:ctypes.CDLL(None)]
for op in ops:
 try:op()
 except PermissionError:continue
 raise AssertionError('forbidden operation succeeded')
print('passed')'''
            run=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT/'src')],text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)

    def test_selection_rejects_pdf_answers_and_symlink_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'native.json';write_new(p,native())
            for name in ['a.pdf','error_detail.jsonl','APIKEY.txt','eval/x.json']:
                q=root/name;q.parent.mkdir(exist_ok=True);q.write_text('{}');s=selection(q)
                with self.assertRaises(ValueError):selected_files(s)
            alias=root/'alias';alias.symlink_to(root,target_is_directory=True)
            s=selection(p);s['artifacts'][0]['path']=str(alias/'native.json')
            with self.assertRaises(ValueError):selected_files(s)
            s=selection(p);s['answers']={'secret':'value'}
            with self.assertRaises(ValueError):selected_files(s)

    def test_real_runtime_module_boundaries(self):
        paths=list((ROOT/'src').rglob('*.py'));self.assertGreater(len(paths),10)
        for path in paths:
            text=path.read_text();tree=ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    self.assertTrue(all(n.name.split('.')[0] not in {'eval_intake','eval_formatter','pypdf','pdfplumber','mineru'} for n in node.names),path)
                elif isinstance(node,ast.ImportFrom):
                    self.assertNotIn((node.module or '').split('.')[0],{'eval_intake','eval_formatter','pypdf','pdfplumber','mineru'},path)
            for literal in ['HL-ERR-','hksa_2026032600825','EVALUATOR_SECRET_SENTINEL']:
                self.assertNotIn(literal,text,path)
