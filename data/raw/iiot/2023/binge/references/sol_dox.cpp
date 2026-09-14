// @check-accepted: examples Li=M N=1 E=1 no-limits
#include <iostream>
#include <vector>
using namespace std;
typedef long long ll;

int main(){
    ll M,N; cin >> M >> N;
    ll rem = M, e, l;
    ll D = 1;
    for(int i = 0; i < N; ++i){
        cin >> e >> l;
        ll cur = min(rem/l, e);
        rem -= cur*l;
        e -= cur;
        if(e == 0)continue;
        ll epd = M/l;
        D += (e + epd - 1)/epd;
        rem = M - l*(e%epd + epd*(e%epd == 0));
    }
    cout << D << ' ' << rem << endl;
}
