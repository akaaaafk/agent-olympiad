PROBLEMS FOR THE 4th INTERNATIONAL TOURNAMENT OF YOUNG
MATHEMATICIANS
3RD – 10TH JULY 2012, ORSAY (FRANCE)
Contents
Notation 1
1. Generalizing Perfectness 1
2. A Number of Residues 2
3. Sums of Powers 3
4. Isosceles Triangles 3
5. Stable Polygons 4
6. Recurrent Sequences 5
7. An Experiment 5
8. Discharged Batteries 6
9. Random Games 6
10. Densities of Natural Subsets 7
Keywords: 1. additive number theory, diophantine equations – 2. number theory, congru-
ence – 3. algebra, polynomials – 4. plane geometry – 5. analytic geometry, center of gravity –
6. recurrent sequences, probability – 7. algebra, iterations – 8. combinatorics, inequalities – 9.
games, random trees – 10. density, series.
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Z, Q, C sets of integer, rational and complex numbers
R, R2 real line and real plane
a mod b remainder (residue) after the division of a byb
Fp ={0, 1,...,p−1}ﬁeld of residue classes modulo a prime p
#M cardinal of a set M
τ(n) number of natural divisors of n
ϕ(n) Euler’s totient function
gcd(x1,...,xn) greatest common divisor of x1,...,xn
lim sup
n→+∞
xn limit superior of a sequence (xn), lim sup
n→+∞
xn = lim
n→+∞
(
sup
m≥n
xm
)
1. Generalizing Perfectness
Any function f : N→C is called arithmetic. Recall that a natural number n≥1 is said to
be perfect if it is equal to the sum of its positive proper divisors (that is all divisors except n).
Examples of perfect numbers are 6, 28 and 496. Euclid proved that if k is a natural number
such that 2k−1 is prime, then n = 2k(2k−1) is perfect.
Date: March 5, 2012.
1

2 3RD – 10TH JULY 2012, ORSAY (FRANCE)
Generalizing this notion, we say that a natural numbern∈N isf-perfect for some arithmetic
function f if
f(n) =
∑
d|n
1≤d≤n−1
f(d).
Thus, n is perfect if and only if n is f-perfect for f(n) = n. For another example, note that
a natural number n≥1 is f-perfect for the constant function f(n) = 1 if and only if n is a
prime.
1. Let τ(n) denote the number of positive divisors of n (including n).
a) Prove that a natural number n≥1 is τ-perfect if and only if n is the square of a prime.
b) Find all f-perfect natural numbersn≥1 for the functionf(n) =τ(n)−1. For as many
values ofk∈Z as possible, ﬁnd allf-perfect natural numbersn≥1 forf(n) =τ(n)+k.
2. Find all f-perfect numbers n, where f(n) =ϕ(n) is Euler’s totient function.
3. a) Prove that if k is a natural number such that 2 k+1−2k−1 is a prime, then n =
2k(2k+1−2k−1) is f-perfect for f(n) =n−1.
b) Find similar suﬃcient conditions forf-perfectness for other polynomial functions of degree
1 such as f(n) =n−2 or f(n) =n + 1.
4. Let f(n) = ln(n). Find all f-perfect numbers n.
5. Let f(n) = (−1)n. Find all f-perfect numbers n. Study the general case that f(n) = ωn,
where ω∈C is a root of unity.
6. Let f(n) =
(
2012
n
)
. Find all f-perfect numbers n. Study the general case where 2012 is
replaced by a natural number m.
7. Consider other arithmetic functions f and ﬁnd suﬃcient and/or necessary conditions for a
number to be f-perfect.
8. Recall that a pair (m,n ) of positive integers is said to be amicable if
n =
∑
d|m
1≤d≤m−1
d and m =
∑
d|n
1≤d≤n−1
d.
An example is (220, 284). For an arithmetic function f, give a reasonable deﬁnition for a pair
(m,n ) of positive integers to bef-amicable. For various arithmetic functionsf, ﬁndf-amicable
pairs or prove that no f-amicable pair exists.
2. A Number of Residues
Denote by Tk = k(k+1)
2 the kth triangular number, where k∈N. For each positive integer n,
let un be the number of distinct members of the sequence ( Tk mod n)k≥1.
1. Find a formula for un when n is a power of 2.
2. Find a formula for un when n is a power of a prime number.
3. Find a formula for un in general case.
4. LetP (x) be a polynomial with rational coeﬃcients such that P (k) is integer for everyk∈Z.
Find the number of distinct residues modulo n in the sequence (P (k))k≥1 , wheren is a positive
integer.
5. Suggest and investigate related questions.

