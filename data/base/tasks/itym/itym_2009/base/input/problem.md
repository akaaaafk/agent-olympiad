PROBLEMS FOR THE 1st INTERNATIONAL TOURNAMENT OF
YOUNG MATHEMATICIANS
ORSAY, FRANCE
Contents
1. Specular Colourings 1
2. A Functional Equation 2
3. Monotonic Squares 2
4. Minimality of Inscribed Polygons 2
5. Integer-valued Polynomials 3
6. Pattern Graphs 3
7. Placements of Pentominoes 5
8. Positivity of Symmetric Polynomials 5
9. Good Numbers 6
10. Centro-Symmetric Shadows 6
Keywords: 1. combinatorics, number theory – 2. functional analysis – 3. arithmetic,
set theory – 4. planar geometry – 5. algebra, number theory – 6. combinatorial group
theory, graph theory – 7. combinatorics, games – 8. real analysis, ﬁeld theory – 9. continued
fractions, number theory – 10. combinatorial geometry.
1. Specular Colourings
1. What is the maximum number of cells of an m×n grid that can be coloured blue, such
that no two blue cells are symmetric with respect to any horizontal or vertical line of the
grid?
2. Some cells of an m×n grid are coloured blue. We call such a colouring specular if for
any interior horizontal or vertical line of the grid there are two blue cells that are symmetric
with respect to this line. Denote by S(m,n ) the minimal number of blue cells in a specular
colouring of an m×n grid.
Find S(m,n ) or estimate it (give lower and upper bounds).
Figure 1. An example of specular, but not minimal, colouring of an 8 × 15 grid.
3. Formulate and investigate 3-dimensional analogs of the problem.
Date: April 17, 2009.
1

2 ORSAY, FRANCE
2. A Functional Equation
Let k be a constant real number.
1. Find some (all) functions f : R→ R with the property that f(f(x) +kx) =xf(x) for all
real numbers x.
2. Find all solutions f : R→ R of the functional equation
(1) f(f(x) +f(y) +kxy) =xf(y) +yf (x), x,y ∈ R.
Consider the case when f is (a) a polynomial, (b) a continuous function, (c) an arbitrary
function.
3. Let n> 2 be a positive integer. Find some (all) functions f : R→ R such that
f(f(x1) +f(x2) +... +f(xn) +kx1x2...xn) =x1f(x2) +x2f(x3) +... +xnf(x1)
for all x1,x 2,...,x n∈ R.
4. Suggest and investigate other generalisations of the functional equation (1).
3. Monotonic Squares
We say that a positive integer a =akak−1...a 1a0, where 0 ⩽ai ⩽ 9 are the digits of a in
base 10, is an increasing square if a =b2 for some integer b and ak ⩽ak−1 ⩽··· ⩽a1 ⩽a0.
For instance, 13456 = 1162.
If we have the reverse inequalities ak ⩾ ak−1 ⩾··· ⩾ a1 ⩾ a0, then the square a is called
decreasing. For instance, 8874441 = 2979 2.
Let a =b2 and c =d2 be two squares with the following representations in base 10:
a =akak−1...a 1a0, b=blbl−1...b 1b0 and c =cmcm−1...c 1c0, d=dndn−1...d 1d0.
We say that a pair of squares a and c is ordered, and write a ≺ c, if the sequence
a0,a 1,...,a k−1,a k is a subsequence of c0,c 1,...,c m−1,c m and the sequence b0,b 1,...,b l−1,b l
is a subsequence of d0,d 1,...,d n−1,d n. For instance, 1156 = 34 2≺ 111556 = 3342.
A set of squares F is called a family if any pair of squares from F is ordered.
1. Find inﬁnite families of increasing squares. For instance, 1156 = 34 2≺ 111556 = 3342≺
11115556 = 33342≺... .
2. Is there any inﬁnite family of decreasing squares?
3. How many elements are in a maximal increasing family? For example, can it have exactly
(a) one increasing square? (b) two increasing squares? (A maximal increasing family F is
a family of increasing squares, such that any increasing square a with the property “either
a≺c or c≺a for all c∈F ” is already in F .)
3. How many elements can a maximal family of decreasing squares have?
4. Investigate the problem in other bases.
4. Minimality of Inscribed Polygons
We say that a polygon P is inscribed in a polygon Q if the vertices of P lie on edges of
Q, no two on the same edge. (A vertex of an inscribed polygon P is not allowed to coincide
with a vertex of the polygon Q.)

