#include <bits/stdc++.h>
using namespace std;

#define DEBUG1 0

int main() {
    int H, N;
    cin >> H;
    cin >> N;

    vector<char> v(N);
    for (int i = 0; i < N; i++) {
        int a, b;
        cin >> a >> b;

        if (a > H and b > H) {
            v[i] = 'R';   // right
        } else if (a < H and b < H) {
            v[i] = 'L';   // left
        } else {
            v[i] = 'W';   // wherever
        }
    }

#if DEBUG1
    for (int i = 0; i < N; i++) {
        cerr << v[i];
    }
    cerr << endl;
#endif

    int answer = 0;

    int left = 0, right = N - 1;
    while (1) {
        while (left < N and v[left] != 'R') {
            left++;
        }

        while (right >= 0 and v[right] != 'L') {
            right--;
        }

        if (left < right) {
            swap(v[left], v[right]);
            answer += 1;
        } else {
            break;
        }
    }

#if DEBUG1
    for (int i = 0; i < N; i++) {
        cerr << v[i];
    }
    cerr << endl;
#endif

    cout << answer << endl;
}
