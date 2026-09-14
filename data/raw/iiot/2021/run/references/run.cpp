/*
 * NOTE: it is recommended to use this even if you don't
 * understand the following code.
 */

#include <iostream>
#include <vector>
#include <cassert>

using namespace std;

const int INF = 1e9 + 100;

// input data
int N;
vector<int> D;

// R[i] = biggest k such that [i, i+k-1] are all >= D[i]
vector<int> R;

vector<pair<int, int>> tree;

void build(int pos = 1, int l = 0, int r = N-1) {
    if (l == r) {
        tree[pos] = {D[l], l};
        return;
    }

    int mid = (l + r) / 2;
    build(pos * 2, l, mid);
    build(pos * 2 + 1, mid + 1, r);
    if (tree[pos * 2 + 1].first >= tree[pos * 2].first) {
        tree[pos] = tree[pos * 2 + 1];
    } else {
        tree[pos] = tree[pos * 2];
    }
}

pair<int, int> query(int b, int e, int pos = 1, int l = 0, int r = N-1) {
    if (r < b || l > e) {
        return { -INF, INF };
    }

    if (l >= b && r <= e) {
        return tree[pos];
    }

    int mid = (l + r) / 2;
    auto x = query(b, e, pos * 2, l, mid);
    auto y = query(b, e, pos * 2 + 1, mid + 1, r);
    if (y.first >= x.first) {
        return y;
    } else {
        return x;
    }
}

int main() {
//  uncomment the following lines if you want to read/write from files
//  freopen("input.txt", "r", stdin);
//  freopen("output.txt", "w", stdout);

    assert(cin >> N);
    D.resize(N);
    for (int &d : D) {
        assert(cin >> d);
    }


    vector<pair<int, int>> Q;
    Q.emplace_back(-1, N);
    R.resize(N);
    for (int i = N-1; i >= 0; i--) {
        while(Q.back().first >= D[i]) {
            Q.pop_back();
        }
        R[i] = Q.back().second - i;
        Q.emplace_back(D[i], i);
    }

    tree.resize(4 * N);
    build();

    int sol = 1;
    for (int i = 0; i < N; i++) {
        int j = query(i, i + R[i] - 1).second;
        sol = max(sol, j - i + 1);
    }

    cout << sol << endl; // print the result
    return 0;
}
