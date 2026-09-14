PROBLEMS FOR THE 3rd INTERNATIONAL TOURNAMENT OF
YOUNG MATHEMATICIANS
30TH JUNE – 7TH JULY 2011, MINSK (BELARUS)
Contents
Notation 1
1. Arithmetic Functions 1
2. Fibonacci and Beyond 2
3. An Abacus 2
4. Rearrangements 3
5. Convergent Triangles 3
6. Inequalities for Sides 4
7. A Game on Cycles 5
8. A verage Chord Length 6
9. Roots of Unity 7
10. Multiple Roots 7
Keywords: 1. additive number theory, diophantine equations – 2. number theory, con-
gruence – 3. combinatorics, discrete dynamics – 4. rearrangements – 5. analytic geometry,
convergence – 6. inequalities – 7. games, graph theory – 8. metric geometry, inequalities –
9. algebra, rational fractions – 10. algebra, polynomials.
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Z, Q, C sets of integer, rational and complex numbers
R, R2 real line and real plane
Fp ={0, 1,...,p−1}ﬁeld of residue classes modulo a prime p
K[x],K (x) sets of polynomials and rational fractions with coeﬃcients in K
ϕ Euler’s totient function
gcd(x1,...,xn) greatest common divisor of x1,...,xn
1. Arithmetic Functions
1. Let n> 2 be a natural number, and let 1 = a1 <a 2 <...<a ϕ(n) =n−1 be the positive
integers less than n which are coprime to n. Find the following sums
ϕ(n)∑
i=1
ai and
ϕ(n)/2∑
i=1
ai.
2. Denote by ψ(n) the number of triples (x,y,z )∈Z3 such that
0≤x<y, 0<z, gcd(x,y,z ) = 1 and yz =n.
Find a formula for ψ(n) depending on n and its prime divisors.
Date: April 13, 2011.
1

2 30TH JUNE – 7TH JULY 2011, MINSK (BELARUS)
3. Let a,b be positive integers. Denote by f(a,b,n ) the number of solutions of the equation
ax +by =n
in natural numbers x and y. Find a formula for f(a,b,n ).
4. Denote by g(n) the number of quadruples (a,b,x,y ) of natural numbers such that
a<b, gcd(a,b ) = gcd(x,y ) = 1 and ax +by =n.
Give a formula for g(n) or estimate it.
5. Suggest and study analogous questions for linear equations a1x1 +a2x2 +...+akxk =n.
2. Fibonacci and Beyond
Let a and b be integers. Consider the sequence ( xn)n∈N deﬁned by the recurrence relation
xn =axn−1 +bxn−2 for any n≥3, where x2 =x1 = 1.
Let p be a natural number. Denote by ( xn)n∈N the sequence of remainders of ( xn)n∈N after
the division by p: for all n∈N, we have xn∈{0, 1,...,p−1}such that xn≡xn mod p.
1. Takea =b = 1, then (xn)n∈N is the Fibonacci sequence. Suppose that p is prime.
a) Show that the sequence (xn)n∈N is periodic, i.e. there existsk∈N such thatxn+k =xn
for any n∈N. The minimal such k is called the period of the sequence.
b) Show that if p≡1, 4 mod 5, then xp−1 = 0 and xp =xp+1 = 1.
c) Show that if p≡2, 3 mod 5, then xp−1 = 1, xp =p−1 and xp+1 = 0.
d) Show that if p≡3 mod 4, then xn̸= 0 for any odd n.
e) Find lower and upper bounds for the period of the sequence ( xn)n∈N.
2. Investigate the previous questions in the case that p is not prime.
3. Study the problem for other values of a and b, for instance when a = 2012 and b = 2011.
3. An Abacus
Consider a simple abacus: a solid frame with n horizontal wires and one bead on each wire.
We assume that the beads are numbered from 1 ton and slide on wires with constant nonzero
speed v1,v 2,...,vn respectively. If a bead hits the frame, then it changes its direction to the
opposite. At any moment when no two beads lie on the same vertical line we project the
numbers of the beads to the lower edge of the frame and obtain a permutation of the ﬁrst n
natural numbers (see the ﬁgure).
1. For which initial position and velocities of the beads all permutations of the natural
numbers 1, 2,...,n will occur in such a way? First, consider the cases n = 2, 3, 4, 5 and
suppose that the beads are simultaneously leaving the left edge of the frame and slide to the
right with some distinct velocities of your choice.
2. Do there exist an initial position and velocities such that any permutation of the ﬁrst n
natural numbers will occur exactly once before reiteration?

