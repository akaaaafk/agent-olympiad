#include <stdio.h>
#include <assert.h>
#include <algorithm>
#include <set>

#define MAXN 1024000
#define MAXK 128
#define MAXH 100

using namespace std;

int M[MAXN];
int P[MAXN];
int rnk[MAXN];
set<pair<int,int>> nxt[MAXN];
int N, L;

// true if cycle
bool rerank(int v, int x) {
    if (v == x) return true;
    int nr = nxt[v].empty() ? 0 : nxt[v].rbegin()->first + 1;
    if (M[v] == -1) {
        rnk[v] = nr;
        return false;
    }
    if (nr == rnk[v]) return false;
    nxt[M[v]].erase(make_pair(rnk[v],v));
    rnk[v] = nr;
    nxt[M[v]].insert(make_pair(rnk[v],v));
    return rerank(M[v], x);
}

void disconnect(int v) {
    if (M[v] == -1) return;
    nxt[M[v]].erase(make_pair(rnk[v],v));
    rerank(M[v], -1);
    M[v] = -1;
}

// true if cycle
bool connect(int v, int u) {
    if (M[v] != -1) disconnect(v);
    nxt[u].insert(make_pair(rnk[v],v));
    if (rerank(u, v)) return true;
    M[v] = u;
    return false;
}

void prepare(int E) {
    for (int i=0; i<N+E; i++) M[i] = -1;
    for (int i=1; i<N; i++)
        assert(not connect(i, P[i]));
    assert(rnk[0] < MAXH);
    L = rnk[0];
}

char emergency(int C, int K, int S[]) {
    for (int i=0; i<K; i++)
        assert(not connect(S[i], N));
    if (connect(N++, C)) return 'c';
    assert(rnk[0] < MAXH);
    char r = rnk[0] > L ? '1' : '0';
    L = rnk[0];
    return r;
}

int main() {
    FILE *fr, *fw;
    int E, C, K, i, j;
    int S[MAXK];

#ifdef EVAL
    fr = fopen("input.txt", "r");
    fw = fopen("output.txt", "w");
#else
    fr = stdin;
    fw = stdout;
#endif
    assert(2 == fscanf(fr, "%d %d", &N, &E));
    for(i=0; i<N; i++)
        assert(1 == fscanf(fr, "%d", &P[i]));
    prepare(E);
    for(i=0; i<E; i++) {
        assert(2 == fscanf(fr, "%d %d", &C, &K));
        for(j=0; j<K; j++)
            assert(1 == fscanf(fr, "%d", &S[j]));
        char c = emergency(C, K, S);
        fprintf(fw, "%c", c);
        if (c == 'c') break;
    }
    fprintf(fw, "\n");
    fclose(fr);
    fclose(fw);
    return 0;
}
