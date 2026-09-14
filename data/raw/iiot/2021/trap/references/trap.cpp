// insert brief description of the solution here

#include <iostream>
#include <map>
#include <string>
#include <vector>

using namespace std;

// input data
int N, L;

vector<string> song;
map<string, bool> founds;
map<string, int> counts;

int main() {
//  uncomment the following lines if you want to read/write from files
//  freopen("input.txt", "r", stdin);
//  freopen("output.txt", "w", stdout);

    cin >> N >> L;
    for (int i=0; i<N; ++i) {
        int M;
        cin >> M;
        for (int j=0; j<M; ++j) {
            string s;
            cin >> s;
            if (i==0) {
                song.push_back(s);
                founds[s] = false;
                counts[s] = 0;
            } else if (founds.count(s) > 0) founds[s] = true;
        }
        if (i>0) {
            auto itf = founds.begin();
            auto itc = counts.begin();
            for (; itf != founds.end(); ++itf, ++itc) {
                itc->second += itf->second;
                itf->second = false;
            }
        }
    }

    for (string s : song) cout << counts[s] << " ";
    cout << endl;
    return 0;
}