PROBLEMS FOR THE 1 st INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
1. A triangle T is inscribed in a triangle ABC, so that ABC is divided into four triangles:
T1,T 2,T 3 and T (see the picture).
(a) Is it always true that area(T ) ⩾ min{area(T1),area (T2),area (T3)}?
(b) Can T have a bisector (median, perimeter, angle, inscribed or circumscribed circle,
etc.) smaller than all bisectors (medians, perimeters, angles, inscribed or circum-
scribed circles, etc.) of the triangles T1,T 2,T 3?
A
B
C
T2
T1
T T3
Figure 2. A triangle T inscribed in a triangle ABC.
2. A convex polygon P = P1P2...P m is inscribed in a convex polygon Q = Q1Q2...Q n,
where 3 ⩽ m ⩽ n, so that Q is divided into m + 1 parts. Can the polygon P possess
a minimality property compared to the parts (for instance, can P have the smallest area,
perimeter, angle, diagonal, etc.)?
3. Formulate and investigate 3-dimensional analogs of the problem.
5. Integer-valued Polynomials
An integer-valued polynomial q(x) is a polynomial taking an integer value q(n) for every
positive integer n. Denote by Q0[x] the set of all integer-valued polynomials with rational
coeﬃcients, that is
Q0[x] ={q(x)∈ Q[x]|q(n)∈ Z,∀n∈ N}.
Let p be a prime number and let Zp ={0, 1,...,p − 1} be the set of residues modulo p.
1. Describe the set of integer-valued polynomials q(x)∈ Q0[x] with the property q(n)≡
0 modp for all n∈ N.
2. Let q(x) be a polynomial from Q0[x]. Deﬁne whether the sequence ( q(n) mod p)n∈N is
periodic and, if it is, ﬁnd or estimate its period.
3. We say that a sequence (αn)n∈N of elements of Zp is realisable if there exists an integer-
valued polynomialq(x)∈ Q0[x] such that q(n)≡αn modp for all n∈ N. Describe the set of
realisable sequences.
4. Let (αn)n∈N be a realisable sequence. Describe the set of integer-valued polynomials
q(x)∈ Q0[x] such that q(n)≡αn modp for all n∈ N.
5. Describe the set Q0[x].
6. Pattern Graphs
Letn be a positive integer. A pattern of length n is a two-line table a1 a2 ... a n
b1 b2 ... b n
, where
a1,a 2,...,a n and b1,b 2,...,b n are some rearrangements of the numbers 1, 2,...,n .

4 ORSAY, FRANCE
Deﬁne two operations A and B on patterns as follows
A : replace each number a of the ﬁrst line with the number that is in the a’th place (from
left to right) of the second line,
B : replace each number b of the second line with the number that is in the b’th place
(from left to right) of the ﬁrst line.
We can construct an oriented labelled graph Gn whose vertices are all the patterns of
length n, and such that for any two vertices v and w there is an A-arrow (resp. a B-arrow)
from v to w if the pattern w is obtained from the pattern v by applying the operation A
(resp. the operation B).
123
213
213
213
213
123B
A
A
B
A
B
123
132
132
132
132
123B
A
A
B
A
B
123
321
321
321
321
123B
A
A
B
A
B
312
123
312
231
123
231
312
312
231
231
123
312
231
312
231
123
A
B
B A B
A
A
B A
B
B
A
A B A
B
123
123A B
312
132
312
213
213
132
321
213
213
231
321
231
132
231
132
321
312
321
A
B
B
ABA
B
A
A
B
A
B
A
BB
A
B
A
Figure 3. The graph G3 has 7 connected components (the 7th one with 9 vertices is not
shown on the picture).

PROBLEMS FOR THE 1 st INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
1. Can the pattern 2 1 3 4 ... n − 1 n
2 3 4 5 ... n 1 be obtained from the pattern
2 3 1 4 ... n − 1 n
2 3 4 5 ... n 1 using the operations A and B?
2. How many connected components of the graph Gn have exactly (a) 2 patterns? (b) 3
patterns?
3. Denote by gn the number of connected components of the graph Gn. Find gn (give a
formula) or estimate it (give lower and upper bounds).
4. Study geometric properties of the connected components ofGn. Can they be drawn nicely
in the plane: without intersections of the edges, symmetrically, etc.?
5. As a generalisation one could consider three-line patterns with 3 · 2 = 6 operations on
them. Investigate this generalisation.
7. Placements of Pentominoes
1. Given an m×n rectangle, denote by T (m,n ) the minimum number of non-overlapping
pentominoes that must be placed (along the grid lines) so that there is no place on the
free cells for another pentomino? Find or estimate the numberT (m,n ) and give an algorithm
for constructing suitable placements.
Figure 4. A placement of pentominoes on a 6 × 7 rectangle: T (6, 7) = 3.
2. Two players alternately place pentominoes on the free cells of an m×n rectangle,
along the grid lines. The loser is the one who cannot place a pentomino. Does any player
have a winning strategy?
3. Study the previous questions for other polyominoes.
8. Positivity of Symmetric Polynomials
A polynomial P (x,y ) with real coeﬃcients is symmetric if the equality P (x,y ) = P (y,x )
holds for all x,y∈ R.
1. Let P (x,y ) = x3 +ax2y +axy2 +y3 be a symmetric polynomial of degree 3. Prove that
P (x,y )> 0 for all x,y >0 if and only if a> −1.
2. Let P (x,y ) =x4 +ax3y +bx2y2 +axy3 +y4 be a symmetric polynomial of degree 4.
(a) Prove that P (x,y ) > 0 for all x,y > 0 if and only if a <−4, b > a2+8
4 or a ⩾−4,
b> −2a− 2.
(b) Prove that P (x,y ) > 0 for all x,y ̸= 0 if and only if |a| > 4, b > a2+8
4 or|a| ⩽ 4,
b> 2|a|− 2.

