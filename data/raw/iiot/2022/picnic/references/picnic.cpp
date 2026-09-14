// @check-accepted: examples binary_height cubic quadratic nlogn linear
#include <cassert>
#include <fstream>
#include <iostream>
#include <unordered_map>
#include <vector>

using namespace std;

const int INF = 1e9 + 100;

int N;
vector<int> H;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> N;
    H.resize(N);
    for (int i = 0; i < N; i++)
        cin >> H[i];
    H.push_back(INF);

    vector<pair<int, int>> minqueue;
    minqueue.emplace_back(INF, -1);

    unordered_map<int, int> lastOfHeight;
    lastOfHeight[INF] = -1;

    int sol = 0;
    for (int k = 0; k < N + 1; k++) {
        while (minqueue.back().first < H[k]) {
            int i = minqueue.back().second;
            minqueue.pop_back();
            int j = lastOfHeight[H[i]];
            if (i != j) {
                int left =
                    lastOfHeight[minqueue[minqueue.size() - 1].first] + 1;
                int right = k - 1;
                left = max(left, 2 * i - right + 1);
                right = min(right, 2 * j - left - 1);
                sol = max(sol, right - left + 1);
            }
        }
        if (minqueue.back().first > H[k]) {
            minqueue.emplace_back(H[k], k);
        }
        lastOfHeight[H[k]] = k;
    }

    assert(sol >= 2);
    cout << sol << endl;
    return 0;
}
