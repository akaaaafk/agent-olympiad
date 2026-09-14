"""Restore the remaining 2021 layouts, exponents and observed book colors."""
import importlib.util
import json
import sys
from scripts.repair_remaining_prompt_text_20260913 import ROOT,Editor,read,sha,require

CACHE='data/.cache/iiot_2021_text_20260913'
REPORT='data/benchmarks/iiot_2021_text_repair_20260913.json'
SAMPLES={
 1:[('2\n4 5 4\n3 4 7','1\n2\n1 0'),('3\n4 5 4\n3 4 7\n1 4 10','2\n2\n1 0\n1\n2')],
 2:[('4 4\naabb\na\nb\nbb\nab','3'),('4 4\naabb\na\nab\naa\naba','0')],
 3:[('5\n2 1 3 5 10','4'),('6\n2 7 3 8 4 7','4')],
 4:[('3 11\n2 4 10','21'),('3 101\n49 50 51','152')],
 5:[('5 2\n3 10\n4 1\n3 5\n-1 20\n3 2','5'),('7 2\n1 10\n-1 1\n3 10\n1 3\n1 7\n0 7\n5 9','14')],
 6:[('4 9\n11 oh sfera sk sk skuh marseille milano oh oui bang bang\n7 sfera ebbasta oh come un bang oh\n4 amo milano oh sfera\n5 sfera ti bang bang ebbasta','2 3 0 0 0 0 1 2 0 2 2'),
    ('5 7\n14 che vi che mi avolta che qui dale merale merale dale avolta merale che\n6 mi nisti nisti nisti mi mi\n11 mi avolta che cele mi dale avolta cele dale cele mi\n7 dale merale che che merale mi cele\n8 merale merale cele avolta che dale avolta che','3 0 3 3 2 3 0 3 2 2 3 2 2 3')],
 7:[('4 3\n0 1 10\n0 1 5\n0 2 2\n1 2 4','12\n7\n6\n6'),('3 4\n0 1 1\n0 2 2\n0 3 3','6\n6\n6')],
 8:[('1 4','1'),('2 8','4')]
}
BOOKS={1:[4,1,3,4,4,4,4],2:[5,1,2,1,3,3,5],3:[4,1,1,1,2,4],4:[3,1,2,2,3,3],
       5:[4,1,3,3,4,4,4],6:[2,1,1,2,2,2,2],7:[4,1,1,1,2,4,4,4],8:[2,1,1,2,2,2,2,2]}
PAGES={1:3,2:2,3:2,4:2,5:3,6:2,7:3,8:2}


def repair(number,text):
    e=Editor(text)
    if number!=5:e.rep('III ((( OOO TTT +++ III ))) ;;;','[IIOT logo]')
    icon='[five-book difficulty indicator; see original colors]' if number==5 else 'ὖE'*5
    require(e.text.count(icon)==len(BOOKS[number]),'Indicator count drift')
    for orange in BOOKS[number]:
        after=f'[book indicator: {orange} orange, {5-orange} grey]';e.text=e.text.replace(icon,after,1);e.changes.append(dict(before=icon,after=after))
    if number!=5:
        examples='\n\nExamples\n\n'+'\n\n'.join(f'Sample {i} input:\n```text\n{a}\n```\n\nSample {i} output:\n```text\n{b}\n```' for i,(a,b) in enumerate(SAMPLES[number],1))+'\n\n'
        # Two tables precede the next page's explanation heading. The intervening
        # bundled-page footer is not an input row and stays in the source PDF.
        pattern=r'Examples input output .*?(?=Explanation)'
        e.rx(pattern,examples)
    if number==1:
        e.rep('Li≤109','Li≤10^9');e.rep('or Sout Sref otherwise','or S_out / S_ref otherwise')
        e.rep('A B L By combining','[Pipe diagram: smaller end diameter A, larger end diameter B, axial length L.] By combining')
        e.text+='\n\n[Example diagrams: sample 1 has part 1 at the bottom and part 0 at the top; sample 2 shows the same assembly alongside the standalone part 2. These are the published example constructions, not a uniqueness claim.]'
    elif number==2:
        e.rep('Ai̸= Aj for each i̸= j','Ai ≠ Aj for each i ≠ j')
        e.rep('Y→a e →ab s →bc ! →c N →aa o →bb ? →cc','\n```text\nY -> a\ne -> ab\ns -> bc\n! -> c\nN -> aa\no -> bb\n? -> cc\n```\n')
    elif number==3:e.rep('Di≤109','Di≤10^9')
    elif number==4:
        e.rep('M≤108','M≤10^8')
        e.rep('2 1 3 0 3 7 3 5 8 7 4 Figure 1:', '[Figure 1 array, zero-based positions: 2,1,3,0,3,7,3,5,8,7,4; position 4 is shaded.] Figure 1:')
        e.rep('1 0 2 3 3 7 3 5 7 4 8 Figure 2:', '[Figure 2 array, zero-based positions: 1,0,2,3,3,7,3,5,7,4,8; positions 2,4,10 are shaded.] Figure 2:')
    elif number==7:
        e.rep('Ai̸= Bi','Ai ≠ Bi');e.rep('Ti≤109','Ti≤10^9')
    elif number==8:e.rep('for holding x2','for holding x^2')
    require('ὖE' not in e.text,'Unreviewed indicator remains')
    return e


def writer():
    # Isolated module globals: do not mutate the frozen 2023 repair/test module.
    spec=importlib.util.spec_from_file_location('_iiot_2021_private_writer',ROOT/'scripts/repair_iiot_2023_text_20260913.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.YEAR=2021;m.CACHE=CACHE;m.REPORT=REPORT;m.EXPECTED_RECORDS=8;m.REVIEWED_PAGES={n:list(range(1,c+1)) for n,c in PAGES.items()};m.SAMPLES=SAMPLES;m.repair=repair
    return m


if __name__=='__main__':
    mode=sys.argv[1];m=writer()
    if mode=='prepare':m.prepare()
    elif mode=='apply':m.apply()
    elif mode=='verify':print(json.dumps(m.verify(read(ROOT/CACHE/'plan.json'))))
    else:raise ValueError(mode)
