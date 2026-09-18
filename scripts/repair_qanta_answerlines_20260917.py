"""Separate reviewed QANTA answerlines from annotations; no runtime fuzzy matching."""
from copy import deepcopy
import json, re, sys, os, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from contest_adapters import _grade_non_programming
from types import SimpleNamespace

# Explicit, unconditional alternatives in the archived answerlines. Timing-bound
# acceptances and prompt-only answers are not unconditional aliases in a full-question task.
ALIASES={
14673:['Effects of Good Government in the City','Effects of Bad Government in the City','Effects of Good Government in the Country','Effects of Bad Government in the Country'],
39387:['Doppler shift'],40825:['Neftalí Ricardo Reyes Basoalto'],142651:['Chicago Eight'],
52404:['virgin','virginity','chastity','chaste'],83383:['pyrexia'],89751:['The Mystic Nativity'],
96580:['Reino de España'],161416:['n-body problem'],161577:['ethanoic acid','acetate'],
46879:['refractive index'],49460:['El hacedor','The Maker'],102045:['Pablo Ruiz y Picasso'],
149935:['Igor Fyodorovich Stravinsky'],150473:['S'],
102465:['Karl der Grosse','Carolus Magnus','Charles the Great','Charles I of France'],
133321:['The Road'],135326:['Cymraeg'],136247:['Ximénez'],
144532:['Doña Rosita la Soltera, o el Lenguaje de las Flores'],
126475:['United Republic of Tanzania','Jamhuri ya Muungano wa Tanzania'],128424:['Chayka'],129066:['RA'],
146818:['Zhongguo ́','Zhonghua ́ Re ́nmin Go`nghe ́guo ́','PRC'],
147291:['United States Virgin Islands','British Virgin Islands'],
122944:['James Augustine Aloysius Joyce'],123034:['Myrddin Emrys'],125688:['Tristan and Isolde'],
112719:['Walzer','valses','Valses nobles et sentimentales','Minute Waltz'],
114201:['Regno d’Italia'],114391:['300s A.D.'],121863:['Thomas Stearns Eliot'],
105981:['stretch','mechanoreception'],106095:['Wu–Yang monopoles','Dirac monopoles'],
106447:['arctic tundra','alpine tundra','antarctic tundra'],
106504:['radio astronomy','radio emissions','radio galaxies'],108623:['Lorraine Vivian Hansberry'],
108704:['Zhongguo'],112933:['Patriotic War of 1812','invasion of Russia','Second Polish War'],
113215:['Kingdom of Morocco','al-Mamlaka al-Maghribia'],106595:['Mirza Asadullah Baig Khan'],
106607:['Maxim Dmitriyevich Shostakovich','Maksim'],
106769:['illusory body','magic','unreality','untruth','māhākāyā'],
107061:['electric potential','scalar potential','electric scalar potential','voltage difference','electric potential difference','scalar potential difference','electric scalar potential difference'],
107843:['extinction event'],
}
REJECT={39387:['red shift','blue shift'],83383:['hyperthermia'],161577:['CH3COOH','CH3COO-'],
101623:['As'],101808:['plates'],102465:['Charles'],147291:['Leeward Islands','Lesser Antilles'],
116237:['music','singing'],105981:['pressure'],106607:['Shostakovich','M. Shostakovich'],
106769:['māyā','gyulu','dream','delusion'],107061:['vector potential','V','phi'],107843:['asteroid impact']}
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def grade(row,answer):
 return _grade_non_programming(SimpleNamespace(benchmark=row,task_type=row['task_type'],question_id=None,max_score=1),answer,'qanta')
