import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'audit_ledger.py'
spec = importlib.util.spec_from_file_location('audit_ledger', SCRIPT)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'audit'
        self.call('init', '--out', str(self.root), '--project', 'Example CLI', '--type', 'cli')
        self.path = self.root / 'audit.json'
        self.data = ledger.load(self.path)
        self.data['scope']['coverage'] = ['CLI output path boundaries']
        self.data['project']['tested_version'] = 'build-2'
        self.case = {'id': 'T01', 'area': 'security', 'objective': 'Keep output within workspace',
                     'actor': 'CLI operator', 'environment': 'local fixture', 'expected': 'Reject external paths',
                     'required': True, 'critical': True, 'runs': []}
        self.data['cases'] = [self.case]
        for name in ['before.txt', 'after.txt']:
            (self.root / 'evidence' / name).write_text('Observed result ' + name)

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return ledger.main(list(args))

    def run_data(self, status='passed', name='after.txt', version='build-2'):
        return {'at': '2026-01-02T10:00:00+00:00', 'version': version, 'status': status,
                'observed': 'Actual outcome', 'evidence': [{'path': 'evidence/' + name}]}

    def save(self):
        self.path.write_text(json.dumps(self.data))

    def ready(self):
        self.data['assessment'] = {'status': 'ready_within_scope', 'rationale': 'Required contracts exercised', 'conditions': []}

    def assert_invalid(self, message):
        with self.assertRaisesRegex(ledger.LedgerError, message):
            ledger.validate(self.data, self.root)

    def test_empty_ledger_never_claims_test_success(self):
        initial = ledger.load(self.path)
        self.assertEqual(initial['assessment']['status'], 'not_assessed')
        self.assertEqual(sum(ledger.counts(initial['cases']).values()), 0)
        initial['assessment'] = {'status': 'ready_within_scope', 'rationale': 'No tests', 'conditions': []}
        with self.assertRaisesRegex(ledger.LedgerError, 'no cases'):
            ledger.validate(initial, self.root)

    def test_required_unexecuted_case_prevents_ready(self):
        self.ready()
        self.assert_invalid('required coverage is incomplete')

    def test_critical_failure_cannot_be_conditional(self):
        self.case['runs'] = [self.run_data('failed')]
        self.data['assessment'] = {'status': 'conditional', 'rationale': 'Some checks pass', 'conditions': ['Later']}
        self.assert_invalid('critical failure')

    def test_failed_then_passed_keeps_history_and_current_counts(self):
        self.case['runs'] = [self.run_data('failed', 'before.txt', 'build-1'), self.run_data()]
        self.ready()
        ledger.validate(self.data, self.root)
        self.assertEqual(ledger.counts(self.data['cases'])['passed'], 1)
        report = ledger.render(self.data, self.root, 'security', self.root / 'reports' / 'security-audit.md')
        self.assertIn('**failed**', report)
        self.assertIn('**passed**', report)
        self.assertIn('Attempt 2', report)
        self.assertIn('../evidence/before.txt', report)

    def test_missing_or_changed_evidence_cannot_pass(self):
        self.case['runs'] = [self.run_data()]
        ref = self.case['runs'][0]['evidence'][0]
        ref['sha256'] = ledger.digest(self.root / ref['path'])
        ledger.validate(self.data, self.root)
        (self.root / ref['path']).write_text('Overwritten result')
        self.assert_invalid('Evidence changed')
        (self.root / ref['path']).unlink()
        self.assert_invalid('Missing evidence')

    def test_successful_outcome_needs_real_file(self):
        self.case['runs'] = [self.run_data()]
        self.case['runs'][0]['evidence'] = []
        self.assert_invalid('executed outcome requires evidence')

    def test_path_traversal_and_symlink_escape_are_rejected(self):
        outside = self.root.parent / 'private.txt'
        outside.write_text('Private data that must not enter the manifest')
        for path in [str(outside), '../private.txt']:
            with self.assertRaises(ledger.LedgerError): ledger.evidence_path(self.root, path)
        link = self.root / 'evidence' / 'link.txt'
        link.symlink_to(outside)
        with self.assertRaisesRegex(ledger.LedgerError, 'symlink escapes'):
            ledger.evidence_path(self.root, 'evidence/link.txt')

    def test_not_applicable_is_separate_and_needs_reason(self):
        run = self.run_data('not_applicable'); run['evidence'] = []
        self.case['runs'] = [run]
        self.ready()
        self.assert_invalid('needs a reason')
        run['reason'] = 'Project has no remote identity boundary; separate local filesystem check covers its contract'
        ledger.validate(self.data, self.root)
        self.assertEqual(ledger.counts(self.data['cases'])['passed'], 0)
        self.assertEqual(ledger.counts(self.data['cases'])['not_applicable'], 1)

    def test_passing_an_old_version_does_not_qualify_current_version(self):
        self.case['runs'] = [self.run_data(version='build-1')]
        self.ready(); self.assert_invalid('another version')

    def test_deployed_claim_needs_evidence_and_version_mapping(self):
        self.case['runs'] = [self.run_data()]; self.ready()
        self.data['project']['target'] = 'deployed'
        self.assert_invalid('release verification')
        self.data['release'] = {'status': 'verified', 'deployed_version': 'image-42',
                                'evidence': [{'path': 'evidence/after.txt'}]}
        self.assert_invalid('explicit mapping')
        self.data['release']['version_mapping'] = 'CI metadata maps image-42 to build-2'
        ledger.validate(self.data, self.root)

    def test_corrected_finding_needs_a_passing_retest(self):
        self.data['findings'] = [{'id': 'F01', 'area': 'security', 'severity': 'high', 'title': 'Unsafe output',
            'origin': 'reproduction', 'impact': 'External file overwritten', 'status': 'corrected',
            'evidence': [{'path': 'evidence/before.txt'}], 'correction': 'Validate resolved path', 'retest_ids': ['T01']}]
        self.assert_invalid('retests must pass')
        self.case['runs'] = [self.run_data()]
        ledger.validate(self.data, self.root)

    def test_record_appends_hashes_and_invalidates_old_readiness(self):
        self.case['runs'] = [self.run_data()]; self.ready(); self.save()
        event = self.root.parent / 'run.json'; event.write_text(json.dumps(self.run_data('failed', 'before.txt')))
        self.call('record', str(self.path), '--case', 'T01', '--run', str(event))
        actual = ledger.load(self.path)
        self.assertEqual(len(actual['cases'][0]['runs']), 2)
        self.assertEqual(actual['cases'][0]['runs'][-1]['status'], 'failed')
        self.assertEqual(actual['assessment']['status'], 'not_assessed')
        self.assertEqual(actual['assessment_history'][0]['status'], 'ready_within_scope')
        self.assertEqual(len(actual['cases'][0]['runs'][-1]['evidence'][0]['sha256']), 64)

    def test_regression_reopens_previously_corrected_finding(self):
        self.case['runs'] = [self.run_data()]
        self.data['findings'] = [{'id': 'F01', 'area': 'security', 'severity': 'high', 'title': 'Unsafe output',
            'origin': 'inspection', 'impact': 'External write', 'status': 'corrected',
            'evidence': [{'path': 'evidence/before.txt'}], 'correction': 'Path validation', 'retest_ids': ['T01']}]
        self.save()
        event = self.root.parent / 'run.json'; event.write_text(json.dumps(self.run_data('failed')))
        self.call('record', str(self.path), '--case', 'T01', '--run', str(event))
        self.assertEqual(ledger.load(self.path)['findings'][0]['status'], 'open')

    def test_manifest_includes_only_referenced_evidence(self):
        self.case['runs'] = [self.run_data()]; self.save()
        (self.root / 'private').mkdir(); (self.root / 'private' / 'credentials.txt').write_text('Do not scan')
        self.call('manifest', str(self.path))
        result = ledger.load(self.root / 'evidence-manifest.json')
        self.assertEqual([x['path'] for x in result['files']], ['evidence/after.txt'])

    def test_overwriting_reports_requires_explicit_force(self):
        self.save(); self.call('report', str(self.path))
        before = (self.root / 'reports' / 'security-audit.md').read_text()
        with self.assertRaisesRegex(ledger.LedgerError, 'Output exists'):
            self.call('report', str(self.path))
        self.assertEqual((self.root / 'reports' / 'security-audit.md').read_text(), before)

    def test_report_directory_cannot_escape_root(self):
        self.save(); outside = self.root.parent / 'external'; outside.mkdir()
        (self.root / 'reports').rmdir(); (self.root / 'reports').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ledger.LedgerError, 'Report directory escapes'):
            self.call('report', str(self.path))

    def test_screenshot_needs_manual_privacy_review(self):
        shot = self.root / 'evidence' / 'screen.png'; shot.write_bytes(b'fixture')
        self.data['screenshots'] = [{'path': 'evidence/screen.png', 'caption': 'Actual screen', 'area': 'delivery'}]
        self.assert_invalid('Review screenshot pixels')

    def test_untrusted_markdown_cannot_insert_a_remote_image(self):
        value = ledger.md('![secret](https://example.invalid/collect) <script>bad</script>')
        self.assertNotIn('![secret](', value)
        self.assertNotIn('<script>', value)


if __name__ == '__main__':
    unittest.main()
