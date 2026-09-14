// @check-accepted: examples loops exp quadr trees cycle no-limits

#include <iomanip>
#include <iostream>
#include <deque>
#include <vector>

using u8 = uint8_t;
using u32 = uint32_t;
using i64 = int64_t;
using u64 = uint64_t;

constexpr u32 MAXN = 100'000;

static u32 n;
static u32 p[MAXN];
static u32 s[MAXN];
static u32 r[MAXN];
static i64 v[MAXN];
static i64 b[MAXN];

static u32 m;
static std::vector<u32> cyc[MAXN];
static u8 vis[MAXN];
static u64 c_num, c_den;

static void build_cycle(u32 i) {
	if (vis[i] == 1) {
		auto j = i;
		u64 num = 0, den = 0;
		do {
			num += s[j];
			den += p[j];
			cyc[m].push_back(j);
			j = r[j];
		} while (j != i);
		m += 1;
		if (num * c_den <= c_num * den) {
			c_num = num;
			c_den = den;
		}
	}
	if (vis[i] != 0) return;
	vis[i] = 1;
	build_cycle(r[i]);
	vis[i] = 2;
}

static i64 best(u32 i) {
	if (vis[i]) return b[i];
	auto par_b = best(r[i]);
	vis[i] = 1;
	return b[i] = std::max<i64>(v[i] + par_b, 0);
}

static bool test(u32 x, u32 y) {
	// std::cerr << "TEST\t" << x << " / " << y << '\n';

	if (c_num * y <= x * c_den) {
		// std::cerr << "CYCLE\n";
		return true;
	}

	for (u32 i = 0; i < n; ++i) {
		v[i] = (i64)x * p[i] - (i64)y * s[i];
		// std::cerr << i << ' ' << v[i] << '\n';
	}

	std::fill(vis, vis + n, 0);

	for (u32 c = 0; c < m; ++c) {
		std::deque<std::pair<u32, i64>> q;
		i64 cur = 0;
		q.emplace_back(0, 0);

		auto const push = [&](u32 tag) {
			while (!q.empty() && q.back().second >= cur) {
				q.pop_back();
			}
			q.emplace_back(tag, cur);

			// std::cerr << "PUSH\t";
			// for (auto [u, v] : q) std::cerr << u << ' ' << v << '\t';
			// std::cerr << '\n';
		};

		auto l = cyc[c].size();

		for (u32 i = 0; i < l; ++i) {
			cur += v[cyc[c][l - i - 1]];
			push(1 + i);
		}

		for (u32 i = 0; i < l; ++i) {
			cur += v[cyc[c][l - i - 1]];
			push(1 + l + i);

			while (1 + l + i - q.front().first >= l)
				q.pop_front();

			b[cyc[c][l - i - 1]] = cur - q.front().second;
			vis[cyc[c][l - i - 1]] = 1;
		}
	}

	// for (u32 i = 0; i < n; ++i) {
	// 	std::cerr << i << ' ' << best(i) << '\n';
	// }

	// std::cerr << "LINES\n";
	for (u32 i = 0; i < n; ++i) {
		auto t = best(r[i]) + p[i] * ((i64)x - y);
		// std::cerr << i << ' ' << best(r[i]) << ' ' << t << '\n';
		if (t >= 0)
			return true;
	}

	return false;
}

int main() {
	std::cin >> n;
	for (u32 i = 0; i < n; ++i) {
		std::cin >> p[i] >> s[i] >> r[i];
	}

	for (u32 i = 0; i < n; ++i) {
		build_cycle(i);
	}

	// for (u32 c = 0; c < m; ++c) {
	// 	for (auto x : cyc[c])
	// 		std::cerr << x << ' ';
	// 	std::cerr << '\n';
	// }

	// std::cerr << c_num << " / " << c_den << '\n';

	constexpr u32 max = 1e9 + 100;

	u32 mn = 0;
	u32 mx = max;
	while (mx - mn > 1) {
		auto md = (mn + mx) >> 1;
		(test(md, max) ? mx : mn) = md;
	}

	std::cout << std::fixed << std::setprecision(9) << 100 - mx * 100.0 / max << '\n';
}
