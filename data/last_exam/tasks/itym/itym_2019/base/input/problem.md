PROBLEMS FOR THE 11th INTERNATIONAL TOURNAMENT
OF YOUNG MATHEMATICIANS
JULY 2019, BARCELONA (SPAIN)
Contents
Notation 1
1. A Divisibility Problem 1
2. A Graph Coloring Game 2
3. Derivatives of Rational Numbers 3
4. Inequalities with a Shift 4
5. Dense Sets of Fractions 4
6. Operation Tables 5
7. Graphs of Finite Groups 6
8. Embeddings of Connected Graphs 7
9. Maximal Orders of Residues 8
10. Optical Illusions 8
Keywords: 1. number theory – 2. games – 3. rational numbers – 4. inequalities – 5. real
analysis, dense sequences – 6. algebra, operations – 7. group theory, graphs – 8. graph theory,
embeddings – 9. number theory, algorithms – 10. metric spaces, geometry
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Zn ={0, 1,...,n−1}ring of residue classes modulon
Z, Q, R, C sets of integer, rational, real and complex numbers
R+ and R≥0 sets of positive and non-negative real numbers
R2 real plane
]a,b [ and [a,b ] open and closed interval froma to b
Z[i] ring of Gaussian integersZ[i] ={a +bi|a,b∈Z}
C+[0, 1] set of strictly positive continuous functions from[0, 1] to R
M×N Cartesian product of two setsM and N
gcd(x1,...,xn) greatest common divisor ofx1,...,xn
|x| absolute value ofx
#M or|M| cardinality of a setM
diam(M) diameter of a setM
inf
x∈M
f(x) and sup
x∈M
f(x) inﬁmum and supremum of a set{f(x) |x∈M}
1. A Divisibility Problem
1. Letn,p be positive integers such thatp is a prime divisor of22n
+1. Prove that2n+1 divides
p−1.
2. We are interested in the triples of positive integers(a,b,c ) such that 2na +b divides cn + 1
for all positive integersn.
© International Tournament of Young Mathematicians. This work is licensed under a “CC BY-SA 4.0”
license.
Date: April 19, 2019.
1

2 JULY 2019, BARCELONA (SPAIN)
(a) Suppose a = b = 1. Is it true that c is necessarily even? That c = 2 2k−1 for some
positive integerk?
(b) Find all triples(a,b,c ), satisfying the above condition.
3. Now, suppose that the positive integersa,b,c are such that2na +b divides cn + 1 for all
integersn of the formak =pk, k≥0, wherep is a prime.
(a) For which values ofc and p, is it necessarily true thata =b = 1?
(b) For a ﬁxed value ofp, what can you say abouta,b,c , in general?
4. What happens if2na +b divides cn+2 + 1 for alln (or for alln =pk) instead?
5. Investigate the previous parts formna +b (the above questions correspond to the case
m = 2) or for other inﬁnite sequencesak.
6. Suggest and study additional directions of research.
2. A Graph Coloring Game
Bob and Riley play a game on a simple connected undirected graphG with n≥2 vertices.
Bob’s favourite color is blue and Riley’s is red. The goal of each of them is to have as many
vertices as possible in their favourite color. Initially all vertices are white.
The players make alternating moves starting with Bob. On his ﬁrst move, each player chooses
any white vertex and colors it in his favorite color. On each consequent move, each player picks
a white vertex connected with an edge to a vertex of his color (if there is no such vertex, the
player skips his move). Then he colors it in his color. The game ﬁnishes when no white vertices
remain.
In this example there are two moves made both from Bob And Riley marked with strong blue
and red. The possible moves of Bob are marked with opaque blue.
Let B(G) be the maximal number of blue vertices, which Bob can guarantee at the end of
the game andR(G) be the maximal number of red vertices, which Riley can guarantee at the
end of the game. The strategies with which they achieve this are called optimal.
1. Describe the optimal strategy for Bob and evaluateB(G) where:
(a) G is a tree;
(b) G is a grid graphM×K;
(c) G is a torus grid graphM×K.

PROBLEMS FOR THE 11th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
2. Let MB(n) = min
G∈S(n)
B(G), whereS(n) is the set of all simple undirected connected graphs
with n vertices. Provide as best as possible upper and lower bounds forMB(n).
3. Provide as best as possible upper and lower bounds forlimn→∞
MB(n)
n .
For the next3 problems consider the following modiﬁcation of the game rules. Instead of
choosing which vertices to color, each of the players has a pawn (blue for Bob and red for Riley),
which can move from vertex to vertex connected with an edge. Each pawn colors the vertex it
is on in its color. The red pawn cannot step on blue vertices and the blue pawn cannot step
on red vertices (but the blue pawn can step back on a blue vertex and the red pawn can step
back on a red vertex).
Initially Bob places his blue pawn on some vertex and than Riley places his red pawn on
a diﬀerent vertex. Then they take turns to move their pawns. In a turn, the pawn must be
moved if possible (it cannot stay in the same vertex, unless there are no possible moves).
Since the game (with the new rules) can continue indeﬁnitely, for this case letB′(G) be the
maximal number of blue vertices Bob can guarantee in a ﬁnite amount of moves andR′(G) be
the maximal number of red vertices Riley can guarantee in a ﬁnite amount of moves.
4. EvaluateB′(G) and R′(G) where:
(a) G is a grid graphM×K;
(b) G is a torus grid graphM×K.
5. Show that there exist graphs withn vertices such thatB′(G) +R′(G) < n. And ﬁnd the
minimal n for which such a graph exists.
6. Provide as best as possible upper and lower bounds of max
G∈S(n)
(n−B′(G)−R′(G)) with
regards ton.
7. Suggest and study additional directions of research.
3. Derivatives of Rational Numbers
The function′: Q→Q satisﬁes the following properties:
•p′= 1 for all positive integer primesp;
•(mn)′=m′n +mn′for allm,n∈Q;
•0′= 0.
Also, for any non-negative integerk let x(k) denote k iterations of′on x.
1. (a) Verify that indeed there is a unique such function.
(b) Prove also that for anyL∈Q there existx,y ∈Q such thatx′< L < y′. Is this true
for x′′=x(2)?
2. Discuss the existence and number (ﬁnite or inﬁnite) of solutions to
(a) x′=a where a∈Q is given. Start witha = 0 and a = 1.
(b) x′=ax +b where a,b∈Q are given. Start withb = 0.
(c) x′′=ax′+bx where a,b∈Q are given.
(d) x(k) =x, x′̸=x where k≥2 is a given positive integer.
Where possible, describe all solutions or generate families of such.
3. Find conditions onx for which the sequencex(k), k = 0, 1, 2, 3,...is monotonic, bounded,
convergent (possibly to inﬁnity), etc.
4. (a) Find allx∈Q such thatx′≡0 (mod 4) (that is, in lowest terms its denominator is
odd and its numerator is divisible by4).

4 JULY 2019, BARCELONA (SPAIN)
(b) What aboutx′≡0 (mod p) where p is a given odd prime (that is, in lowest terms its
numerator is divisible byp and its denominator is not)?
5. Investigate the above problems for other sets (e.g.Q(i)) or other similar functions (e.g. the
logarithmic derivativex′
x).
6. Suggest and study additional directions of research.
4. Inequalities with a Shift
Letx1,x2, ..., xn be positive real numbers, and letk be a positive integer. Deﬁnexn+1 =x1,
xn+2 =x2, ...
1. Denote byσp(n) the cyclic shift of numbers1 ton byp−1 positions. For example,σ3(1) = 3,
σ3(2) = 4, ..., σ3(n−2) =n, σ3(n−1) = 1, σ3(n) = 2.
The goal of this item is to investigate for which cyclic shiftsσp(n) the inequality
n∑
i=1
(
xi
xi+1
)k
≥
n∑
i=1
xi
xσp(i)
(1)
is satisﬁed for all positive numbersx1, x2, ..., xn.
(a) Prove (1) forp = 1.
(b) Prove (1) forp =k + 1.
(c) Prove (1) fork =p =n.
(d) Prove (1) for1<p<k + 1.
(e) For whichk + 1<p<n the inequality (1) is true?
2. Suppose now k is an arbitrary real number. For which p (depending on k) does the
inequality (1) hold for all positive numbersx1, x2, ..., xn?
3. Assume k = 2, n = 3. Find all permutationsσof the numbers from1 to n such that the
following inequality:
n∑
i=1
(
xi
xi+1
)k
≥
n∑
i=1
xi
xσ(i)
(2)
is true for all positivex1, x2, ..., xn.
4. Assume now thatk = 2, n> 3. Find all permutations, for which the inequality (2) holds.
5. Investigate further directions and generalisations of the problem. For example, the left hand
side of the inequalities can be replaced by
n∑
i=1
(
xi
xi+1 +xi+2
)k
, or
n∑
i=1
(
xi +xi+1
xi+2 +xi+3
)k
, or
n∑
i=1
(
xi +xi+1
xi+1 +xi+2
)k
.
5. Dense Sets of Fractions
Let x ={xn}∞
n=1 be a strictly monotonous and unbounded from above sequence of positive
real numbers. We say thatx ={xn}∞
n=1 is of type 0 and writex∈T0, if its set of fractions
θx ={xn/xm|n,m∈N}is dense in the open interval]0,∞[. This means that any non-empty
interval (α,β)⊂]0,∞[ should contain at least one pointt∈θx.
Starting from the sequencex ={xn}∞
n=1, deﬁne the sequence of its partial sums:
S(x) ={x1 +···+xn}∞
n=1.
We shall say thatx ={xn}∞
n=1 is of type m∈N and writex∈Tm if S(x)∈Tm−1.

PROBLEMS FOR THE 11th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
1. (a) Let x ={xn}∞
n=1 ={n}∞
n=1 be the sequence of all natural numbers. Determine, for
whichm∈N∪{0}we havex∈Tm.
(b) Investigate the same question whenx ={xn}∞
n=1 is an arithmetic or geometric progres-
sion.
2. Do there exist sequencesx ={xn}∞
n=1 such that:
(a) x∈T1, butx /∈T0;
(b) x∈T0, butx /∈T1;
(c) x∈Tm, butx /∈Tl for somel̸=m?
3. Investigate how the conditionx∈T0 is related to other properties of the sequencex =
{xn}∞
n=1. In particular, ify ={yn}∞
n=1⊂]0,∞[ is another sequence, we writexk≈yk orx≈y,
if limk→∞xk/yk = 1. Let alsoπx(n) = max{k|xk <n}.
Which of the following conditions imply thatx∈T0 and which of them are implied byx∈T0:
(a) There existsy∈T0 such thatx≈y.
(b) There existsy∈T0 such thatπx(n)≈πy(n).
(c) There existy,z ∈T0 such thatx =y +z.
(d) We havexn+1≈xn, that islimk→∞xk+1/xk = 1.
(e) Starting from some numbern we have 9
10 < πx(n)
n/ lnn < 11
10.
(f) x ={xn}∞
n=1 is the sequence of all prime numbers; or the sequence of all prime numbers
which belong to some arithmetic progression starting with 1 and having a rational
diﬀerence.
(g) x ={xn}∞
n=1 is a sequence of all primes in the sequence of integral parts of an arithmetic
sequence with irrational diﬀerence.
Investigate the similar questions for the conditionx∈Tm, m≥1.
4. Consider the setC+[0, 1] of all strictly positive continuous functions on the closed interval
[0, 1]. For anyf,g ∈C+[0, 1] we say thatf < gif f(x) < g(x) for allx∈[0; 1]. Deﬁne an
interval (f,g ) as a set{h∈C+[0, 1]|f <h<g }. Finally, a subsetθ⊂C+[0, 1] will be called
dense, if any non-empty interval(f,g ) contains at least one element fromθ.
LetF ={fn}∞
n=1⊂C+[0, 1] be a strictly increasing sequence of strictly increasing functions,
that is each functionfk(x) strongly increases on the interval[0, 1] and for anyk∈N we have
fk < fk+1. We say thatF ={fn}∞
n=1 is of type 0 and writeF ∈T0, if the set of fractions
θF ={fk/fl|k,l ∈N}is dense inC+[0, 1]. Is it true that such sequencesF exist?
6. Operation Tables
Let q≥2 be an integer. Denote by[ [0,q−1] ]the set of integers from0 to q−1. A function
⋆: [ [0,q−1] ]×[ [0,q−1] ]→[ [0,q−1] ]
is called aq-operation, if there exists an elemente∈[ [0,q−1] ]such that:
•for allx∈[ [0,q−1] ]we have⋆(x,e ) =x;
•for anyx,y∈[ [0,q−1] ]we have⋆(e,⋆(y,x )) =⋆(x,y ).
If ⋆is aq-operation, we shall writex⋆yinstead of⋆(x,y ).
For any functionf : Z×Z→Z we can construct a function
fq : [ [0,q−1] ]×[ [0,q−1] ]→[ [0,q−1] ], (x,y )↦→f(x,y ) mod q.
For example, forf(x,y ) = x−y and q = 10 we havefq(2, 5) = 7 , since 2−5 = −3≡7
mod 10. Fir simplicity, we shall use the notation+q,−q,×q, gcdq for functionsx +y, x−y,
x×y, gcd(x,y ).

6 JULY 2019, BARCELONA (SPAIN)
1. Verify that+q,−q, gcdq and×q are q-operations and ﬁnd the corresponding elemente for
each of them. Can you ﬁnd other examples ofq-operations?
2. Find the number of possibleq-operations as a function ofq.
We say that a subsetD⊂[ [0,q−1] ]is⋆-complete, if for anyz∈[ [0,q−1] ]there exist elements
x,y∈D such thatx⋆y=z. Deﬁne
cq(⋆) = min{#D,D is ⋆-complete}.
3. Estimate cq(gcdq), cq(−q), cq(+q) and cq(×q) as functions ofq.
4. What can you say aboutcq+1(⋆q+1)−cq(⋆q) for ⋆∈{gcd, +,−,×}?
For anyq-operation ⋆consider the number of smallest⋆-complete subsets:
dq(⋆) = #{D⊂[ [0,q−1] ],D is ⋆-complete and #D =cq(⋆)}.
5. Study the numbersdq(⋆) for ⋆∈{gcd, +,−,×}. In particular, try answering the following
questions:
(a) Whenq divides dq(⋆)?
(b) Can you give an estimate fordq(⋆)?
(c) Are there subsequences ofdq(⋆) that form (inﬁnite) arithmetic sequences?
6. Investigate other interesting operations⋆or explore other tracks of research.
7. Graphs of Finite Groups
For any ﬁnite groupG deﬁne an undirected graphΓ(G) as follows. We setV (Γ(G)) =G\{1}
and connect two verticesx and y by an edge, if there exist natural numbersn and m with
xn =ym̸= 1.
LetSn andAn be the symmetric and the alternating groups onn elements respectively. The
dihedral group Dn of order 2n can be deﬁned as⟨x,y|xn = y2 = (xy)2 = 1⟩or, equivalently,
as the symmetry group of a regularn-gon. Finally, by Zn in this problem we understand the
additive group of the setZn.
For example, the graphΓ(D3) = Γ(S3) looks as follows:
Here the two connected vertices correspond to the rotations of the regular triangle by angles
±2π/3, and the remaining three isolated vertices correspond to the three reﬂection symmetries
of the triangle.
1. Draw Γ(Z4), Γ(D4), Γ(A4) and Γ(S4).
2. For a naturaln compute the number of edges in the following graphs:Γ(Zn), Γ(Dn), Γ(An)
and Γ(Sn).
3. Which of the graphs from the previous question are not connected? Try to ﬁnd or estimate
the number of connected components for them.
4. Which of the graphs from the question 2 (or their connected components, if the graphs are
not connected)
(a) have Eulerian circuit?
(b) have Hamiltonian circuit?
(c) are planar?
(a) have Eulerian circuit?
(b) have Hamiltonian circuit?
(c) are planar?

PROBLEMS FOR THE 11th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
5. Is it true thatΓ(Zp)≃Kp−1 for primep, whereKn is a complete graph withn vertices?
6. Describe
(a) Γ(Zn) for anyn≥2;
(b) Γ(Dn) for anyn≥2;
(c) Γ(A) for an arbitrary ﬁnite abelian groupA.
7. Study Γ(G) for other ﬁnite groups such as a general linear groupGL(n, Zp) (at least for
some smalln and p) or the symmetries of ann-dimensional hypercube?
8. Embeddings of Connected Graphs
Throughout letd be a (ﬁnite) positive integer andG be a connected undirected simple graph.
An embeddingofG in Rd is a map associating the vertices ofG with points inRd and the edges
of G with simple arcs (homeomorphic images of[0, 1]) so that: for any edgee, the endpoints
of the arc associated withe are the points associated with the end-vertices ofe.
Denote by Ed(G) the set of all embeddings ofG in Rd. For verticesu,v of G we deﬁne the
distance dG(u,v ) to be the number of edges in a shortest path fromu to v. Treating||·||as
the standard Euclidean norm inRd, deﬁne thedistortion of G as
Dd(G) = inf
f∈Ed(G)
maxu,v∈G,u̸=v
||f(u)−f(v)||
dG(u,v)
minu,v∈G,u̸=v
||f(u)−f(v)||
dG(u,v)
1. Ford = 2 compute (or give bounds on) the distortion of the following graphs:
(a) Cn – a simple cycle graph of lengthn;
(b) Ln – the ladder graph with vertex set{v1,...,vn,w 1,...,wn}and edge set{viwi : 1≤
i≤n}∪{vivi+1 : 1≤i≤n−1}∪{wiwi+1 : 1≤i≤n−1};
(c) Qn – the hypercube graph formed from the vertices and edges of ann-dimensional
hypercube;
(d) an arbitrary planar graph.
In case you give general bounds, you can check which particular graphs of the corresponding
type attain them.
2. Now letG be a tree. We say thatG is perfectk-ary if there is a unique vertexr (called
the root) of degreek such that the distancedG(r,l ) is the same for any leafl, and each vertex,
except the root and the leaves, has degreek + 1.
(a) Prove that there exist constantsc1,c 2 and an integerN∈N such that for everyperfect
binary (2-ary) tree G on n≥N vertices we havec1≤D1(G) log2n
n ≤c2. Estimate c1
and c2.
(b) Can one derive a similar statement ford≥2?
(c) Consider the above for perfectk−ary trees,k≥3.
(d) Compute (or give bounds on) distortions for other particular trees and in the general
case. In case you give general bounds, you can check which particular graphs of the
corresponding type attain them.
3. Consider distortions of other connected graphs. Suggest and study additional directions of
research.

8 JULY 2019, BARCELONA (SPAIN)
9. Maximal Orders of Residues
Let b and n be two integers such thatgcd(b,n ) = 1. Let d be the minimal positive integer
such thatbd≡1 (modn). We will say thatd is the order of b modulo n, e.g. the order of 2
modulo 7 equals 3. Letf(n) be the maximal positive integerk such that there exists a number
b of orderk modulon. A numberb of orderf(n) modulon will be calledan element of maximal
order modulo n. Denote byg(n) the number of distinct elements of maximal order modulon
(elements a and b are distinct modulon if a̸≡b (modn)). For example,f(5) = 4, g(5) = 2
and the integers 2 and 3 are the elements of maximal order modulo 5.
1. (a) Prove thatf(n) is ﬁnite.
(b) For smalln (2≤n≤10) calculate f(n) and g(n) and ﬁnd all elements of maximal
order modulon.
(c) Prove thatf(p) = p−1, wherep is a prime. What is the value ofg(p)? Does there
exist a compositen such thatf(n) =n−1?
(d) Investigate the previous question forn =pα, α∈N, p is a prime odd number. Suggest
an eﬃcient (polynomial) algorithm that ﬁnds an element of maximal order modulon,
in case that some element of maximal order modulop is known. Try to calculateg(n)
for suchn.
(e) Try to estimatef(n) andg(n) for arbitraryn. Suggest algorithms for ﬁnding an element
of maximal order modulon.
2. Consider the set Z[i] = {a +bi |a,b∈Z}, where i is the imaginary unit. We say that
n∈Z[i] is divisible bym∈Z[i] if there existsq∈Z[i] such thatn =qm. Forc,d∈Z[i] and
n∈Z[i]\{0}, we writec≡d (modn) if c−d is divisible byn. Analogously, one can deﬁne
functions f(n), g(n) and elements of maximal order modulon. Investigate analogues of the
questions 1(a) – 1(e).
3. Consider the setZ[
√
2] =
{
a +b
√
2 |a,b∈Z
}
. Deﬁne arithmetic and modular operations
on Z[
√
2] and investigate the questions 1(a) – 1(e) forZ[
√
2].
4. Investigate the same problem for the setZ[ 3√
2] =
{
a +b 3√
2 +c 3√
4 |a,b,c ∈Z
}
.
10. Optical Illusions
Let (M,d ) and (N,q ) be two metric spaces with distance functionsd,q. We say that they
are visually equivalent if there exists a functionf :M−→N called visual equivalence with the
following properties:
•there existK >0 and C >0 such that 1
Kd(x,y )−C≤q(f(x),f (y))≤Kd(x,y ) +C
for allx,y∈M;
•there existsR> 0 such that for anya∈N there isb∈f(M) for whichq(a,b )≤R.
1. Given an undirected simple connected possibly inﬁnite graphΓ = (V,E ), we introduce a
metric space structure onV as follows:
dΓ(u,v ) = min{n∈N|there is an edge path of lengthn connecting u and v in Γ}
provided that length between adjacent vertices is 1. A functionγ: N−→V is said to be a
ray if dΓ(γ(x),γ(y)) =|x−y|for allx,y ∈N. Determine which of the following properties of
graphs are stable under visually equivalence:
– to have a ﬁnite diameterdiam(M) = supx,y∈MdΓ(x,y );
– to have exactly one ray starting at some ﬁxed vertex;
– to have exactly two rays starting at some ﬁxed vertex.

PROBLEMS FOR THE 11th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 9
2. Determine which of the following metric spaces (with standard distance functions) are
visually equivalent:
(a) R, Z, [0, 1];
(b) R, R≥0;
(c) R2, R≥0×R≥0, R×R≥0;
(d) R2,{(x,y )∈R2|x = 0 or y = 0}.
3. Does there exist:
(a) a graph that is visually equivalent toR2?
(b) a tree (a connected graph with no cycles) that is visually equivalent toR2?
4. For whichn≥2 an inﬁnite tree with one vertex of degreen and all other vertices of degree
2 is visually equivalent to some subset ofR2? Study the case of a tree with more than one big
degree vertex.
5. Suggest and investigate your own directions of this problem.
Email address: oc@itym.org
URL: http://www.itym.org/
