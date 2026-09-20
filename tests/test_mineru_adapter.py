import copy
import unittest
from helpers import native, evidence
from hkex_audit.adapters.html_table import parse

class AdapterTests(unittest.TestCase):
    def test_independently_specified_grid(self):
        e=evidence();cells=[n for n in e['nodes'] if n['kind']=='cell']
        self.assertEqual([(n['row'],n['column'],n['row_span'],n['column_span'],n['text']) for n in cells],
                         [(0,0,2,1,'項目&甲'),(0,1,1,2,'年度'),(1,1,1,1,'0'),(1,2,1,1,'—'),(2,0,1,1,'重複'),(2,1,1,1,''),(2,2,1,1,'重複')])
        self.assertNotEqual(cells[-1]['id'],cells[-3]['id'])
        self.assertEqual(cells[-2]['content_state'],'blank')
        self.assertTrue(any(s['text']=='原文\u2028保留 e\u0301' for s in e['sources']))
        self.assertEqual(len(e['pages'][0]['printed_label_refs']),1)

    def test_bad_grids_never_repaired(self):
        for html in ['<table><tr><td>x', '<table><tr><td rowspan="0">x</td></tr></table>',
                     '<table><tr><td rowspan="2">x</td></tr></table>',
                     '<table><tr><td>x</td><td>y</td></tr><tr><td>z</td></tr></table>']:
            with self.subTest(html=html):self.assertNotEqual(parse(html)['state'],'resolved')
        r=parse('<table><tr><td>x</td><td><img src="/secret"/>y</td></tr></table>')
        self.assertEqual(r['state'],'partial');self.assertEqual(r['cells'][1]['text'],'y')
        self.assertTrue(r['cells'][1]['unsupported'])

    def test_page_local_not_merged_or_deduplicated(self):
        n=native();n['pdf_info'][0]['para_blocks']=[]
        second=copy.deepcopy(n['pdf_info'][0]);second['page_idx']=1
        second['preproc_blocks'][0]['blocks'][0]['lines'][0]['spans'][0]['html']='<table><tr><td>下一頁</td></tr></table>'
        n['pdf_info'].append(second);e=evidence(n)
        tables=[x for x in e['nodes'] if x['kind']=='table']
        self.assertEqual([t['page_index'] for t in tables],[0,1])
        self.assertEqual([t['row_count'] for t in tables],[3,1])
        self.assertEqual(len({t['id'] for t in tables}),2)

    def test_geometry_missing_and_unknown(self):
        n=native();n['pdf_info'][0].pop('page_size');n['pdf_info'][0]['preproc_blocks'][0].pop('bbox')
        e=evidence(n);p=e['pages'][0]
        self.assertIsNone(p['width']);self.assertIsNone(p['units']);self.assertIsNone(p['rotation'])
        self.assertTrue(all(c['bbox'] is None for c in e['nodes'] if c['kind']=='cell'))

    def test_missing_collection_and_foreign_profile(self):
        n=native();n['pdf_info'][0].pop('preproc_blocks');e=evidence(n)
        self.assertTrue(any(x['code']=='missing_preproc_blocks' for x in e['limitations']))
        for key,value in [('_version_name','future'),('_backend','unknown')]:
            n=native();n[key]=value
            with self.assertRaises(ValueError):evidence(n)

    def test_amount_changes_leave_structural_addresses(self):
        n=native();before=evidence(n)
        n['pdf_info'][0]['preproc_blocks'][0]['blocks'][0]['lines'][0]['spans'][0]['html']=n['pdf_info'][0]['preproc_blocks'][0]['blocks'][0]['lines'][0]['spans'][0]['html'].replace('>0<','>999.50<')
        after=evidence(n)
        address=lambda e:[(x['native_pointer'],x['ordinal'],x['row'],x['column'],x['row_span'],x['column_span']) for x in e['nodes'] if x['kind']=='cell']
        self.assertEqual(address(before),address(after))

    def test_benign_proposals_are_portable_native_inputs(self):
        from helpers import ROOT
        from hkex_audit.artifacts import read
        paths=list((ROOT/'tests/fixtures/evidence/benign').glob('*.json'))
        self.assertEqual(len(paths),6)
        for path in paths:
            with self.subTest(fixture=path.name):
                e=evidence(read(path));self.assertTrue(any(n['kind']=='table' for n in e['nodes']))

    def test_entities_multiline_and_markup_spans(self):
        raw='<table>\n<tr><td\ncolspan="1">甲&#x26;乙\u2028&amp;丙</td ></tr></table>'
        r=parse(raw);self.assertEqual(r['state'],'resolved')
        self.assertEqual(r['cells'][0]['text'],'甲&乙\u2028&丙')
        self.assertEqual(raw[r['cells'][0]['start']:r['cells'][0]['end']],'<td\ncolspan="1">甲&#x26;乙\u2028&amp;丙</td >')
