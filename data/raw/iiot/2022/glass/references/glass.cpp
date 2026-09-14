// @check-accepted: *

#include <iostream>
#include <vector>

using u32 = uint32_t;

int main() {
    std::ios::sync_with_stdio(false);

	u32 n, m;
	std::cin >> n >> m;

	std::vector<u32> c(n);
	std::vector<std::vector<u32>> cl(n);
	for (u32 i = 0; i < n; ++i) {
		std::cin >> c[i];
		cl[c[i]].push_back(i);
	}


	std::vector<std::vector<u32>> g(n);
	for (u32 i = 0; i < m; ++i) {
		u32 a, b;
		std::cin >> a >> b;
		g[a].push_back(b);
		g[b].push_back(a);
	}

	std::vector<u32> a(n, n);
	std::vector<u32> d(n, n);
	std::vector<u32> q;
	u32 ans = n;

	for (u32 color = 0; color < n; ++color) {
		for (auto v : cl[color])
			for (auto u : g[v])
				if (c[u] != color) {
					if (a[v] == n) {
						a[v] = c[u];
						d[v] = 1;
						q.push_back(v);
					} else if (c[u] != a[v]) {
						ans = 2;
					}
				}

		for (u32 i = 0; i < q.size(); ++i) {
			auto v = q[i];

			for (auto u : g[v])
				if (c[u] == color) {
					if (a[u] == n) {
						a[u] = a[v];
						d[u] = d[v] + 1;
						q.push_back(u);
					} else if (a[u] != a[v]) {
						ans = std::min(ans, d[v] + d[u] + 1);
					}
				}
		}

		q.clear();
	}
    if(ans == n) std::cout << "-1\n";
    else std::cout << ans << '\n';
}
