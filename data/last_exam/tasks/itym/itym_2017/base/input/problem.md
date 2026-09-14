PROBLEMS FOR THE 9th INTERNATIONAL TOURNAMENT OF YOUNG
MATHEMATICIANS
JULY 2017, IAŞI (ROMANIA)
Contents
Notation 1
1. Numbers from Strings 1
2. Monotonous Functions 2
3. Dense Analytic Curves 2
4. Partitions of Regular Polygons 3
5. Coin Toss Function 4
6. Rooks on Graphs 4
7. Weighted Sums of Distances 5
8. A Communication Network 6
9. An Approximation Problem 7
10. Kinds of Convexity 7
Keywords: 1. discrete optimization – 2. real analysis – 3. complex analysis – 4. combi-
natorial geometry, partition – 5. probability – 6. graph theory, combinatorics – 7. geometry,
optimization – 8. graph theory – 9. number theory – 10. convex analysis
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Zn ={0, 1,...,n−1}ring of residue classes modulon
Z, Q, R, C sets of integer, rational, real and complex numbers
R+ set of positive real numbers
Fq ﬁnite ﬁeld of sizeq =pk
M⊗N mean-product of two functionsM and N
gcd(x1,...,x n) greatest common divisor ofx1,...,x n
P [.] and E [.] probability and expectation
det(A) or|A| determinant of a matrixA
|x| absolute value ofx
#M or|M| cardinality of a setM
sup
x∈M
f (x) supremum of a set{f (x) |x∈M}
1. Numbers from Strings
1. Four fours:
a) What is the largest number we can form with 4 fours by using only the four standard
arithmetic operations? (You are allowed to concatenate several fours to obtain, for
example, 44.)
b) What is the smallest positive number?
c) How many numbers can be formed ?
Date: April 3, 2017.
1

2 JULY 2017, IAŞI (ROMANIA)
2. Five ﬁves:
a) Investigate this question for 5 ﬁves if the additional (ﬁfth) operation of exponentiation
(ab) is allowed.
b) Try another “ﬁfth operation” instead.
3. In this question we consider the number of symbols in the expression we evaluate. For
example, the string “(4 + 4)∗(4 + 4)” uses 11 characters and evaluates to64.
a) Using the digits0 to 9, the 4 operations and brackets, what is the largest number using
n symbols?
b) If we allow variables and assignment statements like “a = 32,b = 77,a∗b∗b”, what
is the largest number that can be obtained by evaluating the string with10; 15 and
20 symbols? Try to generalise. We assume here that statements may involve only 4
arithmetic operations and possibly assignments. Diﬀerent statements are separated by
comma (which also counts as a symbol!), and the ﬁnal result is the evaluated value of
the last statement in the string.
c) If we allow one-argument functionexp, what will be the result?
4. Deﬁne the “value” of a string ofn symbols as logd(eval(string)), whered = #{string}is the
number ofdiﬀerentsymbols used. What is the largest possible value of a string with5, 10, 15
symbols?
2. Monotonous Functions
Denote byf (x),g (x),h (x) some real-valued functions deﬁned for allx∈R such that:
f (x)g(x) = h(x) for allx∈R. (1)
1. Do there exist strictly increasing functionsf (x) and g(x) satisfying (1), ifh(x) = x is the
identical function? Do such functionsf (x) and g(x) exist, if in addition they are:
a) continuous for allx∈R?
b) diﬀerentiable (twice diﬀerentiable, inﬁnitely diﬀerentiable) for allx∈R?
c) entire, that is represented as a sum of the power series converging for allx∈R?
d) discontinuous at a ﬁxed ﬁnite set of points on the line?
e) discontinuous at a ﬁxed countable set of points on the line?
2. Give an answer to the above questions, ifh(x) = a sin(x) +b cos(x) +c is a trigonometric
polynomial.
3. Foreachiteminquestion1, describeclassesoffunctions h(x)forwhichtheanswerispositive.
In other words, describe all functions h(x) that can be represented as (1) with additional
conditions on the strictly increasing functionsf (x) and g(x).
4. Investigate how non-monotonous the functionh(x) can be in each of the classes from the
previous item. In particular, can the functionh(x) be non-monotonous for eachx∈R, that is
the expression (h(x)−h(a))(x−a) has diﬀerent signs on any open interval containingx?
3. Dense Analytic Curves
The problem is concerned with the existence ofanalytic curves that are dense inC.
1. Let L be any line in the complex plane:
L ={at +b : t∈R}, where a,b∈C.

