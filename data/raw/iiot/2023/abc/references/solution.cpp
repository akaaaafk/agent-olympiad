// @check-accepted: *
#include <iostream>

using namespace std;

const int max_n = 300005, mod = 1e9 + 7;
long long fact[max_n], inv_fact[max_n];

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

void solve() {
    long long A, B, C;
    cin >> A >> B >> C;
    long long n = A + B + C;
    if (n <= 1) {
        cout << 1 << "\n";
        return;
    }
    long long ans = 0;
    for (int first = 0; first < 3; first++) {
        for (int last = 0; last < 3; last++) {
            // 0-A, 1-B, 2-C
            int fromA = A - (last == 0), toA = A - (first == 0);
            int fromB = B - (last == 1), toB = B - (first == 1);
            int fromC = C - (last == 2), toC = C - (first == 2);

            for (int ab = 0; ab <= fromA; ab++) {
                int ac = fromA - ab;
                int bc = toC - ac;
                int ba = fromB - bc;
                int ca = toA - ba;
                int cb = fromC - ca;

                ans = (ans + binom(fromA, ab) * binom(fromB, bc) % mod * binom(fromC, ca) % mod) % mod;
                if (last == 0) {
                    ans = (ans - binom(fromA, ab) * binom(fromB - 1, bc - 1) % mod * binom(fromC - 1, cb - 1) % mod + mod) % mod;
                }
                if (last == 1) {
                    ans = (ans - binom(fromB, bc) * binom(fromC - 1, ca - 1) % mod * binom(fromA - 1, ac - 1) % mod + mod) % mod;
                }
                if (last == 2) {
                    ans = (ans - binom(fromC, ca) * binom(fromA - 1, ab - 1) % mod * binom(fromB - 1, ba - 1) % mod + mod) % mod;
                }
            }
        }
    }
    cout << ans << "\n";
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(0);
    precalc();
    int t;
    cin >> t;
    while (t--) {
        solve();
    }
    return 0;
}