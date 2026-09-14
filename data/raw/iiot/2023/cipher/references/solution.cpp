// @check-accepted: examples brute divisible no-limits
#include<chrono>
#include<iostream>
#include<random>
#include<set>
#include<string>
#include<vector>
using namespace std;

#define INIT  ios_base :: sync_with_stdio(false); cin.tie(NULL); cout.tie(NULL); mt19937 rng(chrono::steady_clock::now().time_since_epoch().count());
#define mp make_pair
#define pb push_back
#define ft first
#define sc second
#define ll long long
#define pii pair<int, int>
#define count_bits __builtin_popcount
//#define int ll


int n, k;
string s[200001], keys[200001];




//answer: index of the key, that generates the minimal lexicographical cipher. Print the lowest of the possible answers. -1 if no answer

vector<int> dv[200010];


struct Node{
    int ind=0;
    set<int> st;
    Node *arr[26];
};

Node *trie[200010];

void add(Node *trie, string &s, int i, int ind){
    //cout<<i<<"\n";
    if(trie->ind!=0)trie->ind=min( trie->ind, ind );
    else trie->ind=ind;

    if(i>=((int)s.length()) ){
        return;
    }
    
    //cout<<"began\n";
    if(trie->arr[ s[i]-'a' ]==nullptr){
        trie->arr[ s[i]-'a' ]=new Node();
        trie->arr[ s[i]-'a' ]->ind=ind;
        trie->st.insert( s[i]-'a' );
    }
    //cout<<"further add\n";
    add( trie->arr[ s[i]-'a' ], s, i+1, ind );
}

int query(Node *trie, string &s, int i){
    //cout<<i<<"q\n";
    if(trie->st.size()==0){
        return trie->ind;
    }
    if(i==((int)s.length())){
        return trie->ind;
    }
    //cout<<"began\n";
    char c1=*(trie->st.lower_bound(0));
    char c2=c1;
    if(  trie->st.lower_bound( 'z'-s[i]+1 )!=trie->st.end()  ){
        c2=*(trie->st.lower_bound( 'z'-s[i]+1 ));
    } 
    //cout<<"compr\n";
    
    
    if( ((( s[i]-'a'+c1 )%26)+'a')<=((( s[i]-'a'+c2 )%26)+'a')  ){
        return query(trie->arr[c1], s,  i+1);
    }
        return query(trie->arr[c2], s, i+1);
}




string compose(string &s1, string &s2){
    string s;

    for(int i=0; i<s1.length(); i++){
        char c=(( s1[i]-'a'+s2[i%((int)s2.length()) ]-'a' )%26)+'a';
        s.pb(c);
    }

    return s;

}




int res[200010];


int32_t main(){
    INIT

    for(int i=1; i<=200000; i++){
        for(int j=i; j<=200000; j+=i){
            dv[j].pb(i);
        }
    }

    for(int i=1; i<=200000; i++){
        trie[i]=new Node();
    }

    cin>>n>>k;
    for(int i=1; i<=k; i++){
        cin>>keys[i];
    }
    for(int i=1; i<=n; i++){
        cin>>s[i];
    }

    for(int i=1; i<=k; i++){
        
        add( trie[ (int)keys[i].length() ], keys[i], 0, i );
        //cout<<i<<"\n";
    }
    //cout<<"added\n";
    for(int i=1; i<=n; i++){
        res[i]=-1;
        string best="";
        for(int j=0; j<s[i].length(); j++){
            best.pb('z'+1);
        }
        for(int x:dv[ (int)s[i].length() ]){
            if(trie[x]->ind!=0){
                int ind=query(trie[x], s[i], 0);
                string now=compose(s[i], keys[ind]);
                if(now<best){
                    best=now;
                    res[i]=ind;
                }
            }
        }
        //cout<<res[i]<<"\n";
    }

    for(int i=1; i<=n; i++){
        cout<<res[i]<<"\n";
    }

    return 0;
}
