// @check-accepted: examples N3V N3 N2V NV N
// insert brief description of the solution here

#include <iostream>
#include <fstream>
#include <vector>

using namespace std;

// input data
int N, V;
vector<int> X, Y;

int main() {
//  uncomment the following lines if you want to read/write from files
//  ifstream cin("input.txt");
//  ofstream cout("output.txt");

    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    cin >> N >> V;
    X.resize(2*N);
    Y.resize(2*N);
    for (int i=0; i<2*N; i++)
        cin >> X[i];
    for (int i=0; i<2*N; i++)
        cin >> Y[i];

    int pfx = 0;
    while (pfx < N and X[2*pfx] == Y[2*pfx] and X[2*pfx+1] == Y[2*pfx+1]) pfx++;
    if (pfx == N) {
        cout << "SAME" << endl;
        return 0;
    }

    int sfx = 0;
    while (X[2*N-2*sfx-2] == Y[2*N-2*sfx-2] and X[2*N-2*sfx-1] == Y[2*N-2*sfx-1]) sfx++;
    int l=N-pfx-sfx;
    int k=pfx;

    int mx = 0, my = 0;
    for (int i=k; i<k+l; i++) {
        mx = max(mx, X[2*i]);
        my = max(my, Y[2*i]);
    }
    int f=0;
    if (mx*1 == my*2) f = 1;
    if (mx*2 == my*2) f = 2;
    if (mx*4 == my*2) f = 4;
    if (f == 0) {
        cout << "ORIGINAL " << l << endl;
        return 0;
    }

    mx = my = 0;
    for (int i=k; i<k+l; i++) {
        mx = max(mx, X[2*i+1]);
        my = max(my, Y[2*i+1]);
    }
    int t = my-mx;

    bool same = true;
    for (int i=k; i<k+l; i++) {
        if (X[2*i]*f != Y[2*i]*2 or X[2*i+1]+t != Y[2*i+1]) {
            same = false;
            break;
        }
    }
    if (same) {
        cout << "TRANSFORMED " << l << endl;
        return 0;
    }

    same = true;
    for (int i=0; i<l; i++) {
        if (X[2*(k+i)]*f != Y[2*(k+l-1-i)]*2 or X[2*(k+i)+1]+t != Y[2*(k+l-1-i)+1]) {
            same = false;
            break;
        }
    }
    if (same) {
        cout << "TRANSFORMED " << l << endl;
        return 0;
    }

    cout << "ORIGINAL " << l << endl;
    return 0;
}