6 ORSAY, FRANCE
3. Let P (x,y ) be one of the following symmetric polynomials:
x5 +ax4y +bx3y2 +bx2y3 +axy4 +y5,
x6 +ax5y +bx4y2 +cx3y3 +bx2y4 +axy5 +y6,
x7 +ax6y +bx5y2 +cx4y3 +cx3y4 +bx2y5 +axy6 +y7.
Find necessary and suﬃcient conditions on the coeﬃcients such that P (x,y ) > 0 for all (a)
x,y >0, (b) x,y̸= 0.
4. Find suﬃcient conditions for a homogeneous symmetric polynomial P (x,y ) of degree
n> 7 to take positive values for all (a) x,y >0, (b) x,y̸= 0.
5. Using methods developed in the previous questions, give necessary and suﬃcient conditions
for a non-homogeneous symmetric polynomial of two real variables to be positive.
9. Good Numbers
Any rational number x may be expressed as a continued fraction
x =a0 + 1
a1 + 1
a2 +
...
+ 1
am
where a0 is the integer part of x, and the numbers a1,a 2,...,a m are positive integers called
partial quotients of x. We will also write x = [a0;a1,a 2,...,a m].
1. Find all numbersn> 2 that can be expressed as the sum of two positive integersn =a+b
so that a<b and the continued fraction for a/b has all its partial quotients equal to 1. For
example, 13 = 5 + 8 and 5/8 = [0; 1, 1, 1, 1, 1].
2. A numbern> 2 is called 2-good if for some positive integers a<b we haven =a +b and
the partial quotients ofa/b are equal to 1 or 2. For example, 11 = 4+7 and 4/7 = [0; 1, 1, 2, 1].
(a) Are there inﬁnitely many odd numbers that are not 2-good?
(b) Is it true that any even positive integer, greater than 6, is the sum of two distinct odd
2-good numbers? If it is not, ﬁnd all even numbers with this property.
(c) Describe the set of all 2-good numbers.
3. In general, a number n is called k-good if it can be expressed as the sum of two positive
integersn =a+b so thata<b and the continued fraction fora/b has all its partial quotients
not greater than k.
Does there exist a positive integer K such that all positive integers n> 2 are K-good?
4. Describe the set of numbersn with the property: there exist two coprime positive integers
b>a such that n =b +a or n =b−a and the partial quotients of a/b are equal to 1 or 2.
5. Suggest and study additional directions of research
10. Centro-Symmetric Shadows
A set of points in the plane is said to be centro-symmetric if it has a centre of symmetry.
For example, the vertices of a square form a centro-symmetric set. (Recall that a centre of

PROBLEMS FOR THE 1 st INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
symmetry of a set S in the plane is a point c with the property that for any point p∈ S
there exists a point p′∈S such that p andp′ are equidistant from c and lie on a line passing
thoughtc.)
Given a set of points, its shadow on a line is its orthogonal projection onto this line.
1. Let n ⩾ 3 be a positive integer. Denote by k(n) the minimum positive integer k with the
following property:
for any set S of n points in the plane, if there exist k lines, no two parallel,
such that for each line the shadow of S on this line is centro-symmetric, then
the initial set S is also centro-symmetric.
Find or estimate the number k(n).
Figure 5. A set of 11 points with 4 centro-symmetric shadows: k(11)> 4.
2. Formulate and study 3-dimensional analogs of the problem.
Laboratory of Mathematics, University Paris-Sud 11, 91400 Orsay, FRANCE
E-mail address : organizers.itym@gmail.com
URL: http://www.itym.org/
