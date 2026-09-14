#include <vector>
#include <iostream>
#include <limits>
#include <assert.h>

using namespace std;

using ll = long long;

int N, C;

vector<ll> T;
vector<vector<int>> adj;

vector<vector<ll>> dp;

void f(int u) {
    if (adj[u].size() == 0) {
        dp[u][0] = T[u];
        for (int c = 1; c <= C; c++) {
            dp[u][c] = 0;
        }
        return;
    }

    for (int v : adj[u]) {
        f(v);

        vector<ll> cur(C+1, numeric_limits<ll>::max());
        // assume we have c coins
        for (int c = 0; c <= C; c++) {
            // we give x of them to this child
            for (int x = 0; x <= c; x++) {
                cur[c] = min(cur[c], max(dp[v][x], dp[u][c-x]));
            }
        }
        for (int c = 0; c <= C; c++) {
            dp[u][c] = cur[c];
        }
    }

    vector<ll> cur(C+1);
    // try to spend a coin on u
    cur[0] = T[u] + dp[u][0];
    for (int c = 1; c <= C; c++) {
        cur[c] = min(T[u] + dp[u][c], dp[u][c-1]);
    }
    for (int c = 0; c <= C; c++) {
        dp[u][c] = cur[c];
    }
}

int main() {
    cin >> N >> C;

    T.resize(N);
    adj.resize(N);
    dp.resize(N, vector<ll>(C+1, 0));

    int root = -1;
    for (int i = 0; i < N; i++) {
        int p;
        ll t;
        cin >> p >> t;
        T[i] = t;
        if (p != -1) {
            adj[p].emplace_back(i);
        } else {
            root = i;
        }
    }

    f(root);
    cout << dp[root][C] << endl;
}
