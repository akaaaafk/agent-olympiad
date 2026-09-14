// @check-accepted: *
#include<chrono>
#include<iostream>
#include<map>
#include<random>
#include<set>
using namespace std;

/*
string numeFisier="matgame3_21";
ifstream fin(numeFisier+".in"); ofstream fout(numeFisier+".out");
#define cin fin
#define cout fout
*/
#define INIT  ios_base :: sync_with_stdio(false); cin.tie(NULL); cout.tie(NULL); mt19937 rng(chrono::steady_clock::now().time_since_epoch().count());
#define mp make_pair
#define pb push_back
#define ft first
#define sc second
#define ll long long
#define pii pair<int, int>
#define count_bits __builtin_popcount
//#define int ll


int n;
int a[1001][1001];


map<int, int> h,uh;
set<int> s;




vector<int> g[5001];
int cpl[5001];
bool v[5001];






bool match(int s){
    if(v[s]){
        return false;
    }
    v[s]=true;

    for(int u:g[s]){
        if(cpl[u]==0){
            cpl[s]=u;
            cpl[u]=s;
            return true;
        }
    }

    for(int u:g[s]){
        if(u==cpl[s]){
            continue;
        }
        if(match(cpl[u]) ){
            cpl[s]=u;
            cpl[u]=s;
            return true;
        }
    }
    return false;
}


int GetMaxMatching(int n, int m){

    while(true){
        int res=0;
        for(int i=1; i<=n; i++){
            if(cpl[i]==0){
                res+=(int)match(i);
            }
        }
        for(int i=1; i<=(n+m); i++){
            v[i]=false;
        }
        if(res==0){
            break;
        }
    }

    int k=0;
    for(int i=1; i<=n; i++){
        if(cpl[i]>0){
            k++;
        }
    }

    return k;
}








int32_t main(){
    INIT

    cin>>n;
    for(int i=1; i<=n; i++)
    for(int j=1; j<=n; j++)
    cin>>a[i][j];
    

    for(int i=1; i<=n; i++)
    for(int j=1; j<=n; j++)
    s.insert(a[i][j]);

    int cnt=0;
    for(int x:s){
        cnt++;
        h[x]=cnt;
        uh[cnt]=x;
    }

    for(int i=1; i<=n; i++)
    for(int j=1; j<=n; j++)
    a[i][j]=h[ a[i][j] ];



    int maxmax=h[*prev( s.end() )];
    int l=0, r=maxmax+1, m=(l+r)>>1ll;

    while(l<r){
        bool pos = true;

        for(int i=1; i<=2*n; i++){
            g[i].clear();
            v[i]=false;
            cpl[i]=0;
        }

        for(int i=1; i<=n; i++){
            for(int j=1; j<=n; j++){
                if(a[i][j]>=m){
                    g[i].pb(n+j);
                    g[n+j].pb(i);
                }
            }
        }



        int cnt=GetMaxMatching(n, n);    
        if(cnt<n)pos=false;

        if(pos){
            l=m+1;
        }
        else{
            r=m;
        }
        m=(l+r)>>1ll;
    }
    cout<<uh[m-1]<<"\n";

    return 0;
}
