/*
 * Find an MST in the graph: all those edges have the MST value as the solution.
 * The other edges are considered one at the time: when added to the MST a
 * single loop forms, to obtain a spanning tree we need to remove the largest
 * edge in the loop (but not the one just added).
 * To find the largest edge we need to find the lowest common ancestor, this
 * solution uses binary lifting.
 *
 * Complexity: O(NlogN + NlogS)
 */


#include <cstdio>
#include <cassert>
#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

using ll = long long;
const int LOGS = 18;

struct movie_t {
    int a, b, i;
    ll t;

    bool operator<(const movie_t& m) const {
        return t < m.t;
    }
};

// input data
int N, S;
vector<movie_t> movies;

vector<int> uf;
vector<int> ufRank;

vector<bool> inMst;
ll mstVal;
vector<vector<pair<int, ll>>> adj;

vector<int> depth;
vector<vector<int>> jumps;
vector<vector<ll>> maxInJump;

int find(int u) {
    if (uf[u] == u) return u;
    return uf[u] = find(uf[u]);
}

void merge(int u, int v) {
    u = find(u);
    v = find(v);

    if (ufRank[u] < ufRank[v]) {
        uf[u] = v;
    } else {
        uf[v] = u;
        if (ufRank[u] == ufRank[v]) {
            ufRank[u]++;
        }
    }
}

void kruskal() {
    sort(movies.begin(), movies.end());

    for (int i = 0; i < S; i++) {
        uf[i] = i;
    }

    int mstSize = 0;
    for (int i = 0; i < N; i++) {
        movie_t& m = movies[i];
        if (find(m.a) != find(m.b)) {
            inMst[i] = true;
            merge(m.a, m.b);
            adj[m.a].emplace_back(m.b, m.t);
            adj[m.b].emplace_back(m.a, m.t);
            mstVal += m.t;
            mstSize++;
            if (mstSize >= S-1) {
                break;
            }
        }
    }
}

void dfs(int u, int p) {
    for (auto [v, t] : adj[u]) {
        if (v != p) {
            jumps[0][v] = u;
            maxInJump[0][v] = t;
            depth[v] = depth[u] + 1;
            dfs(v, u);
        }
    }
}

void buildLCA() {
    dfs(0, 0);
    for (int i = 1; i < LOGS; i++) {
        for (int u = 0; u < S; u++) {
            int mid = jumps[i-1][u];
            jumps[i][u] = jumps[i-1][mid];
            maxInJump[i][u] = max(maxInJump[i-1][u], maxInJump[i-1][mid]);
        }
    }
}

pair<int, ll> jump(int u, int d) {
    ll m = 0;
    for (int i = LOGS-1; i >= 0; i--) {
        if ((1 << i) <= d) {
            m = max(m, maxInJump[i][u]);
            u = jumps[i][u];
            d -= 1 << i;
        }
    }
    return {u, m};
}

ll maxBetween(int u, int v) {
    ll m = 0;
    if (depth[u] > depth[v]) {
        auto [uu, mm] = jump(u, depth[u] - depth[v]);
        u = uu;
        m = max(mm, m);
    }
    if (depth[v] > depth[u]) {
        auto [vv, mm] = jump(v, depth[v] - depth[u]);
        v = vv;
        m = max(mm, m);
    }
    for (int i = LOGS-1; i >= 0; i--) {
        if (jumps[i][u] != jumps[i][v]) {
            m = max(m, maxInJump[i][u]);
            m = max(m, maxInJump[i][v]);
            u = jumps[i][u];
            v = jumps[i][v];
        }
    }
    if (u != v) {
        assert(jumps[0][u] == jumps[0][v]);
        m = max(m, maxInJump[0][u]);
        m = max(m, maxInJump[0][v]);
    }
    return m;
}

int main() {
    cin >> N >> S;
    movies.resize(N);
    uf.resize(S);
    ufRank.resize(S);
    adj.resize(S);
    depth.resize(S);
    inMst.resize(N);
    jumps.resize(LOGS, vector<int>(S));
    maxInJump.resize(LOGS, vector<ll>(S));

    for (int i = 0; i < N; i++) {
        cin >> movies[i].a >> movies[i].b >> movies[i].t;
        movies[i].i = i;
    }

    kruskal();

    buildLCA();

    vector<ll> sol(N);

    for (int i = 0; i < N; i++) {
        movie_t& m = movies[i];
        if (inMst[i]) {
            sol[m.i] = mstVal;
        } else {
            sol[m.i] = mstVal - maxBetween(m.a, m.b) + m.t;
        }
    }

    for (int i = 0; i < N; i++) {
        cout << sol[i] << '\n';
    }
    return 0;
}