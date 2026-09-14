#include <cassert>
#include <iostream>
#include <vector>

#define N_MAX 250000
#define LG_MAX 18

using namespace std;

struct PersistentSegmentTree {
    struct Node {
        int cnt;
        int le, ri;
        Node(int _cnt = 0, int _le = 0, int _ri = 0) {
            cnt = _cnt;
            le = _le;
            ri = _ri;
        }
    };
    int N;
    int root[N_MAX + 5];
    Node node_list[40 * N_MAX];
    int len;
    int time;

    void Init(int _N) {
        N = _N;
        root[0] = build(1, N);
    }

    int build(int le, int ri) {
        if(le == ri) {
            return len++;
        }

        int mid = (le + ri) / 2;

        node_list[len] = Node(0, build(le, mid), build(mid + 1, ri));
        return len++;
    }

    int update(int last_node, int le, int ri, int pos, int val) {
        int node = len++;
        
        if(le == ri) {
            node_list[node] = node_list[last_node].cnt + val;
            return node;
        }

        int mid = (le + ri) / 2;
        if(pos <= mid) {
            node_list[node].ri = node_list[last_node].ri;
            node_list[node].le = update(node_list[last_node].le, le, mid, pos, val);
        }
        else {
            node_list[node].le = node_list[last_node].le;
            node_list[node].ri = update(node_list[last_node].ri, mid + 1, ri, pos, val);
        }

        node_list[node].cnt = node_list[node_list[node].le].cnt + node_list[node_list[node].ri].cnt;
        return node;
    }

    int Update(int pos, int val, int last_time = -1) {
        if(last_time == -1) {
            last_time = time;
        }
        time++;

        root[time] = update(root[last_time], 1, N, pos, val);
        return time;
    }

    int query(int lx, int x, int ly, int y, int le, int ri, int k) {
        assert(le <= ri);
        if(le == ri) {
            return le;
        }

        int mid = (le + ri) / 2;

        int freq = node_list[node_list[x].ri].cnt +
            node_list[node_list[y].ri].cnt -
            node_list[node_list[lx].ri].cnt -
            node_list[node_list[ly].ri].cnt;
        
        if(k <= freq) {
            return query(node_list[lx].ri, node_list[x].ri, node_list[ly].ri, node_list[y].ri, mid + 1, ri, k);
        }       
        else {
            return query(node_list[lx].le, node_list[x].le, node_list[ly].le, node_list[y].le, le, mid, k - freq);
        }   
    }

    int Query(int lx, int x, int ly, int y, int k) {
        lx = root[lx];
        x = root[x];
        ly = root[ly];
        y = root[y];

        return query(lx, x, ly, y, 1, N, k);
    }

};

int N;
int V[N_MAX + 5];
int t[N_MAX + 5];
int T[LG_MAX][N_MAX + 5];
int lev[N_MAX + 5];
vector <int> G[N_MAX + 5];
int Q;
PersistentSegmentTree tree;

int get_kth_anc(int node, int k) {
    for(int bit = 0; bit < LG_MAX; bit++) {
        if(k & (1 << bit)) {
            node = T[bit][node];
        }
    }

    return node;
}

int LCA(int a, int b) {
    if(lev[a] > lev[b]) {
        swap(a, b);
    }
    b = get_kth_anc(b, lev[b] - lev[a]);

    if(a == b) {
        return a;
    } 

    for(int bit = 16; bit >= 0; bit--) {
        if(T[bit][a] != T[bit][b]) {
            a = T[bit][a];
            b = T[bit][b];
        }
    }

    return T[0][a];
}

void DFS(int node) {
    t[node] = tree.Update(V[node], 1, t[T[0][node]]);

    for(auto it : G[node]) {
        lev[it] = 1 + lev[node];
        DFS(it);
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(0);
    cout.tie(0);

    cin >> N;
    tree.Init(N);

    for(int i = 1; i <= N; i++) {
        cin >> V[i];
    }
    for(int i = 2; i <= N; i++) {
        cin >> T[0][i];
        G[T[0][i]].push_back(i);
    }

    for(int b = 1; b < LG_MAX; b++) {
        for(int i = 1; i <= N; i++) {
            T[b][i] = T[b - 1][T[b - 1][i]];
        }
    }    

    DFS(1);
    cin >> Q;
    while(Q--) {
        int x, y, k;
        cin >> x >> y >> k;
        assert(1 <= x && x <= N && 1 <= y && y <= N);
        int lca = LCA(x, y);
        assert(1 <= k && k <= lev[x] + lev[y] - 2 * lev[lca] + 1);

        cout << tree.Query(t[lca], t[x], t[T[0][lca]], t[y], k) << "\n";
    }
    return 0;
}
