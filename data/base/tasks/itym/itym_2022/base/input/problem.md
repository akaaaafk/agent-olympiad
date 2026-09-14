PROBLEMS FOR THE 14th INTERNATIONAL TOURNAMENT OF
YOUNG MATHEMATICIANS
OCTOBER–NOVEMBER 2022
Contents
Notation 1
1. Preﬁx Sequences 1
2. Free Triangulations 2
3. Towers of Bricks 3
4. Maximizing Distances 4
5. Random Walks on Finite Graphs 5
6. Integration of Sequences 6
7. Chromatic Polynomials of Numbered Graphs 7
8. Lines over Finite Rings 9
9. Decompositions of Integer Matrices 9
10. Boundary Points of Special Spaces 10
Keywords: 1. divisibility, sequences – 2. counting, conﬁgurations of points, triangulation
– 3. additive number theory, diagrams – 4. combinatorial geometry, optimisation – 5. graphs,
random walks, probability – 6. discrete integration, sequences, density – 7. labeled graphs,
chromatic polynomial – 8. algebra, modular equations – 9. linear algebra, integer matrices –
10. functional analysis, sequences
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Zn ={0, 1,...,n−1}ring of residue classes modulon
Z, Q, R, C sets of integer, rational, real and complex numbers
]a,b [ and [a,b ] open and closed interval froma to b
[ [a,b ] ] set of integers froma to b
Z[i] ring of Gaussian integersZ[i] ={a +bi|a,b∈Z}
Zn×n set of integer square matrices of dimensionn
Z[t] and Q[t] rings of polynomials with integer and rational coeﬃcients
|x| absolute value ofx
#M or|M| cardinality of a setM
M×N Cartesian product of two sets or graphsM and N
M∪N,M \N,M \N union, intersection and diﬀerence of two setsM and N
1. Preﬁx Sequences
Let (ak) = a1,a 2,...,a k,... be a sequence of positive integers, and letn∈N be a positive
integer. The n-preﬁx of(ak) is the sequence (bk) constructed as follows: the number bk is
the smallest positive integer such thatbkak is divisible by n, where x denotes the decimal
expansion ofx. For example, if (ak) = 1, 2, 3, 4, 5, 6,... is the sequence of natural numbers,
then its 3-preﬁx is the periodic sequence2, 1, 3, 2, 1, 3,....
Try to answer the questions 1–3 below when(ak) is:
©International Tournament of Young Mathematicians. This work is licensed under a “CC BY-SA 4.0” license.
Date: September 22, 2022.
1

2 OCTOBER–NOVEMBER 2022
a) the sequence of natural numbers1, 2, 3, 4, 5,...;
b) an arithmetic sequence:ak+1 =ak +d for somed∈N and allk∈N;
c) a geometric sequence:ak+1 =ak·q for someq∈N and allk∈N;
d) the Fibonacci sequence1, 1, 2, 3, 5,...;
e) a recursive sequence:ak+2 = αak+1 + βak for some α, β∈Z and allk∈N;
f) the sequence of primes2, 3, 5, 7, 11,...;
g) another sequence of your choice;
h) an arbitrary sequence.
1. Determine whether then-preﬁx of(ak) contains all integers from 1 ton.
2. Determine whether then-preﬁx of(ak) is periodic.
3. Find a formula for then-preﬁx of(ak).
4. Find necessary and/or suﬃcient conditions for two sequences to have the samen-preﬁx, if
these two sequences are:
a) both arithmetic (with diﬀerencesd1 and d2);
b) both geometric (with ratiosq1 and q2);
c) an arithmetic (with diﬀerenced) and a geometric (with ratioq);
d) both recursive (with coeﬃcientsα1, β1 and α2, β2);
e) arbitrary.
5. Introduce the notion of then-postﬁx of(ak) and study similar questions.
6. Suggest and investigate other directions of research.
2. Free Triangulations
A setS ={P1,...,P 3n}of 3n points in the real plane is given, and no three of these points
are on the same line. Afree triangulationofS is its partition inton triples of points such that
the triangles with vertices at the triples are pairwise disjoint (the triangles don’t have common
inner or boundary points). See examples in Figure 1.
Figure 1. Two free triangulations of the set of vertices of a regular dodecagon.
Denote byf3(S) the number of distinct free triangulates ofS. (Two diﬀerent partitions ofS
give distinct triangulations.)
1. Prove thatS has at least one free triangulation.
2. Show that the inequalityf3(S)≥3 is true for any setS when n≥2.
3. Try to ﬁnd a better lower bound forf3(S) in terms ofn.
4. Find a formula forf3(S) when S is the set of vertices of a regular3n-gon.
5. Find a formula forf3(S) for other particular families of pointsS.
6. Find upper bounds forf3(S) in terms ofn.

