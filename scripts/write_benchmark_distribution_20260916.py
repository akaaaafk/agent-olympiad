"""Write the English catalog inventory and explicitly scoped experiment snapshot."""
import collections
import csv
import json
from datetime import datetime
from pathlib import Path
from build_mini_data import question_units

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'data/benchmarks'
TARGET = ROOT/'docs/from_zhongzheng/benchmark_distribution_and_completed_runs_20260916.md'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def years_text(years):
    if not years:
        return 'Unknown'
    groups=[]
    start=last=years[0]
    for y in years[1:]:
        if y == last+1:
            last=y
        else:
            groups.append(str(start) if start==last else f'{start}-{last}')
            start=last=y
    groups.append(str(start) if start==last else f'{start}-{last}')
    return ', '.join(groups)

index=read(BASE/'index.json')
names={t['id']:t['name'] for t in index['olympiads']}
catalog={t['id']:read(ROOT/t['benchmark_path']) for t in index['olympiads']}
special={
 'arml_power':f"{len(catalog['arml_power'])} seasonal sessions",
 'purple_comet':'22 annual editions; 44 HS/MS sessions',
 'wmtc':'1 edition; 3 age-group sessions',
 'history_olympiad':'Mixed IHO/IHBB packets; edition count unresolved',
 'eoes':f"{len(catalog.get('eoes', []))} task packets; edition count unresolved",
 'ccdc':'14 document/task packets across 12 years',
 'debatebench':'32 debate sessions; mixed events',
 'ethics_bowl_appe':'9 regional/national case collections',
 'nyu_ctf_bench':'11 CSAW Finals editions; no Quals',
 'odyssey_of_the_mind':'Annual synopses plus practice material',
 'wsc_writing':'Source years only; edition assignment unresolved',
}
counts={
 'arml_local':'65 subquestions', 'arml_national_team':'110 subquestions',
 'arml_power':f"{len(catalog['arml_power'])} packets; {sum(question_units(r)[0] for r in catalog['arml_power'])} scoring parts", 'hmmt_team':'140 subquestions',
 'purple_comet':'1,050 subquestions', 'wmtc':'42 subquestions',
 'fyziklani':'858 scoring parts', 'science_olympiad':'1 example packet; 100 scoring parts',
}
lines=['# Benchmark Distribution and Completed Qwen Runs', '',
 f'Generated: {datetime.now():%Y-%m-%d %H:%M:%S} (local time).', '',
 '## Scope and counting rules', '',
 '- Canonical inventory: active entries in `data/benchmarks/index.json`; archived or unindexed benchmark directories are excluded.',
 '- Years covered means distinct years represented in this local collection, not the total years a competition has existed.',
 '- Records use mixed units: questions, full papers, cases, and task packets. Record totals are not a total number of individual questions.',
 '- An annual edition, a seasonal event, a round packet, and an age-group session are different units; the table states the available unit.',
 '- Scoring parts are not automatically independent questions. Question counts are not multiplied by the three settings.',
 '- Catalog inclusion does not imply evaluation readiness. `not_ready` records remain explicitly marked.', '',
 '## Current full catalog', '',
 '| Competition / track | Editions or sessions | Years represented | Distinct years | Questions / tasks | Records | Total questions |',
 '|---|---|---|---:|---|---:|---:|']
