"""Publish an honest checkpoint of completed repairs plus the still-open queue."""
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
from scripts.repair_iol_sources_20260913 import ROOT,read,sha,require
from scripts.repair_data_catalog import Store
from scripts.publish_all_data_audit_20260913 import TESTS as ORIGINAL_TESTS

REPORT='data/benchmarks/data_followup_audit_20260913.json'
DOC='docs/from_zhongzheng/data-followup-repairs-20260913.md'
BATCHES=[
 ('remaining_prompt_repair_20260913','remaining_glyphs_20260913/plan.json'),
 ('odyssey_visibility_repair_20260913','odyssey_visibility_20260913/plan.json'),
 ('eoes_2025_score_metadata_repair_20260913','eoes_2025_score_metadata_20260913/plan.json'),
 ('iiot_2023_test_recovery_20260913','iiot_2023_test_recovery_20260913/apply_plan.json'),
 ('mystery_2000_packets_repair_20260913','mystery_2000_packets_20260913/plan.json'),
 ('debate_event_year_repair_20260913','debate_event_year_20260913/plan.json'),
 ('eoes_biology_text_repair_20260913','eoes_biology_text_20260913/plan.json'),
 ('iiot_2023_text_repair_20260913','iiot_2023_text_20260913/plan.json'),
 ('mystery_2001_packets_repair_20260913','mystery_2001_packets_20260913/plan.json'),
 ('mystery_numerology_repair_20260913','mystery_numerology_20260913/plan.json'),
 ('mystery_2002_packets_repair_20260913','mystery_2002_packets_20260913/plan.json'),
 ('mystery_2003_static_repair_20260913','mystery_2003_static_20260913/plan.json'),
 ('mystery_2003_pdf_packets_repair_20260913','mystery_2003_pdf_packets_20260913/plan.json'),
 ('mystery_2003_scoped_repair_20260913','mystery_2003_scoped_20260913/plan.json'),
 ('mystery_2004_packets_repair_20260913','mystery_2004_packets_20260913/plan.json'),
 ('iiot_2017_text_repair_20260913','iiot_2017_text_20260913/plan.json'),
 ('iiot_2021_text_repair_20260913','iiot_2021_text_20260913/plan.json'),
 ('iiot_2022_text_repair_20260913','iiot_2022_text_20260913/plan.json'),
 ('mystery_linked_archives_repair_20260913','mystery_linked_archives_20260913/plan.json'),
 ('mystery_2005_static_repair_20260913','mystery_2005_static_20260913/plan.json'),
 ('mystery_2005_media_repair_20260913','mystery_2005_media_20260913/plan.json'),
 ('mystery_2006_static_repair_20260913','mystery_2006_static_20260913/plan.json'),
 ('mystery_2006_media_repair_20260913','mystery_2006_media_20260913/plan.json'),
 ('mystery_2007_static_repair_20260913','mystery_2007_static_20260913/plan.json'),
 ('mystery_2007_media_repair_20260913','mystery_2007_media_20260913/plan.json'),
 ('mystery_2008_dossier_repair_20260913','mystery_2008_dossier_20260913/plan.json'),
 ('mystery_2009_static_repair_20260913','mystery_2009_static_20260913/plan.json'),
 ('mystery_2009_media_repair_20260913','mystery_2009_media_20260913/plan.json'),
 ('mystery_2009_attachments_repair_20260913','mystery_2009_attachments_20260913/plan.json'),
 ('mystery_2010_static_repair_20260913','mystery_2010_static_20260913/plan.json'),
 ('mystery_2010_scoped_repair_20260913','mystery_2010_scoped_20260913/plan.json'),
 ('mystery_2010_media_repair_20260913','mystery_2010_media_20260913/plan.json'),
 ('mystery_2011_static_repair_20260913','mystery_2011_static_20260913/plan.json'),
 ('mystery_2011_attachments_repair_20260913','mystery_2011_attachments_20260913/plan.json'),
 ('mystery_2011_blog_repair_20260913','mystery_2011_blog_20260913/plan.json'),
 ('mystery_2012_static_repair_20260913','mystery_2012_static_20260913/plan.json'),
 ('mystery_2012_media_repair_20260913','mystery_2012_media_20260913/plan.json'),
 ('mystery_2012_scoped_repair_20260913','mystery_2012_scoped_20260913/plan.json'),
 ('mystery_2013_static_repair_20260913','mystery_2013_static_20260913/plan.json'),
 ('mystery_2013_attachments_repair_20260913','mystery_2013_attachments_20260913/plan.json'),
 ('mystery_2013_highlight_repair_20260913','mystery_2013_highlight_20260913/plan.json'),
 ('mystery_2015_static_repair_20260913','mystery_2015_static_20260913/plan.json'),
 ('mystery_2015_media_repair_20260913','mystery_2015_media_20260913/plan.json'),
 ('mystery_2016_static_repair_20260913','mystery_2016_static_20260913/plan.json'),
 ('mystery_2016_pdf_repair_20260913','mystery_2016_pdf_20260913/plan.json'),
 ('mystery_2016_orbits_repair_20260913','mystery_2016_orbits_20260913/plan.json'),
 ('mystery_2016_dog_food_repair_20260913','mystery_2016_dog_food_20260913/plan.json'),
 ('mystery_2016_identify_repair_20260913','mystery_2016_identify_20260913/plan.json'),
 ('eoes_2015_scope_repair_20260913','eoes_2015_scope_20260913/plan.json'),
 ('eoes_2015_worksheets_repair_20260913','eoes_2015_worksheets_20260913/plan.json'),
 ('debate_infoslide_scope_repair_20260913','debate_infoslide_scope_20260913/plan.json'),
 ('debate_header_year_repair_20260913','debate_header_year_20260913/plan.json'),
]
TESTS=ORIGINAL_TESTS+['tests.test_mystery_2015_static_repair','tests.test_mystery_2015_media_repair','tests.test_mystery_2016_static_repair','tests.test_mystery_2016_pdf_repair','tests.test_mystery_2016_orbits_repair','tests.test_mystery_2016_dog_food_repair','tests.test_mystery_2016_identify_repair']+['tests.test_'+n for n in (
 'remaining_prompt_repair','odyssey_visibility_repair','eoes_score_metadata_repair','iiot_test_recovery',
 'mystery_2000_packet_repair','debate_event_year_repair','eoes_biology_text_repair','iiot_2023_text_repair',
 'mystery_2001_packet_repair','mystery_numerology_repair','mystery_2002_packet_repair',
 'mystery_2003_static_repair','mystery_2003_pdf_packet_repair','mystery_2003_scoped_repair','mystery_2004_packet_repair',
 'iiot_2017_text_repair','iiot_2021_text_repair','iiot_2022_text_repair',
 'mystery_linked_archives_repair','mystery_2005_static_repair','mystery_2005_media_repair',
 'mystery_2006_static_repair','mystery_2006_media_repair','mystery_2007_static_repair','mystery_2007_media_repair',
 'mystery_2008_dossier_repair','mystery_2009_static_repair','mystery_2009_media_repair','mystery_2009_attachments_repair',
 'mystery_2010_static_repair','mystery_2010_scoped_repair','mystery_2010_media_repair','mystery_2011_static_repair','mystery_2011_attachments_repair','mystery_2011_blog_repair','mystery_2012_static_repair','mystery_2012_media_repair','mystery_2012_scoped_repair','mystery_2013_static_repair','mystery_2013_attachments_repair','mystery_2013_highlight_repair')]


