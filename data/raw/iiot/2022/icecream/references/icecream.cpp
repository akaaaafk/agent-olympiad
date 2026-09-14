// @check-accepted: examples exponential quadratic sorted-flavours no-limits

#include <array>
#include <iostream>
#include <vector>

using namespace std;

constexpr int MAXN = 2'000'000;
constexpr int LETTERS = 26;

struct node {
    array<int, LETTERS> links;
    int count;
    bool solution;
};

node trie[MAXN];
int last_node = 2;
int cur_ans = 1;

void add(const string& S) {
    int n = 1;
    for (char c: S) {
        int l = c - 'a';
        if (!trie[n].links[l]) {
            trie[n].links[l] = last_node++;
        }
        n = trie[n].links[l];
        trie[n].count++;
    }
}

void push(int n) {
    if (trie[n].solution) {
        trie[n].solution = false;
        cur_ans--;
        for (int l: trie[n].links) {
            if (l && trie[l].count) {
                trie[l].solution = true;
                cur_ans++;
            }
        }
    }
}

void remove(const string& S) {
    int n = 1;
    for (char c: S) {
        push(n);
        int l = c - 'a';
        n = trie[n].links[l];
        trie[n].count--;
    }
    push(n);
}

int main() {
    ios::sync_with_stdio(false);

    int N;
    cin >> N;

    vector<string> D(N);
    for (string& d : D) {
        cin >> d;
        add(d);
    }

    trie[1].solution = true;
    push(1);

    vector<int> ans(N);
    for (int i = N - 1; i >= 0; i--) {
        ans[i] = cur_ans;
        remove(D[i]);
    }

    for (int a: ans) {
        cout << a << '\n';
    }

    return 0;
}