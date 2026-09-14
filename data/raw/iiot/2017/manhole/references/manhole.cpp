#include <bits/stdc++.h>
using namespace std;

const int MOD = 10007;

const int MAXL = 1000;
const int MAXN = 100;

int dp[MAXL + 1][MAXN + 1][MAXN + 1];

int L, K, N;
vector<int> manholes;
vector<int> factorial;

int f(int acc, int idx, int tkn) {
	int &ret = dp[min(L, acc)][idx][tkn];

	if (ret != -1) {
		return ret;
	}

	if (tkn == K) {
		if (acc >= L) {
			return (factorial[tkn] * factorial[N - 1 - tkn]) % MOD;
		} else {
			return 0;
		}
	}

	if (idx == N - 1) {
		return 0;
	}
	
	int take = f(acc + manholes[idx], idx + 1, tkn + 1);
	int no_take = f(acc, idx + 1, tkn);

	return ret = (take + no_take) % MOD;
}

int main() {
	cin >> L;
	cin >> N >> K;

	manholes.resize(N - 1);
	factorial.resize(N);
	factorial[0] = 1;
	for (int i = 0; i < N - 1; i++) {
		cin >> manholes[i];
		
		factorial[i + 1] = ((i + 1) * factorial[i]) % MOD;
	}

	memset(dp, -1, sizeof dp);
	cout << f(0, 0, 0) << endl;
}
