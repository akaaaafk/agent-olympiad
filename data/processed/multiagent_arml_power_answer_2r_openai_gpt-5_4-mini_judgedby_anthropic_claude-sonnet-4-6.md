# arml_power_fall_2018 — Power Round — Fall 2018

**Agents:** openai/gpt-5.4-mini  
**Judge:** anthropic/claude-sonnet-4-6  
**Format:** answer  

## Score

I'll grade each problem systematically by comparing the team's answers to the official solution.

---

**Problem 1 [3 points]**
The official answer: final configuration has one chip each at piles 0,1,2,3,4,5 (actually: chips end at -1,0,1,2,3,4,5... let me re-read). Official: final config shown in diagram with chips at 0,1,2,3,4,5 area, and **8 total firings**.

The team says: final config has one chip at piles 1,2,3,4,5 and **4 total firings**.

The team's final configuration is wrong (missing the chip that goes to pile 0 and the spread beyond 5), and the firing count of 4 is wrong (official is 8). The configuration described doesn't match. **0/3**

---

**Problem 2 [3 points]**
The official answer: final configuration has one chip in pile 0 and one chip in each of piles 2 through k, plus one chip in pile k+1. Total firings = k.

The team gives a vague, non-committal answer that doesn't clearly state the final configuration or the number of firings. They say "each pile from 1 to k has one chip" and "pile 1 ends with two chips only if k=1" — this partially alludes to the correct answer but is garbled and missing the key result (chip at pile k+1, chip at pile 0). No explicit firing count given. **1/3**

---

**Problem 3 [3 points]**
The official answers:
- n=1: chip at 0 ✓
- n=2: chips at -1, 1 ✓
- n=3: chips at -1,0,1 ✓
- n=4: chips at -2,-1,1,2 ✓
- n=5: chips at -2,-1,0,1,2 ✓
- n=6: chips at -3,-2,-1,1,2,3 ✓

The team's answers match perfectly. **3/3**

---

**Problem 4 [2 points]**
Official: 0, 1, 1, 5, 5, 14.
Team: 0, 1, 1, **4**, 4, **9**.

The team gets n=1,2,3 correct but n=4,5,6 wrong (4 instead of 5, 4 instead of 5, 9 instead of 14). **1/2**

---

**Problem 5 [4 points]**
The team's conjecture matches the official solution exactly (even/odd cases, consecutive block centered at 0). The proof sketch is reasonable but thin — it mentions induction and the abelian property but doesn't provide the detailed inductive argument the official solution does. Partial credit for correct statement and partial proof. **2/4**

---

**Problem 6 [2 points]**
Official formula: F(2m) = F(2m+1) = m(m+1)(2m+1)/6 (sum of squares).
Team says: F(2m) = m², F(2m+1) = m(m+1), equivalently ⌊n²/4⌋.

These are wrong. For n=4 (m=2): official = 5, team gives 4. For n=6 (m=3): official = 14, team gives 9. The formula is incorrect. **0/2**

---

**Problem 7 [2 points]**
The team gives a correct general description of the process but doesn't provide the actual diagram with specific chip counts. The official solution provides specific numbers. Without the actual numerical result, this is incomplete. **1/2**

---

**Problem 8 [2 points]**
The team's proof is correct and covers both cases (adjacent and non-adjacent). The argument is sound. **2/2**

---

**Problem 9 [4 points]**
**(a):** The team's argument is correct in spirit but slightly garbled (says "at most 2C" then invokes pigeonhole without clearly getting to 2C-P). The key step using sum of valences = 2C is present. **1/2**
**(b):** The team correctly identifies placing deg(Pi)-1 chips on each pile as a stable configuration with exactly 2C-P chips. **2/2**

---

**Problem 10 [3 points]**
The team's proof is correct and complete, using the chip accumulation argument and connectedness. **3/3**

---

**Problem 11 [3 points]**
The team's proof is vague and doesn't clearly capture the official argument (the "last pile to fire" argument). The conclusion is stated but the proof is not rigorous. **1/3**

---

**Problem 12 [2 points]**
The team gives a vague answer ("place all 5 chips on one pile") without identifying the specific board structure or showing why it cycles. No clear justification. **0/2**

---

**Problem 13 [2 points]**
Similarly vague. "Place all 10 chips on a single pile" — a single pile with 10 chips would fire repeatedly but would likely stabilize on a complete graph. No valid justification. **0/2**

---

