#include <stdio.h>
#include <assert.h>

#define MAXM 30

// prints number in matrix, -1 for "no node"
void print(FILE *fw, int num) {
    if (num == -1) fprintf(fw, " . ");
    else fprintf(fw, "%2d ", num);
}

int A[MAXM];
int B[MAXM];

int main() {
    FILE *fr, *fw;
    int H, W, N, M, i, j;

    fr = fopen("input.txt", "r");
    fw = fopen("output.txt", "w");
    assert(4 == fscanf(fr, "%d %d %d %d", &H, &W, &N, &M));
    for(i=0; i<M; i++)
        assert(2 == fscanf(fr, "%d %d", &A[i], &B[i]));

    // insert your code here
    
    for (i = 0; i < H; i++) {
        for (j = 0; j < W; j++)
            print(fw, -1/*solution here*/);
        fprintf(fw, "\n");
    }
    fclose(fr);
    fclose(fw);
    return 0;
}
