PROBLEMS FOR THE 2nd INTERNATIONAL TOURNAMENT OF
YOUNG MATHEMATICIANS
24TH JUNE – 1ST JULY 2010, ORSAY (FRANCE)
Contents
1. Blocking Sets 1
2. Separating Functions 2
3. A Cyclic Inequality 2
4. A Baby Chess 3
5. A Strange Network 3
6. Min/Max Questions 4
7. Friendly Polynomials 5
8. Points on Curves 5
9. A Topological Problem 6
Keywords: 1. probability, graph theory – 2. additive number theory – 3. inequalities
– 4. games – 5. combinatorics, codes – 6. combinatorial geometry – 7. polynomials, ﬁeld
theory – 8. geometry, functional inequalities – 9. topology, set theory.
1. Blocking Sets
Let S ={(a1,b 1), (a2,b 2),..., (an,bn)} be a set of n points in the square [0, 1]× [0, 1] such
that ai̸=aj and bi̸=bj for any i̸=j. Suppose that S contains the points (0, 0) and (1, 1).
(0, 0)
(1, 1) Call such a set acceptable.
We draw an arrow from a point (ai,bi)∈S to an-
other point (aj,bj)∈S if the following conditions
are satisﬁed:
i) ai <a j and bi <b j,
ii) either there is no point ( ak,bk)∈ S such
that ai < ak < aj, or there is no point
(ak,bk)∈S such that bi <b k <b j.
This construction gives a graph that we denote
by GS. Remark that in the obtained graph there
are at most two arrows starting at a vertex.
A directed path in GS (that is, a path following
the arrows) starting at (0 , 0) and ending at (1 , 1)
is called diagonal (see the ﬁgure).
We say that an acceptable set S is blocking if the graph GS has no diagonal path.
1. What is the minimum number of elements that a blocking set can have?
Date: April 2, 2010.
1

2 24TH JUNE – 1ST JULY 2010, ORSAY (FRANCE)
2. Two acceptable sets S ={(ai,bi)} and S′ ={(a′
i,b′
i)} of n points are called equivalent,
we write S∼ S′, if b1 < b2 <··· < bn, b′
1 < b′
2 <··· < b′
n and for any i̸= j we have
ai < aj if and only if a′
i < a′
j. In particular, the graphs of equivalent sets are isomorphic.
Denote by pn the probability of choosing a blocking set, that is, the ratio of the number of
non-equivalent blocking sets of n points to the number of all non-equivalent acceptable sets
of n points. Calculate or estimate pn. What is the limit of this probability as n→∞ ?
3. Let D(S) be the number of diagonal paths in S. Estimate the arithmetic mean of D(S)
over all non-equivalent acceptable n-point sets S, and also over all ﬁnite acceptable sets.
4. What if we replace the condition ii) by ‘either there is no point ( ak,bk)∈ S such that
ai <a k <a j andbi <b k, or there is no point (ak,bk)∈S such thatai <a k andbi <b k <b j’?
5. Formulate and investigateN-dimensional analogs of the problem, where N >2.
2. Separating Functions
Consider n positive integers a1,a 2,...,a n which are coprime, i.e., gcd(a1,a 2,...,a n) = 1.
LetS be the set of all linear combinations of numbers a1,a 2,...,a n with nonnegative integer
coeﬃcients,
S ={x1a1 +x2a2 +··· +xnan : xi∈ Z, xi≥ 0}.
1. Show that there exists a number f∈ N such that for any integer a≥f we havea∈S.
Deﬁne F (a1,a 2,...,a n) as the minimal number f ∈ N such that S contains all integers
starting from f,
F (a1,a 2,...,a n) = min{f∈ N : all integers a≥f belong to S}.
We will call F a separating function.
2. Casen = 2. Find a polynomial p(x,y ) with real coeﬃcients such thatF (a1,a 2) =p(a1,a 2)
for every pair of coprime positive integers a1,a 2.
3. Case n = 3.
a) Show that if two of three coprime positive integersa1,a 2,a 3 are even, thenF (a1,a 2,a 3)
is also even.
b) Suppose a3≥F (a1
d, a2
d ) where d = gcd(a1,a 2). Prove that
F (a1,a 2,a 3) =d·F (a1
d,a2
d ) +F (d,a 3).
4. Suggest and study a generalization of the question 3.a for n> 3.
5. Try to ﬁnd relations and divisibility rules for F (a1,a 2,...,a n).
3. A Cyclic Inequality
Let a be a nonnegative real number, and n a positive integer. Denote by
A(x) = x1 +x2 +··· +xn
n
the arithmetic mean of ann-tuplex = (x1,x 2,...,x n) of positive real numbers. By deﬁnition,
a cyclic mean of order k has the following expression
Ck,a(x) = 1 +a
n
( xk+1
1
xk
1 +axk
2
+ xk+1
2
xk
2 +axk
3
+··· + xk+1
n
xk
n +axk
1
)
.

