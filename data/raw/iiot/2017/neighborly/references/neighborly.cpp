#include <cstring>
#include <iostream>
#include <algorithm>
#include <string>
#include <vector>

using namespace std;

string N, S;
vector<int> suffix;

int commonprefix(int i, int j) {
    char *x = (char *)N.c_str()+i;
    char *y = (char *)S.c_str()+j;
    int k;
    for (k=0; k+i<N.size() and k+j<S.size() and x[k]==y[k]; k++);
    return k;
}

inline int idxcmp(int i, int j) {
    char *x, *y;
    x = i < 0 ? (char*)N.c_str()-i-1 : (char*)S.c_str()+i;
    y = j < 0 ? (char*)N.c_str()-j-1 : (char*)S.c_str()+j;
    return strcmp(x, y);
}

bool idxsorter(int i, int j) {
    return idxcmp(i,j) < 0;
}

int dispute(string N, string S) {
    suffix.resize(S.size());
    for (int i=0; i<S.size(); i++) suffix[i] = i;
    sort(suffix.begin(), suffix.end(), idxsorter);
    int count = 0;
    int idx = 0;
    for (int idx = 0; idx < N.size(); count++) {
        auto p = lower_bound(suffix.begin(), suffix.end(), -idx-1, idxsorter);
        int c1 = commonprefix(idx, *p);
        int c2 = commonprefix(idx, *(--p));
        idx += max(c1, c2);
    }
    return count;
}


int main() {
    getline(cin, N);
    getline(cin, S);
    cout << dispute(N, S) << endl;
    return 0;
}