PROBLEMS FOR THE 3 rd INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
1
v1
1
2
v2
2
3
v3
3
4
v4
4
5
v5
5
6
v6
6
3
v3
3
4
v4
4
5
v5
5
6
v6
6
1
v1
1
2
v2
2
3. In general, describe the set of permutations that will occur, given an initial position and
velocities of the beads.
4. Study abacuses having more than one bead on some wires. For instance, investigate the
case that one of the wires contains several beads that move with the same velocity, and if
two beads collide then they switch their directions to opposite.
5. Study the analogous problem when there are accelerations.
4. Rearrangements
Let a1≤a2≤...≤an be positive integers. Denote by D(a1,a 2,...,an) the set of all
pairs (a,b ) of positive integers such that there exists a rearrangement x1, x2, . . . ,xn of the
sequence a1, a2, . . . ,an with the following property:
|xi−xi+1|=a or b for any 1≤i<n.
1. Givena,b∈N, ﬁnd all positive integers n such that (a,b )∈D(1, 2,...,n ).
2. Givena,b,K ∈N, ﬁnd the largest integer n such that (a,b )∈D(a1,a 2,...,an) for some
distinct natural numbers a1, a2, . . . ,an not exceeding K.
3. Givena,b,n ∈N, ﬁnd the minimal possible value of the diﬀerence an−a1 such that the
pair (a,b ) belongs to the set D(a1,a 2,...,an), where a1 <a 2 <...<a n.
4. Denote by C(a1,a 2,...,an) the set of all pairs ( a,b ) of positive integers such that there
exists a rearrangement x1, x2, . . . ,xn of the sequence a1, a2, . . . ,an with the property:
|xi−xi+1|=a or b for any 1≤i≤n, where xn+1 =x1.
Study the questions 1–3 for the set C(a1,a 2,...,an).
5. Investigate analogous problems for triples (a,b,c ), quadruples (a,b,c,d ) and so on.
5. Convergent Triangles
Let A, B, C be the vertices of a triangle, and K1, L1, M1 the midpoints of the sides BC,
AC and AB respectively. Denote by f the operation of transition from a triangle ∆ ABC
to the triangle whose vertices are the midpoints of the sides of ∆ ABC. By iterating this
operation, we deﬁne the sequence of triangles ∆ KnLnMn such that
∆K1L1M1 =f(∆ABC) and ∆ Kn+1Ln+1Mn+1 =f(∆KnLnMn) for all n∈N.

4 30TH JUNE – 7TH JULY 2011, MINSK (BELARUS)
1. Prove that the sequence of triangles ∆ KnLnMn converges to a point P , determine that
point and estimate the speed of convergence.
Now, we consider the operationg of transition from a triangle ∆ABC to the triangle whose
vertices are the feet of the altitudes of ∆ ABC. Let
∆A1B1C1 =g(∆ABC) and ∆ An+1Bn+1Cn+1 =g(∆AnBnCn) for all n∈N.
A B
C
A1
B1
C1
A2
B2
C2
2. Find a formula for the point A1 in terms of the points A, B and C.
3. Is it true that if the limit of the sequence of triangles ∆ AnBnCn exists, then it necessarily
falls into the circumscribed circle of ∆ ABC? Consider also the circumscribed circle of the
triangle ∆ A1B1C1.
4. Investigate the convergence of the sequence (∆ AnBnCn)n∈N. What happens if one of the
triangles ∆ AnBnCn is right?
5. Denote by H the limit of the sequence (∆ AnBnCn)n∈N if that limit exists. Show that
H = H(ˆA, ˆB, ˆC) is a continuous function of the angles ˆA, ˆB, ˆC, but that it is nowhere
diﬀerentiable. Estimate the diﬀerence H(ˆA +ϵ,ˆB−ϵ,ˆC)−H(ˆA, ˆB, ˆC) in terms of ϵ>0.
6. Study the analogous problem for the feet of the angle bisectors.
6. Inequalities for Sides
Let T be the set of triples ( a,b,c ) of positive real numbers such that there exists a non-
degenerate triangle with side length a, b, c.
1. Letn≥3 be an integer, and a1,a2,...,an positive real numbers satisfying the inequality
(a2
1 +a2
2 +...+a2
n)2 > (n−1)(a4
1 +a4
2 +...+a4
n).
Show that every triple (ai,aj,ak) with distinct indices 1 ≤i,j,k ≤n belongs to T .
2. For a given positive integer n, ﬁnd the inﬁmum and supremum of the expression
n√
an +bn +
n√
bn +cn + n√cn +an
a +b +c over all (a,b,c )∈T.
3. Describe the set of positive real numbers x such that the inequality ax <b x +cx holds for
any triple (a,b,c )∈T with a≥b≥c.

