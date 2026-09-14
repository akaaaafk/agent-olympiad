// @check-accepted: examples NVsmall Nsmall no-limits
// insert brief description of the solution here

#include <fstream>
#include <iostream>
#include <algorithm>
#include <vector>

using namespace std;

int main() {

    int N;
    cin >> N;
    
    vector<int> v(N);
    for(auto &x: v)cin >> x;

    int mi = max_element(v.begin(), v.end()) - v.begin();
    long long ans = 0;
    int pm = 0;
    for(int i = 0; i < mi; ++i){
        pm = max(pm, v[i]);
        ans += pm;
    }
    pm = 0;
    for(int i = N-1; i > mi; --i){
        pm = max(pm, v[i]);
        ans += pm;
    }
    cout << ans << endl; // print the result
    return 0;
}