TESTS += ['tests.test_eoes_2015_scope_repair']
TESTS += ['tests.test_eoes_2015_worksheets_repair']
TESTS += ['tests.test_debate_infoslide_scope_repair']
TESTS += ['tests.test_debate_header_year_repair']


def main():
    data=deepcopy(read(ROOT/'data/.cache/all_data_audit_20260913/after.json'))
    require(not data['issues'],'Structural audit has errors')
    require(not any(r['kind']=='prompt_control_characters' for r in data['review_candidates']),'C0 queue reopened')
    for p,h in data['source_snapshot'].items(): require(sha(ROOT/p)==h,'Audit snapshot is stale: '+p)
    earlier=read(ROOT/'data/benchmarks/all_data_audit_20260913.json')
    for k in ('active_tracks','active_records','status_counts','split_counts','license_counts'):
        require(data[k]==earlier[k],'Unexpected membership/readiness change')
    tasks=set(); batches=[]; backups=set(); original_hashes={}
    for name,plan_name in BATCHES:
        path='data/benchmarks/'+name+'.json'; report=read(ROOT/path)
        require(report.get('status')=='completed','Unfinished repair: '+name)
        backups.add(report['backup'])
        if report.get('newline_recovery_backup'):backups.add(report['newline_recovery_backup'])
        plan=read(ROOT/'data/.cache'/plan_name)
        selected={u['after']['problem_id'] for u in plan.get('updates',[])}
        selected.update(c['task_id'].split('/',1)[1] for c in plan.get('changes',[]) if 'task_id' in c)
        if plan.get('task_id'):selected.add(plan['task_id'].split('/',1)[1])
        if plan.get('after_row'):selected.add(plan['after_row']['problem_id'])
        if report.get('problem_id'):selected.add(report['problem_id'])
        tasks.update(selected)
        for c in plan.get('changes',[]):
            if c.get('source_file') and c.get('source_sha256'):original_hashes[c['source_file']]=c['source_sha256']
        if plan.get('source_file') and plan.get('source_sha256'):original_hashes[plan['source_file']]=plan['source_sha256']
        for u in plan.get('updates',[]):
            for a in u['before'].get('assets',[]):original_hashes[a['path']]=a['sha256']
            rev=u['after'].get('source_review',{})
            if rev.get('original_source_file'):original_hashes[rev['original_source_file']]=rev['original_sha256']
        for p,h in plan.get('protected',{}).items():
            if p.startswith('data/raw/'):original_hashes[p]=h
        batches.append(dict(report=path,sha256=sha(ROOT/path),records=len(selected),task_ids=sorted(selected),backup=report['backup']))
    require(len(tasks)==282,'Unexpected distinct-record count')
    for p,h in original_hashes.items():require(sha(ROOT/p)==h,'Original source changed: '+p)
    latest={}; backed_up=0; archived=[]; manifests=[]
    for backup in sorted(backups):
        path=backup+'/manifest.json'; m=read(ROOT/path)
        # A path may be written repeatedly in one batch; the on-disk backup is
        # its first pre-batch version, not intermediate generated bytes.
        first={}
        for c in m['changed_files']:
            first.setdefault(c['path'],c);latest[c['path']]=c['after_sha256']
        for p,c in first.items():
            if c['before_sha256']:
                require(sha(ROOT/backup/p)==c['before_sha256'],'Backup differs: '+p);backed_up+=1
        for a in m.get('archived',[]):
            require(not (ROOT/a['path']).exists(),'Archived file unexpectedly restored')
            if a.get('sha256'):require(sha(ROOT/a['backup'])==a['sha256'],'Archive differs')
            archived.append(a)
        manifests.append(dict(path=path,sha256=sha(ROOT/path),changed_entries=len(m['changed_files'])))
    for p,h in latest.items():require(sha(ROOT/p)==h,'Latest repair post-hash differs: '+p)
    result=subprocess.run([sys.executable,'-m','unittest',*TESTS,'-q'],cwd=ROOT,text=True,capture_output=True)
    match=re.search(r'Ran (\d+) tests',result.stderr)
    require(result.returncode==0 and match and '\nOK' in result.stderr,'Regression failed: '+result.stdout+result.stderr)
    require(int(match[1])==538,'Unexpected test count')
    mystery=read(ROOT/'data/benchmarks/mystery_hunt/benchmark.json')
    pending_mystery=[r['problem_id'] for r in mystery if not any(a['role']=='agent_visible' for a in r['assets'])]
    reviewed_mystery=[r for r in mystery if r['problem_id'] not in pending_mystery]
    public_mystery_files=sum(a['role']=='agent_visible' for r in reviewed_mystery for a in r['assets'])
    remaining_path='data/benchmarks/remaining_source_review_20260913.json'
    remaining=read(ROOT/remaining_path)
    for p,h in remaining['catalog_snapshot'].items():require(sha(ROOT/p)==h,'Remaining-queue report is stale')
    require(remaining['not_ready_total']==706 and remaining['mystery_hunt']['pending_packets']==len(pending_mystery),'Remaining queue differs')
    mystery_years='、'.join(str(y)+' 年 '+str(sum(r['year']==y for r in reviewed_mystery))+' 条' for y in sorted({r['year'] for r in reviewed_mystery}))
    data.update(outcome='completed_repair_batches_verified_further_source_review_pending',
        previous_snapshot='data/benchmarks/all_data_audit_20260913.json',completed_batches=batches,
        distinct_repaired_records=len(tasks),closed_previous_control_character_cases=8,
        regression=dict(tests=int(match[1]),result='passed',modules=TESTS,output=result.stderr),
        manifest_verification=dict(manifests=manifests,backed_up_files=backed_up,latest_hashes_verified=len(latest),
                                   archived_initial_copies=archived,
                                   note='Historical after-hashes can be superseded by later listed batches. Every available first pre-batch backup and latest post-hash is checked; the documented DebateBench newline recovery is retained.'),
        source_preservation=dict(existing_source_files_rechecked=len(original_hashes),hashes=original_hashes),
        not_ready_counts={t['id']:t['statuses']['not_ready'] for t in data['tracks'] if t['statuses'].get('not_ready')},
        open_work=dict(mystery_hunt_without_reviewed_public_packet=pending_mystery,
                      remaining_source_review=remaining_path,remaining_source_review_sha256=sha(ROOT/remaining_path),
                      source_review_continues=True,
                      local_work_not_declared_externally_blocked=True,
                      grading_and_runtime_recertification_not_performed=True),
        interpretation_limits=earlier['interpretation_limits'])
    store=Store(ROOT);store.save(REPORT,data)
    body=f'''# 数据逐项修复进度与复核（2026-09-13）

这是持续修复过程中的已验证快照，**不是全库修复完成声明**。截至 {data['audited_at_utc']}，本轮 {len(BATCHES)} 批、{len(tasks)} 条不同记录已完成修复；后续源材料核验仍在继续。

## 已完成

| 数据集 | 修复与边界 |
| --- | --- |
| EOES | 6 条题面恢复公式/字体；2025 Task 1、2 官方印刷分项总分分别补为 120、125。另补齐 Task 2 的 Q10、细菌增长公式和词语。仅恢复评分上限，不宣称完整可执行实验评分。 |
| IIOT | 2017、2021、2022、2023 共 31 题完成逐页题面检查，恢复/核对 60 组样例、分数公式、上标和关键图示；2017 一处标题拼写同步修正。原卷的索引矛盾、2022 小数样例与“整数输出”矛盾均保留并标注，不猜测勘误。2023 的 8 题新归档 728 个测试文件、338 对测试，52 个 Cipher 输入别名不重复计数。原始 checker、测试子任务映射和运行限制仍未完整恢复。 |
| Odyssey | 三个示例的初始信息与后续阶段/裁判指引分离；2 份旧公开副本可从备份恢复，原件保留。没有构建阶段运行机制。 |
| Mystery Hunt | {mystery_years}，共 {len(reviewed_mystery)} 条记录恢复显式输入包；{public_mystery_files} 个公开源文件（各题副本分别计数）。补齐关联题页、乐谱、全尺寸图像、城市样式及原 PDF/音频。2004 两道题恢复入口和全部 13 个子页，保留实际是题目正文的 `_answer.html`。2007 `Spin Control` 误存为导航图的同名图片改用官方编号螺旋格，旧图原件保留；从官方索引恢复缺失的四格数独讲义及八页手册。历史事实、特殊符号、Alchemist 原元素表及训练前/后答案变体不擅自现代化或合并。原音频按字节保存并检查帧结构，不宣称试听或语义通过。条件领取讲义、周六追加说明、演员脚本和交餐后线索留在裁判侧；房间出口/meta 子题保留标签，不注入其他题答案或解锁状态。照片任务内部评分与整题答案总分严格区分，未重新认证旧答案、原始分值或端到端评测。 |
| DebateBench | Doxbridge 3 第 3 轮赛事年份由文件名中的 2025 改为 2020；依据同期报道与官方轮次辩题。Astana 第 5 轮官网把族群居住辩题与玩具介绍放在同一轮次卡片，已将背景说明隔离为裁判原件并在公开题包中标注缺口；2 份旧公开副本可恢复。未声称原赛没有背景说明，也不虚构替代内容。文件名、ID、历史分数保留。 |

所有派生题干、资产白名单、隐藏引用及相关分数元数据同步。无新删除的题目或年份；原始材料与历史实验结果不改写。修复清单、原件哈希和可恢复备份见 `{REPORT}` 的 `completed_batches` / `manifest_verification`。

Natolin 5 条记录的赛事年份由 2017 改为 2019，依据主办方的 2019 年活动页面和同期报道，并以原转录前三轮的显式辩题标题交叉确认。主办方页面可由网页阅读器读取，直接下载返回 403，因此保存的是明确标注的阅读核验记录，不冒充原始 HTML；原视频未播放。另从 Natolin 第 1–3 轮转录标题及 Cambridge 第 1 轮开场明确念出的辩题提取四条题面，并以按赛事/轮次排列的独立来源核对。只公开辩题与完整性限制，不公开选手论证、角色标签或历史成绩；背景说明未推断，Natolin 第 4、5 轮和 Cambridge 第 2 轮仍缺独立完整题包。所有记录保持原评测状态。

EOES 2015 的附加讲义按原主卷的发放条件拆分：原第 3、4 页轮廓图作为初始材料，第 1、2 页鉴别图与 Function 表保留在裁判侧；提取件的页面尺寸和渲染像素与原页一致，原件页眉乱码不猜测补写。2 个旧混合阶段公开副本已可恢复归档。该附录不独立赋分，两个 Challenge 1 版本分别记录印刷上限 306、304，Challenge 2 为 306；不将版本总分累加成赛事总分。另恢复 Challenge 2 的三条编号公式及第 13 页 Rf 比值，清理被页面覆盖的文字串。两份原始 27 页参赛者答题纸及 1 页绘图纸逐页查看后补入适用题包；答题纸不是标准答案，不填实验结果。Challenge 1 答题纸 Task A 分项合计 90，与另一主卷版本的 92 不同，明确保留版本限制，不用答题纸覆盖主卷分数。原题的预填数据、空格、TEAM A 水印及一个词典链接原样保留；未跟随该外链，也不推断参赛队伍或完整实验评分。

2008 Dossier 2 的显式 post-meta 剧情留在裁判原件中。2009 年恢复适用于各题的 CSS 背景图、全尺寸链接及原顺序；新增 46 个音频文件、1 个原 FLV、3 个 PDF 共 12 页。音视频仅做完整帧/容器结构检查，未试听、观看或转写。Charity Work 仅恢复首阶段的 32 张原图及指令，校验控件明确置为不可用，不声称完整可玩；Hyperextensions 的 22 个附件保留匿名名称和原字节，不执行、解包或补充文件类型提示。2009 Virtual Sectors 的历史全解锁状态与跨题流程尚未重新界定，仍留在待核验队列。

2010 年的 22 个原 FLV 保留文件头与原元数据，记录原始 filesize 比实际长度多 38 字节的差异，不将容器检查误写为播放认证。2011 年补齐原图、18 个文本附件及 Letter Bank 原 PDF；Stuff Nerd People Like 仅恢复题目明确指定的前 21 篇文章，正文逐篇与原博客比对，后续文章和评论不公开。2012 年恢复 19 个显式输入包，含 2 份 PDF 共 5 页、61 个 MP3、31 个 OGG；音频保留原字节，Ogg 页校验和通过，不宣称试听或两格式语义等价。多层 CSS、全尺寸图片和原站指定字体一并本地化；当前字体服务提供的版本不冒称 2012 年原二进制，随附字体许可也不用于替代题目许可。另将 A Circus Line 误存的总首页修正为官方轮次页面，旧件保留，新源仅在裁判侧，其动态轮次输入仍待界定。Ben Bitdiddle 只恢复原报告、照片和图表，不虚构缺失的实体组件或固件；Betsy Johnson 原信只用于该既有独立信件记录，不提前投放到前置轮次。

2013 年新增 13 个静态题包、244 个公开文件。原 LESS 由同版本 1.3.0 编译器离线转换，字体和图像依赖本地化；不运行题目脚本，不注入其他题答案。保留四个角色的旅行记录、原始日期、虚构信件、密文、空白格及特殊符号。两项原站 404 明确记录：Feynman 题框外装饰图未恢复，保留原灰色回退底色；Get Smart 的另一张失效图只出现在未匹配的样式规则中。没有冒称历史装饰、当前字体版本或动态服务已完全复原。

同年另恢复 Space Monkey Mafia 的 3 页原乐谱，以及 Pulse Pulse Wave Noise 的完整原 ZIP，共 24 个公开文件。16 段 MP3 保持压缩包中的原名、原顺序和原字节；仅在内存中验证 ZIP 校验和与 MPEG 帧，不解包到磁盘、不试听、不转写，也不推测拼接顺序。乐谱 3 页均已渲染查看，空白谱表、音节及调号不补写。

Highlight Reel 修正两个重复目录导致的失效视频链接，保留原 MP4、WebM 及全部 26 段原字幕时间点，新增 19 个公开文件。字幕机械转换为 WebVTT，原视频不转码。两种格式均完成音视频流解码至文件尾；原视频分别为 7,857 与 7,856 帧、约 314 秒，原末段字幕仍保持结束于 319 秒，不补帧、不重定时，也不宣称两格式语义等价。静音、本地文件访问放行的隔离 QA 页面验证了开头、中段与末段字幕可显示；发布题包不自动播放，明确提示普通本地文件浏览器可能需要配套字幕播放器，未宣称完整观看或试听。

2015 年新增 16 个原站题包、377 个公开文件；原图、原字体和 CSS 依赖均已本地化，去除含答案的点击揭示脚本与解答导航。推箱子题的 11 个原 GIF（其中 10 个动画）逐帧解码检查，保持原顺序、时长和字节，不转成静态图。Dory 中的“其他题勘误”是该题线索，只在 Dory 保留，不应用到其他记录。保留彩色格、空白格、特殊符号、刻意错词和完整四张 Hunt-Life 长图。三道 meta 只有提交升级方案的原提示，明确仍缺其他题答案和现场互动；没有因此提高可评测状态。

同年再恢复 3 个附件题包、101 个公开文件：Coins 的 32 张正反面硬币图、合计 72 枚的 16 项数量及显式链接的四条名称文章均保留；`solution-table` 只是原题样式名，不误删。Image 保持原无扩展名附件与原 MD5，不公开转换后的 QA 图或增加格式提示。音乐题的原 MP4、WebM 分别为 78,095,855 与 3,361,618 字节，均完整解码 2,192 帧、约 91 秒及原音轨，不转码、不补字幕、不声称两格式画质或语义相同。隔离的静音 QA 页确认中段原视频能显示，发布题包不自动播放；没有完整观看或试听。

2016 年恢复 9 个静态输入包、200 个公开文件，含原序的 10 张字母格、全尺寸寻物地图与示例、原障碍图和 16,290 × 4,720 像素的数独原图。文字中的下标、箭头、圆点、空位、错词和选项字母保留；超大图仅做字节、尺寸、解码及整体外观检查，不宣称逐格解题验证。四个错误 Bootstrap 字体路径与一个未使用的归档标志路径都有 404 证据，改指同年原站仍存在的对应文件；Google 字体注明当前版本，原美术署名保留。寻物题的队伍规模分档、地图覆盖和现场物品核验规则不转换为新的评分公式，也不虚构实物或主持人交互。

## 全量复查

- 43 个活动赛道、1,720 条记录；结构问题 0，先前 8 条 C0 控制乱码候选已清零。
- {data['unique_files_hashed']:,} 个声明/引用文件路径的哈希检查；{data['declared_pdfs_header_checked']:,} 个 PDF 路径文件头检查。副本分别计数，不是不同原件数，也不等于逐页语义认证。
- `base`、`last_exam` 各 1,720 个实际任务目录与规范数据对齐。
- {int(match[1])} 项相关回归测试通过；{backed_up} 份旧文件备份、{len(latest)} 个最新修改后哈希核验通过。
- 状态不变：ready 661、ready_with_limitations 193、not_ready 706、remote_judge_ready 158、sample_tests_ready 2。
- 同字节公开/裁判资产仍作为复核候选保留：9 条既有 Cybench 输入重复、2 条 Mystery Hunt 2004 原子页与恢复后的公开题页重复。后两条是题目正文的原件溯源副本，不是答案泄漏；不为清零候选而删除原件。

## 尚未完成

逐项证据与需要补充的条件见 [剩余来源复核](remaining-source-review-20260913.md)。该报告记录 Mystery Hunt 15 条初始题包缺口、DebateBench 3 条独立辩题题包缺口及 30 项只读网络检查；区分超时、403/404/410、域名出售与可读取但需要状态隔离的本地源码。没有将全部剩余项目归为外部阻塞，也没有据此宣称无答案或永久失效。

Mystery Hunt 仍有 {len(pending_mystery)} 条未完成显式公开输入包复核，包含可继续修复的本地/公开源材料；不能把它们全部说成外部阻塞。2001 另有原失效图片链接和旧 Windows 程序待核验。Alchemist 的关联元素表已恢复，115 个历史元素页外链仅保留地址与标签，不替换成现代内容；初步队列将 “periodically” 误读为定时发布，现已纠正该无依据判断。2005 两份网格 CSS 仅移除指向失效图片、且实际没有匹配单元格的未使用规则，原 CSS 下载快照保留；现场电影、演出和导览不凭空恢复。DebateBench 未匹配辩题/角色标签、实验与多模态题的来源及评分也仍需逐项检查。

706 条 not_ready 不等于 706 条错误数据或无答案记录。物理实验/机器人、攻防服务、历史现场、私有评分、缺失的 checker/测试分组等不能凭空补造；需要单独的来源恢复或运行/评估适配。所有 split/license 保持原样：1,286 条 split 未指定、1,720 条许可未核验。未运行收费实验、比赛程序或判题服务。

IJSO 2011 已有生物/化学评分材料，物理评分文件仍未恢复；官方及德国赛区档案本次复查未提供该物理答案。保留有效部分，不删除整年。ARML Power Spring 2022 的印刷分项仍只合计 39，而表头为 40；不猜测第 16 题的缺失权重。

旧文档 `all-data-audit-20260913.md` 是此前快照，其中的“8 条待修”已被本轮结果取代。全量结构检查通过不代表所有答案、权重、图表、授权或端到端运行已获认证。
'''
    store.save_text(DOC,body);store.finish(dict(operation='publish_followup_checkpoint',report=REPORT,source_review_still_in_progress=True))
    require(read(ROOT/REPORT)==data,'Report readback differs')
    require((ROOT/DOC).read_text(encoding='utf-8')==body,'Document readback differs')
    print(json.dumps(dict(report=REPORT,records=len(tasks),tests=int(match[1]),pending_mystery=len(pending_mystery),verified_latest_hashes=len(latest)),indent=2))


if __name__=='__main__':main()
