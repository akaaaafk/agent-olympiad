"""Restore fifteen source-reviewed sample tables and 2022 math typography."""
import importlib.util
import json
import sys
from scripts.repair_remaining_prompt_text_20260913 import ROOT,Editor,read,sha,require

CACHE='data/.cache/iiot_2022_text_20260913'
REPORT='data/benchmarks/iiot_2022_text_repair_20260913.json'
SAMPLES={
 1:[('6\n100 90 1\n10 9 2\n90 20 5\n100 80 2\n40 30 3\n100 10 3','80.000000000'),
    ('5\n100 70 1\n10 3 2\n11 3 3\n12 3 1\n10 9 4','72.727272727')],
 2:[('6 6\n2 0 1 1 2 1\n0 2\n1 3\n1 5\n2 4\n2 5\n3 5','3'),('5 3\n0 0 1 2 3\n0 1\n2 1\n3 4','-1')],
 3:[('5\nchocolate\ncoffee\ncookies\npistachio\nstrawberry','1\n2\n1\n2\n3'),
    ('10\norange\npeanutbutter\nmango\nmint\ncheesecacke\ncoconut\noreo\ncherry\npeppermint\nwatermelon','1\n2\n3\n3\n4\n5\n5\n4\n4\n5')],
 4:[('4 4\n1 0\n3 1\n2 3\n2 0','0 1\n1 3\n3 2\n2 0'),
    ('5 7\n0 1\n1 2\n0 3\n3 1\n3 2\n3 4\n4 2','0 1\n1 2\n2 3\n2 4\n3 0\n3 1\n4 3')],
 5:[('7\n3 5 3 0 3 2 2','4'),('5\n1 1 5 5 5','4')],
 6:[('3 127\n48 60\n48 62\n96 64\n48 60\n48 62\n96 64','SAME'),
    ('6 127\n48 60\n48 62\n48 64\n96 60\n48 62\n96 64\n48 60\n48 62\n96 64\n48 60\n48 62\n96 64','ORIGINAL 2'),
    ('7 127\n48 60\n48 62\n48 64\n96 60\n48 62\n48 64\n96 60\n48 60\n24 67\n48 65\n24 69\n24 67\n48 64\n96 60','TRANSFORMED 4')],
 7:[('2 3\n5 3 6 2 5 4\n8 6 7 6 6 5','1.2'),('3 3\n5 3 6 2 5 4\n8 6 7 6 6 5\n14 13 15 14 11 9','2.6')]
}
# Header then subtasks; orange/grey colors are not score weights.
BOOKS={1:[4,1,1,2,3,4,4,4],2:[3,1,3,3,3,3],3:[5,1,2,2,2,5],
       4:[3,1,3,2,1],5:[4,1,1,2,2,4,4],6:[1,1,2,1,3,1,2],7:[3,1,2,3,3]}
PAGES={n:3 if n<7 else 2 for n in range(1,8)}