def main():
 originals={};staged={};source_cache={};review=[]
 def get(p):
  originals.setdefault(p,p.read_bytes());return json.loads(originals[p])
 def put(p,d):staged[p]=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 bp=ROOT/'data/benchmarks/qanta/benchmark.json';rows=get(bp);before=deepcopy(rows)
 for r in rows:
  pid=r['problem_id'];qid=int(pid.rsplit('_',1)[1]);part=r['gold_label']['parts'][0]
  if r.get('provenance',{}).get('answerline_review'):
   review.append({'id':pid,'expected':part['expected'],'aliases':part['aliases'],'original':r['provenance']['answerline_review']['original_answerline']})
   continue
  if not re.search(r'\[|\(|&lt;',part['expected']):continue
  source=ROOT/r['source_file']
  if source not in source_cache:source_cache[source]={x['qanta_id']:x for x in read(source)['questions']}
  raw=source_cache[source][qid]['answer']
  assert raw.strip()==part['expected'],pid
  primary=re.split(r'\[|\(|&lt;',raw)[0].strip().replace('{','').replace('}','')
  # Reversible UTF-8-as-Latin-1 corruption in the archived name, not a new answer.
  if qid==144532:primary=primary.replace('DoÃ±a','Doña')
  aliases=ALIASES.get(qid,[])
  r['gold_label']['expected_answer']=primary
  part.update(expected=primary,aliases=aliases,reference='Reviewed primary answer and explicit unconditional alternatives; original annotation retained in provenance.')
  r['provenance']['answerline_review']={
   'reviewed_at':'2026-09-17','source_file':r['source_file'],'qanta_id':qid,'original_answerline':raw,
   'policy':'Full-question final-answer evaluation. Explicit unconditional alternatives only; prompt-only and before-clue acceptances are not silently accepted. Open-ended equivalence is not automatically implemented.',
   'encoding_repair':'DoÃ±a -> Doña (UTF-8 mojibake)' if qid==144532 else None}
  review.append({'id':pid,'expected':primary,'aliases':aliases,'original':raw})
 assert len(review) in (0,62),len(review)
 if not review:print('Already repaired');return
 for old,new in zip(before,rows):
  # Participant inputs, membership, scoring weights and runtime settings remain untouched.
  assert {k:v for k,v in old.items() if k not in ('gold_label','provenance')}=={k:v for k,v in new.items() if k not in ('gold_label','provenance')}
 put(bp,rows)
 changes={r['problem_id']:r for r in rows if r['problem_id'] in {x['id'] for x in review}}
 mini=ROOT/'data/mini_data/benchmarks/qanta/benchmark.json';mr=get(mini);mini_changed=[]
 for r in mr:
  if r['problem_id'] not in changes:continue
  mainrow=changes[r['problem_id']];r['gold_label']=deepcopy(mainrow['gold_label'])
  r['provenance']['answerline_review']=deepcopy(mainrow['provenance']['answerline_review'])
  r['provenance']['answerline_review']['source_file']=r['source_file'];mini_changed.append(r['problem_id'])
 if mini_changed:put(mini,mr)
 # Curated mappings must not restore the old annotated string on regeneration.
 for base in ['data','data/mini_data']:
  p=ROOT/base/'rubrics/qanta_short_answers.json';mapping=get(p)
  for r in rows:
   pid=r['problem_id']
   if pid in mapping:
    mapping[pid]['1'].update(expected=r['gold_label']['parts'][0]['expected'],aliases=r['gold_label']['parts'][0]['aliases'])
  put(p,mapping)
 checks=0
 for r in rows:
  p=r['gold_label']['parts'][0]
  for answer in [p['expected'],*p.get('aliases',[])]:assert grade(r,answer)==(1.,1.),(r['problem_id'],answer);checks+=1
  for answer in ['', 'THIS_IS_NOT_A_CORRECT_QANTA_ANSWER',*REJECT.get(int(r['problem_id'].rsplit('_',1)[1]),[])]:assert grade(r,answer)==(0.,1.),(r['problem_id'],answer);checks+=1
 # Refresh dependency metadata only for mini files actually changed.
 dep=ROOT/'data/mini_data/dependency_manifest.json';d=get(dep)
 for p,blob in list(staged.items()):
  if p.is_relative_to(ROOT/'data/mini_data'):
   rel=p.relative_to(ROOT/'data/mini_data').as_posix();src=ROOT/'data'/rel
   if rel in d['files']:
    d['files'][rel]['source_sha256']=hashlib.sha256(staged.get(src,src.read_bytes())).hexdigest()
    d['files'][rel]['mini_sha256']=hashlib.sha256(blob).hexdigest()
 put(dep,d)
 for p in staged:assert p.read_bytes()==originals[p],f'Concurrent edit: {p}'
 for p,blob in staged.items():
  if blob==originals[p]:continue
  temp=p.with_name(p.name+'.qanta-tmp');temp.write_bytes(blob);os.replace(temp,p)
 assert read(bp)==rows and read(mini)==mr
 report={'changed_main':len(review),'changed_mini':mini_changed,'grading_checks':checks,'records':review,'last_exam_touched':False,'paid_calls':0}
 out=ROOT/'tmp/qanta_answerline_repair_20260917.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False))
if __name__=='__main__':main()
