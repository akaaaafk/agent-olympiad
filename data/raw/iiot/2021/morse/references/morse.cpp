/*
 * NOTE: it is recommended to use this even if you don't
 * understand the following code.
 */

#include <iostream>
#include <string>
#include <vector>
#include <cassert>

using namespace std;

// constraints
#define MAXN 4000
#define MAXM 4000
#define MAXL 4000

// input data
int N, M;
string S;
vector<string> A;

const int MOD = 1000000007;

vector<int> Zalgo(string s) {
    int n = s.size();
    vector<int> z(n);
    z[0] = -1;
    int l = -1, r = -1;
    for (int i = 1; i < n; i++) {
        if (i < r) {
            z[i] = min(z[i-l], r-i);
        }

        while(i + z[i] < n && s[i + z[i]] == s[z[i]]) {
            z[i]++;
        }

        if (i + z[i] > r) {
            l = i;
            r = i + z[i];
        }
    }

    return z;
}


int main() {
//  uncomment the following lines if you want to read/write from files
//  freopen("input.txt", "r", stdin);
//  freopen("output.txt", "w", stdout);

    // WARNING: do not use scanf/printf!
    ios_base::sync_with_stdio(false);

    assert(cin >> N >> M);
    assert(cin >> S);
    A.resize(M);
    for (string &s : A) {
        assert(cin >> s);
    }

    vector<vector<bool>> matches(N);
    for (int i = 0; i < M; i++) {
        vector<int> z = Zalgo(A[i] + "#" + S);
        int len = A[i].size();
        for (int j = 0; j < N; j++) {
            matches[j].push_back(z[j + len + 1] >= len);
        }
    }


    vector<int> DP(N+1);
    DP[0] = 1;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M; j++) {

            bool match = matches[i][j];
            int len = A[j].size();
            if (match) {
                DP[i + len] += DP[i];
                DP[i + len] %= MOD;
            }
        }
    }


    cout << DP[N] << endl;
    return 0;
}