PROBLEMS FOR THE 4 th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
3. Sums of Powers
Letn≥2 and letz1,z 2,...,zn be complex numbers. Deﬁne Sk =zk
1 +zk
2 +...+zk
n. We assume
that Sk is an integer for all k≥1.
1. a) Prove that the polynomial (X−z1)·(X−z2)·...·(X−zn) has integer coeﬃcients.
b) If z1,z 2,...,zn are rational numbers, prove that they are all integers.
2. a) Suppose that z1,z 2,...,zn are integers. Give a necessary and suﬃcient condition for the
following to be true: there are inﬁnitely many primes p dividing at least one of the numbers
S1,S 2,S 3,....
b) Answer the same question in the general case.
3. a) Find z1,z 2,...,zn such that Sk is the kth power of a rational number for all k≥1. You
may start with the case that z1,z 2,...,zn are all real numbers.
b) Find z1,z 2,...,zn such that 1
nSk is the kth power of a rational number for all k≥1.
4. Letak be the ﬁrst digit of the integerSk and assume that (ak)k is a periodic sequence. What
can be said about the numbers z1,z 2,...,zn? First, you may consider the case that all zi are
integers.
5. Investigate the same questions for the sequenceSk =∑n
i=1fi(n)zn
i , wherefi are polynomials
with complex coeﬃcients.
4. Isosceles Triangles
Consider a triangle ∆ ABC with side lengths a,b,c and median lengths ma,mb,mc as shown
in Figure 1. A well-known fact is that ma =mb if and only ifa =b, i.e. the triangle is isosceles.
A B
C
A0
A1
A2
A′
0
A′
1
A′
2
c
b a
ma
Figure 1. ∆ABC with a median AA0, an internal bisector AA1, a symmedian
AA2, an exmedian AA′
0, an external bisector AA′
1 and an exsymmedian AA′
2.
1. Prove that two internal angle bisectors of a triangle are equal if and only if the triangle is
isosceles.
2. The symmedian through a given vertex of a triangle is constructed by reﬂecting the median
about the internal angle bisector at the same vertex. Prove that two symmedians of a triangle
are equal if and only if the triangle is isosceles.

4 3RD – 10TH JULY 2012, ORSAY (FRANCE)
3. Is it true that two external angle bisectors of a triangle are equal if and only if the triangle
is isosceles?
4. An exmedian is a parallel to a side of a triangle through the opposite vertex. The exsymme-
dian through a vertex of a triangle is constructed by reﬂecting the exmedian about the external
angle bisector at the same vertex. Is it true that two exsymmedians of a triangle are equal if
and only if the triangle is isosceles?
Let n be a nonzero real number. An internal (external) n-line of the triangle is a line
through the vertex that divides internally (externally) the opposite side in proportion of the
nth powers of the adjacent sides. Namely, segments AAn and AA′
n are internal and external
n-lines respectively at the vertex A if one has BAn
AnC = cn
bn and BA′
n
A′nC = cn
bn .
5. Check that the internal bisectors and the symmedians are respectively internal 1-lines and
2-lines of the triangle. Also, the external bisectors and the exsymmedians are respectively
external 1-lines and 2-lines of the triangle.
6. Is it true that two internal n-lines of a triangle are equal if and only if the triangle is
isosceles?
7. Is it true that two external n-lines of a triangle are equal if and only if the triangle is
isosceles?
8. Suggest and study additional directions of research.
5. Stable Polygons
Letn≥3 be a positive integer, and let Pn be the set of vertices of a regular n-gon. A subset
A⊆Pn is called stable if the center of gravity of the points in A coincides with the center of
the regular n-gon.
A1
A2
A3
B6
B1 B2
B3
B4B5
G1
G2
Figure 2. The subset A ={A1,A 2,A 3}of P12 is stable, but the subset B =
{B1,...,B 6}is not.
1. When n is prime, ﬁnd the number of stable subsets A⊆Pn and describe them.
2. The same problem when n is the product of two distinct prime numbers.
3. The same problem when n is a power of a prime number.
4. Investigate the problem for an arbitrary n.
5. Suggest and study additional directions of research.