PROBLEMS FOR THE 2 nd INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
1. Show that if a≥k− 1 then Ck,a(x)≥A(x) for any n-tuple x of positive real numbers.
2. Prove that if 0<a< k−1
k+1 andn> 1 then there exist two n-tuplesx andy of positive real
numbers such that
Ck,a(x)>A (x) but Ck,a(y)<A (y).
3. Investigate the case that k−1
k+1≤a<k − 1.
4. Let l be a positive integer. Consider the following function
Ck,l,a(x) = 1 +a
n
( xk+l
1
xk
1 +axk
2
+ xk+l
2
xk
2 +axk
3
+··· + xk+l
n
xk
n +axk
1
)
.
In particular, Ck,1,a(x) =Ck,a(x). Find the smallest a> 0 such that the inequality
Ck,l,a(x)≥ (A(x))l
holds for any n-tuple x of positive real numbers.
4. A Baby Chess
1. A knight is placed on the square with coordinates (a,b ) of an m×n board. Two students
alternately move the knight (following the chess rules) to a square that hasn’t been visited
yet. The loser is the one who cannot make a move. Find a winning strategy for one of the
students.
1
1
2
2
3
3
4
4
5
5
6
6
7
7
8
8
1
1
2
2
3
3
4
4
5
5
6
6
7
7
8
8
2. The analogous game with the condition that the knight leaves a ‘trace’ – four squares
that should be considered as visited (see the ﬁgure), and it is not allowed to pass through
already visited squares.
3. Study the same games for other chess pieces: a king, a queen, a rook, a bishop.
5. A Strange Network
A code of lengthn is a tupleA = (a1,...,a n) ofn nonnegative integers. A k-subcode ofA is
a tuple (ai1, ..., aik), where 1≤i1 <··· <i k≤n. For example, (0, 2, 0, 0) is a 4-subcode of
(2, 4, 0, 6, 2, 0, 1, 0). Remark that, by deﬁnition, the code A has n!
k!(n−k)! diﬀerent k-subcodes
even though some of the numbers ai’s might be equal.
Clara sends T copies of a code A of length n to Carl. However, the Network is so strange
that instead of receiving T copies of the code A, Carl obtains T diﬀerent k-subcodes of A.
(What Carl knows about the Network is that, as soon as T is not too large, it never gives the

4 24TH JUNE – 1ST JULY 2010, ORSAY (FRANCE)
same k-subcodes. For instance, if n = 3 and Carl receives two 2-subcodes (1 , 2) and (1, 2),
then he can conclude that A is either (1, 1, 2) or (1, 2, 2).)
At the beginning Carl is given a positive integer n and a number α such that 0≤ai≤α
for all 1 ≤ i≤ n. Find or estimate the minimal positive integer Tmin = Tmin(n,k,α ) such
that Carl can restore a code A of length n from any Tmin diﬀerent k-subcodes of A. First,
investigate particular cases: k =n− 1, k =n− 2, k = [n/2], α = 1, etc.
Clara CarlNetwork
(0, 1, 0, 1) (0, 1)
(0, 1, 0, 1) (0, 0)
(0, 1, 0, 1) (0, 1)
(0, 1, 0, 1) (1, 1)
mmm... what message
did Clara send me?
1. Consider the situation when Carl also knows that all ai’s are distinct.
2. Consider the case that the numbers ai’s are not necessary distinct.
3. Suggest and study additional directions of research.
6. Min/Max Questions
1. Let S be an inﬁnite set of points in the plane. Choose N > 2 points in S and consider
the N (N−1)
2 segments connecting them. Denote by lmin andlmax the minimal and the maximal
lengths of these segments respectively. What values can the ratio lmin/lmax take? Investigate
the following cases:
a) S is a line, show that lmax≥ (N− 1)·lmin,
b) S is a circumference,
c) S is the boundary of a convex polygon,
d) S is an m×n rectangular grid,
e) S is an inﬁnite triangular grid,
f) S is the whole plane, show for instance that lmax≥
√
2·lmin for N = 4.
2. Instead of the segments, consider the shortest curves that lie entirely in the set S. (For
example, if S is a circumference then such a curve connecting two points x,y ∈ S is the
smallest arc of S with endpoints at x and y.) Among the lengths of all shortest curves
connecting the chosen N points with each other, let cmin and cmax be the minimal and the
maximal ones respectively. Estimate the ratio cmin/cmax. Study the same cases as in the
previous question.
3. Consider all triangles with the vertices at three of the N chosen points. Estimate the
ratio amin/amax of the minimal area to the maximal area of these triangles.

