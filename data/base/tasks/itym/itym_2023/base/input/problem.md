PROBLEMS FOR THE 15th INTERNATIONAL TOURNAMENT OF
YOUNG MATHEMATICIANS
NOVEMBER 2023
Contents
Notation 1
1. Graphs of Sequences 1
2. Counting Polygons 2
3. Divisibility of Polynomials 3
4. A Game on Rectangles 3
5. An Articulated Robot 4
6. Diophantine Equations 5
7. Pseudoprimes of Matrices 5
8. Mixing Cocktails 6
9. Triangles on Curves 6
10. Maximal Number of Subgraphs 7
Keywords: 1. sequences, graphs – 2. combinatorial geometry, polygons – 3. algebra,
polynomials – 4. game theory, polyominoes – 5. optimisation – 6. Diophantine equations,
congruence – 7. matrices, primes – 8. percentage, coverings – 9. curves, locus, triangles – 10.
extremal graph theory, bipartite graphs
Notation
N ={1,2,3, . . .} set of natural numbers (positive integers)
Zn ={0,1, . . . , n−1}ring of residue classes modulon
Z, Q, R, C sets of integer, rational, real and complex numbers
Rn n-dimensional real space
]a, b[ and [a, b] open and closed interval froma to b
det(A) or|A| determinant of a matrixA
|x| absolute value ofx
#M or|M| cardinality of a setM
M×N Cartesian product of two sets or graphsM and N
M∪N, M\ N, M\N union, intersection and diﬀerence of two setsM and N
1. Graphs of Sequences
Let s = s1, s2, . . . , sk, . . .be a sequence of positive integers, and letn∈N be a positive
integer. Consider the graphG = Gn(s) with set of verticesV ={1,2, ..., n}and the following
set of edges: two vertices x and y of G are connected by an edge if and only if the number
P (x, y) = x + y is a member of the sequences. The functionP will be called theparameter of
the graph G.
We would like to investigate this graph whens is:
a) an arithmetic sequence:ak+1 = ak + d for some d∈N and all k∈N;
b) a geometric sequence:ak+1 = ak·q for some q∈N and all k∈N;
c) the Fibonacci sequence1,1,2,3,5, . . .;
©International Tournament of Young Mathematicians. This work is licensed under a “CC BY-SA 4.0” license.
Date: September 4, 2023.
1

2 NOVEMBER 2023
d) a recursive sequence:ak+2 =αak+1 +βak for someα,β∈Z and all k∈N;
e) the sequence of primes2,3,5,7,11, . . .;
f) the sequence of binomial coeﬃcients
(k
2
)
;
g) another sequence of your choice;
h) an arbitrary sequence.
1. What is the number of connected components ofG?
2. How many edges doesG have?
3. What are possible lengths of cycles?
4. Study other properties ofG.
5. Let now P (x, y) = x·y. Answer the questions above for the corresponding graphG.
6. Same questions whenP (x, y) = ax2 + bxy + cy2 is a quadratic polynomial.
7. Consider other functions as parameters.
8. Suggest and investigate other directions of research.
2. Counting Polygons
Let L be one of the following sets of points in the real plane:
a) the vertices of a regular polygon;
b) a circle;
c) a parabola;
d) Z2;
e) a triangular grid;
f) the entireR2.
For the following functions, give lower and/or upper bounds, and an asymptotic behaviour.
Try to ﬁnd an explicit formula or recurrence relations.
1. The maximum possible number of equilateral triangles among the polygons with vertices in
arbitrary n points of the setL, denoted byEL(n).
2. The maximum possible number of isosceles triangles among the polygons with vertices in
arbitrary n points of the setL, denoted byIL(n).
3. The maximum possible number of right triangles among the polygons with vertices in
arbitrary n points of the setL, denoted byRL(n).
Figure 1. When L is the set of vertices of a regular 12-gon, one hasRL(5)≥5.
4. The maximum possible number of squares among the polygons with vertices in arbitraryn
points of the setL, denoted bySL(n).

PROBLEMS FOR THE 15th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
5. The maximum possible number of parallelograms among the polygons with vertices in
arbitrary n points of the setL, denoted byPL(n).
6. Consider other similar functions.
7. Formulate and investigate the problem in higher dimensions.
3. Divisibility of Polynomials
1. Find all polynomialsP (x) with rational coeﬃcients such thatP (x) divides the polynomial
Q(x) = P (x2).
2. Find all polynomialsP (x) with rational coeﬃcients such thatP (k) divides P (k2) for inﬁn-
itely many positive integersk.
3. Let m > 2 be a positive integer. Characterise all polynomialsP (x) with rational coeﬃcients
such that P (x) divides the polynomialQ(x) = P (xm).
4. Let s and t be distinct positive integers. Characterise all polynomials P (x, y) with real
coeﬃcients such thatP (xs, y) divides P (xt, y).
5. Let k and m be two distinct positive integers. Characterise all polynomialsP (x, y) that
divide P (xk, ym).
6. Investigate analogous questions for polynomialsP (x, y) with rational coeﬃcients.
7. Investigate analogous questions for polynomials with coeﬃcients inZn.
8. Investigate analogous questions for polynomials with more than two variables.
9. Suggest and study other directions of research.
4. A Game on Rectangles
Let a, b and n be positive integers. Alicia and Benjamin are playing a game on ana×b
rectangle. They alternately choose a polyomino of sizen and place it on the rectangle without
overlapping. (A polyomino of size n is a ﬁgure formed by joiningn equal squares edge to edge.)
The loser is the player who cannot place a polyomino anymore. Alicia begins.
Figure 2. Placement of ﬁve polyominoes of size 5 on a6×9 rectangle.
1. On whicha×b rectangles does Alicia have a winning strategy? Consider the following cases:
a) n = 2 (there is only only type of polyominoes of size2);
b) n = 3 (there are two types of polyominoes of size3);
c) n > 3.