PROBLEMS FOR THE 14th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
7. Givenn, describe the setsS of 3n points for whichf3(S) attains its maximum value.
8. In general, letk≥3 and n be positive integers, and letS be a set ofkn points in the
real plane with no three on the same line. Consider the numberfk(S) of partitions ofS into
k-tuples such that one may drawk-gons with vertices at thek-tuples, that don’t intersect each
other. Find lower and upper bounds forfk(S). Try to ﬁnd a formula for particular setsS.
9. LetS beasetof npointsintherealplanewithnothreeonthesameline. Let n =a1+···+ak
be a decomposition ofn into a sum of positive integers more than 2. Does there exist a partition
ofS into ana1-tuple, ..., an ak-tuple so that thek polygons with vertices at these tuples might
be constructed to beconvex and pairwise disjoint? Give an algorithm that checks this and
ﬁnds such a partition if it exists.
10. Suggest and investigate additional directions of research.
3. Towers of Bricks
Let n and k≤n be positive integers. Atower ofn bricks withk ﬂoorsis a sequence ofk
positive integers (u1,u 2,...,u k) such thatu1 +u2 +···+uk =n and
ui+1≥u1 +···+ui for all 1≤i≤k−1.
Denote bya(n,k ) the number of towers ofn bricks withk ﬂoors, and leta(n) =∑n
k=1a(n,k )
be the number of all towers ofn bricks.
Figure 2. A tower of 17 bricks with 4 ﬂoors (u1 = 1,u 2 = 3,u 3 = 4,u 4 = 9).
1. Determine the maximum number of ﬂoors that a tower ofn bricks can have.
2. Give a formula in terms ofn or ﬁnd bounds for
a) a(n, 2);
b) a(n, 3);
c) a(n,k ) with k >3.
3. Find lower/upper bounds and an asymptotic fora(n).
4. Find necessary and/or suﬃcient conditions onn so that
a) a(n) is even;
b) a(n) is divisible by2b for a positive integerb> 1.
5. Let m and n be positive integers. Find necessary and/or suﬃcient conditions onn so that
a) a(m)≡a(n) modulo 4;
b) a(m)≡a(n) modulo 2b for a positive integerb> 2.
6. In general, given a primep and a positive integerb, describe all numbersn∈N such that
a(n) is divisible bypb.
7. Suggest and study additional directions of research.