PROBLEMS FOR THE 9th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
Describe all possibilities forexp(L). Recall that the complex exponentialexp(z) is deﬁned for
z =x +iy as:
exp(z) =
∞∑
n=0
zn/n! = exp(x) exp(iy) = exp(x)(cosy +i siny).
2. Describe all possibilities forexp(exp(L)). In particular, state necessary and suﬃcient con-
ditions for when this is dense inC.
3. Show thatexp(exp(exp(L))) is always dense inC unlessa,b are exceptional. What are these
exceptions?
4. Are there analogous results for maps of the formcos(z), or exp(z) +c, ora cos(z) +bsin(z),
or some other map?
5. Can you ﬁnd similar results in three or more dimensions?
4. Partitions of Regular Polygons
1. Letn≥1 be an integer. We consider the following equation, wheren,a,b andc are positive
integers:
an +bn =nc.
a) Solve the equation forn = 2.
b) Solve the equation whenn is a prime number.
c) Study the solutions of the equation whenn is not prime.
2. Let n≥3 be an integer and letPn be the regular polygon with n sides inscribed in the
unit circle and whose vertices are then complex roots of unity. Fix an integer k ≥3. A
k-angulation ofPn is a collection of diagonals ofPn that may intersect only at their endpoints
and such that every face has degreek (a degree of a face is the number of diagonals or sides of
Pn that surround the face). Fork≥3, letZ(k)
n be the number ofk-angulations ofPn.
a) Find a formula forZ(3)
n . How doesZ(3)
n behave for largen?
b) Fork≥4, expressZ(3)
n . How doesZ(3)
n behave for largen?
3. Let A(k)
n be a k-angulation of Pn chosen randomly among allk-angulations of Pn. Let
χ(A(k)
n ) be the length of the longest diagonal ofA(k)
n . Finda;b> 0 such that:
P(χ(A(3)
n )>a )→1; P(χ(A(3)
n )<b )→1,
as n tends to inﬁnity.
4. Does there exist a functionf : R→R such that for every0≤u≤v we have:
P(u≤χ(A(3)
n )≤v)→
∫v
u
f (x)dx
as n tens to inﬁnity?
5. Investigate questions 3 and 4 whenA(3)
n is replaced byχ(A(k)
n ).
6. Investigate question 3, 4 and 5, whenχ(A(k)
n ) is replaced by the largest area of all faces in
A(k)
n .

4 JULY 2017, IAŞI (ROMANIA)
5. Coin Toss Function
Let p∈(0; 1) be a real number. Consider an inﬁnite process of tossing a coin, such that on
each trial the probability for heads isp. Form the random binary numberX = 0,a 1a2a3...as
follows: if thei-th toss gives heads, thenai = 1, elseai = 0. Ifx∈[0; 1] is a real number, then
denote byFp(x) the probability thatX≤x.
1. Calculate Fp((0, 11111100001)2) and Fp(1/2017) in terms ofp. Can you give general algo-
rithm(s) for calculatingFp(x) for a given decimalx, ifx is:
a) of the forma/2k, a;k∈N;
b) rational;
c) irrational.
2. Let n be a positive integer. Calculate the expected value ofX n.
3. Investigate the functionFp(X) in more detail:
a) Show thatFp(x) is strictly increasing in[0; 1].
b) Show thatFp(x) is continuous in[0; 1].
c) For whichp the functionFp(x) uniformly continuous in[0; 1]?
4. Let n be a positive integer. Find:
a)
∫1
0 Fp(x)ndx.
b) the arc length of the graph ofFp(x)n on the interval[0; 1].
5. Let p̸= 1/2. Denote byfp(x) the derivative ofFp(x) (at pointsx where it exists).
a) Show thatfp(x) does not exist ifx is of the forma/2k, a;k∈N.
b) For a ﬁxedp, describe the behaviour of the derivativefp(x): for whichx∈R does it
exist (or is inﬁnite) and at which points it does not exist? How to ﬁnd its value?
c) Find allx∈R in which the derivative exists (and is not inﬁnite) for allp.
6. Suggest and investigate generalisations. For example, one can deﬁne a similar function in
k-number system, if instead of2 outcomes (0 and 1) we havek outcomes (0, 1, ..., k−1), with
probabilities p0, p1, ..., pk−1.
6. Rooks on Graphs
1. Consider anm byn grid:
A1 A2 A3 A4
B1 B2 B3 B4
C1 C2 C3 C4
a) Place a rook on the lower left corner of this grid. In how many ways can the rook reach
the upper right corner if in a single step it may move one edge up or one edge to the
right, but not down or left? For example, the rock can moveA1−A2−B2−B3−B4−C4
in the grid above.