4 NOVEMBER 2023
2. Now, let us modify the game and allow Alicia and Benjamin to choose any polyomino of
size 1,2, . . . , n. On whicha×b rectangles does Alicia have a winning strategy?
3. Assume that it is up to Benjamin to choose the next polyomino that Alicia will have to
place, and it is up to Alicia to choose the next polyomino that Benjamin will have to place.
Who has a winning strategy? Consider the initial game and its variation.
4. Suggest and study additional directions of research.
5. An Articulated Robot
Martin, an articulated robot, spins a horizontal mechanical wheel which is divided intoN
equal sectors numbered from0 to N−1 counterclockwise. An arrow is ﬁxed on the ground.
At the beginning it is pointing to the sector number0 as shown in Figure 3.
0
1
2
3
4
5
6
7
Figure 3. A mechanical wheel forN = 8 and an arrow.
Since Martin’s joints are limited, he can only spin the wheel by a certain number of sectors
to the right or to the left – bya1 sectors, by a2 sectors, ..., or by aℓsectors, where 0 < a 1 <
. . . < aℓ< N and ℓ < N. Since Martin’s batteries are limited, he can spin the wheel at most
k times.
1. Suppose that ℓ= 1 and k≥N.
a) Given N and a1, what is the largest numberM on a sector that Martin can reach?
b) How many moves does it take, at the least, for Martin to reach the numberM?
c) How many diﬀerent numbers can Martin reach?
2. Solve the previous questions for anyℓ < N.
3. Something is preventing the wheel from turning clockwise. Answer the previous questions
when Martin can only rotate the wheel counterclockwise.
4. The wheel has been unlocked but Martin’s batteries are almost empty. Martin can only spin
the wheel at mostk < N times. Fortunately, he can now choose the numbersa1, . . . , aℓ∈N
as he wishes to better prepare his actions.
a) Given k and ℓ, estimate the maximum number of cells that Martin can reach over all
possible choices ofa1, . . . , aℓ∈N.
b) Estimate, as a function of k, the smallest value of ℓ for which Martin can choose
a1, . . . , aℓallowing him to reach all the sectors of the wheel.
5. Now, Martin can no longer choose in which direction to turn the wheel, and he is forced to
make exactly k = 2 moves. Estimate the smallest value ofℓfor which Martin can choose the
numbers a1, . . . , aℓallowing him to reach all the sectors of the wheel if:
a) Martin must spin the wheel twice in the same direction;
b) Martin must spin the wheel once in one direction and once in the other.

PROBLEMS FOR THE 15th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
6. Generalise and solve the previous question fork > 2.
7. Suggest and study other direction of research.
6. Diophantine Equations
1. Consider the congruencey2≡x3 + m (mod n) where m and n≥2 are given integers.
a) When n≡2 (mod 3) is a prime number, show that the number of solutions(x, y)∈
Zn×Zn does not depend onm.
b) In terms ofm, classify alln∈N for which there is at least one solution(x, y)∈Zn×Zn.
2. Consider the equationy2 + kb2 = x3 + a3. Determine all (or at least several) integersa and
b such that the equation has no solution in non-zero integersx and y when
a) k = 0;
b) k = 1;
c) k = 2;
d) k =−2;
e) k > 2.
3. Find all integer solutions(x, y) of the equations:
a) x3 + 3x2y−3xy2−y3 = 1.
b) y2 = x3−7.
4. Suggest and study additional directions of research.
7. Pseudoprimes of Matrices
Let k and n be positive integers. Let A be an n×n matrix with integer entries. Consider
the polynomial
fA,k(x) = det( Ak−xI)−det(A−xI),
where I is the identity matrix of sizen, and det(·) denotes the determinant.
1. Prove that ifk is prime, then all coeﬃcients offA,k(x) are divisible byk.
2. We say that a numberk is a pseudoprime for A if k is composite and all coeﬃcients of
fA,k(x) are divisible byk.
a) Let n≤3. Among the n×n matrices A with non-negative entries and sum of entries
at most 5, ﬁnd the one(s) whose smallest pseudoprime is largest.
b) What matrices have inﬁnitely many pseudoprimes?
3. Take n = 2. Consider the factorisationk =∏s
i=1 pαi
i into primes. Denote
g(k) = 1
2
s∏
i=1
pαi−1
i (pi + 1) and h(k) = 1
2
s∏
i=1
pαi−1
i (pi−1).
a) Is it true that for anyA and k all coeﬃcients of
det(Ak−xI)−det(Ak−2h(k)−xI)
are divisible byk?
b) Is it true that for anyA and k all coeﬃcients of
det(Ag(k)+h(k)−xI)−det(Ag(k)−h(k)−xI)
are divisible byk?

