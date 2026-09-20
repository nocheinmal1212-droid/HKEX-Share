"""Approval integrity and review completeness, using portable synthetic inputs only."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from helpers import ROOT, evidence, native
from hkex_audit.artifacts import encode, read, sha

sys.path.insert(0, str(ROOT/'eval/milestone1'))
from packet import seal, verify, member
from prepare import fixture_material, table_view, review_bytes


class ReviewPacketTests(unittest.TestCase):
    def test_active_review_rejects_pdf_and_derived_assets_before_open(self):
        from unittest.mock import patch
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('forbidden file opened')):
            with self.assertRaisesRegex(ValueError, 'PDF'):
                member(Path('/private/tmp'), 'forbidden.PDF')
            for name in ['report.pdf', 'report.PDF', 'source-paragraph.png', 'source-paragraph.txt',
                         'error_detail.jsonl', 'APIKEY.txt']:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    review_bytes(Path('/private/tmp')/name)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            source = root/'native.json'
            source.write_text('{}')
            alias = root/'alias.json'
            alias.symlink_to(source)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                review_bytes(alias)

    def test_original_inputs_reject_derived_assets_and_symlinks_before_open(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            source = root/'source.json'
            source.write_bytes(b'{}')
            (root/'alias.json').symlink_to(source)
            for name in ['source-paragraph.txt', 'source-paragraph.png', 'alias.json']:
                review = {'inputs': [{'path': name, 'sha256': sha(b'{}')}]}
                directory = root/('packet-' + name)
                seal(directory, review, {'index.html': b'review'})
                original = Path.read_bytes
                def guarded(path):
                    if path == root/name:
                        raise AssertionError('prohibited original input opened')
                    return original(path)
                with patch.object(Path, 'read_bytes', guarded):
                    with self.subTest(name=name), self.assertRaises(ValueError):
                        verify(directory, root=root)

    def test_packet_directory_symlink_is_rejected(self):
        review, files = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            seal(root/'packet', review, files)
            (root/'alias').symlink_to(root/'packet', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                verify(root/'alias')

    def test_preparation_intake_rejects_prohibited_selector_before_open(self):
        from unittest.mock import patch
        sys.path.insert(0, str(ROOT/'tools/eval-format-tools'))
        from validate import verified_intake
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            config = root/'eval/milestone1/selection.json'
            config.parent.mkdir(parents=True)
            config.write_bytes(encode({'ready_selector': 'forbidden.PDF', 'cases': []}))
            import builtins
            original = builtins.open
            def guarded(path, *args, **kwargs):
                if Path(path) == root/'forbidden.PDF':
                    raise AssertionError('prohibited selector opened')
                return original(path, *args, **kwargs)
            with patch('validate.ROOT', root), patch('builtins.open', guarded):
                with self.assertRaisesRegex(ValueError, 'forbidden'):
                    verified_intake()

    def fixture(self, name='rounding', raw=None):
        f = next(x for x in read(ROOT/'eval/negatives/milestone1-proposals.json')['fixtures'] if x['fixture_id'] == name)
        f['qualification'] = read(ROOT/'eval/milestone1/review-guidance.json')['fixtures'][name]
        raw = raw if raw is not None else (ROOT/f['input_path']).read_bytes()
        item, e, html = fixture_material(f, raw)
        review = {'inputs': [{'path': f['input_path'], 'snapshot': item['native_snapshot'], 'sha256': sha(raw)}],
                  'fixtures': [item]}
        files = {item['native_snapshot']: raw, item['ir_snapshot']: encode(e), 'index.html': html.encode()}
        return review, files

    def test_fixture_amount_mutation_changes_both_bindings(self):
        before, files = self.fixture()
        raw = files['fixtures/rounding.native.json'].replace(b'<td>3</td>', b'<td>30</td>')
        self.assertIn(b'<td>30</td>', raw)
        after, changed = self.fixture(raw=raw)
        with tempfile.TemporaryDirectory() as tmp:
            a = seal(Path(tmp).resolve()/'a', before, files)
            b = seal(Path(tmp).resolve()/'b', after, changed)
            self.assertNotEqual(a['content_fingerprint'], b['content_fingerprint'])
            self.assertNotEqual(a['approval_fingerprint'], b['approval_fingerprint'])
            with self.assertRaisesRegex(ValueError, 'approved fingerprint differs'):
                verify(Path(tmp).resolve()/'b', a['approval_fingerprint'])

    def test_report_fixture_and_expectation_tampering_rejected(self):
        review, files = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            for index, name in enumerate(['index.html', 'fixtures/rounding.native.json', 'review.json', 'fixtures/rounding.evidence.json']):
                directory = Path(tmp).resolve()/str(index)
                manifest = seal(directory, review, files)
                verify(directory, manifest['approval_fingerprint'])
                with (directory/name).open('ab') as stream:
                    stream.write(b' ')
                with self.assertRaisesRegex(ValueError, 'packet file changed'):
                    verify(directory, manifest['approval_fingerprint'])
            changed = copy.deepcopy(review)
            changed['fixtures'][0]['expected_behavior'] = 'Changed expectation'
            a = seal(Path(tmp).resolve()/'old', review, files)
            b = seal(Path(tmp).resolve()/'new', changed, files)
            self.assertNotEqual(a['content_fingerprint'], b['content_fingerprint'])
            self.assertNotEqual(a['approval_fingerprint'], b['approval_fingerprint'])
            different_html = {**files, 'index.html': b'Changed rendering'}
            c = seal(Path(tmp).resolve()/'render', review, different_html)
            self.assertEqual(a['content_fingerprint'], c['content_fingerprint'])
            self.assertNotEqual(a['approval_fingerprint'], c['approval_fingerprint'])

    def test_original_input_mutation_and_snapshot_mismatch_rejected(self):
        review, files = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            source = root/review['inputs'][0]['path']
            source.parent.mkdir(parents=True)
            source.write_bytes(files['fixtures/rounding.native.json'])
            manifest = seal(root/'packet', review, files)
            verify(root/'packet', manifest['approval_fingerprint'], root)
            source.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'source input changed'):
                verify(root/'packet', manifest['approval_fingerprint'], root)
            verify(root/'packet', manifest['approval_fingerprint'])  # portable offline mode
            review['inputs'][0]['sha256'] = '0'*64
            seal(root/'bad', review, files)
            with self.assertRaisesRegex(ValueError, 'input snapshot hash mismatch'):
                verify(root/'bad')

    def test_supporting_note_text_pointer_and_ir_are_displayed(self):
        review, files = self.fixture('reference')
        html = files['index.html'].decode()
        self.assertIn('附註甲 收入分項', html)
        self.assertIn('/pdf_info/0/preproc_blocks/1/lines/0/spans/0/content', html)
        ir = read(ROOT/'tests/fixtures/evidence/benign/reference.json')
        self.assertEqual(ir['pdf_info'][0]['preproc_blocks'][1]['lines'][0]['spans'][0]['content'], '附註甲 收入分項')
        self.assertIn('Supporting text IR IDs and spans', html)
        self.assertIn('fixtures/reference.evidence.json', html)

    def test_partial_content_and_raw_markup_are_visible(self):
        n = native()
        n['pdf_info'][0]['preproc_blocks'][0]['blocks'][0]['lines'][0]['spans'][0]['html'] = '<table><tr><td>甲</td><td><img src="hidden.png">乙</td></tr></table>'
        html = table_view(evidence(n), 0, 0)
        self.assertIn('Grid: partial', html)
        self.assertIn('r0 c1 · unsupported', html)
        self.assertIn('unsupported_cell_content', html)
        self.assertIn('unsupported_inline_content', html)
        self.assertIn('&lt;img src=', html)
        self.assertNotIn('<img src=', html)
        self.assertIn('must abstain', html)
        self.assertIn('capabilities', html)

    def test_deterministic_seal_refuses_overwrite_and_symlinks(self):
        review, files = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            a = seal(root/'a', review, files)
            b = seal(root/'b', review, files)
            self.assertEqual(a, b)
            for name in [*a['files'], 'packet-manifest.json']:
                self.assertEqual((root/'a'/name).read_bytes(), (root/'b'/name).read_bytes())
            with self.assertRaisesRegex(ValueError, 'review path exists'):
                seal(root/'a', review, files)
            (root/'a/index.html').unlink()
            (root/'a/index.html').symlink_to(root/'b/index.html')
            with self.assertRaisesRegex(ValueError, 'symlinks'):
                verify(root/'a')
            with self.assertRaisesRegex(ValueError, 'invalid packet member'):
                seal(root/'escape', review, {**files, '../escape.html': b'x'})
            self.assertFalse((root/'escape').exists())