PROBLEMS FOR THE 9th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
b) Now suppose the rook can move in each of the four directions. In how many ways it can
reach the upper left corner (A1 andC1 in the grid in the picture), if at the beginning it
is placed on the lower left corner and the rook can’t go through an edge more than once?
An example of a valid path isA1−A2−A3−A4−B4−C4−C3−C2−B2−B1−C1
in the grid above. Start with smallm = 2, 3, 4,...
c) Find the number of rook paths, which do not pass through the same edge more than
once and join the opposite vertices of the grid (A1 and C4 in the grid on the picture).
Start with the case when the grid is square (m =n) and some small value ofm.
2. Now assume the grid is inﬁnite.
a) Find the number of paths which start and end at the same vertex, do not pass through
the same edge more than once and go through exactlyt edges (vertices do not need to
be necessarily distinct).
b) Start at an arbitrary vertex and start moving along the grid with equal probability in
each direction. Find the probability of the event that the path of the rook forms a cycle
of lengtht without repeating edges.
3. Now instead of a grid we will generalise the problem by looking at a graphG(V ;E) without
loops or multiple edges.
a) Find the number of cycles of lengtht in a complete graphG =Kn withn vertices (the
vertices can be repeated but the edges can not).
b) For whichn does there exist a cycle which covers all edges of the complete graphKn?
(Each edge is used exactly once.)
4. Now remove one edge from the complete graphKn.
a) Find the the number of cycles of lengtht in the new graphK′
n.
b) How the answer will change if we remove 2 edges from the complete graphKn? Does
the answer depend on which 2 edges were removed?
5. Suppose again thatG = Kn is the complete graph withn vertices. Start at an arbitrary
vertex and start moving along the graph with equal probability. Give upper and lower bound
for the probability of the event that the path forms a cycle of lengtht without repeating edges.
7. Weighted Sums of Distances
Let△ABC be a triangle and(λ,µ,ν) be a triple of real numbers withλ+µ+ν̸= 0. Let
alsoX be a point in the plane of the triangle. Denote byd1,d2,d3 the oriented distances from
X to the linesBC, CA and AB, respectively. We are interested in the function:
f (X) = λd2
1 +µd2
2 +νd2
3
and in particular, in its minimum and maximum (if they exist).
1. Letλ=µ=ν= 1. Prove that the minimum off exists and is attained only at the Lemoine
point of△ABC.
2. Let λ,µ,νbe non-negative.
a) Supposeλµν̸= 0. Prove thatf (X) always has a minimum and describe the points (in
terms ofλ,µ,ν) at which it is attained.
b) What happens in the caseλµν= 0?
3. Consider the case when exactly one ofλ, µor νis negative.
4. Consider the general case:

6 JULY 2017, IAŞI (ROMANIA)
a) Find all triples (λ,µ,ν), λ+µ+ν̸= 0 (and the respective attainable pointsX) for
whichf (X) has a minimum, and those for which it has a maximum.
b) Answer the above question in the cases whenλ+µ+ν= 0.
5. Answer question 4 for the function
f (X) = λd3
1 +µd3
2 +νd3
3.
6. Now instead of the triangle consider a tetrahedron and quadruples(λ1;λ2;λ3;λ4) of real
numbers with non-zero sum. Similarly, we can deﬁne a function
f (X) = λ1d2
1 +λ2d2
2 +λ3d2
3 +λ4d2
4,
where di are the distances from a pointX in space to the planes containing the faces of the
tetrahedronA1A2A3A4. Find all quadruples (and the respective attainable pointsX) for which
f (X) has a minimum, and those for which it has a maximum.
7. Similarly, consider ann-dimensional simplex and an analogously deﬁned function (with
squared distances) for points inn-dimensional space.
8. A Communication Network
Consider the communication network consisting of nodes and communication channels be-
tween some of the nodes. Two nodes can communicate either via the direct channel between
them (if any), or via any other channels connecting these nodes. The network is called valid, if
any two nodes are able to exchange messages.
There is some secret information split between nodes in such a way that each node contains
a part of the secret not known to any other node in the network. Any nodeN can broadcast
a message. In this case all its information (its initial part of the secret and all secret parts
received from other nodes up to this moment) becomes known to all nodes connected withN
via the direct channel. The minimal number of such messages in order for all nodes to obtain
the entire secret (i.e. the secrets from all other nodes) is calleda secret connectivity numberor
just asecret numberof the network.
We can model such communication network by a graphG, where vertices ofG correspond to
nodes and edges ofG become direct communication channels. A valid communication network
corresponds to a connected simple graphG.
Denote bys(G) the secret connectivity number of the corresponding network. For example,
if G = P4 is a simple chain with vertices{v1,v 2,v 3,v 4}and edges{v1v2,v 2v3,v 3v4}, then
s(G) = 5, and one of the optimal sequences of messages is{v1,v 4,v 3,v 2,v 3}.
1. Find s(G) for the following graphs:
a) the complete graphKn;
b) the simple cycle graphCn (i.e. the graph represented by a regularn-gon);
c) the simple chainPn;
d) the completek-partite graphKn1,n2,...,nk;
e) the graph of a three-dimensional cube;
f) the Petersen graph.
2. Let T be an arbitrary connected tree withn vertices. Finds(T ) and describe an algorithm
generating an optimal sequence of messages.
3. Consider the case of a connected unicyclic graph, that is a connected graph with a single
cycle.
4. Consider the graphGm,nof them byn grid (see Problem 6).

