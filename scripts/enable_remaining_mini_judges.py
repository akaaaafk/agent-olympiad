"""Register four scoped mini tasks with explicit input and scoring contracts."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard, update_track_index

TRACKS = ('cfa_research_challenge', 'eoes', 'odyssey_of_the_mind', 'science_olympiad')
ANCHORS = ('Score only submitted evidence: 0 absent or incorrect; 25% major gaps; '
           '50% partly correct with material gaps; 75% coherent with minor gaps; '
           '100% complete, accurate and well supported. Intermediate scores allowed. '
           'Do not infer unobserved events or reward fabricated facts.')


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def criterion(key, name, maximum, description):
    return dict(id=key, name=name, min_score=0, max_score=maximum, observable=True,
                description=description + ' ' + ANCHORS)


def science_parts(row):
    sets = {9: 'D F K L N', 50: 'B E', 51: 'A E', 52: 'C D E', 95: 'EE HH GG', 96: 'II FF'}
    aliases = {3: ['Caloris', 'Caloris Planitia', 'Caloris Basin'], 27: ['Hellas', 'Hellas Impact Basin'],
        29: ['artists', 'authors', 'composers', 'artists, authors, composers'],
        33: ['Giant Impact Hypothesis', 'Big Splash'], 38: ['August 21, 2017', '2017-08-21'],
        39: ["Bailey's Beads", "Baily's Beads"], 47: ['6 AM', '6 hours after midnight', '06:00'],
        48: ['January 20-22', 'January 20 to 22'], 53: ['Curiosity', 'Curiosity Rover'],
        55: ['MRO', 'Mars Reconnaissance Orbiter'], 68: ['S', 'Stony', 'S-type'],
        69: ['M', 'Metallic', 'M-type', 'X', 'X-Group', 'X-type'], 70: ['C', 'Carbonaceous', 'C-type'],
        79: ['PHO', 'Potentially Hazardous Objects']}
    ranges = {23: (3.8e9, 4.1e9, {'billion years ago': 1e9, 'billion years': 1e9, 'years ago': 1, 'years': 1, 'ga': 1e9}),
        32: (20e6, 100e6, {'million years': 1e6, 'million years ago': 1e6, 'years': 1, 'years ago': 1, 'ma': 1e6}),
        63: (5.0, 5.3, {'years': 1, 'year': 1}), 64: (5, 6, {'au': 1, 'astronomical units': 1})}
    for part in row['gold_label']['parts']:
        number = int(part['id'])
        part['match_mode'] = 'normalized'
        part['aliases'] = list(dict.fromkeys(part.get('aliases', []) + aliases.get(number, [])))
        if number in sets or number == 49:
            part['match_mode'] = 'structured_reference'
            part['answer_spec'] = dict(kind='ordered_sequence' if number == 49 else 'unordered_set',
                items=('C D A E B' if number == 49 else sets[number]).split())
            part.setdefault('printed_reference', part['expected'])
            part['expected'] = ' '.join(part['answer_spec']['items'])
        elif number in ranges:
            lo, hi, units = ranges[number]
            part['match_mode'] = 'structured_reference'
            part['answer_spec'] = dict(kind='range', minimum=lo, maximum=hi, units=units)


def main():
    mini = ROOT / 'data/mini_data'
    backup = ROOT / 'tmp' / ('before_remaining_judges_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    staged, originals = {}, {}

    def put(path, obj):
        originals.setdefault(path, path.read_bytes() if path.exists() else None)
        staged[path] = obj if isinstance(obj, bytes) else (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode()

    def asset(path, data):
        put(path, data)
        return dict(path=path.relative_to(ROOT).as_posix(), role='agent_visible',
            mime_type='application/pdf', sha256=hashlib.sha256(data).hexdigest())

    selected = {t: {r['problem_id'] for r in read(mini / 'benchmarks' / t / 'benchmark.json')} for t in TRACKS}
    selected['eoes'] = {'eoes_t1', 'eoes_t2'}
    for track in TRACKS:
        path = ROOT / 'data/benchmarks' / track / 'benchmark.json'
        rows = read(path)
        for row in rows:
            if row['problem_id'] not in selected[track]:
                continue
            ev = row['evaluation']
            ev.setdefault('before_remaining_repair', deepcopy(ev))
            sources = []
            if track == 'science_olympiad':
                science_parts(row)
                prompt = ('Submit numbered answers 1-100, one per line. For multiple labels separate tokens with spaces; '
                    'preserve order when requested. Include units for numeric ages, periods and distances. '
                    'Each answer is worth one point. This is the archived example exam; the printed reference controls.')
                limitations = ['Historical example exam, not an official tournament result.',
                    'Explicit printed aliases, unordered sets, ordered sequences and numeric ranges are supported; other paraphrases may not match.',
                    'The existing research roster is a benchmark adaptation, not an official active event team size.']
                ev.update(evaluator_id='gold_answer_v1', answer_contract='Deterministic registered per-question reference contracts.')
                rubric_path = ROOT / ev['rubric_path']
            elif track == 'cfa_research_challenge':
                base = read(ROOT / 'data/rubrics/cfa_research_challenge_written_report_2025_2026_v1.json')
                descriptions = [
                    'Describe the supplied company, segments and business model using the issuer packet.',
                    'Assess competitive positioning and industry exposures; distinguish sourced facts from assumptions.',
                    'Give a clear recommendation and catalysts with stated information date and uncertainties.',
                    'Provide reproducible valuation, explicit forecasts, discount-rate/multiple assumptions and sensitivity analysis. A conditional price threshold is acceptable when no historical market quote is supplied.',
                    'Analyze the supplied financial statements, cash flows, leverage and business drivers. Reconcile units and reporting periods.',
                    'Explain material investment risks and how they affect valuation and recommendation.',
                    'Analyze governance, environmental and social exposures using dated evidence; identify unavailable facts explicitly.']
                criteria = [criterion(c['id'], c['name'], c['max_score'], desc) for c, desc in zip(base['criteria'], descriptions)]
                prompt = ('Prepare an equity research report on Canadian Tire Corporation using the issuer input packet. '
                    'The benchmark information boundary is 2015-12-31, a dataset choice, not an asserted official 2016 deadline. '
                    'Use only supplied historical information; state valuation assumptions, missing peer/market inputs and a conditional buy/hold/sell price threshold when needed. '
                    'Do not import later outcomes or invent historical market prices. Cover business, industry, investment summary, valuation, financial analysis, risks and ESG. '
                    'The 2025-2026 written-report scorecard is reused explicitly for this historical-source benchmark, not claimed as the 2016 official scorecard.')
                packet = fitz.open()
                annual = ROOT / 'tmp/cfa_source_review_20260917/annual2014.pdf'
                quarter = ROOT / 'tmp/cfa_source_review_20260917/q32015.pdf'
                for source, pages in [(annual, list(range(7, 14)) + list(range(65, 70))), (quarter, list(range(1, 59)))]:
                    doc = fitz.open(source)
                    for page in pages:
                        packet.insert_pdf(doc, from_page=page-1, to_page=page-1)
                    dest = ROOT / 'data/raw/cfa_research_challenge/historical_2016' / source.name
                    put(dest, source.read_bytes())
                    sources.append(dict(path=dest.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(source.read_bytes()).hexdigest(), pages=pages))
                a = asset(ROOT / 'data/raw/cfa_research_challenge/historical_2016/research_packet.pdf', packet.tobytes())
                row['assets'] = [a] + [a for a in row['assets'] if a['role'] == 'judge_only']
                row['problem_description'] = prompt + '\nPacket pages 1-12: 2014 annual report original PDF pages 7-13 and 65-69. Pages 13-70: complete 2015 Q3 report.\n'
                row['problem_description'] += '\n'.join(f'Packet page {i+1}:\n{packet[i].get_text(sort=True)}' for i in [2,3,4,5,6,7,8,10,19,24,25,26])
                limitations = ['Historical issuer inputs with benchmark information boundary; not the original complete 2016 contest packet.',
                    '2025-2026 same-competition written-report weights reused; no assertion of historical official equivalence.',
                    'No live presentation, realized investment return or unsupplied market price is scored.']
                weight_basis = 'Published 2025-2026 written-report weights, explicitly reused for historical source analysis.'
            elif track == 'eoes':
                day = row['problem_id'][-1]
                doc = fitz.open()
                for name in ['t'+day, 'a'+day]:
                    source = ROOT / 'data/raw/eoes/eoes/2021' / (name + '.pdf')
                    doc.insert_pdf(fitz.open(source))
                    sources.append(dict(path=source.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
                a = asset(ROOT / 'data/raw/eoes/eoes/2021' / ('task_' + day + '_with_blank_answers.pdf'), doc.tobytes())
                row['assets'] = [a] + [a for a in row['assets'] if a['role'] == 'judge_only']
                prompt = ('Written experimental-analysis benchmark: address the paired task and blank answer sheet by section and question. '
                    'Solve questions using supplied constants, tables and figures. For questions requiring measurements not supplied, provide a reproducible protocol, formulas, expected relationships and uncertainty analysis; label the result NOT MEASURED. '
                    'Never invent experimental readings, laboratory actions or signatures. Submit an integrated report covering all three disciplines. '
                    'Scoring is 100 benchmark points: scientific reasoning 30, methods 25, supplied-data analysis 30, uncertainty and evidence integrity 15. These are explicit benchmark weights, not the official practical exam marks.')
                criteria = [criterion('reasoning', 'Scientific reasoning', 30, 'Assess accurate biology, chemistry and physics reasoning for the actual questions in all sections.'),
                    criterion('methods', 'Experimental methods', 25, 'Assess feasible task-specific measurement and calibration protocols, controls, equipment and safe procedure descriptions. Do not infer their execution.'),
                    criterion('analysis', 'Analysis of supplied data', 30, 'Check calculations, units, graphs and conclusions against supplied tables and figures. For missing measurements assess correct symbolic derivation and the specified required inputs, not invented readings.'),
                    criterion('uncertainty', 'Uncertainty and evidence integrity', 15, 'Assess error propagation, limitations and distinction between supplied, derived and unmeasured quantities. Fabricated measurements receive no credit.')]
                row['problem_description'] += '\n\n' + prompt + '\nThe blank answer sheet is included after the task pages in the single PDF.'
                limitations = ['Written scientific analysis only; physical measurements and live laboratory performance are not scored.',
                    '100-point benchmark rubric derived from the task requirements, not an official 2021 marking scheme.',
                    'Blank answer sheets are companion inputs, not independent tasks or solutions.']
                weight_basis = 'Explicit benchmark operationalization of supplied integrated experimental tasks; 30/25/30/15 weights.'
            else:
                source = ROOT / 'data/raw/odyssey_of_the_mind/2019/long_term_synopses.md'
                synopsis = next(line for line in source.read_text(encoding='utf-8').splitlines() if line.startswith('5. '))
                prompt = ('Create a complete written script and staging plan for the 2019 Opposites Distract public synopsis below. '
                    'Include dialogue, characters, scene sequence, two successful distractions, distinct dramatic styles, attention-getting effects and the final discovery/capture. '
                    'Describe how effects could be produced; do not claim any live performance occurred. '
                    'This is a public-synopsis writing benchmark, not the member-only full problem or an official 350-point tournament score. '
                    'Five written criteria are each worth 20 benchmark points: plot requirements, distractions, dramatic styles, effects and humorous coherence.\n\n' + synopsis)
                row['problem_description'] = prompt
                criteria = [criterion('plot', 'Plot requirements and resolution', 20, 'A sneaky character seeks control of a specified thing; groups ultimately discover the distractions and catch it before control is achieved.'),
                    criterion('distractions', 'Two successful distractions', 20, 'Two distinct silly arguments demonstrably distract the groups within the written plot, serving the character goal.'),
                    criterion('styles', 'Different dramatic styles', 20, 'The arguments use recognizably different dramatic styles, realized through dialogue and stage directions.'),
                    criterion('effects', 'Attention-getting effects', 20, 'Specific, coherent, plausibly realizable effects support the arguments and distraction; assess the design only.'),
                    criterion('humor', 'Humorous creative coherence', 20, 'Assess originality, humor, readable dialogue and coherent integration of the public synopsis requirements.')]
                sources = [dict(path=source.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(source.read_bytes()).hexdigest(), selected_synopsis=5)]
                limitations = ['Public synopsis only; private full-problem constraints are not asserted or scored.',
                    'Five equal 20-point benchmark criteria operationalize the published synopsis; these are not official weights.',
                    'Written script/design only; no live performance, physical construction, spontaneous event or cohort normalization.']
                weight_basis = 'Explicit benchmark rubric derived from the five observable public-synopsis requirements; equal weights.'
            if track != 'science_olympiad':
                if track == 'cfa_research_challenge':
                    rubric_source = ROOT / 'data/rubrics/cfa_research_challenge_written_report_2025_2026_v1.json'
                    sources.append(dict(path=rubric_source.relative_to(ROOT).as_posix(),
                        sha256=hashlib.sha256(rubric_source.read_bytes()).hexdigest(), role='scoring_weight_source'))
                rubric = dict(rubric_id=track + '_mini_written_20260917_v1', title=track + ' scoped written benchmark',
                    total_points=100, criteria=criteria, not_observable_from_deck=limitations,
                    provenance=dict(sources=sources, weight_basis=weight_basis, official_score_equivalent=False))
                rubric_path = ROOT / 'data/rubrics' / (rubric['rubric_id'] + '.json')
                put(rubric_path, rubric)
                ev.update(evaluator_id='rubric_llm_v1', rubric_path=rubric_path.relative_to(ROOT).as_posix(),
                    reference_policy='rubric_only', grading_scope='written_artifact_benchmark',
                    official_score_equivalent=False, score_basis=weight_basis)
                row['gold_label']['grading_rubric'] = ev['rubric_path']
            else:
                row['problem_description'] += '\n\n' + prompt
            ev.update(status='ready_with_limitations', reason='Scoped input and executable scoring contract registered.', limitations=limitations)
            row['total_points'] = 100
            row.setdefault('source_review', {})['remaining_mini_repair'] = dict(sources=sources, version='20260917_v1')
            pdfs = [a for a in row['assets'] if a['role'] == 'agent_visible' and a['path'].endswith('.pdf')]
            if pdfs:
                assert len(pdfs) == 1
                a = pdfs[0]
                data = staged.get(ROOT / a['path']) or (ROOT / a['path']).read_bytes()
                count = len(fitz.open(stream=data, filetype='pdf'))
                allowpath = ROOT / 'data/problem_pdf_allowlist.json'
                allow = json.loads(staged[allowpath]) if allowpath in staged else read(allowpath)
                allow['assets'] = [entry for entry in allow['assets'] if entry['problem_id'] != row['problem_id']]
                allow['assets'].append(dict(problem_id=row['problem_id'], path=a['path'], sha256=a['sha256'], pages=list(range(1,count+1)),
                    review_status='approved_problem_only', review_evidence='Reviewed contestant tasks/blank sheets or historical public issuer disclosures; no contestant solutions. Rendered contact sheets inspected; original PDF bytes/pages retained.'))
                put(allowpath, allow)
                if track != 'science_olympiad':
                    ev['task_pdf_required'] = True
        put(path, rows)
        mini_rows = json.loads(json.dumps([r for r in rows if r['problem_id'] in selected[track]]).replace('data/', 'data/mini_data/'))
        put(mini / 'benchmarks' / track / 'benchmark.json', mini_rows)
        for data, records in [(ROOT / 'data', rows), (mini, mini_rows)]:
            cardpath = data / 'rules' / track / 'competition.json'
            card = read(cardpath)
            card['deliverable']['answer_format'] = prompt
            card['rules_text'] = track + '. ' + prompt + '\nResources: ' + json.dumps(card['resources'])
            put(cardpath, card)
            collabpath = data / 'rules' / track / 'collaboration.json'
            collab = read(collabpath)
            collab['simulation']['deliverable_pipeline'].update(kind='native', grading_status='registered_selected_record_evaluator', fidelity='scoped_benchmark')
            put(collabpath, collab)
            evalpath = data / 'rules' / track / 'evaluation.json'
            rules = read(evalpath)
            scoring = rules['scoring']
            scoring.setdefault('record_evaluator_overrides', {}).update({r['problem_id']: r['evaluation']['evaluator_id'] for r in records if r['problem_id'] in selected[track]})
            scoring.setdefault('record_rubric_overrides', {}).update({r['problem_id']: r['evaluation']['rubric_path'] for r in records if r['problem_id'] in selected[track]})
            scoring['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in records) for s in {r['evaluation']['status'] for r in records}}
            put(evalpath, rules)
            indexpath = data / 'benchmarks/index.json'
            index = json.loads(staged[indexpath]) if indexpath in staged else read(indexpath)
            update_track_index(index, track, records)
            put(indexpath, index)
        for r in mini_rows:
            for a in r['assets']:
                src = ROOT / a['path'].replace('data/mini_data/', 'data/', 1)
                put(ROOT / a['path'], staged[src] if src in staged else src.read_bytes())
    # Copy only newly staged canonical assets and rubrics into the independent root.
    for path, value in list(staged.items()):
        if path.is_relative_to(ROOT / 'data') and not path.is_relative_to(mini) and any(part in path.parts for part in ['raw', 'rubrics']):
            dst = mini / path.relative_to(ROOT / 'data')
            if path.suffix == '.json':
                value = value.decode().replace('data/', 'data/mini_data/').encode()
            put(dst, value)
    allow = json.loads(staged[ROOT / 'data/problem_pdf_allowlist.json'])
    mini_allow = read(mini / 'problem_pdf_allowlist.json')
    ids = set().union(*selected.values())
    mini_allow['assets'] = [a for a in mini_allow['assets'] if a['problem_id'] not in ids] + json.loads(json.dumps([a for a in allow['assets'] if a['problem_id'] in ids]).replace('data/', 'data/mini_data/'))
    put(mini / 'problem_pdf_allowlist.json', mini_allow)
    for track in TRACKS:
        for data in [ROOT / 'data', mini]:
            records = json.loads(staged[data / 'benchmarks' / track / 'benchmark.json'])
            p = data / 'rubrics/task_scorecards' / (track + '.json')
            payload = read(p)
            payload['records'] = [scorecard(r, ROOT,
                read_json=lambda p: json.loads(staged[ROOT / p]) if ROOT / p in staged else read(ROOT / p),
                hash_file=lambda p: hashlib.sha256(staged[ROOT / p] if ROOT / p in staged else (ROOT / p).read_bytes()).hexdigest()) for r in records]
            put(p, payload)
    p = mini / 'selection_manifest.json'
    selection = read(p)
    for t in selection['tracks']:
        if t['competition_id'] not in TRACKS:
            continue
        if t['competition_id'] == 'eoes':
            t['companion_record_ids'] = ['eoes_a1', 'eoes_a2']
            t['selected_record_ids'] = ['eoes_t1', 'eoes_t2']
            t['selected_records'] = 2
            t['sessions'] = 2
        t['route'] = 'native'
    put(p, selection)
    for path, original in originals.items():
        if (path.read_bytes() if path.exists() else None) != original:
            raise RuntimeError('Concurrent edit: ' + str(path))
    for path, value in staged.items():
        if originals[path] is not None:
            saved = backup / path.relative_to(ROOT)
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(originals[path])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    print(json.dumps(dict(tracks=TRACKS, backup=str(backup))))


if __name__ == '__main__':
    main()
