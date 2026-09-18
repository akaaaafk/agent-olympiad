"""Combine wildcard instructions and seven VM policies into one written-plan task."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import update_track_index
from enable_remaining_mini_judges import criterion

TASK = 'ccdc_Wildcard26_Readme_http'
COMPANION = 'ccdc_2026-NCCDC-Wildcard'
VM_CRITERIA = [
    ('mint', 'Mint 21', 'Preserve LightDM, UFW, required applications and sudo-only administration. Plan Auditd watches on /etc/sudoers and /etc/sudoers.d/. Keep Docker rootful and restricted to authorized administrators. Preserve apache/mariadb honeypot names, images, addresses, ports, database password and running containers; do not rewrite application code or data.'),
    ('ubuntu_a', 'Ubuntu 22.04_A', 'Preserve GDM3, UFW and required applications. Plan secure sshd access for all authorized users and vsftpd access to /srv/ftp; preserve both critical services and authorized accounts.'),
    ('ubuntu_b', 'Ubuntu 22.04_B', 'Preserve GDM3, UFW and required applications. Plan secure Squid configuration and validation of business proxy functionality. Do not copy Ubuntu A service assumptions into this VM.'),
    ('windows10', 'Windows 10', 'Preserve required applications and Windows Action Center; avoid feature updates, Insider builds and resets. Plan Sysmon deployment with the supplied C:\\sysmon-config.xml path, but do not invent the unprovided file contents. No additional critical service is specified for this VM.'),
    ('windows11', 'Windows 11', 'Preserve Apache2 at C:\\Apache24, MariaDB at C:\\MariaDB, the ecorp_directory database and application availability. Propose investigation of reported table loss without inventing a diagnosis. Preserve WinRM for the specified users. Do not install Windows Updates during the task; configure automatic updates as requested. Preserve approved applications and avoid feature updates or resets.'),
    ('server2019', 'Windows Server 2019', 'Preserve FileZilla anonymous access to C:\\Users\\Public\\Documents while preventing sensitive-data exposure. Retain C:\\ProgramData\\filezilla-server\\ configuration storage, required applications, the OS and the no-feature-update/reset restrictions.'),
    ('server2022', 'Windows Server 2022', 'Plan review of AD DS and AD CS without inventing domain state. Include PowerShell script-block logging and protected event logging with a valid certificate. Preserve critical services and approved applications. Do not install Windows Updates during the task; configure automatic updates as requested, and avoid feature updates or resets.'),
]


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    data = ROOT / 'data'
    bp = data / 'benchmarks/ccdc/benchmark.json'
    rows = read(bp)
    row = next(r for r in rows if r['problem_id'] == TASK)
    if row['evaluation']['status'] != 'not_ready':
        print('Wildcard written plan already registered; no changes.')
        return
    companion = next(r for r in rows if r['problem_id'] == COMPANION)
    original_row = deepcopy(row)
    before, staged = {}, {}
    backup = ROOT / 'tmp' / ('before_ccdc_wildcard_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    def put(p, v):
        before[p] = p.read_bytes() if p.exists() else None
        staged[p] = (json.dumps(v, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    assets = deepcopy(row['assets'] + companion['assets'])
    for a in assets:
        assert a['role'] == 'agent_visible'
        assert hashlib.sha256((ROOT / a['path']).read_bytes()).hexdigest() == a['sha256']
    limitations = [
        'Written pre-execution plan only; no VM images, live CCS results, injects or desktop forensic questions are provided.',
        'Seven 10-point VM criteria plus 20 common-policy and 10 evidence-integrity points are benchmark weights, not 100 official points per VM.',
        'Do not infer current vulnerabilities, configuration file contents, repaired systems, forensic answers or official rankings.',
        'Historical scenario software requirements are constraints of this archive, not current deployment recommendations.']
    rubric = dict(rubric_id='ccdc_wildcard_2026_seven_vm_plan_v1', title='CCDC 2026 wildcard seven-VM written plan',
        total_points=100, criteria=[criterion(k, title, 10, desc) for k, title, desc in VM_CRITERIA] + [
            criterion('common', 'Shared policy and coordinated workflow', 20,
                'Preserve CCS Client/files, UTC time, and server connectivity on TCP 80/443. Keep authorized accounts/home directories and respect the auto-login password exception. Plan evidence capture before changes, least privilege, service validation and a reversible sequence. Only one operator uses a VM console at once. The event permits power/revert but no new snapshots or clones; do not promise snapshots as an available recovery method. Identify reverting loses VM work and score.'),
            criterion('evidence', 'Evidence integrity and uncertainty', 10,
                'Separate supplied requirements from hypotheses and missing observations. List needed VM inspection, unavailable desktop forensic questions, configuration and logs. Do not invent evidence, repaired issues or CCS scores. Give conditional diagnostic steps and verification criteria.')],
        not_observable_from_deck=limitations,
        provenance=dict(sources=[dict(path=a['path'], sha256=a['sha256']) for a in assets],
            weight_basis='Explicit written-plan benchmark: 7 x 10 VM policy points, 20 shared workflow points, 10 evidence points.',
            official_score_equivalent=False))
    rp = data / 'rubrics' / (rubric['rubric_id'] + '.json')
    put(rp, rubric)
    row['assets'] = assets
    row['total_points'] = 100
    row['topic'] = '2026 Wildcard: seven-VM written hardening plan'
    row['problem_description'] = (
        'BENCHMARK TASK: Produce one written pre-execution hardening and validation plan covering all seven VM policies below. '
        'Give a separate section per VM, a coordinated sequence, recovery options and evidence requirements. '
        'Do not execute against real systems or contact the event portal. No VM images, injects, logs or desktop forensic questions are provided. '
        'The general wildcard readme is a companion input, not a second independently scored task. '
        'Use only capabilities allowed in the packet: no new snapshots or VM clones. Preserve named service exceptions even when a generic hardening rule would disable them. '
        'A plan is scored out of 100 benchmark points (seven VM sections at 10 each, shared policy/workflow 20, evidence integrity 10), '
        'not the official 100-per-VM execution score. Distinguish proposed changes and conditional diagnoses from observations. '
        'Source-required software versions are historical task constraints.\n\n' + original_row['problem_description'] +
        '\n\nGENERAL EVENT COMPANION INSTRUCTIONS:\n' + companion['problem_description'])
    row['evaluation'].update(before_wildcard_plan=deepcopy(row['evaluation']),
        evaluator_id='rubric_llm_v1', status='ready_with_limitations', rubric_path=rp.relative_to(ROOT).as_posix(),
        deliverable='seven_vm_written_hardening_plan', reference_policy='rubric_only', grading_scope='written_artifact_benchmark',
        official_score_equivalent=False, limitations=limitations, score_basis=rubric['provenance']['weight_basis'],
        reason='Paired event instructions and seven VM policies support a scoped written plan, not live repair grading.')
    row['gold_label']['grading_rubric'] = row['evaluation']['rubric_path']
    row.setdefault('source_review', {})['wildcard_pairing'] = dict(companion_record=COMPANION, retained_record=TASK,
        reason='General access instructions accompany VM-specific policies; no duplicate independent score.')
    row['provenance']['files'] = deepcopy(assets)
    rows = [r for r in rows if r['problem_id'] != COMPANION]
    put(bp, rows)
    put(data / 'excluded/ccdc_wildcard_companion_20260917/manifest.json', dict(
        reason='Reclassified general event instructions as companion input to seven-VM task; original assets remain active.',
        original_record=companion, original_task=original_row, retained_problem_id=TASK))
    for base in [data, data / 'mini_data']:
        dest = base / 'rubrics' / rp.name
        if base != data:
            put(dest, json.loads(json.dumps(rubric).replace('data/', 'data/mini_data/')))
        p = base / 'rules/ccdc/evaluation.json'
        rules = read(p)
        for k in ['record_evaluator_overrides', 'record_rubric_overrides']:
            rules['scoring'].get(k, {}).pop(COMPANION, None)
        rules['scoring']['record_evaluator_overrides'][TASK] = 'rubric_llm_v1'
        rules['scoring']['record_rubric_overrides'][TASK] = dest.relative_to(ROOT).as_posix()
        selected = rows if base == data else read(base / 'benchmarks/ccdc/benchmark.json')
        rules['scoring']['evaluation_status_counts'] = dict(Counter(r['evaluation']['status'] for r in selected))
        put(p, rules)
    p = data / 'problem_pdf_allowlist.json'
    registry = read(p)
    registry['assets'] = [a for a in registry['assets'] if a.get('problem_id') not in {TASK, COMPANION}]
    for asset, count in zip(assets, [24, 3]):
        registry['assets'].append(dict(problem_id=TASK, path=asset['path'], sha256=asset['sha256'],
            pages=list(range(1, count + 1)), review_status='approved_problem_only',
            review_evidence='2026-09-17: archived seven-VM policies and general access instructions; contestant requirements and example UI, no solutions. Policy pages visually checked in tmp/ccdc_wildcard_review_20260917.'))
    put(p, registry)
    p = data / 'benchmarks/index.json'
    index = read(p)
    update_track_index(index, 'ccdc', rows)
    put(p, index)
    put(ROOT / 'tmp/main_ccdc_wildcard_expansion_20260917.json', dict(promoted=[TASK], companion_merged=COMPANION,
        scope='Seven-VM written plan only', paid_calls=0))
    for p, v in before.items():
        assert (p.read_bytes() if p.exists() else None) == v, f'Concurrent edit: {p}'
    for p, v in staged.items():
        if before[p] is not None:
            dest = backup / p.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(before[p])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(v)
    print(json.dumps(dict(promoted=1, companions_merged=1, backup=str(backup))))


if __name__ == '__main__':
    main()