def repair(number,text):
    e=Editor(text)
    e.rep('III ((( OOO TTT +++ III ))) ;;;','[IIOT logo]')
    icon='ὖ∠'*5
    require(e.text.count(icon)==len(BOOKS[number]),'Indicator count drift')
    for orange in BOOKS[number]:
        after=f'[book indicator: {orange} orange, {5-orange} grey]'
        e.text=e.text.replace(icon,after,1);e.changes.append(dict(before=icon,after=after))
    examples='\n\nExamples\n\n'+'\n\n'.join(f'Sample {i} input:\n```text\n{a}\n```\n\nSample {i} output:\n```text\n{b}\n```' for i,(a,b) in enumerate(SAMPLES[number],1))+'\n\n'
    e.rx(r'Examples input output .*?(?=Explanation)',examples)
    if number==1:
        e.rep('100 ( 1− Pdiscount Ptot )','100 (1 − P_discount / P_tot)')
        e.rep('100 ( 1− 40 200 )','100 (1 − 40/200)')
        e.rep('100 ( 1− 9 33 )','100 (1 − 9/33)')
        e.rep('10−6','10^−6')
    elif number==2:
        e.rep('Ai̸= Bi','Ai ≠ Bi')
        e.rep('0 1 2 34 52 0 1 12 1 Figure 2:',
              '[Graph: vertices 0,1,2,3,4,5 have colors 2,0,1,1,2,1 respectively; undirected edges are 0–2, 1–3, 1–5, 2–4, 2–5, 3–5.] Figure 2:')
        e.rep('0 1 2 3 4 0 0 1 2 3 Figure 3:',
              '[Graph: vertices 0,1,2,3,4 have colors 0,0,1,2,3 respectively; undirected edges are 0–1, 2–1, 3–4.] Figure 3:')
    elif number==3:
        e.rep('chocolate choco • k = 2','[Cup choco: chocolate.] • k = 2')
        e.rep('chocolate choco coffee coffee • k = 3','[Cup choco: chocolate. Cup coffee: coffee.] • k = 3')
        e.rep('cookies coffee chocolate c • k = 4','[Cup c: cookies, coffee, chocolate.] • k = 4')
        e.rep('cookies coffee chocolate c pistachio pi • k = 5','[Cup c: cookies, coffee, chocolate. Cup pi: pistachio.] • k = 5')
        e.rep('cookies coffee chocolate c pistachio pi strawberry straw','[Cup c: cookies, coffee, chocolate. Cup pi: pistachio. Cup straw: strawberry.]')
        e.text+='\n\nSource note: the flavour string "cheesecacke" is spelled that way in the published second sample; it has not been corrected to a different input.'
    elif number==4:
        e.rep('Ai̸= Bi','Ai ≠ Bi')
        e.rep('sample case: 0 1 3 2','sample case: [Directed cycle in the diagram: 0 → 1 → 3 → 2 → 0.]')
    elif number==5:
        e.rep('3 5 3 0 3 2 2 picnic Page 14','[Diagram heights, left to right: 3,5,3,0,3,2,2; the horizontal table is at height 3. The original placement drawing remains in the source PDF.] picnic Page 14')
        e.rep('1 1 5 5 5 picnic Page 15','[Diagram heights, left to right: 1,1,5,5,5; the horizontal table is at height 5. The original placement drawing remains in the source PDF.] picnic Page 15')
    elif number==6:e.rep('V ≤ 109','V ≤ 10^9')
    elif number==7:
        e.rep('10−6','10^−6')
        e.rep('Day Buy[A] Sell[A] Buy[F] Sell[F] Buy[G] Sell[G] 1 5 3 6 2 5 4 2 8 6 7 6 6 5',
              '\n```text\nDay Buy[A] Sell[A] Buy[F] Sell[F] Buy[G] Sell[G]\n1   5      3       6      2       5      4\n2   8      6       7      6       6      5\n```\n')
        for a,b in [('1 .20','1.20'),('0 .1714285714','0.1714285714'),('2 .40','2.40'),('2 .60','2.60')]:e.rep(a,b)
        e.text+='\n\nSource note: the printed Output paragraph says "integer", but the same source specifies floating-point tolerance and publishes outputs 1.2 and 2.6. This source inconsistency is retained and flagged; no unpublished erratum or integer-only judging rule is assumed.'
    require('ὖ∠' not in e.text,'Unreviewed indicator remains')
    return e


def writer():
    spec=importlib.util.spec_from_file_location('_iiot_2022_private_writer',ROOT/'scripts/repair_iiot_2023_text_20260913.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.YEAR=2022;m.CACHE=CACHE;m.REPORT=REPORT;m.EXPECTED_RECORDS=7;m.REVIEWED_PAGES={n:list(range(1,c+1)) for n,c in PAGES.items()};m.SAMPLES=SAMPLES;m.repair=repair
    return m


if __name__=='__main__':
    mode=sys.argv[1];m=writer()
    if mode=='prepare':m.prepare()
    elif mode=='apply':m.apply()
    elif mode=='verify':print(json.dumps(m.verify(read(ROOT/CACHE/'plan.json'))))
    else:raise ValueError(mode)
