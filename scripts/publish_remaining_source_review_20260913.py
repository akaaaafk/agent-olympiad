"""Evidence-backed remaining queue; does not mutate benchmark records or readiness."""
from collections import Counter
import json
from scripts.repair_iol_sources_20260913 import ROOT,read,sha,require
from scripts.repair_data_catalog import Store

REPORT='data/benchmarks/remaining_source_review_20260913.json'
DOC='docs/from_zhongzheng/remaining-source-review-20260913.md'
CACHE='data/.cache/mystery_remaining_review_20260913/'
CASES={
 9:('staged_historical_inputs','Initial reuse email, later floppy-disk release and conditional plaintext must not be collapsed into one initial packet.','Recover authoritative team/phase release state; local reusefind alone is not the whole event.'),
 15:('team_specific_historical_inputs','A team was assigned one of five coloured actor scripts, not the union of all scripts.','Establish the assigned script and delivery context; do not choose or aggregate silently.'),
 68:('cross_puzzle_dependencies','The endgame depends on earlier meta answers and digit lookup; those antecedent inputs are not a self-contained packet.','Define the original prerequisite packet without exposing solved prerequisites prematurely.'),
 138:('missing_original_external_image','The linked historical Marvel image was not recovered; direct access failed and the checked archive availability response was empty.','Recover that exact historical image; a modern character picture is not a verified replacement.'),
 182:('legacy_executable_unrecovered','Both checked official/mirror EXE downloads timed out. A timeout is not a 404 or proof of permanent loss.','Recover the original executable and separately authorize an isolated compatibility review; nothing was executed.'),
 1244:('historical_unlock_state','The archived page contains an all-unlocked state and disabled Spin Control; original starting state is not established.','Recover the release/unlock state before staging the fourteen sectors as initial inputs.'),
 1374:('missing_historical_maps','Exact 2010 MBTA and WMATA map editions matter to the puzzle. The Harvard candidate returned HTML 403; the checked WMATA archive lookup had no snapshot.','Recover matching historical maps; do not substitute present-day routes, station markers or accessibility labels.'),
 1497:('external_video_dependencies','Seven local images include eighteen video links. oEmbed succeeded for fourteen, returned 403 for two and 404 for two; this is metadata, not playback verification.','Recover or verify the actual linked historical videos and their exact image-map positions; do not replace them with titles.'),
 1543:('dynamic_round_release','The official round source was recovered, but its dynamic release, guesses and points still require a defined starting state.','Specify the isolated round controller and original starting inputs.'),
 1732:('unavailable_host_and_runtime','The original Glitch host returns 410. Archived author code uses Python 2, Bottle and a mutable SQLite-backed game.','A separately scoped isolated runtime adaptation is needed; do not import or run the source against original services.'),
 1752:('lost_dynamic_service','The original Snow Day host redirects to a domain-sale page; the author page reports that the puzzle no longer works and original assets are being sought.','Recover original author assets; no replacement game or answer is invented.'),
 1794:('server_session_state','The original script posts to new-session and move-lever endpoints and receives hidden light/lever state. It was read, not executed.','Recover server rules and an isolated initial-state contract; no live session requests were made.'),
 1800:('local_interactive_mechanics','Original JavaScript implements a four-dimensional maze with walls revealed on collision. A static all-wall map changes available information.','A separately scoped interaction adapter is needed; do not publish hidden walls as starting clues.'),
 2030:('server_card_state','Goldfish Memory uses a sequenced POST session and a flip-card endpoint; its 2,602-byte session helper was fully read.','Recover isolated card/session rules; no flips, sessions or reset calls were sent to the original service.'),
 2144:('archived_hidden_game_bank','The archived Believe script contains the formerly server-hidden word bank and hangman state.','An isolated stateful adapter must keep the hidden bank out of initial assets; do not expose all words as a static puzzle.'),
}


