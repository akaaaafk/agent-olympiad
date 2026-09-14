[IIOT logo] IIOT2023 – International Final [book indicator: 5 orange, 0 grey] Port Said, Egypt, May 26th to May 30th, 2023 matgame • EN Game on a Matrix ( matgame) John is playing a game on a square matrix of dimensionsN × N. The rows and the columns of the matrix are numbered from1 to N. Cell (i, j) is the cell located in thej-th column of thei-th row. The matrix contains integers in each cell, speciﬁcally, the number written in cell(i, j) is ai,j. The game consists of a sequence of moves of the form: • Select a cell(i, j). • The score of the move is the valueai,jwritten in cell(i, j). • Remove the i-th row and thej-th column from the matrix. • Repeat the same process until the matrix becomes empty. The score of the game is deﬁned as theminimum of the scores of the moves . John asks you to determine the maximum possible score of a game that can be played on the given matrix. Among the attachments of this task you may ﬁnd a template ﬁlematgame.* with a sample incomplete implementation. Input The ﬁrst line of input containsN, the number of rows and columns of the matrix. Each of the nextN lines contains N numbers. The j-th number in thei-th line is the valueai,j, i.e., the number written in cell(i, j). Output Output a single number, representing the maximal possible score achievable in a game. Constraints • 1 ≤ N ≤ 1 000. • 0 ≤ ai,j≤ 10^9 for each i = 1 . . . Nand j = 1 . . . N. Scoring Your program will be tested against several test cases grouped in subtasks. In order to obtain the score of a subtask, your program needs to correctly solve all of its test cases. –Subtask 1 (0 points) [book indicator: 1 orange, 4 grey] Examples. –Subtask 2 (10 points) [book indicator: 2 orange, 3 grey] N ≤ 10. –Subtask 3 (30 points) [book indicator: 5 orange, 0 grey] N ≤ 300, 0 ≤ ai,j≤ 1 for each i = 1 . . . Nand j = 1 . . . N. –Subtask 4 (45 points) [book indicator: 5 orange, 0 grey] N ≤ 100. matgame Page 1 of 2

–Subtask 5 (15 points) [book indicator: 5 orange, 0 grey] No additional limitations. 

Examples

Sample 1 input:
```text
3
8 0 7
5 6 9
1 7 9
```

Sample 1 output:
```text
7
```

Explanation In the sample case, one possible optimal way of playing the game is as follows: • First, select cell(1,1) with the value8, and remove the ﬁrst row and the ﬁrst column. The matrix becomes this:
```text
6 9
7 9
```
 • Then, select the cell(2,1) of this new matrix with the value7, and remove the second row and the ﬁrst column. The matrix will consist of a single value9. • Finally, select the single value9 in the matrix, and remove it so that the matrix becomes empty. The score of the game is the minimum of the scores of the moves, which is7. matgame Page 2 of 2