for cid,rows in catalog.items():
    years=sorted({r['year'] for r in rows if isinstance(r.get('year'),int)})
    unknown=sum(r.get('year') is None for r in rows)
    if cid=='wsc_writing':
        years=sorted({y for r in rows for y in r.get('source_years',[])})
    yearstr=years_text(years)
    if unknown and cid!='wsc_writing':
        yearstr+='; unknown-year records also present'
    edition=special.get(cid,f'{len(years)} annual year groups')
    units={r.get('eval_unit') for r in rows}
    count=counts.get(cid,f'{len(rows)} questions' if units <= {'question','problem'} else f'{len(rows)} full task/case packets; internal count not verified')
    if cid=='qanta':
        edition=f"{len({(r['year'],r['tournament']) for r in rows})} year/tournament editions"
        count=f'{len(rows)} sampled questions'
    if cid=='science_bowl':
        edition=f"{len({r['parent_session_id'] for r in rows})} round packets; formal edition count unresolved"
        count=f'{len(rows)} sampled questions'
    if cid=='history_olympiad':
        count=f"{len(rows)} packets; {sum(r.get('n_questions',0) for r in rows):,} subquestions"
    if cid=='cybench':
        edition='4 source competition editions'
    n=str(len(years))+(' + unknown' if unknown and cid!='wsc_writing' else '')
    total_questions = sum(question_units(row)[0] for row in rows)
    lines.append(f"| {names.get(cid,cid)} (`{cid}`) | {edition} | {yearstr} | {n} | {count} | {len(rows)} | {total_questions:,} |")
total=sum(map(len,catalog.values()))
assert total==index['total_records']
total_question_units = sum(question_units(row)[0] for rows in catalog.values() for row in rows)
lines += ['', f"'Total questions' counts all data in the active full catalog: all years and all readiness statuses across the {len(catalog)} tracks, including all {total:,} records. It is not restricted to mini data or completed runs. Per record, use structured `gold_label.parts`, then `questions`, then a positive `n_questions` or `question_count`; otherwise count one whole-task unit. Scoring parts and whole-task fallbacks are not necessarily independent questions. No count is multiplied by baseline settings. " + f'**Total question/task units: {total_question_units:,}.**']
lines+=['',f'**Total: {len(catalog)} tracks and {total:,} mixed-unit records.** Codeforces has been removed from the active catalog.', '',
 '## Applied scope reductions', '',
 '| Track | Policy | Before | After |', '|---|---|---:|---:|',
 '| Odyssey of the Mind | Remove pre-2010 and unknown-year records | 50 | 18 |',
 '| QANTA | Remove pre-2010 and unknown-year records | 240 | 110 |',
 f"| QANTA | Keep strictly post-2010 years (2011+); archive original raw and old QANTA catalogs outside this checkout | 110 | {len(catalog['qanta'])} |",
 '| DOE Science Bowl | Remove unknown-year records | 140 | 120 |',
 '| Wharton Investment | Remove unknown-year records | 4 | 3 |',
 '| CFA Research Challenge | Remove pre-2010 records | 19 | 17 |',
 '| Codeforces | Remove the entire active benchmark | 1 | 0 |',
 '| NYU CTF Bench | Keep CSAW Finals only; remove all Quals | 194 | 66 |',
 '| CCDC | Remove 2007 and 2011 records | 16 | 14 |',
 '| HMMT Guts Round | Remove from the active catalog; retain canonical/raw files and historical results as archives | 45 | 0 |',
 '| WRO | Remove the entire active benchmark | 20 | 0 |',
 '| History Olympiad | Remove 67 unresolved packets; retain validated static answer-sheet packets | 95 | 28 |',
 f"| MIT Mystery Hunt | Remove all pre-2010 records | 247 | {len(catalog['mystery_hunt'])} |",
 f"| EOES / EUSO | Remove 2003, 2004 and 2006 | 30 | {len(catalog['eoes'])} |",
 f"| IYPT | Keep strictly post-2010 years (2011+) | 39 | {len(catalog['iypt'])} |",
 '| IJSO Practical | Keep strictly post-2010 years (2011+) | 15 | 11 |',
 '| IOL Team | Keep strictly post-2010 years (2011+) | 18 | 13 |',
 f"| IJSO Practical | Delete unready 2011 and 2015 editions and exclusive sources | 11 | {len(catalog['ijso_practical'])} |",
 f"| IOL Team | Delete unready 2011, 2012, 2016, 2017, 2019, 2022 and 2024 editions and exclusive sources | 13 | {len(catalog['iol_team'])} |",
 f"| ARML Power | Delete unready Spring 2022 edition and exclusive sources | 15 | {len(catalog['arml_power'])} |",
 f"| ITYM | Keep strictly post-2010 years (2011+) | 17 | {len(catalog['itym'])} |",
 f"| EOES / EUSO | Keep strictly post-2010 years (2011+); already satisfied after earlier exclusions | 24 | {len(catalog['eoes'])} |", '',
 'Historical backup payloads formerly stored under `data/excluded/` were deleted by request on 2026-09-16. Four referenced audit manifests remain. The IOL/IJSO/ARML Power unready-edition cleanup retains only deletion inventories under `docs/cleanup_audits/`, not historical task copies.', '',
 'QANTA original raw files, pre-filter catalogs and QANTA-only backups are stored outside this checkout under `E:/agent_olympiad/dataset_backups/qanta_post2010_*/`. Current QANTA data is restricted to 2011+; text, answers and splits are preserved. Historical paid outputs and active frozen snapshots are preserved. QANTA remains excluded from dispatch.', '',
 'NYU identity audit found no duplicate IDs, source paths, or year/event/category/challenge identities before the stage filter. The current 66 records represent 11 Finals editions, 2013-2023.', '',
 '### NYU Finals distribution', '', '| Year | Questions |', '|---|---:|']