PROBLEMS FOR THE 3 rd INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
4. For a given positive integer n, ﬁnd the largest real k =k(n) such that the inequality
an +bn +cn≥k(a +b +c)n
holds for all triples (a,b,c )∈T .
5. In the questions 2−4, you may also replace the set T by
a) the set Tac of triples (a,b,c ) for which there exists an acute-angled triangle with side
length a, b, c;
b) the set Tob of triples (a,b,c ) for which there exists an obtuse-angled triangle with side
length a, b, c;
c) the set Tre of triples (a,b,c ) of positive real numbers such that a2 =b2 +c2.
7. A Game on Cycles
Consider an undirected graph G in the plane possibly with loops but with no multiple
edges. Let V be the set of its vertices, and E the set of its edges. A path of length k is a
sequence of distinct edges (v0,v 1), (v1,v 2),..., (vk−1,vk)∈E. We call v0,vk∈V respectively
the start and end vertex of the path, and v1,...,vk−1∈V are the internal vertices. We say
that a path is simple if its vertices are distinct, except possibly for the start and end vertex.
A cycle of length k is a simple path of lengthk such thatv0 =vk. (So, the cycles of length 1
are exactly the loops of G, and there is no cycle of length 2.)
In directed graphs, an oriented edge is called anarrow. One deﬁnes analogously the notions
of a directed path, a simple directed path and a directed cycle. Note that in a directed graph,
for any two vertices a, b, there exists at most one arrow from a to b and at most one arrow
from b to a, which are denoted by ( a,b ) and (b,a ) respectively. (So, there can be directed
cycles of length 2.)
Let n≥5 and k≥1 be positive integers. Suppose that n points are given in the plane.
1. The high school students Clara and Carl play the following game: they alternately draw
an edge between two points that are not connected by an edge yet. Clara starts the game.
In each of the following cases, ﬁnd a winning strategy for one of the students:
a) The loser is the one after whose move the obtained undirected graph will contain a
cycle of length at least k.
b) The loser is the one after whose move the obtained undirected graph will contain a
cycle of length exactly k.
c) The winner is the one after whose move the obtained undirected graph will contain a
cycle of length at least k.
d) The winner is the one after whose move the obtained undirected graph will contain a
cycle of length exactly k.
Consider two diﬀerent problems: when loops are allowed and when loops are not allowed.
2. Formulate and study similar questions in the directed case.
3. Investigate variations of the game when Clara and Carl draw edges/arrows of two distinct
colours, say red and blue respectively. The loser/winner is the one after whose move the
obtained undirected/directed graph will contain a one-color cycle of length at least/exactlyk.
4. Suggest and study the analogous game for more than two players.

