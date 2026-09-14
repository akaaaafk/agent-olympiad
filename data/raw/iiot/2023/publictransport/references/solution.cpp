// @check-accepted: examples NMsmall M3-Nmedium NMmedium Sk-inc-Ti-eq Sk-inc no-limits
#include <iostream>
#include <vector>
#include <array>
#include <algorithm>
#include <complex>
#include <tuple>

using namespace std;
using ll = long long;
using ull = unsigned long long;
using point = complex<ll>;
#define x real
#define y imag

const int MAXN = 100010, MAXQ = 200010;
int N, M, Q;
array<int, MAXN> S, T;
ll pref[MAXN], ans[MAXQ], ans_base[MAXQ];

struct query {
    int a, c;
    int diff;
    int id;
    query(int _a = 0, int _c = 0, int _diff = 0, int _id = 0) 
        : a(_a), c(_c), diff(_diff), id(_id) {}
};
vector<query> queries;

int st[18][100010];

int log2_floor(ull i) {
    return i ? __builtin_clzll(1) - __builtin_clzll(i) : -1;
}
void RMQinit() {
    std::copy(S.begin(), S.end(), st[0]);
    for (int i=1; i<18; ++i)
        for (int j=0; j+(1<<i) <= N; ++j)
            st[i][j] = min(st[i-1][j], st[i-1][j+(1<<(i-1))]);
}
int RMQquery(int L, int R) {
    int i = log2_floor(R - L + 1);
    return min(st[i][L], st[i][R-(1<<i)+1]);
}

int n;
vector<point> seg;

ll dot(point a, point b) {
    return (conj(a) * b).x();
}
ll f(point a, ll x) {
    return dot(a, {x, 1});
}
void add_line(point nw, int node = 1, int lo = 0, int hi = n) {
    int mid = (lo + hi) / 2;
    bool lef = f(nw, lo) < f(seg[node], lo);
    bool md = f(nw, mid) < f(seg[node], mid);
    if (md) {
        swap(seg[node], nw);
    }
    if (lo+1 == hi) {
        return;
    } else if (lef != md) {
        add_line(nw, 2*node, lo, mid);
    } else {
        add_line(nw, 2*node+1, mid, hi);
    }
}
ll get_point(int x, int node = 1, int lo = 0, int hi = n) {
    int mid = (lo + hi) / 2;
    if(lo+1 == hi) {
        return f(seg[node], x);
    } else if (x < mid) {
        return min(f(seg[node], x), get_point(x, 2*node, lo, mid));
    } else {
        return min(f(seg[node], x), get_point(x, 2*node+1, mid, hi));
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin >> N >> M >> Q;
    for (int i=0; i<N; ++i) cin >> S[i];
    for (int i=1; i<N; ++i) {
        cin >> T[i];
        pref[i] = pref[i-1] + T[i];
    }
    queries.resize(Q);
    RMQinit();
    for (int q=0; q<Q; ++q) {
        int a,b,c,d;
        cin >> a >> b >> c >> d;
        if (a>c) swap(a,c), swap(b,d);
        if (b>d) swap(b,d);
        queries[q] = query(a, c, min(d-b, M-d+b), q);
        ans_base[q] = pref[c] - pref[a];
        ans[q] = 1ll*RMQquery(a,c) * queries[q].diff;
    }

    for (n=1; 2*n<=M+50; n<<=1);
    seg.assign(2*n, point(0, (ll)1e18));
    sort(queries.begin(), queries.end(), [](const query& q1, const query& q2) {
        return make_tuple(q1.a, q1.c, q1.diff, q1.id) < make_tuple(q2.a, q2.c, q2.diff, q2.id);
    });
    int qid = 0;
    for (int a=0; a<N; ++a) {
        add_line(point(S[a], -2ll*pref[a]));
        while (qid < Q && queries[qid].a == a) {
            int id = queries[qid].id;
            ans[id] = min(ans[id], 2ll*pref[a] + get_point(queries[qid].diff));
            ++qid;
        }
    }

    seg.assign(2*n, point(0, (ll)1e18));
    sort(queries.begin(), queries.end(), [](const query& q1, const query& q2) {
        return make_tuple(q1.c, q1.a, q1.diff, q1.id) > make_tuple(q2.c, q2.a, q2.diff, q2.id);
    });
    qid = 0;
    for (int c=N-1; c>=0; --c) {
        add_line(point(S[c], 2ll*pref[c]));
        while (qid < Q && queries[qid].c == c) {
            int id = queries[qid].id;
            ans[id] = min(ans[id], -2ll*pref[c] + get_point(queries[qid].diff));
            ++qid;
        }
    }

    for (int q=0; q<Q; ++q) {
        cout << ans_base[q] + ans[q] << "\n";
    }

    return 0;
}
