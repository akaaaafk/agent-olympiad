// @check-accepted: examples AB small cubic quadratic C2 no-limits
#include<iostream>
#include<vector>
#include<map>
#include<set>
#include<cassert>
#include<cassert>
#include<unordered_map>
#include<unordered_set>
#include<functional>
#include<queue>
#include<stack>
#include<cstring>
#include<algorithm>
#include<cmath>
#include<sstream>
#include<iomanip>
#include<cstdio>
#include<cstdlib>
#include<numeric>
#include<random>
#include<chrono>
#include<bitset>
#include<ext/pb_ds/assoc_container.hpp>
#include<ext/pb_ds/tree_policy.hpp>
using namespace std;
using namespace __gnu_pbds;

#define all(x) (x).begin(), (x).end()
#define pb push_back
#define eb emplace_back
#define xx first
#define yy second
#define sz(x) (int)(x).size()
#define gc getchar
#define IO ios_base::sync_with_stdio(false);cin.tie(0);cout.tie(0)
#define mp make_pair
#define ins insert

#ifndef ONLINE_JUDGE
#  define LOG(x) (cerr << #x << " = " << (x) << endl)
#else
#  define LOG(x) ((void)0)
#endif

using ll = long long;
using ull = unsigned long long ;
using ld = long double ;
using str = string;
using ordered_set=tree<pair<int,int>, null_type, less<pair<int,int>>, rb_tree_tag, tree_order_statistics_node_update>;

const double PI=acos(-1);
const ll INF = 1LL<<62;
const ll MINF = -(1LL<<62);

template<typename T> T getint() {
    T val=0;
    char c;
    
    bool neg=false;
    while((c=gc()) && !(c>='0' && c<='9')) {
        neg|=c=='-';
    }

    do {
        val=(val*10)+c-'0';
    } while((c=gc()) && (c>='0' && c<='9'));

    return val*(neg?-1:1);
}

//mt19937 rng(chrono::steady_clock::now().time_since_epoch().count()); uniform_int_distribution<int>(0, n-1)(rng)

const ll mod=1e9+7;

const int MAXN=300001;

ll fact[MAXN], ifact[MAXN], inv[MAXN];
void init_comb() {
	fact[0]=fact[1]=1;
	ifact[0]=ifact[1]=1;
	inv[1]=1;
	for(ll i=2;i<MAXN;++i) {
		fact[i]=fact[i-1]*i%mod;
		inv[i]=(mod-(mod/i)*inv[mod%i]%mod)%mod;
		ifact[i]=ifact[i-1]*inv[i]%mod;
	}
}

ll binom(ll x, ll y) {
	if(x<y||y<0) return 0;
	return fact[x]*ifact[x-y]%mod*ifact[y]%mod;
}


ll fastpow(ll a, ll b, ll mod) {
	ll ans=1, mul=a%mod;
	while(b>0) {
		if(b&1) {
			ans=ans*mul%mod;
		}
		
		mul=(mul*mul)%mod;
		b/=2;
	}

	return ans;
}

int main() {
    IO;
    init_comb();
    
    int T;
    cin>>T;
    while(T--) {
        int A,B,C;
        cin>>A>>B>>C;
        
        if(A+B+C==1) {
            cout<<"1\n";
            continue ;
        }
        
        auto calc=[&](int A, int B, int C) -> ll {
            ll ans=0;
            for(int b=0;b<=C+1;++b) {
                int a=A-B+b;
                int ures=C+1-a-b;
                int rem=(A+B-a-b)/2;
                ll cans=binom(C+1, a)*binom(C+1-a, b)%mod*binom(rem-ures+C, C)%mod*fastpow(2, ures, mod)%mod;
                ans=(ans+cans)%mod;
            }
            return ans;
        };
        
        ll ans=calc(A,B,C)+calc(A,B,C-1)*2+calc(A,B,C-2);
        ans%=mod;
        
        cout<<ans<<"\n";
    }
    return 0;
}