4 OCTOBER–NOVEMBER 2022
4. Maximizing Distances
Consider the Euclidean planeR2. The Euclidean distance is the functiond2 : R2×R2→R
such that
d2
(
(x1,y 1), (x2,y 2)
)
=
∑
(x2−x1)2 + (y2−y1)2.
Given n-points with coordinates (x1,y 1),..., (xn,y n)∈R2, let us denote byS2 the sum of
all pairwise distances between them:
S2
(
(x1,y 1),..., (xn,y n)
)
=
∑
1≤i<j≤n
d2
(
(xi,y i), (xj,y j)
)
.
See an example of such a sum for four points in Figure 3.
5
4
√13
3
√
50
√53
(0, 3)
(4, 0)
(4, 3)
(−3, 1)
Figure 3. S2
(
(−3, 1), (0, 3), (4, 0), (4, 3)
)
= 12 +
√
13 +
√
50 +
√
53.
In this problem,Ω will stand for a convex compact subset ofR2, that is:
•for any two points(x1,y 1), (x2,y 2)∈Ω and anyt∈[0, 1], one has
(tx1 + (1−t)x2, ty1 + (1−t)y2)∈Ω;
•for any sequence of points (x1,y 1),..., (xn,y n),... from Ω, if both limn→∞xn and
limn→∞yn exist, then the point(limn→∞xn, limn→∞yn) is also inΩ;
•Ω is contained in a disc ofR2.
We are interested in ﬁnding the following expression:
M2(Ω,n ) = max
{
S2
(
(x1,y 1),..., (xn,y n)
)
|(x1,y 1),..., (xn,y n)∈Ω
}
which is the maximum value taken byS2 on a set ofn points from Ω.
For a positive integerd, denote byΩ d the full regulard-gon whose vertices are on the circle
of radius 1. For instance, Ω 1 is a point, Ω 2 is a line segment of length2 and Ω 3 is a regular
triangle with side length
√
3.
1. Check that Ω d is a convex compact subset.
2. Givenn∈N, determineM2(Ω,n ) when:
a) Ω = Ω 2;
b) Ω = Ω 3;
c) Ω = Ω d for anyd> 3;
d) Ω is a disc of radius1;
e) Ω = Ω a,b={(x,y∈R2, x2
a2 + y2
b2 ⩽ 1}is an ellipse with width2a> 0 and height2b> 0.
3. For each of the above subsets, describe the conﬁgurations of points(x1,y 1),..., (xn,y n)∈Ω
for which the maximumM2(Ω,n ) is reached.
4. Among the convex compact subsets ofΩ ⊂R2 of area 1, which of them have the largest
value ofM2(Ω,n )?

PROBLEMS FOR THE 14th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
5. Given d, ﬁnd all positive integers n ∈N for which there exist n + 1 points
(x1,y 1),..., (xn+1,y n+1)∈Ω d satisfying the two following relations at the same time:



S2
(
(x1,y 1),..., (xn,y n)
)
=M2(Ω d,n ),
S2
(
(x1,y 1),..., (xn+1,y n+1)
)
=M2(Ω d,n + 1).
6. Given n, describe the convex compact subsets of Ω ⊂R2 which contain n + 1 points
(x1,y 1),..., (xn+1,y n+1) satisfying the two following relations at the same time:



S2
(
(x1,y 1),..., (xn,y n)
)
=M2(Ω,n ),
S2
(
(x1,y 1),..., (xn+1,y n+1)
)
=M2(Ω,n + 1).
7. In the previous questions, what happens if we replace the functionS2 by the functionSp
such that
Sp
(
(x1,y 1),..., (xn,y n)
)
=
∑
1≤i<j≤n
p
∑
|xi−yi|p +|xj−yj|p
for a parameterp∈[1, +∞[?
8. Investigate a similar problem inR3.
9. Suggest and investigate additional directions of research.
5. Random Walks on Finite Graphs
LetG = (V,E ) be a simple ﬁnite graph drawn in the real plane, whereV is its set of vertices
and E is its set of edges. Two vertices are said to beneighbours or neighbouring if they are
connected by an edge. In the beginning, a beetle is situated at some vertexa of the graph.
Every second it either moves to one of the neighbouring vertices or stays where it is, all with
equal probabilities. For instance, ifG is the 4×4 square grid anda is the lower left corner
vertex as in Figure 4, then after 1 second it can still be at the corner with probability 1/3 or
at one of its two neighbours with probabilities 1/3. Denote byP n
a (v) the probability that after
n seconds the beetle will be at the vertexv.
a a v
w
Figure 4. A 4×4 square grid with a beetle at the lower left cornera, and two
verticesv and w such thatv≤a w.
For two verticesv,w ∈V, we will writev≤a w if there exists a shortest path froma to w
that passes throughv (see Figure 4).
1. Let G be them×k square grid for some natural numbersm and k that are the lengths of
the sides of the grid. Determine all pairs of verticesv and w such that
v≤a w and P n
a (v)≥P n
a (w). (1)
Consider the following cases:
a) m =k = 3, n = 6 and a is the lower left corner vertex ofG;
b) m =k = 5, n = 10 and a is the lower left corner vertex ofG;
c) m =k = 3 or 5, the vertexa is at the lower left corner ofG but n is arbitrary;
d) m =k = 3 or 5 but a and n is arbitrary;

