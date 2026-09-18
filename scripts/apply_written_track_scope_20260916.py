"""Apply the user-requested artifact-only scope and remove the history catalog."""
from pathlib import Path
import sys
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    scopes = {
        'ijso_practical': ('written_report', 'One shared written scientific report.',
            'Archived marking materials anchor a 40-point written-report benchmark rubric. Physical measurement and instrument operation are unavailable. Use supplied data only; label proposed procedures and missing observations explicitly.'),
        'iypt': ('research_presentation_deck', 'One shared self-contained research presentation deck.',
            'Assess only the submitted research slides with the normalized 100-point benchmark rubric. Physical experiments, oral defense, opponent/reviewer exchanges, and jury coefficients are not reproduced. This is not an official Physics Fight score.'),
        'itym': ('research_solution_paper', 'One shared research solution paper.',
            'Assess only the submitted research paper with the normalized 100-point benchmark rubric. Live mathematical fights, external opponents/reviewers, and official jury scoring are not reproduced.'),
        'ichto': ('written_report', 'One shared written chemistry research report.',
            'Reuse the 2025 scientific criteria across editions as a 9-point written-report subtotal. No live debate, external opponent/reviewer, official TP/RP conversion, or team ranking is reproduced.'),
    }
    report = {'operation': 'user_requested_written_track_scope', 'tracks': {}}
    for cid, (deliverable, answer, basis) in scopes.items():
        path = f'data/benchmarks/{cid}/benchmark.json'
        rows = deepcopy(store.read(path))
        for row in rows:
            row['evaluation'].update(deliverable=deliverable, score_basis=basis,
                limitations=basis, collaboration_score_separate=True)
            row['gold_label']['grading_rubric'] = basis
        store.save(path, rows)
        report['tracks'][cid] = len(rows)
        cp = f'data/rules/{cid}/competition.json'
        competition = deepcopy(store.read(cp))
        competition['rules_text'] = answer + ' ' + basis + ' Collaborate within the participating team, verify the final artifact, and do not invent data or access hidden scoring materials.'
        competition['human_constraints'] = [answer, basis, 'Use only the resources allowed by this benchmark; no hidden answer keys or outside assistance.']
        competition['deliverable']['answer_format'] = answer
        competition['team']['collaboration'] = 'Jointly prepare and internally review one shared artifact.'
        adaptations = competition['provenance'].setdefault('adaptations', [])
        if basis not in adaptations:
            adaptations.append(basis)
        store.save(cp, competition)
        mp = f'data/rules/{cid}/collaboration.json'
        method = deepcopy(store.read(mp))
        method['rule_sections'] = {
            'competition_format': [answer, basis],
            'timeline': ['The runner turn budget bounds artifact preparation; no live tournament stages are simulated.'],
            'resource_policy': ['Use the declared allowed tools and supplied contestant materials only.'],
            'collaboration_protocol': ['Divide research and writing, share evidence, and have another teammate review the final artifact.'],
            'integrity_and_compliance': ['Do not fabricate measurements, citations, proofs, or results; distinguish proposals from evidence.'],
            'deliverable_format': [answer],
        }
        if cid in ('ichto', 'ijso_practical'):
            titles = (['report coordinator', 'scientific lead', 'evidence reviewer', 'report editor'] if cid == 'ichto'
                      else ['procedure analyst', 'evidence reviewer', 'analysis and report editor'])
            for role, title in zip(method['agent_roles'], titles):
                role['title'] = title
                role['duties'] = ['Prepare and verify the shared written report using supplied evidence.',
                                  'Share reasoning and review teammates\' contributions.']
        store.save(mp, method)
        ep = f'data/rules/{cid}/evaluation.json'
        evaluation = deepcopy(store.read(ep))
        evaluation['evaluation_guidance'] = basis + ' Use the selected record rubric for LLM-as-a-judge task scoring. Report the existing teammate collaboration score separately.'
        scoring = evaluation['scoring']
        scoring['score_basis'] = basis
        current = scoring.setdefault('current_repository_availability', {})
        current['submission_adaptation'] = deliverable
        current['proxy_limitations'] = [basis]
        scoring.setdefault('collaboration_quality', {})['reported_separately_from_performance'] = True
        store.save(ep, evaluation)
    rp = 'data/rubrics/iypt_research_report_100_v1.json'
    rubric = deepcopy(store.read(rp))
    rubric['title'] = 'IYPT submitted research slides benchmark rubric'
    rubric['scoring_basis'] = scopes['iypt'][2]
    rubric['criteria'][-1].update(name='Slide clarity', description='Submitted slides communicate assumptions, methods, evidence, conclusions, and citations clearly; no oral delivery is assessed.')
    rubric['criteria'][1]['description'] = 'Assess the documented analysis, simulation, or proposed investigation design; physical execution is not required and must not be assumed.'
    rubric['criteria'][2]['description'] = 'Documented evidence supports conclusions; distinguish supplied observations, simulation, literature, and hypotheses. Never reward invented measurements.'
    store.save(rp, rubric)
    iolp = 'data/benchmarks/iol_team/benchmark.json'
    rows = deepcopy(store.read(iolp))
    row = next(r for r in rows if r['problem_id'] == 'iol_team_2014')
    verification = dict(reviewed_at='2026-09-16', official_maximum=None,
        official_partial_credit_rule=None, status='not_found_in_public_primary_materials',
        checked_sources=['https://ioling.org/problems/2014/',
            'https://ioling.org/booklets/iol-2014-team-prob.en-gb.pdf',
            'https://ioling.org/booklets/iol-2014-team.m.pdf',
            'https://ioling.org/booklets/iol-2014-team-sol.m.pdf',
            'https://ioling.org/results/2014'],
        evidence='Official results include 23.5 team points, but do not establish item weights, a denominator, or the partial-credit algorithm. Problem and solution PDFs contain no scoring scheme.',
        required_contestant_files=[row['source_file'], 'data/raw/iol/recovered_20260913/2014/iol-2014-team.m.pdf'],
        page_counts=[4, 3], supplement_language='multilingual', solution_language='multilingual')
    row['source_review']['scoring_verification'] = verification
    row['evaluation']['official_scoring_verified'] = False
    store.save(iolp, rows)
    report['iol_2014'] = verification
    index = deepcopy(store.read('data/benchmarks/index.json'))
    history = store.read('data/benchmarks/history_olympiad/benchmark.json')
    assert len(history) == 28 and len({r['problem_id'] for r in history}) == 28
    report['history_removed_ids'] = [r['problem_id'] for r in history]
    # Save the exact deletion manifest before moving the canonical catalog.
    store.finish(report)
    store.archive('data/benchmarks/history_olympiad')
    index['olympiads'] = [t for t in index['olympiads'] if t['id'] != 'history_olympiad']
    index['total_records'] = sum(t['problems_collected'] for t in index['olympiads'])
    store.save('data/benchmarks/index.json', index)
    store.finish(report)
    print('Backup:', store.backup)
    print('Tracks:', report['tracks'], 'history removed:', len(history))


if __name__ == '__main__':
    main()
