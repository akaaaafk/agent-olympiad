// @check-accepted: *
#include <iostream>
#include <cassert>

using namespace std;
const int max_n = 300005, mod = 1e9 + 7;
long long fact[max_n], inv_fact[max_n], po2[max_n];

long long mod_inverse(long long x) {
    long long po = mod - 2, ans = 1;
    while (po) {
        if (po % 2) {
            ans = ans * x % mod;
        }
        x = x * x % mod;
        po /= 2;
    }
    return ans;
}

void precalc() {
    po2[0] = 1;
    for (int i = 1; i < max_n; i++) {
        po2[i] = 2 * po2[i - 1] % mod;
    }
    fact[0] = 1, inv_fact[0] = 1;
    for (int i = 1; i < max_n; i++) {
        fact[i] = fact[i - 1] * i % mod;
    }
    inv_fact[max_n - 1] = mod_inverse(fact[max_n - 1]);
    for (int i = max_n - 2; i >= 1; i--) {
        inv_fact[i] = inv_fact[i + 1] * (i + 1) % mod;
    }
}

long long binom(long long a, long long b) {
    if (a < 0 || a < b || b < 0) {
        return 0;
    }
    return fact[a] * inv_fact[b] % mod * inv_fact[a - b] % mod;
}


long long calc(int len, int x, int y) {
    // there are len groups, x from one letter, and y from another letter
    if (len < 0 || len > x + y) {
        return 0;
    }
    if (x == 0 && y == 0) {
        assert(len == 0);
        return 1;
    }
    if (x < y) swap(x, y);
    long long res = 0;
    for (int i = x - y; i <= len; i += 2) {
        long long rem = x + y - 2 * len + i;
        // the number of colorings, with exactly i odd gropus
        long long cl = binom(len, i) * binom(len + rem / 2 - 1, rem / 2) % mod;  

        // there are cnt ways to place the two different letter there
        long long cnt = po2[len - i] * binom(i, (i - (x - y)) / 2) % mod;  

        res = (res + cl * cnt) % mod;
    }
    return res;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(0);
    precalc();
    long long n, a, b, c;
    int t;
    cin >> t;
    while(t--) {
        cin >> a >> b >> c;
        cout << (calc(c - 1, a, b) + 2 * calc(c, a, b) + calc(c + 1, a, b)) % mod << "\n";
    }

    return 0;
}