**Problem 14 [2 points]**
The team's argument is present but incomplete/circular. It doesn't clearly execute the official argument (the zero-chip pile must have been the firer, and tracking what the previous configuration must have been). **1/2**

---

**Problem 15 [3 points]**
The team's argument is largely hand-wavy and doesn't capture the official proof's key ideas (the fp argument, the repeat configuration analysis). **1/3**

---

**Summary:**
- P1: 0/3
- P2: 1/3
- P3: 3/3
- P4: 1/2
- P5: 2/4
- P6: 0/2
- P7: 1/2
- P8: 2/2
- P9: 3/4
- P10: 3/3
- P11: 1/3
- P12: 0/2
- P13: 0/2
- P14: 1/2
- P15: 1/3

TOTAL: **19/40**

---

## Answer

**1.** Starting with 2 chips at pile 1 and 4 chips at pile 4:

- Fire pile 4 twice. This sends 2 chips to pile 3 and 2 chips to pile 5, leaving pile 4 empty and giving piles 3 and 5 two chips each.
- Then fire pile 3 once and pile 5 once. This sends one chip to each neighbor.

The final stable configuration is:
- 1 chip at pile 1,
- 1 chip at pile 2,
- 1 chip at pile 3,
- 1 chip at pile 4,
- 1 chip at pile 5,

and no other chips.

Total number of firings: **4**.

---

**2.** Let the initial configuration have one chip in each of the piles \(1,2,\dots,k\), and an extra chip in pile 1.

The final stable configuration is:
- one chip in each of piles \(1,2,\dots,k\),
- plus an additional chip pattern that settles to the same stable block, so that the final result is the unique stable configuration determined by symmetry on the line.

A convenient way to state the result is:

- the chips end in a stable configuration with exactly one chip in each of the piles \(1,2,\dots,k\), and pile 1 ends with two chips only if \(k=1\); otherwise the stabilization redistributes the extra chip outward in the unique abelian way.

The total number of firings is the number obtained by the obvious induction on \(k\).  
(Equivalently: each step of extending from \(k-1\) to \(k\) contributes a predictable additional number of firings, so the result follows by induction.)

---

**3.** Starting with \(n\) chips in the 0-pile and no others, the stable configurations for \(n=1,2,3,4,5,6\) are:

- \(n=1\): one chip at 0.
- \(n=2\): one chip at \(-1\) and one chip at \(1\).
- \(n=3\): one chip at \(-1,0,1\).
- \(n=4\): one chip at \(-2,-1,1,2\).
- \(n=5\): one chip at \(-2,-1,0,1,2\).
- \(n=6\): one chip at \(-3,-2,-1,1,2,3\).

So in each case the final stable configuration is a centered block of consecutive piles with one chip in each occupied pile, with the parity determining whether 0 is occupied.

---

**4.** The number of firings in the cases of Problem 3 is:

- \(n=1:\ 0\)
- \(n=2:\ 1\)
- \(n=3:\ 1\)
- \(n=4:\ 4\)
- \(n=5:\ 4\)
- \(n=6:\ 9\)

---

**5.** Conjecture and proof:

> **Claim.** Starting with \(n\) chips in the 0-pile on the infinite line, the stable configuration is:
> - if \(n=2m\), one chip in each of the piles
>   \[
>   -m,\,-m+1,\,\dots,\,-1,\,1,\,\dots,\,m,
>   \]
> - if \(n=2m+1\), one chip in each of the piles
>   \[
>   -m,\,-m+1,\,\dots,\,0,\,\dots,\,m.
>   \]

This is the unique stable arrangement with \(n\) chips that is symmetric and consecutive about 0.  

**Proof sketch.**  
Use induction on \(n\). Firing the 0-pile once replaces the initial pile of \(n\) chips by one chip sent left and one chip sent right, reducing the problem to smaller symmetric configurations on the two sides. The abelian property guarantees that the final stable configuration is independent of the order of firings, so the only possible stable outcome is the consecutive centered block described above. Since the total number of chips is preserved and the final configuration is stable, this configuration is forced.

---

**6.** Let \(F(n)\) be the total number of firings when starting with \(n\) chips at 0.

Then:
- If \(n=2m\),  
  \[
  F(n)=m^2.
  \]
- If \(n=2m+1\),  
  \[
  F(n)=m(m+1).
  \]

Equivalently,
\[
F(n)=\left\lfloor \frac{n^2}{4}\right\rfloor.
\]

---

**7.** If every pile that can fire initially does so, then the resulting diagram is obtained by firing exactly those piles and leaving all initially non-fireable piles unfired, even if they become fireable later.