for y,n in sorted(collections.Counter(r['year'] for r in catalog['nyu_ctf_bench']).items()):
    lines.append(f'| {y} | {n} |')
mini_path=ROOT/'data/mini_data/selection_manifest.json'
if mini_path.exists():
    mini=read(mini_path)
    mt=mini['totals']
    lines+=['', '## Mini dataset', '',
        'The mini catalog uses seed 920 and selects one available year per active competition; all records and internal parts in that year are retained. WSC has no assigned year and contributes one randomly selected record. Readiness labels and split assignments are preserved.', '',
        f"Current mini scope: {mt['competitions']} tracks, {mt['records']} records, and {mt['question_or_task_units']:,} question/task units ({mt['explicit_question_units']:,} explicit structured parts plus {mt['whole_task_fallback_units']} whole-task fallbacks). These mixed units are not a verified count of independent questions.", '',
        f"Records with runnable status labels: {mt['runnable_status_records']}; runtime preflight is still required. PDF, rules, rubric and judge assets use shared canonical paths.", '',
        'Selection and year table: `data/mini_data/README.md`. Full record IDs and source hashes: `data/mini_data/selection_manifest.json`.', '']
lines+=['', '## Data source and experiment scope alignment', '',
 'The canonical benchmark collection is under the repository `data/` directory. Execution uses benchmark JSON plus contest manifests; PDF/raw assets and evaluator resources live in other `data/` subdirectories.', '',
 'The continuing extension runner does **not** read the edited main catalog directly. `scripts/run_qwen_requested_remaining_20260915.py` passes `--benchmark-root E:/agent_olympiad/qwen-extension-runtime-20260915/data/benchmarks` and uses registered manifests under its result directory. This is a frozen runtime/data copy.', '',
 'The earlier ARML/ICPC continuation uses `E:/agent_olympiad/tinker-frozen-runtime-20260915/data`, as configured by `scripts/resume_qwen_frozen_20260915.py`.', '',
 'Changing the main catalog therefore does not automatically change an existing paid run. Historical outputs, registered run identities, and active frozen snapshots are preserved. The running queue has not been retargeted to the edited catalog.', '',
 '### Extension snapshot versus current catalog', '',
 '| Track | Frozen snapshot records | Current catalog records | Snapshot IDs excluded from current catalog |',
 '|---|---:|---:|---:|']
snapshot=ROOT.parent/'qwen-extension-runtime-20260915/data/benchmarks'
for cid in ['history_olympiad','qanta','science_bowl','nyu_ctf_bench']:
    frozen=read(snapshot/cid/'benchmark.json')
    current={r['problem_id'] for r in catalog.get(cid, [])}
    excluded={r['problem_id'] for r in frozen}-current
    lines.append(f'| {cid} | {len(frozen)} | {len(current)} | {len(excluded)} |')
