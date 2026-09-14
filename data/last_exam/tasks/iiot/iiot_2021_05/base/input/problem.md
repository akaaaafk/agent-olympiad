IIOT International Informatics Olympiads in Teams [book indicator: 4 orange, 1 grey] Online, May 8th 2021 tasks •EN Map of Tasks ( tasks) Giorgio’s high-school in Italy isserious about the IIOT: all its the students are training for the next edition of the contest, and they absolutely want to earn their school a medal. The head Computer Science professor of the school has prepared a detailed training program for his students: a map of all the tasks that should be fully solved in order to be ready for the competition. The map is given as a rooted tree withN nodes (numbered from0 to N−1) where each node represents a task, and the parent-child relationships represent restrictions in the order in which the tasks should be solved. More speciﬁcally: if a tasku has a taskv among its children, this means that the tasku should be solved ﬁrst in order to “unlock” the taskv. The students know, for each tasku, the timeTu (in hours) that it would take a single student to solve the task with no external help. Because of how the map is made, these tasks can be attempted in parallel: multiple tasks can be attempted at the same time by diﬀerent students, however it’s not possible for multiple students to work on the same task. Help the students calculate the minimum amount of hours that it will take them to solve all the tasks in the map. But wait! To make things more interesting, the professor agreed that the students can “cheat” a maximum ofC times: this means that forC tasks they will be able to simply ﬁnd a solution online, spending 0 hours on those tasks. Among the attachments of this task you may ﬁnd a template ﬁletasks.* with a sample incomplete implementation. tasks Page 10 of 19

Input The ﬁrst line contains two integersN and C, the total number of tasks in the map and the number of tasks that students are allowed to solve by “cheating”. The nextN lines describe the tasks: thei-th line (with i going from 0 to N−1) contains two integersPi and Ti, which indicate that: • Before solving taski, a student must solve taskPi. If Pi =−1, then taski is the root of the map and it’s the ﬁrst task to solve. • Solving task i without any help will take a studentTi hours. Output You need to write a single integer: the minimum number of hours that the students will need to solve all the tasks. Constraints • 1≤N≤10 000. • 0≤C≤100. • 0≤Ti≤10^9 for each i = 0 . . . N−1. • Pi =−1 for exactly one value ofi, and 0≤Pi < N for all other values ofi. • Following thei→Pi→PPi→. . .chain always leads to the root of the tree, for eachi = 0 . . . N−1. • The school has enough students to tackle as many tasks in parallel as needed. Scoring Your program will be tested against several test cases grouped in subtasks. In order to obtain the score of a subtask, your program needs to correctly solve all of its test cases. –Subtask 1(0 points) [book indicator: 1 orange, 4 grey] Examples. –Subtask 2(18 points) [book indicator: 3 orange, 2 grey] N≤15. –Subtask 3(9 points) [book indicator: 3 orange, 2 grey] C = 0. –Subtask 4(23 points) [book indicator: 4 orange, 1 grey] C = 1. –Subtask 5(29 points) [book indicator: 4 orange, 1 grey] C≤20. –Subtask 6(21 points) [book indicator: 4 orange, 1 grey] No additional limitations. tasks Page 11 of 19

Examples

Sample 1 input:
```text
5 2
3 10
4 1
3 5
-1 20
3 2
```
Sample 1 output: `5`

Sample 2 input:
```text
7 2
1 10
-1 1
3 10
1 3
1 7
0 7
5 9
```
Sample 2 output: `14`

Explanation [First example diagram: root 3; edges 3→0, 3→4, 3→2, 4→1. Durations: task 0 = 10, task 1 = 1, task 2 = 5, task 3 = 20, task 4 = 2 hours. Tasks 0 and 3 are skipped, so their durations become 0.] The ﬁrst sample caseis shown on the left: there are 5 tasks and only 2 of them can beskipped. Skipping task 0 and task 3 leads to the optimal so- lution, whose total time is 5 hours. After skipping task 3 (the root), task 4 and 2 can be tackled in par- allel; after 2 hours task 4 is solved and task 1 can be started. After 5 hours task 2 is solved and you cannot choose another set of tasks to skip to reduce this time. The second sample casehas 7 tasks and only 2 of them can beskipped. A possible optimal solution is shown on the right, reducing the total time down to 14 hours. [Second example diagram: root 1; edges 1→0, 1→3, 1→4, 0→5, 3→2, 5→6. Durations: task 0 = 10, task 1 = 1, task 2 = 10, task 3 = 3, task 4 = 7, task 5 = 7, task 6 = 9 hours. Tasks 0 and 5 are skipped, so their durations become 0.] tasks Page 12 of 19
