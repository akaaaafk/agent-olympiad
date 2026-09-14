// @check-accepted: examples N,M<=4 N,M<=50 no-limits
#include <fstream>
#include <iostream>
#include <vector>

using namespace std;
int ans[1000][1000];
int main() {
    int N, M;
    cin >> N >> M;
    if (N % 4 == 0) {
        int id = 0;
        for (int j = 0; j < M; j++) {
            for (int i = 0; i < N; i++) {
                ans[i][j] = id;
                if (i % 4 == 3) id++;
            }
        }
    } else if (M % 4 == 0) {
        int id = 0;
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < M; j++) {
                ans[i][j] = id;
                if (j % 4 == 3) id++;
            }
        }
    } else if (N % 2 == 0 && M % 2 == 0) {
        int id = 0;
        for (int i = 0; i < N; i += 2) {
            for (int j = 0; j < M; j += 2) {
                ans[i][j] = id;
                ans[i + 1][j] = id;
                ans[i][j + 1] = id;
                ans[i + 1][j + 1] = id;
                id++;
            }
        }
    } else {
        cout << "-1" << endl;
        return 0;
    }

    cout << (N * M) / 4 << endl;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M; j++) {
            cout << ans[i][j] << " ";
        }
        cout << endl;
    }
}