6 OCTOBER–NOVEMBER 2022
e) m, k, n and a are arbitrary.
2. Find all verticesv and w satisfying (1) for a given starting vertexa when G is
a) a ﬁnite triangular grid;
b) an inﬁnite triangular grid;
c) a ﬁnite hexagonal grid.
d) an inﬁnite hexagonal grid.
e) a regular tree of degreed (the inﬁnite tree withd edges at each vertex).
3. Investigate an analogous problem whenG is a 3-dimensional gridm×k×ℓ.
4. A permutohedron Ad of order d is the polytope in the d-dimensional space Rd with d!
vertices formed by permuting coordinates of the point(1, 2,...,d ) and such that two vertices
(a1,...,a d) and (b1,...,b d) are connected by an edge if and only if one can be obtained from
the other by swapping two coordinates, whose values diﬀer by 1. Investigate the analogous
problem for the permutohedronAd.
5. Now, suppose that the beetle cannot stay where it is and always moves to one of the
neighbouring vertices. Try to understand how it aﬀects the ordering of probabilities.
6. Suggest and study additional directions of research.
6. Integration of Sequences
Let X be a nonempty set of real numbers, and letW be a family of subsets ofX such that
∅∈W and X∈W. Let p : W →[0, +∞[ be an additive function onW, that is, for any
elementE∈W and any partition{Ei}n
i=1 of E with n∈N and E1,...,E n∈W, one has
p(E) =
n∑
i=1
p(Ei).
(A partition of a set is a collection of its subsets which are pairwise disjoint and whose union
is the entire set. For example,{{1, 2},{3},{4, 5, 6}}is a partition of the set{1, 2, 3, 4, 5, 6}.)
The triple(X,W,p ) will be calledadmissible if, for any bounded real functionf :X→R, any
partitions{Ei}n
i=1⊆W and{Dj}k
j=1⊆W ofX and any real numbersm1,...,m n,M 1,...,M k,
the condition that
f(Ei\Dj)⊆[mi,M j] for all 1≤i≤n and 1≤j≤k (2)
implies the inequality
n∑
i=1
mip(Ei)≤
k∑
j=1
Mjp(Dj).
Moreover, if for such a functionf, there exists a unique numberI such that
n∑
i=1
mip(Ei)≤I≤
k∑
j=1
Mjp(Dj)
for any Ei,D j,m i,M j as above satisfying (2), then f is said to be Riemann integrable on
(X,W,p ) and I is called itsintegral.
The pair (X,W ) is said to be aRiemann pair if the triple (X,W,p ) is admissible for any
additive functionp on W.
1. Denote by W∗the set W excluding the trivial elements ∅ and X. Determine whether
(X,W ) is a Riemann pair in the following cases:
a) X ={1, 2, 3, 4, 5, 6}and W∗={{1, 2},{2, 3},{3, 4},{4, 5},{5, 6},{6, 1}};
b) X is a ﬁnite set andW∗is the family of all its subsets of cardinality 2;

