// @check-accepted: examples N<=300 N<=2000 rest
// insert brief description of the solution here

#include <fstream>
#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;
using ll = long long ;

int n,k;
vector<pair<int, ll>> adj[200001]; 

void dfs(int x, vector<ll>& dist, ll curr=0, int par=-1) {
    dist[x]=curr;
    for(auto i:adj[x]) {
        if(par==i.first) continue ;
        dfs(i.first, dist, curr+i.second, x);
    }
}

int main() { 
    ios_base::sync_with_stdio(false);
    cin.tie(0);
    cin>>n>>k;
    ll ans=0;
    for(int i=1;i<n;++i) {
        int a,b,c;
        cin>>a>>b>>c;
        adj[a].push_back({b,c});
        adj[b].push_back({a,c});
        ans+=2*c;
    }

    vector<ll> dist(n+1, 0);
    dfs(1, dist);
    dfs(max_element(dist.begin(), dist.end())-dist.begin(), dist);

    cout<<(k>1?ans-*max_element(dist.begin(), dist.end()):ans)<<"\n";

    return 0;
}