6 30TH JUNE – 7TH JULY 2011, MINSK (BELARUS)
8. A verage Chord Length
LetL be a closed curve symmetric about the origin O and bounding a convex shape in the
plane C = R2. Deﬁne the L-distance dL(M,N ) between two distinct points M, N in R2 as
the ratio d(M,N )/d(O,P ), where d is the usual Euclidean distance and P is an intersection
point of L and the parallel to (MN ) through O.
A chord is a segment joining two points ofL. We are interested in the average chord length
of L, in the following sense:
– consider a parametrization of L byM(θ) =r(θ)eiθ, θ∈[0, 2π],
– integrate the quantity dL(M(u),M (v)) times the areas of the elementary triangles
∆OM(u)M(u +du) and ∆ OM(v)M(v +dv) for u,v∈[0, 2π],
– divide the result by the square of the area of the convex shape bounded by L.
1. Show that the elementary triangle ∆ OM(u)M(u +du) has area 1
2r(u)2du.
2. Show that the average chord length is
E(L) =
∫2π
u=0
∫2π
v=0dL(M(u),M (v))r(u)2r(v)2dudv
(∫2π
u=0r(u)2du
)2
3. Show that 1/2<E (L)< 2. Improve these bounds the best you can.
4. Compute E(L) when L is a) a square; b) a parallelogram; c) a circle.
5. How does E(L) vary when L is changed by a linear transformation?
6. SupposeL is a polygon with verticesv0,v 1,...,v 2n−1. Denote by si the side [vivi+1], where
v2n =v0.
a) For t∈[0, 1], denote bysi(t) the point (1−t)vi+tvi+1 onsi. Show that dL(si(s),sj(t))
is piecewise linear in s and t.
b) Relate E(L) to the quantities
aij =
∫1
s=0
∫1
t=0
dL(si(s),sj(t))dsdt
c) Find an algorithm to compute E(L) when L is a polygon.
7. Find a formula for E(L) when L is a regular n-gon, where n is even and n ⩾ 4.
8. Show that any convex hexagon symmetric about O can be sent by a linear transform to
a hexagon Hx,y with vertices (x,y ), (1, 1), (−1, 1), (−x,−y), (−1,−1), (1,−1), where x ⩾ 1,
y ⩾ 0 and x +y ⩽ 2.
9. Find a formula for E(Hx,y) for such (x,y ).
10. Find the range of E(H) for all hexagons.
11. Compute E(L) for examples of L of your choice.
12. Find or conjecture the range of E(L) for all possible L.

PROBLEMS FOR THE 3 rd INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
13. Formulate and study the analogous problem in dimension 3. For instance, computeE(L)
when L is a) a sphere; b) a regular octahedron; c) a cube.
9. Roots of Unity
Let n be a natural number. There are exactly n distinct complex numbers satisfying the
equation zn = 1, they are called nth roots of unity .
Let K be a ﬁeld. We denote by K(x) the set of rational fractions with coeﬃcients in K,
that is,
p(x)
q(x) = akxk +...+a1x +a0
blxl +...+b1x +b0
,
where p(x), q(x) are polynomials with coeﬃcients in K and q(x)̸≡0.
1. Find all rational fractions f∈Q(x) such that, for any n∈N and each nth root of unity
s∈C, the number f(s) is an nth root of unity as well.
2. Find all rational fractions f∈Q(x) with the following property:
there exists n0∈N such that, for any natural n≥n0 and each nth root of
unitys∈C, the number f(s) is an nth root of unity as well.
3. Study the same questions for ﬁnite extensions of Q. For instance when K = Q[
√
5], ﬁnd
all rational fractionsf∈K(x) preserving the set ofnth roots of unity for any natural number
n large enough.
10. Multiple Roots
Let K be some ﬁeld, and K[x] the set of polynomials with coeﬃcients from K. Given a
polynomial Q∈K[x] and one of its roots a∈K, the multiplicity of a is the largest integer
m such that (x−a)m divides Q. A root a is called multiple if its multiplicity is at least 2.
1. Consider the ﬁeld Fp ={0, 1,...,p−1}of residue classes modulo a prime p. For a given
n∈N, denote by αn the probability that a random polynomial Q∈Fp[x] of degree n has a
multiple root in Fp. Find αn or estimate it. What is the limit of αn as n→∞?
2. The same questions for a ﬁnite extension of Fp.
3. The sequence of complex polynomials Pn(x)∈C[x] is such that
P1(x) =ax +b and Pn(x) =x
(
Pn−1(x) +Pn−1(cx +d)
)
for any n≥2,
where a,b,c,d are given complex numbers.
a) Find all n∈N such that the polynomial Pn(x) has a multiple root.
b) Find all a,b,c,d ∈C such that none of the polynomials Pn(x) has a multiple root.
c) Study the analogous problem when the polynomial P1(x) is nonlinear. You can also
consider the sequence
Pn(x) =Q(x)·
(
Pn−1(x) +Pn−1(cx +d)
)
, n ≥2,
for a given polynomial Q(x)∈C[x].
4. Suggest and study additional directions of research.

8 30TH JUNE – 7TH JULY 2011, MINSK (BELARUS)
Laboratory of Mathematics, University Paris-Sud 11, 91400 Orsay, FRANCE
E-mail address : organizers.itym@gmail.com
URL: http://www.itym.org/
