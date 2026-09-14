#include <bits/stdc++.h>
using namespace std;

int main() {
	int B, G;
	set<string> bad, good;

	int count_legit = 0, count_spam = 0;

	cin >> B;
	while (B--) {
		string s;
		cin >> s;
		bad.insert(s);
	}

	cin >> G;
	while (G--) {
		string s;
		cin >> s;
		good.insert(s);
	}

	int E;
	cin >> E;
	while (E--) {
		bool spam = false, legit = false;

		int N;
		cin >> N;
		while (N--) {
			string s;
			cin >> s;

			if (bad.count(s)) spam = true;
			if (good.count(s)) legit = true;
		}

		if (spam && legit);
		else if (spam) count_spam += 1;
		else if (legit) count_legit += 1;
	}

	cout << count_spam << " " << count_legit << endl;
}
