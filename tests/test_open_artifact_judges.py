"""Offline integration checks for the registered open-task scoring contract."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from contest_manifest import ContestManifest, ManifestTask
from contest_task_judge import judge_task, task_judge_specs
from contest_manifest import load_contest_manifest
from contest_adapters import grade_contest_result
from evaluation.models import load_rubric, EvaluationError
from evaluation.rubric_llm import RubricDocumentEvaluator
from llm import LLMResponse

TRACKS = ('debatebench', 'wharton_investment', 'gcch_harvard', 'ccdc', 'ioai_team')


def rows():
    for track in TRACKS:
        yield from json.loads((ROOT / 'data/mini_data/benchmarks' / track / 'benchmark.json').read_text(encoding='utf-8'))


def task(row):
    return ManifestTask(row['problem_id'], row['problem_id'], None, row['problem_description'],
                        row['task_type'], row['total_points'], False, row)


def response(request):
    rubric, _ = json.JSONDecoder().raw_decode(request.user_prompt.split('STRUCTURED RUBRIC:', 1)[1].lstrip())
    criteria = [dict(id=c['id'], score=c['max_score'] * .75, max_score=c['max_score'],
        evidence=['submitted argument'], justification='Offline scoring fixture.', confidence=.8,
        observable=True) for c in rubric['criteria']]
    return LLMResponse(json.dumps(dict(criteria=criteria, total_score=sum(c['score'] for c in criteria),
        max_score=rubric['total_points'], warnings=[], limitations=[])), 'mock', 'offline')


class OpenArtifactTests(unittest.TestCase):
    def test_iiot_code_review_keeps_reference_private_and_skips_execution(self):
        import tempfile
        source_rows = json.loads((ROOT / 'data/mini_data/benchmarks/iiot/benchmark.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'manifest.json'
            path.write_text(json.dumps(dict(session_id='iiot-test', competition_id='iiot',
                problem_ids=[r['problem_id'] for r in source_rows])), encoding='utf-8')
            manifest = load_contest_manifest(path, benchmark_root=ROOT / 'data/mini_data/benchmarks')
        for t in manifest.tasks:
            self.assertFalse(t.programming)
            self.assertNotIn('Publisher reference implementation', t.prompt)
            specs = task_judge_specs(ContestManifest('test', 'iiot', (t,)))
            self.assertTrue(specs[t.task_id]['judge_reference_files'])
            seen = []
            def judge(request):
                seen.append(request.user_prompt)
                return response(request)
            value = judge_task(t, 'int main() {}', judge)
            self.assertIn('Publisher reference implementation', seen[0])
            self.assertEqual(value['method'], 'source_review_llm_v1')
            self.assertFalse(value['execution_verified'])
            self.assertIsNone(value['official_test_pass_rate'])
            bad = json.loads(json.dumps(t.benchmark))
            bad['evaluation']['judge_reference_files'][0]['sha256'] = '0' * 64
            from dataclasses import replace
            with self.assertRaises(ValueError):
                task_judge_specs(ContestManifest('test', 'iiot', (replace(t, benchmark=bad),)))

    def test_selected_rubrics_are_executable_and_sourced(self):
        for row in rows():
            with self.subTest(task=row['problem_id']):
                ev = row['evaluation']
                rubric = load_rubric(ROOT / ev['rubric_path'])
                raw = json.loads((ROOT / ev['rubric_path']).read_text(encoding='utf-8'))
                self.assertEqual(rubric.total_points, row['total_points'])
                self.assertTrue((ROOT / raw['provenance']['source_path']).is_file())
                self.assertFalse(raw['provenance']['official_score_equivalent'])
                self.assertEqual(ev['reference_policy'], 'rubric_only')
                self.assertEqual(ev['status'], 'ready_with_limitations')
                # Original task and historical readiness are retained for audit.
                self.assertEqual(ev['before_open_artifact_llm']['status'], 'not_ready')

    def test_native_judge_scores_new_work_without_historical_winner(self):
        for row in rows():
            if row['competition_id'] not in {'debatebench', 'wharton_investment'}:
                continue
            t = task(row)
            manifest = ContestManifest('open-artifact-test', row['competition_id'], (t,))
            with patch('judge_references.winner_references', side_effect=AssertionError('historical answer loaded')):
                self.assertIn(t.task_id, task_judge_specs(manifest))
                submission = 'PM: submitted argument\nDPM: submitted argument'
                value = judge_task(t, submission, response)
            self.assertEqual(len(value['evaluation']['criteria']), 2 if row['competition_id'] == 'debatebench' else 4)
            self.assertAlmostEqual(value['utility'], .75)
            self.assertFalse(value['official_score_equivalent'])
            result = dict(submissions={t.task_id: submission}, task_judgements={t.task_id: value})
            self.assertTrue(grade_contest_result(manifest, result)['graded'])
            result['submissions'][t.task_id] = 'changed submission'
            self.assertFalse(grade_contest_result(manifest, result)['graded'])

    def test_absent_submission_does_not_invoke_judge(self):
        for row in rows():
            with patch('evaluation.rubric_llm.RubricDocumentEvaluator.evaluate', side_effect=AssertionError('paid call')):
                value = judge_task(task(row), '', response)
            self.assertEqual(value['score'], 0)
            self.assertEqual(value['max_score'], row['total_points'])

    def test_invalid_judge_criterion_maximum_rejected(self):
        r = next(rows())
        def invalid(req):
            value = json.loads(response(req).text)
            value['criteria'][0]['max_score'] += 1
            return LLMResponse(json.dumps(value), 'mock', 'offline')
        with self.assertRaises(EvaluationError):
            RubricDocumentEvaluator(invalid, load_rubric(ROOT / r['evaluation']['rubric_path']),
                                    submission_text='PM: example\nDPM: example').evaluate()


if __name__ == '__main__':
    unittest.main()
