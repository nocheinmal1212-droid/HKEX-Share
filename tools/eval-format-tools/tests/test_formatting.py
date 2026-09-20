import json
from pathlib import Path
import tempfile
import unittest
from eval_formatter.cli import main
from eval_formatter.formatting import FormatError, format_jsonl, format_taxonomy


class FormattingTests(unittest.TestCase):
    def test_v2_unicode_geometry_depth_and_idempotence(self):
        raw=(json.dumps({'review_notes':[{'field':'location','reason':'中文','evidence_refs':[{'nested':{'a':1}}]}],'location':{'rectangle':[1.2,2.3,4.5,6.7]},'error_id':'HL-ERR-2'},ensure_ascii=False)+'\n'+json.dumps({'error_id':'HL-ERR-1'})+'\n').encode()
        actual,_=format_jsonl(raw)
        self.assertIn('中文'.encode(),actual)
        self.assertEqual(json.loads(actual.splitlines()[0])['error_id'],'HL-ERR-1')
        self.assertEqual(actual,format_jsonl(actual)[0])

    def test_bad_json(self):
        for raw in [b'{"error_id":"x","a":NaN}\n',b'{"error_id":"x","a":1e999}\n',b'{"error_id":"x","error_id":"y"}\n',b'{"error_id":"x"}\n\n{"error_id":"y"}\n']:
            with self.subTest(raw=raw), self.assertRaises((FormatError,ValueError)):format_jsonl(raw)

    def test_yaml_v2_comments_without_dependency_order(self):
        raw=b'''taxonomy_version: 2.0.0
spec_version: 2.0.0
categories:
  # retained comment
  - name: Example
    description: Example prose.
    code: example
    revision: 2
    status: active
    scope: global
'''
        result=format_taxonomy(raw)
        self.assertIn(b'# retained comment',result)
        self.assertNotIn(b'depends_on',result)
        self.assertEqual(format_taxonomy(result),result)
        for raw in [b'categories: [1]',b'categories: [&x {code: a}, *x]']:
            with self.assertRaises(FormatError):format_taxonomy(raw)

    def test_discovery_and_corpus_guard(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            self.assertEqual(main(['--check',d]),2)
            p=root/'eval/records/b/v.jsonl';p.parent.mkdir(parents=True);p.write_text('{ "error_id": "x" }\n')
            self.assertEqual(main(['--check',d]),1)
            self.assertEqual(main([d]),0)
            self.assertEqual(main(['--check',d]),0)
            raw=root/'corpus/error_detail.jsonl';raw.parent.mkdir();raw.write_text(p.read_text());before=raw.read_bytes()
            self.assertEqual(main([str(raw)]),2)
            alias=root/'alias.jsonl';alias.symlink_to(raw)
            self.assertEqual(main([str(alias)]),2)
            self.assertEqual(raw.read_bytes(),before)


if __name__=='__main__': unittest.main()

class PreservationRegressionTests(unittest.TestCase):
    def test_unicode_line_separator_is_literal_text(self):
        record={'error_id':'id','original_text':'甲\u2028乙\u2029丙'}
        raw=(json.dumps(record,ensure_ascii=False)+'\n').encode()
        self.assertEqual(json.loads(format_jsonl(raw)[0])['original_text'],record['original_text'])

    def test_duplicate_ids_rejected(self):
        with self.assertRaisesRegex(FormatError,'duplicate error_id'):
            format_jsonl(b'{"error_id":"x"}\n{"error_id":"x"}\n')
