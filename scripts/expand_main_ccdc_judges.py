"""Enable written defense planning for five reviewed historical team packets."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import pymupdf

CASES = {
    2013: (25, 21, "TJCI", "Physical and cloud services, public mail/DNS/web access, ICMP and VoIP, workstation preservation and change approval."),
    2014: (25, 21, "Warp Core", "Game hosting including Minecraft, Unreal Tournament and voice services; preserve client connectivity, public services, VoIP and proxy use."),
    2020: (20, 14, "Hylian", "Auto-parts retail service continuity, DHCP pool 10.X.X.101 to 10.X.X.150, preserved valid accounts, transparent proxy and DNS configuration. Cloud details withheld until event start remain unknown."),
    2021: (18, 13, "Malachor", "Renewable-energy business, remote employee access, legacy application compatibility, warehouse and monitoring networks, anonymous FTP and required public RDP/SSH access."),
    2026: (21, 15, "Marill", "Water-authority continuity, SCADA and pump-station dependencies, HR migration, protected ccdc account and CCSClient, and required scoring-network access."),
}

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard, update_track_index
from enable_open_artifact_judges import definition


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main(cases=CASES, report_name='main_ccdc_expansion_20260917.json', scanned=False):
    data = ROOT / 'data'
    path = data / 'benchmarks/ccdc/benchmark.json'
    rows = read(path)
    staged, originals, promoted = {}, {}, []
    backup = ROOT / 'tmp' / ('before_main_ccdc_expansion_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    def put(path, value):
        originals.setdefault(path, path.read_bytes() if path.exists() else None)
        staged[path] = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

    rubrics = {}
    for row in rows:
        if row['year'] not in cases or not row['problem_id'].endswith('TeamPacket'):
            continue
        if row['evaluation']['status'] != 'not_ready':
            continue
        count, map_page, organization, focus = cases[row['year']]
        assert len(row['assets']) == (2 if scanned else 1)
        for item in row['assets']:
            assert item['role'] == 'agent_visible'
            assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']
        asset = row['assets'][0]
        assert asset['path'].endswith('.pdf')
        with pymupdf.open(ROOT / asset['path']) as doc:
            assert len(doc) == count
            if scanned:
                assert row['assets'][1]['path'].endswith('.ocr.md')
                source_text = (ROOT / row['assets'][1]['path']).read_text(encoding='utf-8')
                assert doc[map_page - 1].get_images(), 'Reviewed map must contain a scanned image'
            else:
                source_text = '\n'.join(page.get_text() for page in doc)
                assert 'Team Network Diagram' in doc[map_page - 1].get_text()
            assert organization in source_text
            assert ('Scored Services' if row['year'] == 2026 else 'Critical Services') in source_text
        rubric, prompt, _, limitations = definition('ccdc', data)
        rubric['rubric_id'] = f"ccdc_{row['year']}_written_defense_v1"
        rubric['title'] = f"{row['year']} {organization} written defense benchmark"
        uncertainty = ('Some event-day credentials, injects and live system state are not archived. '
            'Keep unavailable details symbolic and identify needed verification. '
            'If the diagram, narrative or rules disagree, cite the conflicting passages and state a conditional plan; '
            'do not silently repair the source or invent official clarification. '
            'No credit for claimed uptime, attacks prevented, completed injects or observations without evidence.')
        if scanned:
            uncertainty += (' OCR is a search aid and contains recognition errors, especially IP addresses and service names. '
                'Verify exact values against the original PDF; ambiguous or unreadable details must remain uncertain. '
                f'Network-map location: PDF page {map_page} (one-based PDF page, not necessarily printed page number).')
        rubric['criteria'][0]['description'] += ' Scenario focus: ' + focus + ' ' + uncertainty
        rubric['criteria'][1]['description'] += (' Address the actual organization and its business dependencies. '
            'Include approval, evidence preservation, communication and rollback procedures. ' + uncertainty)
        limitations += ['Missing event-day inputs are not supplied by this written route; historical source inconsistencies remain unresolved.']
        rubric['not_observable_from_deck'] = limitations
        rubric['provenance']['sources'] = [dict(path=asset['path'], sha256=asset['sha256'],
            pages=list(range(1, count + 1)), network_map_page=map_page)]
        if scanned:
            rubric['provenance']['sources'].append(dict(path=row['assets'][1]['path'],
                sha256=row['assets'][1]['sha256'], role='searchable_ocr_not_authoritative'))
            rubric['provenance']['visual_review'] = dict(
                scope='Original network map, scenario letter, network details and critical-service pages',
                date='2026-09-17', network_map_pdf_page=map_page)
        rubric['provenance']['weight_basis'] = ('Two 50-point written-plan benchmark weights; historical service/business considerations '
            'are context, not a claim of official historical weighting or live scores.')
        rp = data / 'rubrics' / (rubric['rubric_id'] + '.json')
        put(rp, rubric)
        rubrics[row['problem_id']] = (rp, rubric)
        ev = row['evaluation']
        ev['before_main_report_review'] = deepcopy(ev)
        ev.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations', rubric_path=rp.relative_to(ROOT).as_posix(),
            reference_policy='rubric_only', grading_scope='written_artifact_benchmark', official_score_equivalent=False,
            limitations=limitations, score_basis=rubric['provenance']['weight_basis'],
            deliverable='written_defense_and_business_response_plan',
            reason='Archived team packet and network map reviewed for explicitly scoped written planning.')
        row['problem_description'] += ('\n\n' + prompt + '\nScenario focus: ' + focus + '\n' + uncertainty +
            '\nUse the attached original PDF for network diagrams and service mappings. '
            'Organization names in the actual scenario letter control over stale table-of-contents headings. '
            'Any approval or notification described is a proposed in-scenario procedure, not an instruction to contact organizers.')
        row['total_points'] = 100
        row['gold_label']['grading_rubric'] = ev['rubric_path']
        row.setdefault('source_review', {})['main_written_defense'] = rubric['provenance']
        promoted.append(row['problem_id'])
    if not promoted:
        print('No unprocessed reviewed packets; no files changed.')
        return
    put(path, rows)
    for base in [data, data / 'mini_data']:
        p = base / 'rules/ccdc/evaluation.json'
        rules = read(p)
        for key, (rp, rubric) in rubrics.items():
            dest = base / 'rubrics' / rp.name
            if base != data:
                put(dest, json.loads(json.dumps(rubric).replace('data/', 'data/mini_data/')))
            rules['scoring']['record_evaluator_overrides'][key] = 'rubric_llm_v1'
            rules['scoring']['record_rubric_overrides'][key] = dest.relative_to(ROOT).as_posix()
        current = rows if base == data else read(base / 'benchmarks/ccdc/benchmark.json')
        rules['scoring']['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in current) for s in {r['evaluation']['status'] for r in current}}
        put(p, rules)
    ip = data / 'benchmarks/index.json'
    index = read(ip)
    update_track_index(index, 'ccdc', rows)
    put(ip, index)
    sp = data / 'rubrics/task_scorecards/ccdc.json'
    cards = read(sp)
    cards['records'] = [scorecard(r, ROOT,
        read_json=lambda p: json.loads(staged[ROOT / p]) if ROOT / p in staged else read(ROOT / p),
        hash_file=lambda p: hashlib.sha256(staged[ROOT / p] if ROOT / p in staged else (ROOT / p).read_bytes()).hexdigest()) for r in rows]
    put(sp, cards)
    put(ROOT / 'tmp' / report_name, dict(promoted=promoted,
        scope='Written defense and business response only; no live cyber-defense scores', mini_membership_changed=False, paid_calls=0))
    for path, before in originals.items():
        if (path.read_bytes() if path.exists() else None) != before:
            raise RuntimeError('Concurrent edit: ' + str(path))
    for path, value in staged.items():
        if originals[path] is not None:
            dest = backup / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(originals[path])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    print(json.dumps(dict(promoted=len(promoted), backup=str(backup))))


if __name__ == '__main__':
    main()
