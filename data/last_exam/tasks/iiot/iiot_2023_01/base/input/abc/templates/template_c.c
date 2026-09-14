// NOTE: it is recommended to use this even if you don't understand the following code.

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

// constraints
#define MAXA 100000

// input data
int A, B, C;

void solve() {
    assert(3 == scanf("%d%d%d", &A, &B, &C));
    
    // insert your code here

    printf("%d\n", 42); // print the result
}

int main() {
    // uncomment the following lines if you want to read/write from files
    // freopen("input.txt", "r", stdin);
    // freopen("output.txt", "w", stdout);

    int T;
    assert(1 == scanf("%d", &T));
    for (int i = 0; i < T; i++) {
        solve();
    }
    
    return 0;
}