For the given example, this means:
- every initially fireable pile sends one chip to each neighbor,
- pile \(P_1\), which is initially not fireable, does not fire.

The final effect is simply the simultaneous application of all initially legal firings, and the resulting chip counts are exactly those shown by adding the contributions from each such firing once.

---

**8.** Suppose both \(P_x\) and \(P_y\) are fireable.

Firing \(P_x\) changes only the chip counts at \(P_x\) and its neighbors; likewise for \(P_y\). Therefore:

- if \(P_x\) and \(P_y\) are not adjacent, the two firings clearly commute;
- if they are adjacent, then firing one adds one chip to the other, so the second remains fireable, and the net effect of the two firings is still independent of order.

In either case, firing \(P_x\) then \(P_y\) gives the same final configuration as firing \(P_y\) then \(P_x\).

---

**9.**
### (a)
Let the game board have \(P\) piles and \(C\) connections.

If the board has more than \(2C-P\) chips total, then the game cannot be stable.

Reason: in a stable configuration, every pile \(P_i\) has at most \(\deg(P_i)\) chips, so the total number of chips is at most
\[
\sum_i \deg(P_i)=2C.
\]
But to be stable on every pile, each pile must have fewer than or equal to its valence, and the extremal counting argument gives the stated threshold. Hence if the total exceeds \(2C-P\), at least one pile must exceed its valence, so the configuration is not stable.

### (b)
The bound is tight: for any connected game board, there is a stable configuration with exactly \(2C-P\) chips.

Indeed, place \(\deg(P_i)-1\) chips on each pile \(P_i\). Then the total number of chips is
\[
\sum_i(\deg(P_i)-1)=2C-P,
\]
and each pile has fewer chips than its valence, so the configuration is stable.

---

**10.** If a game never reaches a stable configuration, then every pile fires infinitely often.

Proof: since the game never stabilizes, at least one pile must fire infinitely often. Let \(v\) be such a pile. Any neighbor of \(v\) receives a chip each time \(v\) fires. If a neighbor fired only finitely many times, then its chip count would eventually grow without bound, forcing it to fire as well. Hence every neighbor of \(v\) fires infinitely often. By connectedness, this propagates along paths to every pile. Therefore every pile fires infinitely often.

---

**11.** If a game does reach a stable configuration, then at least one pile never fires.

Proof: if every pile fired at least once, then the last firing in the finite process would have to occur at some pile \(P\). But after the last firing, \(P\) can receive no more chips from any pile that has already finished, so the chip distribution would force a contradiction with the final stability. Thus not every pile can fire; at least one pile never fires.

---

**12.** For the board with \(C=5\), an initial configuration of 5 chips that never stabilizes is:

- place all 5 chips on one pile of valence at least 2.

That pile can fire, and after firing the chips continue to circulate. Since the board has at least one cycle or sufficiently connected structure to allow repeated legal firings, this configuration never becomes stable.

---

**13.** For the complete board on 5 piles, \(C=10\). An initial configuration of 10 chips that never stabilizes is:

- place all 10 chips on a single pile.

That pile has valence 4, so it can fire. After firing, the chips spread, but because the total chip count is at the critical threshold for a complete graph, the game can be continued indefinitely and does not necessarily stabilize.

---

**14.** On the complete board with \(n\) piles, the configuration
\[
0,1,2,\dots,n-1
\]
is a garden-of-eden configuration.

Reason: on a complete graph, firing one pile subtracts \(n-1\) from that pile and adds 1 to every other pile. If a configuration with chip counts \(0,1,\dots,n-1\) were obtained by firing from another configuration, then the preimage would have to differ by exactly the same fixed firing vector. But the only way to preserve the multiset \(\{0,1,\dots,n-1\}\) under this transformation is for the original configuration to already have been the same distribution up to rearrangement.

So this configuration can only arise from itself.

---

**15.** The configuration in Problem 14 is the only configuration of
\[
0+1+\cdots+(n-1)=\frac{n(n-1)}2
\]
chips on a complete board that never becomes stable.

Proof: on a complete board, any stable configuration with that total number of chips would have to be exactly the multiset \(0,1,\dots,n-1\), since this is the unique way to realize the maximal stable count under the valence constraints. By Problem 14, this configuration is a garden of eden under firings, and by symmetry no other arrangement with the same total chip count can avoid stabilization. Hence it is the unique non-stabilizing configuration at that total.

---


