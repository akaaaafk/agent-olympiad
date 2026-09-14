#include <iostream>
#include <cassert>

using namespace std;

// calculates multiplicative period of a number
int period(int g, int m) {
    int x = g, i = 1;
    for (; x != 1; ++i) x = (x*g) % m;
    return i;
}

// computes the minimum generator in a modulus
int mingen(int m) {
    for (int i = 2; i < m; i += 1 + i%2)
        if (period(i,m) == m-1)
            return i;
    return 0;
}

// constraints
constexpr int MOD = 10000019;
constexpr int GEN = 7; //mingen(MOD);

using ll = long long;

// modular inverses
int INV[MOD];
// hash counts for (N+1)/2
int counts[MOD];
// hash counts for N/2
int locnts[MOD];

// input data
int N, H, UN, LN;

// use fermat's small theorem to calculate inverses
void calc_inv() {
    counts[0] = 1;
    for (int i=1; i<MOD-1; ++i)
        counts[i] = (counts[i-1]*GEN)%MOD;
    INV[1] = 1;
    for (int i=1; i<MOD-1; ++i)
        INV[counts[i]] = counts[MOD-1-i];
    for (int i=0; i<MOD; ++i) counts[i] = 0;
}

void bruteforce(int n, int d, int nd, int c, int h) {
    if (n == UN) {
        counts[h] = (counts[h]+c) % MOD;
        return;
    }
    if (n == LN)
        locnts[h] = (locnts[h]+c) % MOD;
    c = (c*n) % MOD;
    bruteforce(n+1, d, nd+1, (ll(c)*INV[nd+1]) % MOD, (h*d) % MOD);
    for (int x=d+1; x<10; ++x)
        bruteforce(n+1, x, 1, c, (h*x) % MOD);
}

int meetinthemiddle() {
    int* locnts = N % 2 ? ::locnts : counts;
    for (int i=1; i<MOD; ++i) INV[i] = (INV[i]*ll(H))%MOD;
    int r = 0;
    for (int i=1; i<MOD; ++i)
        r = (r + ll(counts[i]) * locnts[INV[i]]) % MOD;
    return r;
}

int main() {
//  uncomment the following lines if you want to read/write from files
//  freopen("input.txt", "r", stdin);
//  freopen("output.txt", "w", stdout);

    assert(cin >> N);
    assert(cin >> H);

    UN = (N+1)/2 + 1;
    LN = (N+0)/2 + 1;

    calc_inv();
    bruteforce(1, 1, 0, 1, 1);
    
    cout << meetinthemiddle() << endl; // print the result
    return 0;
}
