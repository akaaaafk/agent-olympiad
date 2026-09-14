// @check-accepted: examples cycle exp no-limits
// Greedily ensures one outgoing and one ingoing edge for every node.
#include <fstream>
#include <iostream>
#include <vector>

using namespace std;

// input data
int N, M;
vector<vector<pair<int, int>>> adj;
vector<vector<int>> dir;
vector<bool> edge_taken;
vector<bool> visited;

int take_free_edge(int u) {
    for (auto next : adj[u]) {
        if (!edge_taken[next.second]) {
            edge_taken[next.second] = true;
            return next.first;
        }
    }
    return -1;
}

void dfs(int u, bool need_in, bool need_out) {
    visited[u] = true;
    if (need_out) {
        int v = take_free_edge(u);
        if (v != -1) {
            dir[u].push_back(v);
            dfs(v, false, true);
        }
    }
    if (need_in) {
        int v = take_free_edge(u);
        if (v != -1) {
            dir[v].push_back(u);
            dfs(v, true, false);
        }
    }
}

int main() {
    cin >> N >> M;
    adj.resize(N);
    dir.resize(N);
    edge_taken.resize(M, false);
    visited.resize(N, false);
    int u, v;
    for (int i = 0; i < M; i++) {
        cin >> u >> v;
        adj[u].push_back({v, i});
        adj[v].push_back({u, i});
    }

    for (int i = 0; i < N; i++)
        if (!visited[i])
            dfs(i, true, true);

    for (int u = 0; u < N; u++)
        while ((v = take_free_edge(u)) != -1)
            dir[u].push_back(v);

    for (int u = 0; u < N; u++)
        for (int v : dir[u])
            cout << u << " " << v << endl;
    return 0;
}