lines+=['',
 'The registered History extension jobs reference 92 distinct packets / 5,462 questions across 7 years. History Olympiad has been removed from the active main catalog by user request. The full frozen History JSON has 95 records; not all were registered for execution.', '',
 'For a current-catalog comparison, include only jobs whose **entire** registered question set remains in the catalog. This membership check alone does not establish identical content, evaluator versions, token budgets, or task grouping. Mixed-membership historical sessions are excluded as a whole; do not reinterpret a historical score as a score on a shortened session.', '',
 'New experiments should use newly generated manifests and a new frozen snapshot/output identity from the current catalog. Existing completed paid runs should not be rerun merely to recount them.', '',
 '## Completed Qwen runs: historical registered scope', '',
 'Model: `Qwen/Qwen3.6-35B-A3B`; provider: `tinker`. Settings: `single_agent`, `vallina_otc`, `otc`. Remaining `vallina_otc` jobs are paused by request.', '',
 'Finished means `contest_session.json` exists. It includes evaluation-pending results. Counts below are **finished / registered total** and retain the original experiment scope.', '',
 '| Track | single_agent | vallina_otc | otc | Evaluated | Evaluation pending |',
 '|---|---:|---:|---:|---:|---:|']
jobs=[]
batches=['tinker_task_based_arml_icpc_20260914','tinker_requested_remaining_20260915']
if (ROOT/'results/tinker_requested_current_20260916/registry.json').exists():
    batches.append('tinker_requested_current_20260916')
for batch in batches:
    directory=ROOT/'results'/batch
    for job in read(directory/'registry.json')['jobs']:
        if job.get('kind') == 'artifact':
            continue  # Artifact finals have a separate result.json completion contract.
        if job.get('output') and Path(job['output']).parent != directory/'runs':
            continue
        path=directory/'runs'/job['id']/'contest_session.json'
        status='unfinished'
        if path.exists():
            result=read(path)
            status='evaluation_pending' if result.get('evaluation_pending') else 'complete'
        current={r['problem_id'] for r in catalog.get(job['competition'],[])}
        eligible=bool(job.get('problem_ids')) and set(job['problem_ids'])<=current
        jobs.append({**job,'status':status,'current_catalog_member':eligible,'batch':batch})
for cid in sorted({j['competition'] for j in jobs}):
    group=[j for j in jobs if j['competition']==cid]
    values=[]
    for variant in ['single_agent','vallina_otc','otc']:
        g=[j for j in group if j['variant']==variant]
        values.append(f"{sum(j['status']!='unfinished' for j in g)}/{len(g)}")
    a=sum(j['status']=='complete' for j in group)
    q=sum(j['status']=='evaluation_pending' for j in group)
    lines.append(f'| {cid} | '+' | '.join(values)+f' | {a} | {q} |')
a=sum(j['status']=='complete' for j in jobs)
q=sum(j['status']=='evaluation_pending' for j in jobs)
lines+=['',f'**Historical total: {a+q} finished runs; {a} evaluated; {q} evaluation pending.**', '',
 '### Current-catalog membership subset (not a rescored cohort)', '',
 '| Track | Registered jobs entirely in current catalog | Finished eligible jobs | Registered jobs excluded by membership |',
 '|---|---:|---:|---:|']
for cid in sorted({j['competition'] for j in jobs}):
    g=[j for j in jobs if j['competition']==cid]
    eligible=[j for j in g if j['current_catalog_member']]
    lines.append(f"| {cid} | {len(eligible)} | {sum(j['status']!='unfinished' for j in eligible)} | {len(g)-len(eligible)} |")
cohort=TARGET.with_name('current_catalog_run_membership_20260916.csv')
with cohort.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['batch','id','competition','variant','status','current_catalog_member'])
    writer.writeheader()
    writer.writerows({k:j[k] for k in writer.fieldnames} for j in jobs)
