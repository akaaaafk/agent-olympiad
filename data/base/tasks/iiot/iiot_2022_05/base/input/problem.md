[IIOT logo] International Informatics Olympiads in Teams [book indicator: 4 orange, 1 grey] Bologna, May 19th, 2022 picnic • EN Picnic’s Table ( picnic) Filippo is organizing a picnic with his friends, and he is planning where to go. He really likes the park next to his house, but the ground is so bumpy he needs to inspect it carefully for finding the best place. The park is a narrow strip of land of negligible width, and Filippo measured the heightHi of N points one meter apart. He wants to buy a long table to place on the ground, such thatit lays completely horizontal and isheld by at least two pointson the floor. In order to be stable enough, the table should rest on at least one point strictly before the middle of the table, and at least one point strictly after the middle of the table. In particular, the table should start at an integer coordinate and end at an integer coordinate. Furthermore, the table cannot extend past the start or the end of the park. How long is the longest table Filippo can use? ☞ Among the attachments of this task you may find a template filepicnic.* with a sample incomplete implementation. Input The first line contains the only integerN. The second line containsN integers Hi. Output You need to write a single line with an integer: the length of the longest table Filippo can use. Constraints • 2≤ N≤ 10 000 000. • 0≤ Hi≤ 1 000 000 000for each i = 0 . . . N− 1. • It is guaranteed that a solution exists. picnic Page 13 of 20

Scoring Your program will be tested against several test cases grouped in subtasks. In order to obtain the score of a subtask, your program needs to correctly solve all of its test cases. – Subtask 1(0 points) [book indicator: 1 orange, 4 grey] Examples. – Subtask 2(10 points) [book indicator: 1 orange, 4 grey] Hi≤ 1 for each i = 0 . . . N− 1. – Subtask 3(15 points) [book indicator: 2 orange, 3 grey] N≤ 100. – Subtask 4(15 points) [book indicator: 2 orange, 3 grey] N≤ 5000. – Subtask 5(25 points) [book indicator: 4 orange, 1 grey] N≤ 100 000. – Subtask 6(35 points) [book indicator: 4 orange, 1 grey] No additional limitations. 

Examples

Sample 1 input:
```text
7
3 5 3 0 3 2 2
```

Sample 1 output:
```text
4
```

Sample 2 input:
```text
5
1 1 5 5 5
```

Sample 2 output:
```text
4
```

Explanation In thefirst sample casethe table can be at most 4 meters long. If it had been extended one more unit to the right, it wouldn’t be balanced anymore. [Diagram heights, left to right: 3,5,3,0,3,2,2; the horizontal table is at height 3. The original placement drawing remains in the source PDF.] picnic Page 14 of 20

In thesecond sample casethe table cannot be extended further to the right because it cannot exceed the limits of the park. [Diagram heights, left to right: 1,1,5,5,5; the horizontal table is at height 5. The original placement drawing remains in the source PDF.] picnic Page 15 of 20
