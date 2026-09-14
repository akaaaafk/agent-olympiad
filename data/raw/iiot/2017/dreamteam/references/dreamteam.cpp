#include <stdio.h>
#include <assert.h>
#include <algorithm>

#define MAXN 100000
#define INF  10000000

using namespace std;

int V[MAXN];

int select(int N, int K, int F[], int P[], int Q[]) {
    for (int i=0; i<N; i++) V[i] = INF;
    for (int i=0; i<N; i++) if (V[i] == INF) {
        V[i] = max(P[i], P[F[i]]);
        V[F[i]] = Q[i] + Q[F[i]] - V[i];
    }
    sort(V, V+N);
    int sum = 0;
    for (int i=N-1; i>=N-K; i--) sum += V[i];
    return sum;
}


int F[MAXN];
int P[MAXN];
int Q[MAXN];

int main() {
    FILE *fr, *fw;
    int N, K, i;

#ifdef EVAL
    fr = fopen("input.txt", "r");
    fw = fopen("output.txt", "w");
#else
    fr = stdin;
    fw = stdout;
#endif
    assert(2 == fscanf(fr, "%d %d", &N, &K));
    for(i=0; i<N; i++)
        assert(3 == fscanf(fr, "%d %d %d", &F[i], &P[i], &Q[i]));

    fprintf(fw, "%d\n", select(N, K, F, P, Q));
    fclose(fr);
    fclose(fw);
    return 0;
}