PROBLEMS FOR THE 14th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
c) X is a ﬁnite set andW∗is the family of all its subsets of cardinalityℓ∈N;
d) X is a ﬁnite set andW∗is the family of all its nonempty subsets of cardinality at mostℓ.
2. Suppose thatX = N is the set of natural numbers, and letW be the family of all subsets
E⊆X such that eitherE or X\E is ﬁnite.
a) Is (X,W ) a Riemann pair?
b) Let p : W →[0, +∞[ be the function such that, for anyE∈W, one hasp(E) = 0
if E is ﬁnite andp(E) = 1 if X\E is ﬁnite. Find alld∈N for which the function
f(x) = sin(xd) and/or f(x) = sin(dx) is Riemann integrable on(X,W,p )?
c) Is it true that a bounded functionf :X→R is Riemann integrable on(X,W,p ) if and
only if limn→+∞f(n) exists?
3. Suppose thatX = N is the set of natural numbers, and letW be the family of all subsets
E⊆X for which the following limit exists (also called thedensity of E):
p(E) = limn→+∞
|E\ [1,n ]|
n . (3)
a) Show that the functionp deﬁned in (3) is additive onW.
b) LetA,B∈W. Is it true thatA\B, A∪B and/or A\B also belong toW?
c) Let B ∈W. Is it true that, for any number α∈[0,p (B)], there exists an element
A∈W such thatA⊆B and p(A) = α?
d) Determine whether the following sets belong toW and, if yes, ﬁnd their densities:
– an arithmetic sequence with diﬀerenced∈N;
– the set of Fibonacci numbers;
– the set of primes;
– the set of indices of the primes of the form4k + 3 in the sequence of primes
p1 = 2,p 2 = 3,p 3 = 5,p 4 = 7,....
e) Is the triple(X,W,p ) admissible?
f) Is (X,W ) a Riemann pair?
4. Let the triple (X,W,p ) be as in the previous question, and letf : X→R be a bounded
function. Determine interconnections between the following assertions (ﬁnd out whether from
any of them follows another):
a) limn→+∞f(n) exists;
b) limn→+∞
f (1)+···+f (n)
n exists;
c) the functionf is Riemann integrable on(X,W,p );
d) for any ﬁnite interval]a,b [⊆R, the preimagef−1 (]a,b [) belongs toW.
5. Check the properties a)–d) of the previous question for the functionsf(x) = sin( cx),
f(x) = arcsin(cx), f(x) = sin(sin(cx)), f(x) = sin(xd) and f(x) = sin(dx), wherec∈R and
d∈N are constants. Find the limits and the integrals if they exist.
6. Suggest and study additional directions of research.
7. Chromatic Polynomials of Numbered Graphs
Let G = (V,E,λ) be a simple undirected labeled graph, whereV is its vertex set,E is its
edge set and λ: E →N is a labeling of its edges with positive integers. A proper vertex
k-numbering of G is a labelingν: V →{1,...,k}of its vertices with integers from1 to k