PROBLEMS FOR THE 2 nd INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
7. Friendly Polynomials
LetK be some ﬁeld, and K[x] the set of polynomials with coeﬃcients from K. Given such
a polynomial P (x) =anxn +··· +a1x +a0∈K[x], the following polynomial
P (1)(x) = (P (x))′ =nanxn−1 +··· + 2a2x +a1
is called the ( ﬁrst) derivative of P . Denote by P (k) the kth successive derivative of P , it is
deﬁned recursively by
P (k)(x) =
(
P (k−1)(x)
)′
for k≥ 2.
We say that Q∈ K[x] divides P if there is a polynomial R∈ K[x] such that P = QR.
Two polynomials P1,P 2∈K[x] are said to be coprime if there is no polynomial Q∈K[x] of
degree at least 1 that divides both P1 and P2.
We will call a polynomial P∈K[x] of degree n friendly if it is not coprime with any of its
derivatives, that is, for all 1≤k <n, the polynomials P andP (k) share a common divisor of
degree at least 1.
1. Consider the ﬁeld Fp ={0, 1,...,p − 1} of residue classes modulo a prime p. Try to ﬁnd
all friendly polynomials P∈ Fp[x] of degree n∈ N.
2. Let C be the ﬁeld of complex numbers. Is it true that if a polynomial P∈ C[x] of degreen
is friendly then P (x) =c(x−a)n for somea,c∈ C? Study this question for particular values
of n (e.g., 2, 3, 4, 5), and also when n is a prime number, a power of a prime number, etc.
8. Points on Curves
1. Let bef : [0, 1]→ R be a continuous function. Find all positive integers n such that there
exists a sequence of real numbers 0 = t0 <t 1 <··· <t n−1 <t n = 1 for which the expression
0 t1 ... tn−1 1
|f(ti+1)−f(ti)| +|ti+1−ti|
does not depend on i = 0, 1,...,n − 1.
Consider the case that f is
a) a polygonal chain (that is, piecewise linear);
b) a polynomial of degree k = 2, 3,... ;
c) a trigonometric function.
2. A sequence A0,A 1,...,A n of n + 1 points in the plane is called α-tight, where α∈ R, if
A0 = (0, 0) and the distance between points Ai and Aj satisﬁes
d(Ai,Aj)≤
(j−i
n
)α
, for all 0≤i<j ≤n.
Let{Ai = (xi,yi)}n
i=0 be an α-tight sequence of n + 1 points. A function F : R2→ R is
called C-ﬁtting for the sequence{Ai}n
i=0 if the following inequalities hold
|F (Aj)−F (Ai)−xjyi +xiyj|≤C· j−i
n , for all 0≤i<j ≤n.
Find all (some) numbers C such that for any positive integer n and any α-tight sequence
{Ai}n
i=0 there exists a C-ﬁtting function for{Ai}n
i=0. Consider the case that
a) α = 1; b) α = 2010
2011; c) α = 1
2.

6 24TH JUNE – 1ST JULY 2010, ORSAY (FRANCE)
9. A Topological Problem
Consider the n-dimensional Euclidean space Rn with the ordinary metric
d(x,y ) =
√
(x1−y1)2 +··· + (xn−yn)2,
where (x1,...,x n) and (y1,...,y n) are the coordinates of points x,y∈ Rn respectively. The
open ball of radius r >0 centered at a point p in Rn, usually denoted by Br(p), is deﬁned by
Br(p) ={x∈ Rn : d(x,p )<r}.
For instance, open balls in the real line R are open intervals ]a,b [, open balls in the plane R2
are circles without their circumferences.
pBr(p)
an open set a convex hull
A set X⊂ Rn is called open if, for any point p∈X, there exists a real number r >0 such
that Br(p)⊂X. A set Y⊂ Rn is called closed if its complement X = Rn\Y is open. A set
Z⊂ Rn is called convex if, for any two points p,q∈Z, the line segment connecting p and q
is in Z. Obviously, there exist sets that are neither open nor closed nor convex.
Introduce three operations on the subsets of Rn:
(int) the interior of a set A⊂ Rn, denoted by int(A), is the union of all open sets X
contained in A,
int(A) =
⋃
X,
open X⊂A
(cl) the closure of a set A⊂ Rn, denoted by cl(A), is the intersection of all closed sets Y
containingA,
cl(A) =
⋂
Y,
closed Y⊃A
(conv) the convex hull of a set A⊂ Rn, denoted by conv(A), is the intersection of all convex
sets Z containingA,
conv(A) =
⋂
Z.
convexZ⊃A
1. Case n = 1. What is the maximal number of distinct sets that can be obtained from a
set A⊂ R using the operations int and cl?
2. Case n = 2.
a) Show that for any set A⊂ R2 such that int(conv(A))̸=∅ we have
int(conv(A)) =int(conv(cl(A))).
b) What is the maximal number of distinct sets that can be obtained from a set A⊂ R2
using the operations int,cl andconv? Consider the cases that int(conv(A)) =∅ and
int(conv(A))̸=∅.
3. Study the previous questions for n> 2.

PROBLEMS FOR THE 2 nd INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
Laboratory of Mathematics, University Paris-Sud 11, 91400 Orsay, FRANCE
E-mail address : organizers.itym@gmail.com
URL: http://www.itym.org/
