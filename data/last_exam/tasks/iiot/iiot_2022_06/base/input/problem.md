[IIOT logo] International Informatics Olympiads in Teams [book indicator: 1 orange, 4 grey] Bologna, May 19th, 2022 plagiarism • EN Plagiarism Detection ( plagiarism) Giorgio is pursuing a career as a singer-songwriter! However, the music world is tough, and you always need to watch out for plagiarism. In fact, the last song that Alessandro wrote sounds suspiciously similar to one of Giorgio’s songs, and now Giorgio wants to prove Alessandro’s mischief. Figure 1: Giorgio writing a new song. Both Giorgio’s and Alessandro’s songs areN notes long. Each note1 is encoded by two integers between 0 and V: its durationdi, followed by its pitchpi. Each song is then encoded as a sequence of2N integers. Of course, the plagiarism case will be uncontroversial if the two songs are identical. If not, the plagiarism case will be stronger if Giorgio can find ashort contiguous sequence of notes that needs to be modified to transform Giorgio’s song into Alessandro’s. For such a sequence, if possible, it would be better for Giorgio if he can prove that applyingsome of these classical tune transformations transforms his song into Alessandro’s: • Transposition: increase or decrease every pitch in the sequence by the same amount; • Doubling (resp. halving): double (resp, halve) every duration in the sequence; • Retrogradation: invert the sequence of notes, playing them from the last one to the first. Note that each operation can be used at most once. Help Giorgio file his claim on Alessandro’s mischief as strongly as possible by finding the shortest sequence to change! 1In the MINI (Musical Instrument Note Information) format. plagiarism Page 16 of 20

☞ Among the attachments of this task you may find a template fileplagiarism.* with a sample incomplete implementation. Input The first line contains the two integersN and V. The next N lines contain two integers each (di and pi) describing Giorgio’s song. The next N lines contain two integers each (di and pi) describing Alessandro’s song. Output You need to write a single line with one of the following contents: • “SAME”: if the two songs are identical; • “TRANSFORMED L”: if Alessandro’s song can be obtained by modifying a sequence of lengthL using some of the operations described above; • “ORIGINAL L”: there is a sequence of length L that cannot be obtained just by applying the operations described above. Constraints • 1≤ N≤ 100 000. • 1≤ V ≤ 10^9. • 0≤ di, pi≤ V for each i = 0 . . . N− 1 for both songs. Scoring Your program will be tested against several test cases grouped in subtasks. In order to obtain the score of a subtask, your program needs to correctly solve all of its test cases. – Subtask 1(0 points) [book indicator: 1 orange, 4 grey] Examples. – Subtask 2(20 points) [book indicator: 2 orange, 3 grey] N, V ≤ 500. – Subtask 3(15 points) [book indicator: 1 orange, 4 grey] N≤ 500. – Subtask 4(25 points) [book indicator: 3 orange, 2 grey] N, V ≤ 10 000. – Subtask 5(10 points) [book indicator: 1 orange, 4 grey] V ≤ 10 000. – Subtask 6(30 points) [book indicator: 2 orange, 3 grey] No additional limitations. plagiarism Page 17 of 20



Examples

Sample 1 input:
```text
3 127
48 60
48 62
96 64
48 60
48 62
96 64
```

Sample 1 output:
```text
SAME
```

Sample 2 input:
```text
6 127
48 60
48 62
48 64
96 60
48 62
96 64
48 60
48 62
96 64
48 60
48 62
96 64
```

Sample 2 output:
```text
ORIGINAL 2
```

Sample 3 input:
```text
7 127
48 60
48 62
48 64
96 60
48 62
48 64
96 60
48 60
24 67
48 65
24 69
24 67
48 64
96 60
```

Sample 3 output:
```text
TRANSFORMED 4
```

Explanation In thefirst sample case, the two songs are identical. In thesecond sample case, Alessandro’s song is obtained by rewriting the third and fourth notes48 64, 96 60 into 96 64 , 48 60 , leaving the rest unchanged. Note that this isnot obtainable through a combination of some classical tune transformations. In thethird sample case, Alessandro’s song can be obtained by transforming the sequence from the second note to the fifth, by applying halving, retrogradation and then a+5 transposition. plagiarism Page 18 of 20
