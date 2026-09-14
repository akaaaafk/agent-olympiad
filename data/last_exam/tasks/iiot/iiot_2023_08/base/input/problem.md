[IIOT logo] IIOT2023 – International Final [book indicator: 2 orange, 3 grey] Port Said, Egypt, May 26th to May 30th, 2023 tetris • EN Winning Tetris ( tetris) Tommaso is one of the best Tetris players in the world. Today he became bored of playing the game and decided to create a diﬀerent version. He wants to ﬁll aN × M grid with the standard Tetris pieces. Figure 1: All the pieces avaiable to Tommaso.
[Diagram transcription: seven tetrominoes, with # occupied and . empty; rows are separated by /.]
O: ##/##; I: #/#/#/#; S: .##/##.; Z: ##./.##; L: #./#./##; J: .#/.#/##; T: ###/.#.
 The pieces can be rotated, but they cannot overlap or go outside the grid. Help Tommaso by writing a program that, given the size of the grid, ﬁnds a way to completely ﬁll it with tetris pieces. Among the attachments of this task you may ﬁnd a template ﬁletetris.* with a sample incomplete implementation. Input The ﬁrst line contains the integersN and M. Output If it is not possible to ﬁll the grid, you need to write a single line with the number−1. Otherwise on the ﬁrst line you need to write the numberK of pieces used to ﬁll the grid. Then you need to write N lines with M numbers each, where thej-th number of thei-th line is the number of the piece used to ﬁll the cell(i, j). The diﬀerent pieces must be numbered from0 to K − 1. Constraints • 1 ≤ N ≤ 500. • 1 ≤ M ≤ 500. • If there are multiple solutions, you can print any of them. • Tommaso has an inﬁnite amount of pieces of each type. Scoring Your program will be tested against several test cases grouped in subtasks. In order to obtain the score of a subtask, your program needs to correctly solve all of its test cases. tetris Page 1 of 2

–Subtask 1(0 points) [book indicator: 1 orange, 4 grey] Examples. –Subtask 2(20 points) [book indicator: 1 orange, 4 grey] N, M≤ 4. –Subtask 3(30 points) [book indicator: 2 orange, 3 grey] N, M≤ 50. –Subtask 4(50 points) [book indicator: 2 orange, 3 grey] No additional limitations. 

Examples

Sample 1 input:
```text
2 3
```

Sample 1 output:
```text
-1
```

Sample 2 input:
```text
4 3
```

Sample 2 output:
```text
3
0 0 0
1 2 0
1 2 2
1 1 2
```

Explanation In theﬁrst sample casethere is no way to completely ﬁll a2 × 3 grid. In thesecond sample casea possible way to ﬁll the grid is shown in the image below: tetris Page 2 of 2
