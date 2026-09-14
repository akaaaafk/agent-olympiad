// @check-accepted: *

#include <iostream>
#include <fstream>
#include <vector>
#include <iomanip>

using namespace std;

int main() {
	ios::sync_with_stdio(false);

//  uncomment the following lines if you want to read/write from files
//  ifstream cin("input.txt");
//  ofstream cout("output.txt");

    int N, K;
    cin >> N >> K;

    vector<vector<int>> B(N, vector<int>(K));
    vector<vector<int>> S(N, vector<int>(K));

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < K; j++) {
            cin >> B[i][j] >> S[i][j];
        }
    }

    vector<long double> dp1(K + 1), dp2(K + 1);
    dp1[K] = 1;
    for (int i = 0; i < N; i++) {
        dp2 = dp1;
        for (int j = 0; j < K; j++) {
            dp2[K] = max(dp2[K], dp1[j] * S[i][j]);
        }
        for (int j = 0; j < K; j++) {
            dp2[j] = max(dp2[j], dp2[K] / B[i][j]);
        }
        swap(dp1, dp2);
    }

    cout << setprecision(15) << dp1[K] << endl;

    return 0;
}