readiness=collections.Counter((r.get('evaluation') or {}).get('status','unspecified') for rows in catalog.values() for r in rows)
lines+=['', '## Further reduction options (not applied)', '',
 'These are scope choices for the next benchmark version. They have not been deleted automatically.', '',
 '| Option | Current size affected | Consequence |', '|---|---|---|',
 f"| Restrict the active evaluation subset to ready records | {readiness.get('not_ready',0)} `not_ready` records | Removes unresolved tasks from the execution cohort; keep source archives for later repairs. |",
 f"| Exclude MIT Mystery Hunt from a compact first release | {len(catalog['mystery_hunt'])} records, all currently not_ready | Removes an unresolved track; retain its source archive. |",
 '| Keep one of ARML Local / National Team / HMMT Team | 65 / 110 / 140 questions | Reduces overlapping team-math formats but changes track diversity. |',
 '| Keep only Purple Comet HS | 44 papers / 1,050 questions before filtering | Removes the MS age group; preserve the selected HS years. |',
 '| Remove overview/example material from the executable subset | Odyssey: 18 records; Science Olympiad: 1 example | Annual synopses and annotated examples are different from full contest tasks. |',
 '| Resolve or exclude mixed-source History packets | 28 packets / 1,648 questions | Require event identity and sample/backup labels rather than treating every packet as a live edition. |',
 '| Use a matched recent-year subset | e.g. 2015+ or 2020+ across selected tracks | A single year rule simplifies reporting, but can eliminate tracks represented only by older editions. |', '',
 'Recommended first reduction: use an evaluation-ready subset and remove overview/example material from that subset. Apply a common year window only after choosing which competition formats must remain.', '',
 '## Output locations and validation', '',
 '### Current ten-lane dispatch', '',
 'The current dispatcher is `scripts/run_requested_qwen_10lane_20260916.py`. Following the latest instruction, MCM/ICM PDF-text artifact jobs run first, followed by the remaining requested document and native jobs. QANTA is deferred. Historical evaluation retries are retained at lower priority. Old frozen snapshots remain the source for identity-compatible native resumes; new native jobs use `E:/agent_olympiad/qwen-current-native-runtime-20260916`. Artifact jobs use the repaired current checkout and validate their registered identity before launch.', '',
 'Registered remaining contest jobs at dispatch: QANTA 168, Science Bowl 133, HMMT Team 28, WSC Writing 84, and History 2. These are run/setting counts, not edition counts. New contestant execution uses only `single_agent` and `otc`; `vallina_otc` solving remains paused. Completed historical paid jobs are preserved even when repaired catalog content now differs.', '',
 'The repaired Tinker artifact pipeline now parses approved task PDFs into text before model calls, saves `task_extracted.txt` and `task_delivery.json`, and records the input-text hash. A provider/model switch is no longer needed. Text extraction may lose diagrams, equations, and layout; it does not perform OCR. This is PDF-to-text delivery, not visual PDF input.', '',
 'Artifact queue: MCM 36, ICM 38, ARML National Power 22, ARML Power 28, PUMaC Power 26, IOL Team 12, IOAA Group 8, IJSO Practical 18; total 188 run/setting entries (94 cases across two settings). Already completed MCM runs are preserved and skipped. Queue order gives MCM/ICM first priority. Ten non-ready document records remain excluded: ARML Power 1, IOL Team 7, IJSO Practical 2.', '',
 'Two multi-PDF task inputs were assembled from declared agent-visible PDF assets, in their original asset order and within declared page ranges. No judge-only solutions were added. Bundles and their original-PDF hashes are recorded in `results/tinker_requested_current_20260916/pdftext_preflight.json` and benchmark provenance.', '',
 'Pending auxiliary judge retries use `scripts/resume_qwen_evaluation_only_20260916.py` with a 16,384-token output capacity. This override is recorded as `evaluation_retry_config` in each affected result; contestant turns, token budgets, submissions, memory events, and original run identity are preserved. It retries failed stages and does not fabricate missing scores.', '',
 '- Unified queue / blocked records: `results/tinker_requested_current_20260916/registry.json`.',
 '- Per-job dispatch state: `results/tinker_requested_current_20260916/states/`.',
 '- Current supervisor logs: `results/tinker_requested_current_20260916/supervisor_pdftext_priority.stdout.log` and `supervisor_pdftext_priority.stderr.log`.',
 '- New native/artifact results: `results/tinker_requested_current_20260916/runs/`. Existing MCM PDF-text outputs stay under `results/tinker_mcm_pdftext_20260916/runs/`.',
 '- Artifact completion requires `result.json` with a terminal status; `contest_session.json` alone can exist before document rendering/evaluation finishes and must not be counted as a completed artifact.',
 '- Resume/evaluation results stay in their original batch directories. Aggregate counts exclude these unified references to avoid double counting.',
 '- Watchdog: restart/resume a worker after 480 seconds without log/checkpoint/result progress; maximum 10 simultaneous workers across the two keys.', '',
 '- Original batch: `results/tinker_task_based_arml_icpc_20260914/`.',
 '- Extension batch: `results/tinker_requested_remaining_20260915/`.',
 '- Per-run result: `runs/<job_id>/contest_session.json` inside its batch.',
 '- Original-scope aggregate: `results/tinker_requested_remaining_20260915/aggregates/combined_results_latest.csv`.',
 '- Membership audit: `docs/from_zhongzheng/current_catalog_run_membership_20260916.csv`.',
 '- Derived regeneration: `python scripts/repair_data_catalog.py --derived-only`.', '',
 'Referenced source-audit evidence formerly stored in `data/.cache/` was retained under `data/raw/cache_referenced_evidence_20260916/`, with active metadata references updated. Cache deletion inventories are under `data/excluded/cache_cleanup_*/manifest.json`. The cache directory is temporary and may be recreated by later repair scripts.', '',
 'This document is a static snapshot. Ongoing run counts change after generation. Membership filtering is reported separately from historical totals.', '']