PROBLEMS FOR THE 4 th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
6. Recurrent Sequences
1. Let (un)n≥1 be a sequence of real numbers such that, for any n≥2,
un+1 = u2
1 +u2
2 +···+u2
n
n .
Study properties of the sequence (un)n≥1 depending onu1 andu2. For example, is it monotonic,
bounded, convergent, . . . ?
2. Let (un)n≥1 be a sequence of real numbers such that, for any n≥2,
un+1 = u1un +u2un−1 +···+un−1u2 +unu1
n .
Study properties of the sequence (un)n≥1 depending on u1 and u2.
3. Let u1 and u2 be real numbers. A random sequence ( un)n≥1 is constructed as follows. For
eachn≥2, if u1,u 2,...,un are already constructed, choose a random permutation σof the set
{1, 2,...,n}with probability 1/n! and set
un+1 = u1uσ(1) +u2uσ(2) +···+unuσ(n)
n .
a) Study properties of the sequence ( un)n≥1 depending on u1 and u2.
b) Same question ifσis a random function{1, 2,...,n}→{1, 2,...,n}instead of a random
permutation.
4. Let (un)n≥1 be a sequence of real numbers such that, for any n≥4,
un = u1un+1 +u2un +···+unu2 +un+1u1
n + 1 .
a) Study properties of the sequence ( un)n≥1 depending on u1, u2, u3 and u4.
b) Suppose in addition that u1 = u2 = u3 = 1. Does there exist a value of u4 such that
0≤u4 < 1 and un < 1 for every n≥1?
7. An Experiment
Consider the set F2 ={0, 1}of residues modulo 2 with addition rules 0 + 0 = 0, 0 + 1 = 1
and 1 + 1 = 0. Let n be a positive integer. Deﬁne an operation α on the set of n-tuples:
α(x1,x 2,...,xn) = (x1 +x2,x 2 +x3,...,xn +x1), for any ( x1,x 2,...,xn)∈(F2)n.
We say that an n-tuple is balanced if exactly half of its elements are zeros (in this case n is
even). A balanced tuple X = (x1,x 2,...,xn)∈(F2)n is called superbalanced if its images
α(X), α(α(X)), ..., αk(X) = α(α(...α( 
k
X ))), ...
are balanced for all k∈N.
1. a) Let ℓbe a positive integer. Find the number of balanced n-tuplesX = (x1,x 2,...,xn) in
the set (F2)n such that then-tuples α(X),..., αℓ(X) are balanced as well. Start withℓ= 1, 2, 3.
b) Do there exist superbalanced n-tuples? How many?
2. Invent and investigate your own problem analogous or related to the given one (even if you
have no answer to the ﬁrst question). As an idea, you may generalize the problem and consider
other cases, or slightly reformulate it by modiﬁng the conditions. A problem suggested by your
team must be new (unsolved in literature, in papers and over the internet).

6 3RD – 10TH JULY 2012, ORSAY (FRANCE)
8. Discharged Batteries
1. A racer has an electric car that needs two batteries to run. Unfortunately, the only reserve
at his disposal is a set of 10 batteries, and the only thing he knows is that ﬁve of them are
charged and the other ﬁve are uncharged. Call a 2-try the act of putting two batteries in the
car and trying to make it run. What strategy would you suggest to the racer to apply in order
to minimize the number of 2-tries needed to ﬁnd a charged pair?
2. Now, suppose that the car is bigger and it needs three charged batteries instead. Suppose
also that the racer has only eight batteries, but still a symmetric distribution between charged
and uncharged. Give a strategy to minimize the number of 3-tries.
3. Investigate the case where there are c > 2 charged batteries and u > 0 uncharged ones.
What is the order of growth of the number of 2-tries as a function ofc andu? Is there anything
special about the case c =u?
4. Generalize the problem for triples (c,u,n ), where c> 2 is the number of charged batteries,
u > 0 is the number of uncharged ones, and the car needs n < cbatteries to run. Find a
strategy minimizing the number of n-tries to make the car work.
5. A further generalization: given positive integers c,u,n ≥2 and m > n, what is the best
strategy to ﬁnd m charged batteries among c charged and u uncharged batteries by using an
“n-testing-car”?
6. Investigate the case where the car could run with half-charged batteries, but not all being
half-charged. We suppose that (contrary to most real-world batteries) a half-charged battery
furnishes half of the power of a fully charged one. Consider a tuple ( c,h,u,n,p ) of positive
integers, where c is the number of charged batteries, h is the number of half-charged batteries,
u is the number of uncharged ones, and the car needs n batteries with a total power p≤n.
Find a strategy minimizing the number of n-tries to make the car work.
7. Suppose that in the previous situation you don’t want to run the car, but rather ﬁnd k≤c
among the charged batteries. How does the strategy change?
9. Random Games
Given a graph G and a vertex v, consider the following two-player games. Both games begin
with a token placed on v, and the players alternately move the token from its current vertex
to a neighbouring one, never returning to already visited vertices. In the game G1, a player
unable to move the token in this way loses. In the game G2, a player who is unable to move
wins. The games may be a win for the ﬁrst player, a win for the second one or else a draw (if
the graph is inﬁnite). The goal of this problem is to play such games on random graphs.
Let µ= (µi)i≥0 be a sequence of nonnegative real numbers such that
∞∑
i=0
µi = 1 and µ0 +µ1 < 1.
The Galton-Watson tree with oﬀspring distribution µ, or shortly the GW µtree, is a random
plane tree deﬁned as follows. Start with a single vertex (the ancestor) having a random number
of children distributed according to µ, which means that the probability of having i children is
µi. Then each of its children has itself an independent random number of children distributed
according to µ, and so on. The genealogical tree of this population is the GW µtree. It is a
random ﬁnite or inﬁnite tree. We denote by pext the probability that the GWµtree is ﬁnite.

