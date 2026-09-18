"""Register sourced, explicitly adapted LLM scoring for selected mini editions.

Also update the same records in the main catalog. Never use historical answers
as contestant inputs, promote other years, or change historical experiment files.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
TRACKS = ('debatebench', 'wharton_investment', 'gcch_harvard', 'ccdc', 'ioai_team')
VERSION = 'open_artifact_llm_20260917_v1'
NETWORK = '''Reviewed transcription of the image on packet page 14 (retain the original diagram's addresses; page 16 gives assigned team subnets):
Win 2019 Sirius 10.11.11.5 DNS/AD/DHCP alias ns1;
Debian Gemini 10.11.11.6 POP3/SMTP alias mail;
FreeBSD Lyra 10.11.11.9 HTTP alias www;
Rocky Triton 10.11.11.12 HTTP alias hrm;
Ubuntu Pegasus 10.11.11.18 HTTP alias finance;
FreeBSD Ganymede 10.11.11.21 SQL/SSH alias db;
Fedora Leo 10.11.11.24 HTTP alias shop;
Mint Rigel 10.11.11.27 SSH alias fileserver;
Windows 2019 Vega 10.11.11.33 HTTP alias helpdesk;
Debian Ceres 10.11.11.36 workstation;
Windows 11 Betelgeuse and Bellatrix DHCP workstations; Windows 10 Octo DHCP workstation.
Oscorp Cloud Complex 172.16.11.3-254: VM1 Canopus SSH .105; VM2 Arcturus SSH .110;
VM3 Polaris HTTP .115; VM4 Ares HTTP .120; VM5 Olympus HTTP .125;
VM6 DND SSH .130; VM7 GR27 HTTP .135; VM8 Sable SSH .140;
VM9 Monolith .145; VM10 Hornet .150. Do not infer extra connections from the decorative background.
The diagram and written service list differ in places (e.g. Rigel SSH versus the listed FTP service);
preserve and discuss the discrepancy rather than silently changing the task.'''
ANCHORS = ('Benchmark scoring anchors: 0 = absent, irrelevant, or unsupported; '
           '25% = major gaps; 50% = partly supported with material weaknesses; '
           '75% = coherent and mostly supported; 100% = thorough, specific and well supported. '
           'Intermediate scores are allowed. Cite submitted evidence; do not infer unobserved work.')


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def criterion(key, name, maximum, description):
    return dict(id=key, name=name, max_score=maximum, description=description,
                min_score=0, observable=True)


def definition(track, data):
    if track == 'debatebench':
        source = data / 'rubrics/debatebench_wudc_speaker_100_v1.json'
        description = read(source)['criteria'][0]['description']
        criteria = [criterion(role, role + ' written speech', 100,
            f'Evaluate only the labeled {role} speech. ' + description +
            ' For this text-only benchmark, a missing speech scores zero; a substantive speech uses '
            'the 50-100 WUDC scale. Do not award oral delivery, actual POIs or rebuttal to an '
            'unprovided opponent. Anticipated objections must be labeled hypothetical.') for role in ('PM', 'DPM')]
        prompt = ('BENCHMARK SUBMISSION: You are one Opening Government team. Submit two labeled '
                  'written speeches, PM and DPM, supporting the motion. PM defines and establishes the case; '
                  'DPM develops and strengthens it. You may anticipate objections explicitly as hypothetical. '
                  'No opposing speeches or live POIs are supplied; do not invent that they occurred. '
                  'Only your two speeches are scored, separately out of 100, total 200. '
                  'This is written preparation, not a four-team ranking or an oral-performance score.')
        limitations = ['Text-only preparation; no actual opposition, POIs, oral delivery or room ranking.',
                       'Two speaker scores are added as a benchmark team aggregate; missing speech = zero.',
                       'Historical human transcripts and scores do not grade newly generated speeches.']
        route = 'native'
        weight_basis = 'Published single-speaker scale; benchmark sum of two written speeches.'
    elif track == 'wharton_investment':
        source = data / 'rubrics/wharton_investment_current_v1.json'
        descriptions = [
            'Assess coherence, diversification, risk management and feasibility of the proposed investment strategy.',
            'Assess how recommendations address the actual client objectives, horizon, resources and constraints in the case.',
            'Assess research quality, traceable sources, quantitative reasoning and treatment of uncertainty. '
            'Require dates and explicit assumptions; do not accept current facts passed off as historical facts.',
            'Assess clear written explanation and reasoned defense of recommendations, including counterarguments. '
            'Do not infer live presentation or Q&A performance.']
        criteria = [criterion(c['id'], c['name'], 25, d + ' ' + ANCHORS)
                    for c, d in zip(read(source)['criteria'], descriptions)]
        prompt = ('BENCHMARK SUBMISSION: Prepare a written investment policy statement and final strategy report '
                  'for the client in this archived case. State the information date, cite and date research, '
                  'and distinguish supplied facts from assumptions. Explain portfolio choices, risk, client fit '
                  'and alternatives. Do not claim simulator trades, realized performance or live Q&A. '
                  'The four published qualitative considerations are each scored out of 25 for this benchmark; '
                  'these are benchmark weights, not a historical official scorecard.')
        limitations = ['Current same-competition qualitative criteria reused for the 2021 case; historical equivalence unverified.',
                       'Equal 25-point weights and scoring anchors are benchmark choices, not published official weights.',
                       'Written report only; no OTIS execution, portfolio-return score or oral Q&A.']
        route = 'native'
        weight_basis = 'Equal benchmark weights for four published qualitative considerations.'
    elif track == 'gcch_harvard':
        source = data / 'raw/gcch_harvard/case-2021.pdf'
        criteria = [criterion(key, name, 20, desc + ' ' + ANCHORS) for key, name, desc in [
            ('recommendation', 'Recommendation and executive summary', 'Assess the clarity and evidence supporting the answer to whether Nvidia and AMD should merge.'),
            ('context', 'Company and industry context', 'Assess relevant company operations, market position, strategic direction and industry context.'),
            ('financial', 'Financial due diligence', 'Assess valuation using DCF and/or multiples, financial feasibility, profitability metrics and proposed financing; require sources, dates and assumptions.'),
            ('strategic', 'Strategic due diligence', 'Assess synergies, integration threats, complementary capabilities and industry implications.'),
            ('conclusion', 'Balanced conclusion and alternatives', 'Assess the balance of supporting and opposing evidence, next steps for a recommended deal or defensible alternatives. A different structure is acceptable.')]]
        prompt = ''  # The artifact route supplies the original case PDF with these guidelines.
        limitations = ['Five recommended solution topics in the original 2021 case operationalized as benchmark criteria.',
                       'Equal 20-point weights and anchors are benchmark choices; the case does not publish official judging weights.',
                       'Judge only the submitted deck; no video pitch, oral delivery or live panel Q&A.']
        route = 'slides'
        weight_basis = 'Equal benchmark weights for the five recommended solution topics in the original 2021 case.'
    elif track == 'ioai_team':
        source = data / 'raw/ioai/Team-Challenge/recovered_20260913/2025/task_statement.txt'
        criteria = [criterion(key, title, 25, desc + ' ' + ANCHORS) for key, title, desc in [
            ('navigation', 'Navigation and obstacle avoidance', 'Review the submitted control code and reasoning for moving through the warehouse without collisions, using the guide constraints. Do not infer a successful trajectory from a claim.'),
            ('perception', 'Item localization and organization', 'Review how the code locates scattered items, maintains item state and determines target shelf placement; identify assumptions and missing sensor inputs.'),
            ('manipulation', 'Manipulation and robot constraints', 'Review grasp, transport and placement logic, coordinate handling, joint limits, reach and load constraints from the guide.'),
            ('integration', 'Integrated control and efficiency', 'Review executable program structure, use of the supplied interfaces, sequencing, failures and recovery, and reasoning about efficiency. Claimed completion times or success rates are not measured outcomes.')]]
        prompt = ('BENCHMARK SUBMISSION: Submit a Python robot-control program and technical explanation for '
                  'the warehouse task in the supplied 2025 guide. Specify required scene/sensor inputs and '
                  'assumptions. LLM review evaluates navigation, item localization, manipulation and integrated '
                  'control at 25 points each. These are benchmark review criteria derived from the task requirements, '
                  'not an official referee score. No simulator or physical robot runs in this route; do not fabricate '
                  'execution evidence, trajectories, success rates or completion times.')
        limitations = ['Static program and design review against the 2025 task guide; no simulator or physical robot execution.',
                       'Four equal 25-point weights and anchors are benchmark operationalization of task requirements, not official scoring weights.',
                       'Historical scene/referee equivalence remains unverified; no measured completion, collision or speed score.']
        route = 'native'
        weight_basis = 'Task-requirement-based benchmark static program review, with four equal weights.'
    else:
        source = data / 'rubrics/ccdc_official_scoring_protocol_v1.json'
        criteria = [criterion('service_defense_plan', 'Service defense and continuity plan', 50,
            'Evaluate the written plan for the packet network: prioritized service inventory, hardening, '
            'monitoring, validation, rollback and recovery, consistent with supplied constraints. '
            'Do not award actual uptime or claimed penetration prevention without execution evidence. ' + ANCHORS),
            criterion('business_incident_plan', 'Business response and incident reporting plan', 50,
            'Evaluate actionable handling and reporting of business requirements and incidents: evidence capture, '
            'triage, roles, communications and response workflow. Apply only requirements present in the packet. '
            'Do not invent timed injects or mark hypothetical injects as completed. ' + ANCHORS)]
        prompt = ('BENCHMARK SUBMISSION: Using this team packet, submit a written defense and business-response '
                  'plan for the described network. Include service priorities, hardening, monitoring, recovery, '
                  'incident reporting and coordination. Clearly distinguish proposals from observed evidence. '
                  'No live network or event-day injects are supplied. The two written-plan criteria receive '
                  '50 points each as a benchmark adaptation of service and business-task considerations. '
                  'This score is not service uptime, completed inject points, or an official CCDC result.')
        limitations = ['Written planning adaptation of the archived scenario, not an operational cyber-defense run.',
                       'Two equal 50-point weights are benchmark choices, not exact official national weights.',
                       'No live service checks, red-team outcomes, timed injects or official deductions are scored.']
        route = 'native'
        weight_basis = 'Benchmark written-plan criteria derived from service and business-task scoring components.'
    rubric = dict(rubric_id=track + '_' + VERSION, title=track + ' written artifact benchmark',
                  total_points=sum(c['max_score'] for c in criteria), criteria=criteria,
                  not_observable_from_deck=limitations,
                  provenance=dict(source_path=str(source.relative_to(ROOT)).replace('\\', '/'),
                                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                                  weight_basis=weight_basis, official_score_equivalent=False))
    return rubric, prompt, route, limitations


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = ROOT / 'tmp' / ('before_open_artifact_judges_' + stamp)
    staged = {}
    originals = {}

    def stage(path, obj):
        if path not in originals:
            originals[path] = path.read_bytes() if path.exists() else None
        staged[path] = (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

    changed = {}
    selected = {k: {r['problem_id'] for r in read(ROOT / 'data/mini_data/benchmarks' / k / 'benchmark.json')}
                for k in TRACKS}
    for data in (ROOT / 'data', ROOT / 'data/mini_data'):
        for track in TRACKS:
            rubric, prompt, route, limitations = definition(track, data)
            rubric_path = data / 'rubrics' / (rubric['rubric_id'] + '.json')
            stage(rubric_path, rubric)
            path = data / 'benchmarks' / track / 'benchmark.json'
            rows = read(path)
            for row in rows:
                if row['problem_id'] not in selected[track]:
                    continue
                ev = row['evaluation']
                ev.setdefault('before_open_artifact_llm', deepcopy(ev))
                ev.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations',
                          rubric_path=str(rubric_path.relative_to(ROOT)).replace('\\', '/'),
                          reason='Sourced written-artifact rubric and pipeline registered.',
                          grading_scope='written_artifact_benchmark', official_score_equivalent=False,
                          reference_policy='rubric_only', limitations=limitations,
                          score_basis=rubric['provenance']['weight_basis'], adaptation_version=VERSION)
                if track == 'ioai_team':
                    ev.update(grading_scope='robot_program_static_review', execution_verified=False,
                              official_execution_status='not_ready')
                if prompt and prompt not in row['problem_description']:
                    row['problem_description'] += '\n\n' + prompt
                if track == 'ccdc':
                    ev['task_pdf_required'] = True
                    if NETWORK not in row['problem_description']:
                        row['problem_description'] += '\n\n' + NETWORK
                    allowpath = data / 'problem_pdf_allowlist.json'
                    allow = read(allowpath)
                    asset = next(a for a in row['assets'] if a['role'] == 'agent_visible' and a['path'].endswith('.pdf'))
                    allow['assets'] = [a for a in allow['assets'] if a.get('problem_id') != row['problem_id']]
                    allow['assets'].append(dict(problem_id=row['problem_id'], path=asset['path'],
                        sha256=asset['sha256'], pages=list(range(1, 21)),
                        review_status='approved_problem_only',
                        review_evidence='2025 team packet: all 20 pages inspected in rendered contact sheet; '
                        'page 14 enlarged and transcribed. Schedule, rules, scoring instructions, '
                        'network diagram and scenario requirements; no solution or historical team score.'))
                    stage(allowpath, allow)
                row['total_points'] = rubric['total_points']
                row['gold_label']['grading_rubric'] = ev['rubric_path']
                changed[row['problem_id']] = deepcopy(ev)
            stage(path, rows)
            cardpath = data / 'rules' / track / 'competition.json'
            card = read(cardpath)
            if prompt:
                card['deliverable']['answer_format'] = prompt
                # Keep archival human constraints as background; current contract is explicit.
                card['rules_text'] = (track + '. ' + prompt + '\nResources: ' +
                                      json.dumps(card['resources'], ensure_ascii=False))
            if track == 'debatebench':
                card['team'].update(active_min=2, active_default=2, active_max=2,
                    collaboration='One Opening Government pair prepares PM and DPM written speeches.',
                    range_basis='benchmark_adaptation')
                card['execution']['coalitions'] = card['execution']['coalitions'][:1]
                card['execution']['coalition_privacy'] = 'one_participating_team'
            stage(cardpath, card)
            collabpath = data / 'rules' / track / 'collaboration.json'
            collab = read(collabpath)
            collab['simulation']['deliverable_pipeline'].update(kind=route,
                grading_status='registered_per_record_rubric', fidelity='written_artifact_benchmark')
            if track == 'debatebench':
                collab['agent_roles'] = collab['agent_roles'][:2]
                collab['agent_roles'][1]['duties'] = ['Develop and strengthen the case with Agent_1; label anticipated objections hypothetical.']
            stage(collabpath, collab)
            evalpath = data / 'rules' / track / 'evaluation.json'
            payload = read(evalpath)
            scoring = payload['scoring']
            scoring['record_evaluator_overrides'].update({i: 'rubric_llm_v1' for i in selected[track]})
            scoring['record_rubric_overrides'].update({i: str(rubric_path.relative_to(ROOT)).replace('\\', '/') for i in selected[track]})
            scoring['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in rows)
                for s in {r['evaluation']['status'] for r in rows}}
            scoring['current_repository_availability']['readiness_scope'] = 'Selected records support written-artifact LLM scoring; official environment reproduction remains separate.'
            payload['evaluation_guidance'] = ('Use the selected record rubric and written-artifact contract. '
                'Save each criterion score, evidence and justification; aggregate as a benchmark score. '
                'Do not use historical human scores as gold, infer live outcomes or claim official equivalence. '
                'Evaluate collaboration separately for teams; single_agent skips collaboration only.')
            stage(evalpath, payload)
            scorepath = data / 'rubrics/task_scorecards' / (track + '.json')
            from dataset_catalog import scorecard
            score_payload = read(scorepath)
            # Existing file schema is retained.
            by_id = {r['problem_id']: r for r in rows}
            score_payload['records'] = [scorecard(by_id[r['problem_id']], ROOT,
                read_json=lambda p: json.loads(staged[ROOT / p]) if ROOT / p in staged else read(ROOT / p),
                hash_file=lambda p: hashlib.sha256(staged.get(ROOT / p) or (ROOT / p).read_bytes()).hexdigest())
                if r['problem_id'] in selected[track] else r for r in score_payload['records']]
            stage(scorepath, score_payload)
        from dataset_catalog import update_track_index
        indexpath = data / 'benchmarks/index.json'
        index = read(indexpath)
        for track in TRACKS:
            update_track_index(index, track, json.loads(staged[data / 'benchmarks' / track / 'benchmark.json']))
        stage(indexpath, index)
    # Prepare all edits before writing, detect other agents' concurrent changes.
    for path, before in originals.items():
        if (path.read_bytes() if path.exists() else None) != before:
            raise RuntimeError('Concurrent edit: ' + str(path))
    for path, value in staged.items():
        if originals[path] == value:
            continue
        if originals[path] is not None:
            saved = backup / path.relative_to(ROOT)
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(originals[path])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    print(json.dumps(dict(tracks=TRACKS, records=len(changed), backup=str(backup), paid_calls=0)))


if __name__ == '__main__':
    main()