queue_path=ROOT/'results/tinker_requested_current_20260916/registry.json'
if queue_path.exists():
    artifact_jobs=[j for j in read(queue_path)['jobs'] if j.get('kind')=='artifact']
    if artifact_jobs:
        lines += ['', '## PDF-text artifact completion snapshot', '',
            'This table counts final `result.json` files separately from native contest outputs. Finished includes `complete` and `unsubmitted`; evaluated requires `graded: true`.', '',
            '| Track | Registered | Finished | Evaluated | Unsubmitted |', '|---|---:|---:|---:|---:|']
        artifact_rows=[]
        for cid in sorted({j['competition'] for j in artifact_jobs}):
            group=[j for j in artifact_jobs if j['competition']==cid]
            finished=evaluated=unsubmitted=0
            for j in group:
                result_path=Path(j['output'])/'result.json'
                result=read(result_path) if result_path.exists() else {}
                status=result.get('status','unfinished')
                finished += status in {'complete','unsubmitted'}
                evaluated += result.get('graded') is True
                unsubmitted += status=='unsubmitted'
                grade=result.get('evaluation') or {}
                artifact_rows.append(dict(competition=cid,problem_id=j['problem_id'],variant=j['variant'],
                    status=status,graded=result.get('graded',False),score=grade.get('total_score',''),
                    max_score=grade.get('max_score',''),output_path=j['output']))
            lines.append(f'| {cid} | {len(group)} | {finished} | {evaluated} | {unsubmitted} |')
        artifact_csv=ROOT/'results/tinker_requested_current_20260916/aggregates/artifact_results_latest.csv'
        artifact_csv.parent.mkdir(parents=True,exist_ok=True)
        with artifact_csv.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(artifact_rows[0]))
            writer.writeheader();writer.writerows(artifact_rows)
        lines+=['', 'Artifact score details: `results/tinker_requested_current_20260916/aggregates/artifact_results_latest.csv`.', '']
text='\n'.join(lines)
TARGET.write_text(text,encoding='utf-8-sig')
assert TARGET.read_text(encoding='utf-8-sig')==text
assert not any('\u4e00'<=c<='\u9fff' for c in text)
assert '\ufffd' not in text
print(f'English report verified: tracks={len(catalog)}, records={total}, finished={a+q}')
