[IIOT logo] IIOT2023 – International Final [book indicator: 3 orange, 2 grey] Port Said, Egypt, May 26th to May 30th, 2023 tourdetree •EN Tour de Treeland ( tourdetree) In the distant future the organizers of Tour de France have relocated the competition to Treeland. Treeland consists ofN cities, numbered from 1 to N, and N−1 bidirectional roads numbered from1 to N−1. Road i connects city ai to city bi and has length ci. It’s possible to reach every city from every other city using these roads. Due to strange socio-economical factors the cities with only one road adjacent to them have becomemetropolises. The rules of the competition are the following: 1. The cyclists start from ametropolis chosen by the organizers. 2. They visit all cities using the roads in some way. They may visit the same city and use the same road multiple times. 3. They ﬁnish in ametropolis chosen by the organizers. The organizers chooseK metropolises, where K is either 1 or 2. If K = 1, then the chosen metropolis is used to start as well as to ﬁnish the race. IfK = 2, then two diﬀerent metropolises are chosen, one of them serving as the start, the other as the ﬁnish of the race. Given the map of Treeland and the value ofK, what is the minimum total length of the roads the cyclists have to cycle through from start to ﬁnish, if both the organizers and the cyclists want to minimize this sum? Among the attachments of this task you may ﬁnd a template ﬁletourdetree.* with a sample incomplete implementation. Input The ﬁrst line contains two integersN and K. The next N−1 lines contains three integers each, the numbers ai, bi and ci for road i. Output You need to write a single line with an integer: the minimal sum of road lengths that the cyclists need to traverse. tourdetree Page 1 of 2

Constraints • 2≤N≤100 000. • 1≤K≤2. • 1≤ai ≠ bi≤N for each i = 1 . . . N−1. • 1≤ci≤1 000 000 000for each i = 1 . . . N−1. Scoring Your program will be tested against several test cases grouped in subtasks. In order to obtain the score of a subtask, your program needs to correctly solve all of its test cases. –Subtask 1(0 points) [book indicator: 1 orange, 4 grey] Examples. –Subtask 2(20 points) [book indicator: 2 orange, 3 grey] N≤300 and ci≤10^6. –Subtask 3(30 points) [book indicator: 2 orange, 3 grey] N≤2000 and ci≤10^6. –Subtask 4(50 points) [book indicator: 3 orange, 2 grey] No additional limitations. 

Examples

Sample 1 input:
```text
3 1
1 2 4
2 3 5
```

Sample 1 output:
```text
18
```

Sample 2 input:
```text
4 2
1 2 10
2 3 10
2 4 11
```

Sample 2 output:
```text
41
```

Explanation In theﬁrst sample casethe value ofK is 1. Choosing the metropolis with index1 results in the cyclists taking the path1→2→3→2→1 which has a length of4 + 5 + 5 + 4 = 18 . In thesecond sample caseK = 2, and it is optimal to choose metropolises1 and 4. tourdetree Page 2 of 2