PROBLEMS FOR THE 4 th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
1. For 0≤x≤1, consider the series
F (x) =
∞∑
i=0
µixi.
a) Show that pext is the smallest solution of the equation F (x) =x in the interval [0, 1].
b) Give a necessary and suﬃcient condition in order to have pext = 1.
τ1 τ2
Figure 3. Two distinct plane trees τ1 and τ2.
Two players play the gamesG1 andG2 on the GWµtree starting from the ancestor. Set:
w = P (ﬁrst player wins the gameG1), ˜w = P (ﬁrst player wins the gameG2)
l = P (ﬁrst player loses the gameG1), ˜l = P (ﬁrst player loses the gameG2)
d = P (draw in the gameG1), ˜d = P (draw in the gameG2)
2. Estimate w,l,d, ˜w,˜l, ˜d.
3. Find inequalities between w,l,d, ˜w,˜l, ˜d.
4. Forλ>0 and i≥0, set:
µ(λ)
i = λi
i!e−λ.
Let w(λ),l (λ),d (λ), ˜w(λ),˜l(λ), ˜d(λ) be deﬁned as previously. Are these functions continuous with
respect to λ? Diﬀerentiable with respect to λ?
5. Investigate gamesG1 andG2 on other types of random graphs.
10. Densities of Natural Subsets
Introduce the following functionals on the set of all subsets of N:
µ1(E) = lim sup
n→+∞
#(E∩[1,n ])
n , for any E⊆N,
µ2(E) = lim sup
x→1−
(1−x)
∑
n∈E
xn, for any E⊆N,
µ3(E) = lim sup
x→1+
(x−1)
∑
n∈E
1
nx, for any E⊆N.
Real numbers µ1(E), µ2(E) and µ3(E) will be called densities of a set E.
1. Show that the densities µ1, µ2 and µ3 are well-deﬁned.
2. What are the densities µ1(E), µ2(E) and µ3(E) of a ﬁnite set E?

8 3RD – 10TH JULY 2012, ORSAY (FRANCE)
3. Find the densities µ1(E), µ2(E) and µ3(E) of an arithmetic progression
E ={a +nd |n∈N∪{0}},
where a and d are positive integers.
4. Find the densities µ1(E), µ2(E) and µ3(E) of a set
E ={[xn] |n∈N∪{0}},
where x≥1 is a real number and [·] stands for the integral part.
5. Find or estimate the densities of other subsets of N, for instance, of the Fibonacci sequence.
Try to construct subsets with “interesting” densities.
6. Is it true that the following equality
µ1(A∪B) +µ1(A∩B) =µ1(A) +µ1(B)
holds for any subsets A,B⊆N ?
7. The same question for µ2 and µ3.
8. Introduce and investigate other densities on natural subsets.
Laboratory of Mathematics, University Paris-Sud, 91400 Orsay, FRANCE
E-mail address : organizers.itym@gmail.com
URL: http://www.itym.org/