6 NOVEMBER 2023
Give a proof or a counterexample.
4. Investigate the previous question forn = 3.
5. The well-known test for prime numbers based on Fermat’s little theorem corresponds to
the case n = 1 in the question 1. Try to ﬁnd another test for prime numbers and generalise it
appropriately to matrices. Then, formulate and study an analogue to the question 2..
6. Suggest and study additional directions of research.
8. Mixing Cocktails
At a birthday party, various milk cocktails mixed withn juices are being served. Every
cocktail corresponds to a tuple ofn + 1 nonnegative real numbers (a0, a1, . . . , an), where a0
is percentage of the milk, and ai is percentage of the i-th juice (1 ≤i ≤n). Of course,
a0 + a1 +···+ an = 100.
Let f : Rn+1 →[0,+∞[ be a nonnegative function. We will say that two cocktails
(a0, a1, . . . , an) and (b0, b1, . . . , bn) areε-close if
f (a0−b0, a1−b1, . . . , an−bn) <ε.
1. Suppose that n = 2.
a) How many diﬀerent cocktails could there be at the party, if we know that no two
cocktails (a0, a1, a2) and (b0, b1, b2) satisfy the inequality:
max{|a0−b0|,|a1−b1|,|a2−b2|}< 20?
b) How many diﬀerent cocktails could there be at the party, if we know that no two
cocktails (a0, a1, a2) and (b0, b1, b2) satisfy the inequality:
|a0−b0|+|a1−b1|+|a2−b2|< 20?
2. Letε be a positive real number. Denote bydn(ε) the maximum possible number of cocktails
at a party, such that no two cocktails areε-close. Find dn(ε) or give lower and upper bounds
in the case that:
a) f (x0, x1, . . . , xn) = max{|x0|,|x1|, . . . ,|xn|};
b) f (x0, x1, . . . , xn) =|x0|+|x1|+···+|xn|.
You may start withn = 2 and 3.
3. Consider other interesting functionsf.
4. Suggest and investigate additional directions of research.
9. Triangles on Curves
Recall that the second order curve is the set of pointsR in the real plane determined by a
quadratic equation
ax2 + bxy + cy2 + dx + ey + f = 0 where a2 + b2 + c2̸= 0.
Let R be a second order curve such that there is a non-degenerate triangle whose vertices
belong to it. LetA and B be two ﬁxed points onR.
Try to solve the questions 1-5 below. You can ﬁrst consider the following simpliﬁcations of
the problem:
a) Chose a particular curve and particular points on it (for examplex2 + y2 = 2 and
A = (
√
2,0), B= (1,1)).
b) Chose a particular curve and give an answer depending on the position of pointsA and
B on it.

PROBLEMS FOR THE 15th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
c) Solve the problem for a speciﬁc type of second order curves.
1. Describe the locus of incentres of non-degenerate trianglesABC with C∈R.
2. Describe the locus of orthocentres of non-degenerate trianglesABC with C∈R.
3. Describe the locus of circumcentres of non-degenerate trianglesABC with C∈R.
4. Describe the locus of points of intersection of medians of non-degenerate trianglesABC
with C∈R.
5. Describe the locus of points of intersection of symmedians of non-degenerate trianglesABC
with C∈R.
6. Suggest and study additional directions of research.
10. Maximal Number of Subgraphs
Let H be a graph. Denote by sH (G) the number of subgraphs in a graph G which are
isomorphic to H. Let tH (n) be the maximum ofsH (G) over all graphsG with n vertices that
are triangle-free:
tH (n) = max{sH (G) |G is triangle-free and hasn vertices}.
We would like to understand for which graphsG this maximum is achieved, that is,sH (G) =
tH (n). Such graphs will be calledmaximising for H.
1. Let H be:
a) a path of length 1;
b) a four-cycle.
Find tH (n) and describe the maximising graphsG for H.
2. Are there any bipartite graphsH with a maximising graph which is not a complete bipartite
graph?
3. Suppose that H is bipartite and has a perfect matching. Does it follow that any its
maximising graph is a complete bipartite graph?
4. Can you come up with extra conditions on the graphH so that its maximising graph would
necessary be a complete bipartite graph? For instance, additional assumption onH might be:
having a matching onn−2 vertices, small radius, small diameter, large minimum degree, small
maximum degree, etc.
5. What happens if we introduce extra assumptions onG? For instance, small diameter, large
minimum degree, small maximum degree, contains no pentagons, etc. In other words, instead
of tH (n), consider another function of maximisation of sH (G) over a subset of triangle-free
graphs G with n vertices.
6. The same question for a combination of extra conditions onH and G.
7. Try to generalise the problem by takingKr-free graphs instead of triangle-free graphs.
8. Suggest and study other directions of research.
Email address: oc@itym.org
URL: http://www.itym.org/