def main():
    store=Store(ROOT);index=read(ROOT/'data/benchmarks/index.json');benchmarks={};hashes={};counts={};remaining=[]
    for t in index['olympiads']:
        path=t['benchmark_path'];rows=read(ROOT/path);benchmarks[t['id']]=rows;hashes[path]=sha(ROOT/path)
        n=sum(r['evaluation']['status']=='not_ready' for r in rows)
        if n:counts[t['id']]=n
    mystery=benchmarks['mystery_hunt'];pending=[r for r in mystery if not any(a['role']=='agent_visible' for a in r['assets'])]
    require({int(r['problem_id'].rsplit('_',1)[1]) for r in pending}==set(CASES),'Remaining mystery membership changed')
    for r in pending:
        key=int(r['problem_id'].rsplit('_',1)[1]);kind,evidence,need=CASES[key]
        remaining.append(dict(problem_id=r['problem_id'],year=r['year'],title=r['title'],category=kind,review=evidence,next_requirement=need,
            source_file=r['source_file'],source_sha256=sha(ROOT/r['source_file']),status=r['evaluation']['status'],no_answerlessness_inferred=True))
    network=read(ROOT/CACHE/'network-review.json');receipts=list(network['network_receipts'])
    helper=CACHE+'responses/50547fcb229b296ba4c144c7b5b1734cb91e4820422f96101f7282ccdaee18d7.json'
    receipts.append(read(ROOT/helper))
    for r in receipts:
        if r.get('path'):require(sha(ROOT/r['path'])==r['sha256'],'Network evidence drift')
    debate=benchmarks['debatebench'];missing=[r['problem_id'] for r in debate if not r.get('source_review',{}).get('motion_recovered')]
    require(len(missing)==3,'Debate motion count changed')
    report=dict(reviewed_at_utc=store.stamp,scope='Bounded data-only source review; no services, original puzzle code, paid experiments or redesigned evaluators executed.',
        catalog_snapshot=hashes,not_ready_counts=counts,not_ready_total=sum(counts.values()),
        not_ready_does_not_mean_wrong_or_answerless=True,all_sources_semantically_certified=False,all_remaining_work_externally_blocked=False,
        mystery_hunt=dict(reviewed_public_packets=len(mystery)-len(pending),pending_packets=len(pending),records=remaining),
        debatebench=dict(motions_with_source_review=sum(bool(r.get('source_review',{}).get('motion_recovered')) for r in debate),
            unresolved_motion_records=missing,astana_round5_slide_quarantined=True,
            header_recovery_does_not_certify_complete_background_slides=True,historical_scores_not_new_speech_gold=True),
        network_evidence=receipts,network_http_counts=dict(Counter(str(r.get('http_status','request_error')) for r in receipts)),
        interpretation=['Only known, reviewed source gaps are described; this is not an exhaustive proof that no undiscovered semantic defect remains.',
            'Working local sources are not all external blockers; several cases instead require explicit historical stage/team choices or a separately scoped runtime adapter.',
            'No year is removed solely because of missing execution support; failed downloads are not proof that an answer never existed.',
            'Unverified licences, splits, private marking schemes, exact historical information cutoffs and experiment observations have not been fabricated.'])
    body='# 剩余来源与评测缺口（逐项复核）\n\n'
    body+='本文件记录本轮数据修复之后仍未解决的边界，不是全库已可评测或全部原文已认证的声明。原题、答案及历史实验结果不改写。\n\n'
    body+=f"当前 {len(index['olympiads'])} 个赛道，{sum(len(r) for r in benchmarks.values()):,} 条记录；其中 {sum(counts.values())} 条保持 `not_ready`。这不是同等数量的错误数据，也不是无答案年份数。\n\n"
    body+='## Mystery Hunt 尚未形成已核验初始题包的 15 条\n\n| 记录 | 已核对的缺口 | 后续所需 |\n| --- | --- | --- |\n'
    for r in remaining:body+=f"| {r['problem_id']} / {r['title']} | {r['review']} | {r['next_requirement']} |\n"
    body+='\n## DebateBench\n\n29 条记录已有明确来源的辩题，其中 4 条仅恢复原始转录中明确写出或念出的辩题，不代表完整背景页已齐。Astana 第 5 轮背景说明已隔离；历史人类分数仍不用于给新生成的演讲打分。尚未恢复独立辩题题包的记录：\n\n'
    for pid in missing:body+='- '+pid+'\n'
    body+='\nNatolin 第 4、5 轮及 Cambridge 第 2 轮已找到二级来源线索，但尚未完成原始完整题包认证；这些线索不是无答案或永久失效的证据。\n\n'
    body+='## 其他赛道\n\n各条记录的现有具体限制保留在规范数据的 `evaluation.limitations`。物理实验/机器人与现场观测、CTF/攻防目标服务、原始 checker 与测试子任务映射、私有评分及历史信息时间边界，需要来源恢复或独立运行/评估适配，不能用静态数据补写来冒充完成。\n\n'
    body+='| 赛道 | not_ready |\n| --- | ---: |\n'
    for cid,n in sorted(counts.items(),key=lambda x:(-x[1],x[0])):body+=f'| {cid} | {n} |\n'
    body+='\n网络证据共 30 项只读检查，含 18 项视频元数据检查和 Goldfish Memory 会话脚本文本；没有执行原题脚本、提交答案、建立游戏会话或运行旧程序。403、404、410、超时与域名出售分别记录，不混称失效。全部响应字节及 SHA-256 见 JSON 报告。\n'
    store.save(REPORT,report);store.save_text(DOC,body);store.finish(dict(operation='publish_remaining_source_review',canonical_records_changed=False))
    for p,h in hashes.items():require(sha(ROOT/p)==h,'Canonical data changed during report')
    require(read(ROOT/REPORT)==report and (ROOT/DOC).read_text(encoding='utf-8')==body,'Report readback differs')
    print(json.dumps(dict(report=REPORT,mystery_pending=len(pending),debate_missing_motions=len(missing),network_checks=len(receipts),not_ready=sum(counts.values()))))


if __name__=='__main__':main()
