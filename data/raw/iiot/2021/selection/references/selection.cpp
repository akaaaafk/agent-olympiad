#include <iostream>
#include <unordered_map>
#include <vector>

using namespace std;

#define MAXN 1000

// input data
int N, M, K[MAXN+2], _data[MAXN*(MAXN+1)/2];

inline int& DP(int i, int j) {
    return _data[(j-2)*(j-1)/2 + i];
}

int main() {
//  uncomment the following lines if you want to read/write from files
//  freopen("input.txt", "r", stdin);
//  freopen("output.txt", "w", stdout);

    cin >> N >> M;
    K[0] = -1;
    for (int i=0; i<N; ++i) cin >> K[i+1];
    K[N+1] = M;

    for (int i=0; i<N; ++i)
        DP(i,i+2) = K[i+2] > K[i]+2 ? K[i+2]-K[i]-1 : 0;
    for (int l=3; l<N+2; ++l)
        for (int i=0; i+l<N+2; ++i) {
            DP(i,i+l) = min(DP(i+1,i+l), DP(i,i+l-1));
            for (int k=i+2; k<i+l-1; ++k)
                DP(i,i+l) = min(DP(i,i+l), DP(i,k) + DP(k,i+l));
            DP(i,i+l) += K[i+l]-K[i]-1;
        }

    cout << DP(0, N+1) << endl;
    return 0;
}