8 OCTOBER–NOVEMBER 2022
satisfying the following condition: if any two verticesu andv are connected by an edgee, then
|ν(u)−ν(v)|≥λ(e).
Note that it is not necessary that all the integers from1 to k are used (see also Figure 5).
9
4
7
5
7
1
2
2
1
2
2
Figure 5. A proper vertex9-numbering of a labeled graph.
Denote byNG(k) the number of properk-numberings of a given labeled graphG = (V,E,λ).
In the questions1-6 below, we additionally suppose thatλ(e)∈{1, 2}for alle∈E.
1. Prove that there exists a unique polynomialpG(t)∈Q[t] with rational coeﬃcients such that
for some constantk0∈N (depending only onG andλ) and allk≥k0, one haspG(k) =NG(k).
We callpG(t) the chromatic polynomial ofG.
2. Prove thatpG(t)∈Z[t], that is, the coeﬃcients ofpG(t) are in fact integers.
3. Show the following statements aboutpG(t):
a) its degree equals the numbern =|V|of vertices ofG;
b) its leading coeﬃcient is1;
c) the coeﬃcient attn−1 equals|E|−2S(G), where|E|is the number of edges ofG and
S(G) =∑
e∈Eλ(e) is the sum of the edge labels ofG.
4. Compute (as many as you can) the remaining coeﬃcients ofpG(t).
5. Denote byG−e = (V,E \{e},λ) the graph obtained fromG by deleting its edgee but
preserving all the vertices and all other edges’ labels:λ(h) =λ(h) for allh∈E\{e}.
a) Prove that ife is an edge with label1, then the diﬀerencepG−e(t)−pG(t) is actually
the chromatic polynomial of another labeled graphH:
pH(t) =pG−e(t)−pG(t).
Relate the graphH to the graphG.
b) Try to ﬁnd a similar relation for the edges with label2.
6. Is it true that the coeﬃcients ofpG(t) alternate in sign, that is,pG(t) = ∑n
i=0(−1)iaitn−i
for some nonnegative integersa0,...,a n?
7. When ispG(t) irreducible over Z?
8. Find other properties of chromatic polynomials.
9. Study the previous questions in a more general setting, for example, when the edge labels
can be more than 2.
10. Suggest and study additional directions of research.

PROBLEMS FOR THE 14th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 9
8. Lines over Finite Rings
Let Zn ={0, 1,...,n−1}be the ring of residues modulo a positive integern. For any two
elementsa,b∈Zn, we consider the set
L(a,b,n ) =
{
(x,y )∈Z2
n |a·x +b·y = 0
}
and call it theline over Zn with coeﬃcientsa and b.
1. Givenn, what can the cardinality of a line overZn be?
2. Givenn, ﬁndallpossiblevaluesofthecardinality |L(a1,b 1,n )\L(a2,b 2,n )|oftheintersection
of two lines overZn.
3. Given n and (a,b )∈Z2
n, ﬁnd the cardinality|
{
(a1,b 1)∈Z2
n |L(a1,b 1,n )⊆L(a,b,n )
}
|,
that is the number of the lines contained in the lineL(a,b,n ).
Let Zn[t] be the ring of polynomials with coeﬃcients in Zn, and let f(t) ∈Zn[t] be a
polynomial. Recall thatZn[t]/(f(t)) denotes the quotient ring of polynomials in which addition
and multiplication are deﬁned modulof(t). For example, Z2[t]/(t2 +t + 1) consists of four
elements 0, 1,t and t + 1.
Put R = Zn[t]/(f(t)) and introduce, for any two elementsa(t) and b(t) from R, the set
LR(a,b,n ) =
{
(p,q )∈R2 |a(t)·p(t) +b(t)·q(t)≡0
}
that we will call theline overR with coeﬃcientsa and b.
4. Solve the problems similar to the questions 1, 2, and 3 above, whenf(t) is a polynomial of
second degree and
a) n is prime;
b) n is any positive integer.
5. Suggest and study further generalizations and additional directions of research.
9. Decompositions of Integer Matrices
For anyn×n real matrixA, there are well-known classical decompositions:
•LU decomposition: A = LU, where L is a lower triangular matrix, U is an upper
triangular matrix.
•Symmetric decomposition: A =S1S2, whereS1 and S2 are two symmetric matrices.
•Jordan-Chevalley decomposition: A =N +S, whereS is a semi-simple matrix,N is a
nilpotent matrix andSN =NS.
Denote by Zn×n the set of all matrices withn rows and columns and integer entries (square
integer matrices of dimensionn).
1. Let A∈Zn×n be an integer matrix.
a) Find necessary and/or suﬃcient conditions onA so that there exists a decomposition
of the above type (LU, symmetric or Jordan-Chevalley) intointeger matrices.
b) Is such a decomposition unique? If not, describe all possibilities.
2. A matrixB∈Zn×n is calledprime if|det(B)|is a prime number.
a) Isittruethat, forevery A∈Zn×n with det(A)̸= 0, thereexist(notnecessarilydiﬀerent)
prime matricesB1,...,Bk∈Zn×n such thatA =B1···Bk?
b) Is such a decomposition unique? If not, describe all possibilities. Start withn = 1, 2.

