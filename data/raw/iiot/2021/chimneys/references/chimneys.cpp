/*
 * NOTE: it is recommended to use this even if you don't
 * understand the following code.
 */

#include <iostream>
#include <vector>
#include <algorithm>
#include <cassert>

using namespace std;

// input data
int N, C;
vector<int> A, B, L;

typedef long long ll;

struct chimney_t {
    vector<int> edges;
    ll length;
};

ll length_before(const chimney_t &x, int d) {
    ll before = 0;
    if (d == A[x.edges[0]]) {
        return 0;
    }
    for (int e : x.edges) {
        before += L[e];
        if (B[e] == d) {
            break;
        }
    }
    return before;
}

ll value_crossover(const chimney_t &x, const chimney_t &y, int d) {
    ll before_x = length_before(x, d);
    ll before_y = length_before(y, d);

    ll after_x = x.length - before_x;
    ll after_y = y.length - before_y;

    ll new_x = before_x + after_y;
    ll new_y = before_y + after_x;

    if (new_x == 0 || new_y == 0) {
        // merge two chimneys
        return max(new_x, new_y);
    }
    return min(new_x, new_y);
}


void crossover(chimney_t &x, chimney_t &y, int d) {
    ll before_x = length_before(x, d);
    ll before_y = length_before(y, d);
    ll after_x = x.length - before_x;
    ll after_y = y.length - before_y;

    vector<int> new_x, new_y;

    auto it_x = find_if(x.edges.begin(), x.edges.end(), [&](int e) { return A[e] == d; });
    auto it_y = find_if(y.edges.begin(), y.edges.end(), [&](int e) { return A[e] == d; });

    // first half
    new_x.insert(new_x.begin(), x.edges.begin(), it_x);
    new_y.insert(new_y.begin(), y.edges.begin(), it_y);
    // second half
    if (it_x != x.edges.end()) {
        new_y.insert(new_y.end(), it_x, x.edges.end());
    }
    if (it_y != y.edges.end()) {
        new_x.insert(new_x.end(), it_y, y.edges.end());
    }

    x.edges = new_x;
    x.length = 0;
    for (int e : x.edges) {
        x.length += L[e];
    }

    y.edges = new_y;
    y.length = 0;
    for (int e : y.edges) {
        y.length += L[e];
    }

    assert(x.length == before_x + after_y);
    assert(y.length == before_y + after_x);
}


bool improve(vector<chimney_t> &chimneys) {
    // find the shortest chimney
    int worst = 0;
    for (int i = 1; i < (int)chimneys.size(); i++) {
        if (chimneys[i].length < chimneys[worst].length) {
            worst = i;
        }
    }

    // try all possible crossovers
    ll best_value = chimneys[worst].length;
    int other = -1, crossover_on = -1;
    for (int i = 0; i < (int)chimneys.size(); i++) {
        if (i == worst) {
            continue;
        }

        for (int edge_worst : chimneys[worst].edges) {
            for (int edge_i : chimneys[i].edges) {
                pair<ll, int> local_best = {-1, -1};
                if (A[edge_worst] == A[edge_i] || A[edge_worst] == B[edge_i]) {
                    ll value = value_crossover(chimneys[i], chimneys[worst], A[edge_worst]);
                    local_best = max(local_best, {value, A[edge_worst]});
                }
                if (B[edge_worst] == A[edge_i] || B[edge_worst] == B[edge_i]) {
                    ll value = value_crossover(chimneys[i], chimneys[worst], B[edge_worst]);
                    local_best = max(local_best, {value, B[edge_worst]});
                }

                if (local_best.first > best_value) {
                    best_value = local_best.first;
                    other = i;
                    crossover_on = local_best.second;
                }
            }
        }
    }


    if (other != -1) {
        crossover(chimneys[worst], chimneys[other], crossover_on);
        if (chimneys[worst].length == 0) {
            chimneys.erase(chimneys.begin() + worst);
        } else if (chimneys[other].length == 0) {
            chimneys.erase(chimneys.begin() + other);
        }
    }

    return other != -1;
}


int main() {
    //  uncomment the following lines if you want to read/write from files
    //  freopen("input.txt", "r", stdin);
    //  freopen("output.txt", "w", stdout);

    cin >> N;
    A.resize(N);
    B.resize(N);
    L.resize(N);
    for (int i = 0; i < N; i++) {
        cin >> A[i] >> B[i] >> L[i];
    }

    // insert your code here
    vector<chimney_t> chimneys;
    for (int i = 0; i < N; i++) {
        chimneys.push_back({{i}, L[i]});
    }

    while (improve(chimneys)) {}

    cout << chimneys.size() << "\n";
    for (chimney_t &c : chimneys) {
        cout << c.edges.size() << "\n";
        for (int e : c.edges) {
            cout << e << " ";
        }
        cout << "\n";
    }

    return 0;
}
