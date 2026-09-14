[IOI in Teams logo] IOI in Teams 2017 Bologna, May 17-20th 2017 proxies •EN Masters and Slaves ( proxies) Figure 1: William connecting a newly-recycled proxy. William has ﬁnally solved the nasty “L/10-L/16-bipasso” problem, and is now ready to start earning money im- mediately! For this noble purpose, he arranged hisN fully functional comput- ers (numbered from0 to N−1) into a tree-shaped network rooted at server0, so that computer i is a “slave” of com- puter Mi (conventionally, we assume that M0 =−1). Now the most demand- ing tasks from all over the world are be- ing delivered to his farm, and will even- tually be completed (hopefully)! Sadly, some of his computers are already experiencing severe heating problems, not being able to handle the output of all of their slaves. Since the recycling bin for electronic waste is always ﬁlling up, William can promptly solve this emergencies throughproxying: when some computers are overheating, William selects K of their slaves S0, . . . , SK−1 and delegates those to a newly-recycled proxy. Afterwards, the proxy is connected to another computerC. 
[Graph transcription: arrows point from a slave to its master; parent arrays list nodes in ascending ID order, with −1 for the root.]
Before: [-1,0,0,2,2,2,2,1]. After adding node 8: [-1,0,0,2,2,8,8,8,2].
In this case, computers 1 and 2 are overheating (left) thus William delegates K = 3 of their slaves (computers 5, 6, and 7) to the new proxy 8, connecting it to computer C = 2. Even though this reconﬁguration can solve the overheating problem, William is worried that the tree structure would grow too high,1 slowing down the computations. What is worse, a wrong reconﬁguration could even create a cycle2 causing an inﬁnite data ﬂow! Given a sequence ofE reconﬁgurations, help William keep track of the situation by determining whether each emergency causes the height to increase or, even worse, creates a cycle. Among the attachments of this task you may ﬁnd a template ﬁleproxies.* with a sample incomplete implementation. 1The height of a rooted tree is measured as the maximum number of links that are necessary to reach the root from a node: the sample graphs have height 2 (left) and 3 (right). 2A cycle is a circular sequence of computer, where each of them is a slave of the next. proxies Page 12 of 17

[IOI in Teams logo] IOI in Teams 2017 Bologna, May 17-20th 2017 proxies •EN Input The ﬁrst line contains integersN, E. The second line contains integersM0, M1, . . . , MN −1. Each of the following E lines contains integersC, K followed on the same line by integersS0, S1, . . . , SK−1. Output You need to write a single line with a sequence of characters, such that thei-th character is: •‘c’: if the i-th reconﬁguration creates a cycle; •‘1’: if the i-th reconﬁguration causes the tree height to increase; •‘0’: if the i-th reconﬁguration does not cause the tree height to increase. You need to output a characteruntil either a cycle is created or the reconﬁgurations are ﬁnished. In other words, the sequence can either consist ofE characters among‘0’and ‘1’or less thanE characters among ‘0’and ‘1’followed by a single‘c’. Constraints •1≤N≤1 000 000. •1≤E≤10 000. •0≤C, Si, Mi < N for each i = 1 . . . N−1, M0 =−1. •0≤K≤100 in each emergency. •The master/slave structure forms a tree (there are no circular links). •The height of the tree never grows above100. Scoring Your program will be tested against several test cases grouped in subtasks. In order to obtain the score of a subtask, your program needs to correctly solve all of its test cases. •Subtask 1 [ 5 points]: Examples. •Subtask 2 [25 points]: N, E≤10. •Subtask 3 [30 points]: N≤1000. •Subtask 4 [20 points]: Si’s master isC, for eachi and reconﬁguration. •Subtask 5 [20 points]: No additional limitations. proxies Page 13 of 17

[IOI in Teams logo] IOI in Teams 2017 Bologna, May 17-20th 2017 proxies •EN 

Examples

Sample 1 input:
```text
3 5
-1 0 0
0 2 1 2
3 0
2 2 4 3
1 1 0
6 5 4 2 3 1 5
```

Sample 1 output:
```text
10c
```

Sample 2 input:
```text
8 4
-1 0 0 2 2 2 2 1
2 3 5 6 7
2 2 5 4
8 2 6 7
1 0
```

Sample 2 output:
```text
1010
```

Explanation In theﬁrst sample case, the network structure evolves as follows: 
[Sample 1 diagram sequence, slave-to-master parent arrays:]
Initial: [-1,0,0]. Step 1: [-1,3,3,0]. Step 2: [-1,3,3,0,3]. Step 3: [-1,3,3,5,5,2], showing the directed cycle 2→3→5→2.
 After the third reconﬁguration, a cycle is detected hence the following reconﬁgurations do not take place. proxies Page 14 of 17

[IOI in Teams logo] IOI in Teams 2017 Bologna, May 17-20th 2017 proxies •EN The second sample casecorresponds to the structure described in the text, which evolves as follows: 
[Sample 2 diagram sequence, slave-to-master parent arrays:]
Initial: [-1,0,0,2,2,2,2,1].
Step 1: [-1,0,0,2,2,8,8,8,2].
Step 2: [-1,0,0,2,9,9,8,8,2,2].
Step 3: [-1,0,0,2,9,9,10,10,2,2,8].
Step 4: [-1,0,0,2,9,9,10,10,2,2,8,1].
 proxies Page 15 of 17