10 OCTOBER–NOVEMBER 2022
A matrixE∈Zn×n is calledunit if|det(E)|= 1. We say that two integer matricesA andB
are weakly similarif there exist unitsE andF such thatEAF =B. We say they aresimilar if
there is a unitE such thatEAE−1 =B. We say that they arestrongly similarif there exists
a unitE which is orthogonal (that is,ETE =In) and such thatEAE−1 =B.
3. Is it true that every integer matrix is weakly similar to a diagonal matrix?
4. Describe all integer matrices that are similar (weakly similar, strongly similar) to a diagonal
matrix.
5. Describe all integer matrices that are similar (weakly similar, strongly similar) to an upper
triangular matrix.
6. Study existence and uniqueness of other classical decompositions (QZ-decomposition, sin-
gular value decomposition, etc.) for integer matrices.
7. Study similar questions for matrices with entries from the set of Gaussian integersZ[i] =
{a +bi|a,b∈Z}.
8. Suggest and study additional directions of research.
10. Boundary Points of Special Spaces
A ﬁnite subset of natural numbersF ⊂N will be calledgood if its cardinality isn’t larger
than its minimal element:|F|≤minF. A good set F is called perfect if|F|= minF. For
example, the set{5, 8, 13}is good while the set{5, 8, 13, 14, 17}is perfect.
A sequence (xk) = x1,x 2,...,x k,... of real numbers will be calledspecial if the following
two conditions are satisﬁed:
(i) ∑
i∈F
|xi|≤1 for all good setsF;
(ii) ∑
i∈F
|xi|= 1 for at least one good setF (such a set is calledmaximal for the sequence).
Denote byS the space of all special sequences. An element(xk)∈S will be called aboundary
point, if from the equality
(xk) =t·(yk) + (1−t)·(zk) for some elements(yk), (zk)∈S and a real numbert∈]0, 1[
necessary follows that(xk) = (yk) = (zk).
1. Find all boundary points(xk) of S with xk = 0 for allk >6.
2. Prove that for any boundary point(xk) of S one hasx1 =±1.
3. Prove that the following sequence is a boundary point ofS:
1, 2
5, 3
5, 1
5, 1
5, 1
5, 1
5, 1
5, 1
5, 1
5, 0, 0,....
4. LetF be a maximal set for an element(xk)∈S. Suppose that(xk) =t·(yk) + (1−t)·(zk)
for some (yk), (zk)∈S and t∈]0, 1[. Show thatF is also maximal for(yk) and (zk).
5. Prove that, for any boundary point(xk)∈S with ﬁnitely many non-zero terms, there exists
exactly one maximal non-perfect setF such thatxi̸= 0 for alli∈F.
6. Prove that, for any boundary point(xk)∈S with n nonzero terms, there exist at leastn
diﬀerent maximal setsF such thatxi̸= 0 for alli∈F.
7. Does the space S have inﬁnitely many boundary points? Try to ﬁnd as many boundary
points as possible.

PROBLEMS FOR THE 14th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 11
8. Try to describe all boundary points ofS.
9. Let c >0 be a rational number. A ﬁnite subset of natural numbersF⊂N will be called
c-good if|F|≤c·minF. Extend and study the problem forc-good sets instead of good sets.
10. A ﬁnite subset of natural numbersF ⊂N will be calledsquare-good if|F|≤(minF )2.
Investigate an analogous problem by considering square-good sets instead of good sets.
11. Suggest and study additional directions of research.
Email address: oc@itym.org
URL: http://www.itym.org/