PROBLEMS FOR THE 9th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
5. Try to relates(G) or at least estimates fors(G) with other known numeric invariants of
graphs.
9. An Approximation Problem
1. Consider the following subset of rational numbers
U =
{
x−1
x |x∈Q, x̸= 0
}
.
a) Show thatU is dense in the real line (that is for any non-empty intervalI⊂R, there
exists an elementr∈U which belongs toI)?
b) Denote byaU the set of productsar with r∈U. Show that for any reala̸= 0, the set
aU is also dense inR.
2. Study intersectionsaU\bU where a and b are integers. In particular, determine whether
aU\bU is a) empty; b) inﬁnite; c) dense inR.
3. Let n >2 be a natural number. Study intersectionsa1U\...\anU where a1,...,a n are
integers.
4. More generally, let f : D →R be a real-valued function deﬁned on a domainD ⊂R.
Consider the following set
Uf ={f (x) |x∈Q\D}.
For example, in the previous questionsU =Uf with f (x) = x−1/x and D = R\{0}.
Check the density of setsa1Uf\...\anUf where n is a natural number anda1,...,a n are
integers, in the following situations:
a) f is a polynomial with integer coeﬃcients;
b) f (x) = P (x)
Q(x), whereP (x) andQ(x) are polynomials with integer coeﬃcients (start with
polynomials of degree at most2);
c) f is a trigonometric function;
d) f (x) = S(x)
T (x), where S(x) and T (x) are trigonometric polynomials with integer coeﬃ-
cients.
5. Suggest and investigate additional directions of research.
10. Kinds of Convexity
Recall that a functionf (x) deﬁned on an intervalI⊂R is called convex on I, if for any
x,y∈I and anyλ∈[0; 1] we have the following inequality:
f (λx+ (1−λ)y)≤λf(x) + (1−λ)f (y)
1. Let f (x) be a convex function onI. Let a1≤a2≤...an, b1≤b2≤...bn and ai +bj∈I
for all 1≤i,j ≤n. Prove the following inequality:
n∑
i=1
f (ai +bi)≥
n∑
i=1
f (ai +bn−i+1).
2. Let f (x) be a convex function onI. Leta1≤a2≤...an, b1≤b2≤...bn and aibj∈I for
all 1≤i,j ≤n.
a) Is it true that
n∑
i=1
f (aibi)≥
n∑
i=1
f (aibn−i+1)?

8 JULY 2017, IAŞI (ROMANIA)
b) If not, try to ﬁnd additional conditions onai and bi, so that it becomes true.
3. Fix a positive real numbers. Let us say that the functionf (x) is s-convex of ﬁrst kind, if
for anyx,y∈I and anyλ∈[0; 1] we have the following inequality:
f (λx+ (1−λ)y)≤λf(x)s + (1−λ)f (y)s.
a) For whichs there exist a functionf (x) on a closed intervalI⊂R, which iss-convex of
ﬁrst kind, but not convex?
b) Which of the inequalities from questions 1 and 2 hold for anys-convex function of ﬁrst
kind?
4. Let us say that the functionf (x) is s-convex of second kind, if for anyx,y ∈I and any
λ∈[0; 1] we have the following inequality:
f (λx+ (1−λ)y)≤λsf (x) + (1−λ)sf (y).
Solve question 3 fors-convex functions of second kind.
E-mail address : oc@itym.org
URL: http://www.itym.org/
