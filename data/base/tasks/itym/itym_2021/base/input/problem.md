PROBLEMS FOR THE 13th INTERNATIONAL TOURNAMENT OF
YOUNG MATHEMATICIANS
OCTOBER 2021
Contents
Notation 1
1. Power Sums of Distances 1
2. Sequences of Coprime Integers 2
3. Circular Permutations in the Plane 3
4. Convex Functions 4
5. Odd and Even 5
6. Binomial Coeﬃcients and Prime Numbers 7
7. Proper Numberings of Graphs 7
8. Unimodality of Permutations 8
9. Wobbly Tables 10
10. Non-nilpotent Graphs of Groups 11
Keywords: 1. plane geometry, locus – 2. sequences, coprime numbers – 3. circular per-
mutations, conﬁgurations of points – 4. convexity, inequalities – 5. real analysis, parity – 6.
binomial coeﬃcients, divisibility – 7. graph theory, optimisation – 8. permutations, counting,
sorting – 9. three-dimensional geometry, quadrilaterals on surfaces – 10. graphs of groups,
nilpotency
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Zn ={0, 1,...,n−1}ring of residue classes modulon
Z, Q, R, C sets of integer, rational, real and complex numbers
Rn n-dimensional real space
Sn set ofn-permutations
]a,b [ and [a,b ] open and closed interval froma to b
[ [a,b ] ] set of integers froma to b
|x| absolute value ofx
#M or|M| cardinality of a setM
M×N Cartesian product of two sets or graphsM and N
M∪N,M \N,M \N union, intersection and diﬀerence of two setsM and N
1. Power Sums of Distances
A set ofn points P ={A1,...,An}is given in the real plane. For an integerk >0 and a
real numberc> 0, we denote byFk(P,c ) the locus of pointsX in the plane such that
|XA 1|k +···+|XAn|k =c,
where|XA 1|, ..., |XAn|are the distances fromX to A1, ..., An respectively.
©International Tournament of Young Mathematicians. This work is licensed under a “CC BY-SA 4.0” license.
Date: July 2, 2021.
1

2 OCTOBER 2021
X
A1
A2
A3
Figure 1. If P is the set of vertices of an equilateral triangle andc is large
enough, then the lociF2(P,c ) and F4(P,c ) are circles.
1. Take forP the vertices of an equilateral triangle (see Figure 1).
a) Show thatF2(P,c ) is either a circle or an empty set.
b) Show thatF4(P,c ) is either a circle or an empty set.
c) DescribeFk(P,c ) for allk.
d) Find the smallestc for whichFk(P,c ) is not empty.
e) Find allk and c such thatFk(P,c ) is the circumscribed circle of the triangle.
2. Consider the same questions for the vertices of an arbitrary triangle.
3. Describe Fk(P,c ), whereP is the set of vertices of a regularn-gon.
4. In general, describeFk(P,c ) for an arbitrary setP.
5. Given a circle in the plane, ﬁnd the triples(n,k,c ) for which there exists a setP such that
Fk(P,c ) is this circle.
6. Generalise the problem to three dimensions.
7. Suggest and investigate additional directions of research.
2. Sequences of Coprime Integers
A ﬁnite or inﬁnite integer sequencea1,a 2,...,ak,... will be calledn-prime if the numbers
a1 +n, a 2 +n, ..., a k +n,...
are pairwise coprime.
1. Let a1 <a 2 be a sequence of two positive integers.
a) Show that there are inﬁnitely manyn∈N for which the sequence isn-prime.
b) Find necessary and/or suﬃcient conditions for the sequence to ben-prime for alln∈N?
2. Let a1 <a 2 <a 3 be a sequence of three positive integers.
a) Show that there are inﬁnitely manyn∈N for which the sequence isn-prime.
b) Find necessary and/or suﬃcient conditions for the sequence to ben-prime for alln∈N?
3. Takek≥4. Does there exist a sequencea1 <a 2 <···<a k of k positive integers which
a) isn-prime for alln∈N?
b) isn’tn-prime for alln∈N?
Start withk = 4.
4. In general, ﬁnd or describe all ﬁnite strictly increasing sequences of positive integers that

PROBLEMS FOR THE 13th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
a) aren-prime for alln∈N.
b) aren-prime for inﬁnitely manyn∈N.
c) aren’tn-prime for alln∈N.
5. Same questions for inﬁnite strictly increasing sequences of positive integers.
6. A further generalisation is to considerP (n)-prime sequences, whereP (x) =cdxd+···+c1x+
c0 is a polynomial with integer coeﬃcients. For example, identify sequencesa1 <a 2 <···<a k
such thata1 +n2021,a 2 +n2021,...,ak +n2021 are pairwise coprime for inﬁnitely manyn∈N.
7. Suggest and investigate other directions of research.
3. Circular Permutations in the Plane
Given n points in the plane R2, numbered from 1 to n. Assume that the points are in
general position, that is, no line passes through three of them. Then there are exactly
(n
2
)
lines containing two of these points. An agent, standing anywhere in the plane outside of
these lines, observes one of (n−1)! circular permutations of the points (see Figure 2). A
circular n-permutation is an arrangement of the numbers 1, ..., n on a circle where only
the order matters. Circular n-permutations can be presented asn-cycles (a1 ... an) with
{a1,...,an}={1,...,n}. The set of all circularn-permutations will be denoted byPn.
We are interested in studying the following question: how many diﬀerent circular permu-
tations can the agent observe while wandering in the plane? Denote byc(n) the maximum
possible number of such circularn-permutations.
4
1
3
5
2
Figure 2. The circular permutation(4 1 3 5 2) is observed forn = 5.
1. The entire plane can be divided into maximal (by inclusion) connected regions such that if
the agent is moving inside a region, an observed permutation doesn’t change.
a) What are the boundaries of the regions?
b) How does an observed permutation change if the agent crosses a boundary?
2. Is it possible to placen points in the plane so that every circularn-permutation can be
observed by the wandering agent?
3. Find lower bounds forc(n) by providing explicit constructions.
4. Let n≥5 points be the vertices of a regularn-gon numbered in the clockwise direction.
a) Can the following permutation be observed:
(1, 2, ..., m−1, m+ 1, ..., n−1, n, m), where m =
⌊n + 1
2
⌋
?
b) Describe the permutations that can be observed.

4 OCTOBER 2021
c) Find the exact number of permutations or give upper and lower bounds.
6. Show that
c(n)≤n(n−1)(n2−n−2)
8 .
7. Show that
c(n)≤(n−1)(2−n)
2 +
n−1∑
k=1
(n−k)
(
1 + (k−1)(2n−k)
2
)
.
8. The upper bounds in the previous two questions are equivalent to1
8n4 as n→∞. Is it
possible to improve this asymptotic?
9. Find a formula forc(n).
10. A subset S ⊆Pn of circular n-permutation will be called realisable if there exists a
conﬁgurationofnpointsintheplane, forwhich S isexactlythesetofallobservedpermutations.
Investigate realisable sets (describe properties, ﬁnd possible cardinalities, etc.).
11. Suggest and study additional directions of research.
4. Convex Functions
Let I⊆R be a nonempty interval. A functionf :I→R is calledstrictly convexif, for any
distinct x,y∈I and anyλ∈]0, 1[, the following inequality is satisﬁed:
f
(
λx+ (1−λ)y
)
<λf(x) + (1−λ)f(y). (1)
Let p be a real number. A functionf : I→]0, +∞[ is calledp-convex if, for any distinct
x,y∈I and anyλ∈]0, 1[, the following inequality is satisﬁed:
f
(
λx+ (1−λ)y
)
<H λ,p(f(x),f (y)),
where
Hλ,p(u,v ) =
⌋


(λup + (1−λ)vp)1/p for p̸= 0;
uλv1−λ for p = 0.
Let h : ]0, 1[→[0, +∞[ be a function. A functionf : I→R is calledh-convex if, for any
distinct x,y∈I and anyλ∈]0, 1[, the following inequality is satisﬁed:
f
(
λx+ (1−λ)y
)
<L λ,h(f(x),f (y)),
where
Lλ,h(u,v ) =h(λ)u +h(1−λ)v.
1. Consider the following statement(S):
“If fora,b,c,d ∈I one hasa +b =c +d and f(a) +f(b) =f(c) +f(d), thena =c or a =d.”
a) Show that the statement is true for strictly convex functions.
b) Is it true forp-convex functions? Find similar true statements forp-convex functions.
c) Generalise and investigate the statement for six numbers fromI instead of four.
2. Describe functionsh such that the statement(S) is true for
a) allh-convex functionsf.
b) someh-convex functionsf, and ﬁnd all such functionsf.

PROBLEMS FOR THE 13th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
3. Develop a method of solving equations by using convexity. For example, solve the following
equations by applying the statement(S) above:
4
√
x2 +x + 10 +
4
√
7−x2−x = 3,
(x2 +x + 2)(x2−3x + 6) = 5(2x2−2x + 3).
4. Takeh(λ) =
√
λ
2
√
1−λ.
a) Show that for all positive real numbersx andy and allλ∈]0, 1[, one has the inequality
Lλ,h(x,y ) ⩾H1/2,−1(x,y ).
b) Find the maximump∈R such that for all positivex,y∈R and allλ∈]0, 1[, one has
Lλ,h(x,y ) ⩾H1/2,p(x,y ).
c) Find the maximump∈R such that for all positivex,y∈R and allλ∈]0, 1[, one has
Lλ,h(x,y ) ⩾Hλ,p(x,y ).
5. Let p0 be a real number. Suggest a way of ﬁnding a functionh : ]0, 1[→[0, +∞[ such that
the following inequality holds for all positivex,y ∈R, all λ∈]0, 1[ and all p ⩽ p0, but for
p>p 0 it is false:
a) Lλ,h(x,y ) ⩾H1/2,p(x,y ).
b) Lλ,h(x,y ) ⩾Hλ,p(x,y ).
6. Suggest and study additional directions of research.
5. Odd and Even
Let A be a set of real-valued functions deﬁned onR. Given a real numberr∈R, we denote
byAO(r) the subset of all functions inA which areodd atr, that is,
f(r−t) +f(r +t) = 0, for anyt∈R, (2)
and denote byAE(r) the subset of all functions inA which areeven atr, that is,
f(r−t)−f(r +t) = 0, for anyt∈R. (3)
If B and C are two sets of real-valued functions deﬁned onR, then B +C is the set of all
functions f that can be presented asf =g +h with g∈B and h∈C.
1. Is it true that any functionf can be presented asf =g +h, whereg is an odd function at
0 and h is an even function at0. Is such a presentation unique?
2. Check whether the relationA =AO(r) +AE(r) is true for anyr∈R in the following cases:
a) A = F is the set of all real-valued functions onR;
b) A = M is the set of all bounded real-valued functions onR;
c) A = F\M is the set of all unbounded real-valued functions onR;
d) A = D1 is the set of all real-valued functions onR diﬀerentiable at at least one point;
e) A = F\D1 is the set of all real-valued functions onR which are nowhere diﬀerentiable.
3. Let c1,c 2 > 0 be positive real numbers. Find all realc >0 for which there exist functions
f∈M(r), g∈MO(r) and h∈ME(r) such that
f =g +h and max
x∈R
|f(x)|=c, max
x∈R
|g(x)|=c1, max
x∈R
|h(x)|=c2.
4. Let S, S1 and S2 be subsets of R. Do there exist functions f ∈F(r), g∈FO(r) and
h∈FE(r) such thatf =g +h and the sets of points where these functions are diﬀerentiable

6 OCTOBER 2021
are exactlyS, S1 and S2 respectively? Start by investigating the question for particularS, S1
and S2.
5. Let r1 and r2 be distinct real numbers. Check whether the relationsA =AO(r1) +AE(r2),
A = AO(r1) +AO(r2) and A = AE(r1) +AE(r2) are true, and investigate uniqueness of a
presentationf =g +h, in the following cases:
a) A = P2 is the set of polynomials of degree at most 2 with real coeﬃcients;
b) A = P is the set of all polynomials with real coeﬃcients;
c) A = C is the set of all continuous real-valued functions onR;
d) A = D is the set of all diﬀerentiable real-valued functions onR;
e) A = M;
f) A = F.
A functionf is calledlocally odd atr if the equation (2) is satisﬁed in a neighbourhood of 0,
that is, there existsε>0 such that
f(r−t) +f(r +t) = 0, for anyt∈[−ε,ε].
If the equation (3) is satisﬁed in a neighbourhood of 0, thenf is locally even atr. A function
f is calledlocally quasiodd atr if there existsε>0 such that
f(r−t) +f(r +t)−2f(r) = 0, for anyt∈[−ε,ε].
Denote byAloc
O (r), Aloc
E (r) and Aloc
Q (r) the subsets of all functions inA which are locally odd,
locally even and locally quasiodd atr respectively.
Let k be a real number. A functionf is calledk-asymptotically odd atr if
lim
t→0
f(r−t) +f(r +t)
tk = 0,
and k-asymptotically even atr if
lim
t→0
f(r−t)−f(r +t)
tk = 0.
A functionf is calledk-asymptotically quasiodd atr if
lim
t→0
f(r +t) +f(r−t)−2f(r)
tk = 0.
Denote byAk
O(r),Ak
E(r) andAk
Q(r) the subsets of all functions inA which arek-asymptotically
odd, k-asymptotically even andk-asymptotically quasiodd atr respectively.
6. Describe the functionsf∈A such that
a) f∈Aloc
O (r) for allr∈R;
b) f∈Aloc
E (r) for allr∈R;
c) f∈Aloc
Q (r) for allr∈R;
d) f∈Ak
O(r) for allr∈R;
e) f∈Ak
E(r) for allr∈R;
f) f∈Ak
Q(r) for allr∈R.
Do they form a linear subspace ofA? If yes, what is its dimension? Start withA = F and
A = M.
7. Given a real k, is there a continuous function that is neitherk-asymptotically odd nor
k-asymptotically even at all points? Start withk = 0.
8. Suggest and study additional directions of research.

PROBLEMS FOR THE 13th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
6. Binomial Coeﬃcients and Prime Numbers
Let S⊆N be a subset of positive integers. An integern≥2 will be calledS-compound if,
for each1≤k≤n−1, the binomial coeﬃcient
(n
k
)
is divisible by at least one number fromS.
Given a positive integerℓ, we will say thatn isℓ-compound if it isS-compound for some setS
consisting of exactlyℓprime numbers.
Denote byq(n) the largest prime number less thann≥3, and letq(1) =q(2) = 0.
1. Determine all integersn≥2 which are
a) S-compound, whereS ={p}for a primep;
b) 1-compound.
2. Suppose thatS consists of exactlyℓprime numbers.
a) Prove that there are inﬁnitely many positive integers which areS-compound.
b) Is it true that there are inﬁnitely many positive integers which are notS-compound?
3. Prove thatn is 2-compound in the following case:
a) n =pα+ 1, wherep is prime andαis a non-negative integer;
b) n = pα1
1 pα2
2 ···pαs
s is a prime factorisation such that pα1
1 < pα2
2 < ···< pαs
s and
n<q (n) +pαs
s ;
c) n =pkm where p is prime,m isn’t divisible byp and k is large enough.
4. Letn be a positive integer having a prime factorisationn =pα1
1 pα2
2 ···pαs
s withpα1
1 <p α2
2 <
···<p αs
s . Prove thatn is 3-compound in the following cases:
a) n is even, it is not a power of2, andq(n)<n −pαs
s < 2q(n
2 );
b) n< 6pαs−1
s−1 pαs
s ;
c) n< 6q(n
d) for a divisord> 1 of n.
5. Is it true that all integersn≥2 are
a) 2-compound?
b) 3-compound?
c) ℓ-compound, whereℓ>3 is a given integer?
6. Find or describeS-compound integers for particular ﬁnite or inﬁnite subsetsS of positive
integers.
7. Generalise and investigate the problem for multinomial coeﬃcients.
8. Suggest and study additional directions of research.
7. Proper Numberings of Graphs
LetG = (V,E, λ) be a simple undirected labeled graph, whereV is its vertex set,E is its edge
set andλ :E→N is a labeling of its edges with positive integers. Aproper vertexk-numbering
of G is a labelingν: V →{1,...,k}of its vertices with integers from1 to k satisfying the
following condition: if any two verticesu and v are connected by an edgee, then
|ν(u)−ν(v)|≥λ(e).
Note that it is not necessary that all the integers from1 to k are used (see Figure 3).
For a vertexv, lets(v) be the sum of the labels on all the edges with an endpointv. Denote
byS(G) the maximum of such sums:
S(G) = max
v∈V
s(v).

8 OCTOBER 2021
9
2
44
16
50
7
7
41
13
5
22
Figure 3. A proper vertex50-numbering of a labeled graph withS(G) = 66.
1. Consider the following algorithm: list the vertices ofG in an arbitrary order and, according
to this order, give to each vertex the least possible number for which the required condition for
a properk-numbering will not be violated. Is it true that this algorithm successfully produces
a proper vertexk-numbering with
a) k = 2S(G) + 1, for anyG?
b) k = 2S(G), for any connectedG?
c) k = 2S(G)−1, for any connectedG with at least 2021 vertices?
2. Prove that any graphG has a proper vertex(S(G) + 1)-numbering.
3. Give examples of graphsG that do not have any proper vertexS(G)-numbering.
4. Find necessary and/or suﬃcient conditions for a graphG to have a proper vertexS(G)-
numbering. First, consider the case when all edges ofG are labeled with1.
5. Find lower bounds, upper bounds or exact values (depending onG) for the minimum positive
integerk such thatG has a proper vertexk-numbering, ifG is
a) a labeled complete graph;
b) a labeled even cycle;
c) a labeled odd cycle;
d) a labeled bipartite graph;
e) a labeled triangle-free graph;
f) a labeled planar graph.
6. Suggest and study additional directions of research.
8. Unimodality of Permutations
For a positive integern, we denote [ [1,n ] ] ={1,...,n}. Let a1,...,an be a sequence of
real numbers. It is called strongly unimodal if there is an indexk∈[ [1,n ] ]such that a1 <
a2 < ···< ak and ak > ak+1 > ···> an. It is called unimodal if there is a partition
{i1,...,ip}∪{j1,...,jq}= [ [1,n ] ], wherep andq are positive integers withp +q =n, such that
i1 <···<i p, j1 <···<j q and
ai1 <···<a ip >a j1 >···>a jq.
A sequence is calledweakly unimodalif it is the union of a decreasing subsequence and a strongly
unimodal subsequence that have the same ﬁrst element. More formally, there is a partition
{i1,...,ip}∪{j1,...,jq}= [ [2,n ] ], wherep andq are positive integers withp +q =n−1, such
that 1<i 1 <···<i p, 1<j 1 <···<j q and
a1,ai1,...,aip is decreasing but a1,aj1,...,ajq is strongly unimodal.

PROBLEMS FOR THE 13th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 9
Let Sn be the set of n-permutations, that is, the set of sequences a1,...,an such that
{a1,...,an}= [ [1,n ] ]. Denote bySUn, Un and WUn the sets of strongly unimodal, unimodal
and weakly unimodaln-permutations respectively.
A sequence is calledstrongly classiﬁedif it can be sorted in ascending order with a stack (an
example is shown in Figure 4).
≻ ≻
2, 4, 5, 3, 1
(i)
≻ ≻
2, 4
5
3
1
(ii)
≻ ≻
2, 4
3
1
5
(iii)
≻ ≻
2
4
3
1
5
(iv)
≻ ≻
2
1
3, 4, 5
(v)
≻ ≻
2
1
3, 4, 5
(vi)
≻ ≻
1, 2, 3, 4, 5
(vii)
Figure 4. The permutation 2, 4, 5, 3, 1 is strongly classiﬁed.
A sequence is calledclassiﬁedif it can be sorted in ascending order with a limited dequeue,
and weakly classiﬁedif it can be sorted in ascending order with a dequeue (see Figure 5).
≻ ≻
≻
(a)
≻ ≻
≻≻
(b)
Figure 5. A limited dequeue (A) and a dequeue (B).
Denote bySCn, Cn and WCn the sets of strongly classiﬁed, classiﬁed and weakly classiﬁed
n-permutations respectively.
1. Determine forn = 3 and n = 4:
a) SUn; b) Un; c) WUn; d) SCn; e) Cn; f) WCn.
2. Find a formula or give lower and upper bounds for the following cardinalities:
a)|SUn|; b) |Un|; c) |WUn|; d) |SCn|; e) |Cn|; f) |WCn|.
Let k∈N. A sequence is calledk-strongly unimodal(resp. k-unimodal, k-weakly unimodal,
k-strongly classiﬁed,k-classiﬁedork-weakly classiﬁed) if it is a disjoint union ofk subsequences
that are strongly unimodal (resp. unimodal, weakly unimodal, strongly classiﬁed, classiﬁed or
weakly classiﬁed).
For a permutationσ∈Sn, we denote bykSU (σ),kU(σ),kWU (σ),kSC (σ),kC(σ) andkWC (σ)
the smallest positive integerk for which σ is k-strongly unimodal,k-unimodal, k-weakly uni-
modal, k-strongly classiﬁed,k-classiﬁed andk-weakly classiﬁed respectively.
For any subsetM⊆Sn, deﬁne
kSU (M) = max
σ∈M
kSU (σ) and ¯kSU (M) = 1
|M|
∑
σ∈M
kSU (σ).

10 OCTOBER 2021
Similarly, we deﬁnekU(M), kWU (M), kSC (M), kC(M), kWC (M) and ¯kU(M), ¯kWU (M),
¯kSC (M), ¯kC(M), ¯kWC (M).
3. Find a formula and an asymptotic or give lower and upper bounds for:
a) kSU (Sn); b) kU(Sn); c) kWU (Sn); d) kSC (Sn); e) kC(Sn); f) kWC (Sn).
4. Find a formula and an asymptotic or give lower and upper bounds for:
a)kSU (SCn); b) kSU (Cn); c) kSU (WCn); d) kWU (SCn); e) kWU (Cn); f) kWU (WCn).
5. Find a formula and an asymptotic or give lower and upper bounds for:
a) ¯kSU (Sn); b) ¯kU(Sn); c) ¯kWU (Sn); d) ¯kSC (Sn); e) ¯kC(Sn); f) ¯kWC (Sn).
6. Suggest and study additional directions of research.
9. Wobbly Tables
We would like to place a table on the ﬂoor of a room. The ﬂoor is parametrised by a surface
z =f(x,y ), wheref : [−1, 1]×[−1, 1]→R is a continuous map. For instance, this could be
•a horizontal plane:f1(x,y ) = 0;
•an inclined plane:f2(x,y ) =ax +by with a,b∈R;
•a horse saddle:f3(x,y ) =sxy with s∈R\{0};
•a sphere:f4(x,y ) =
√
1−x2+y2
R2 with radiusR>
√
2;
•a double periodic surface:f5(x,y ) = cos( 2πx
ω) cos(2πy
ω) with ω∈]0,∞[.
The table has four legs of the same large length. LetPi = (xi,yi,zi)∈[−1, 1]×[−1, 1]×R,
where 1≤i≤4, be the positions of the tips of the legs. We assume that the pointsP1,P2,P3
and P4 lie in the same plane andP1P2P3P4 is a ﬂat convex quadrilateralQ.
We say that the table isgrounded if the following two conditions are met:
•the pointsP1, P2 and P3 are situated on the ﬂoor, that is,zi =f(xi,yi) for 1≤i≤3;
•the pointP4 is situated on the ﬂoor or above it, that is,z4≥f(x4,y 4).
A grounded table is calledstabilised if z4 =f(x4,y 4) and wobbly if z4 >f (x4,y 4).
P2
P3 P4
P1
Figure 6. A wobbly table.
1. For the surfaces parametrised by the functionsf1,...,f 5, can the table be grounded when
a) Q is a square with sides of length
√
2?
b) Q is a rectangle with sides of lengthr and s such thatr2 +s2 = 4?
c) Q is a rhombus with an axis of length2 and an axis of lengthℓ, where 0<ℓ<2?
d) Q is any convex quadrilateral contained in a disc of radius1?

PROBLEMS FOR THE 13th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 11
2. For which of the above surfaces and quadrilaterals could the table be
a) wobbly?
b) stabilised?
3. For the above surfaces and quadrilaterals, when the table can be stabilised, what are the
possible values of the angleαbetween the plane of the tips(P1P2P3P4) and the horizontal
plane z = 0?
4. Describe surfaces on which all tables withQ contained in a disc of radius1 can be
a) grounded;
b) stabilised.
5. For a general surfacez =f(x,y ) of the ﬂoor, give conditions onf so that the table can be
stabilised for quadrilaterals of the question 1.
6. Suggest and study additional directions of research.
10. Non-nilpotent Graphs of Groups
Throughout this problemSn andAn are the symmetric and the alternating groups of degree
n respectively,Dn =
⣨
x,y
⏐⏐⏐xn =y2 = (xy)2 = 1
⟩
is the dihedral group of order2n,|G|is the
order of a groupG,⟨x,y⟩is a subgroup generated byx andy,G1≃G2 means that groupsG1
and G2 are isomorphic, Γ1≃Γ2 means that graphsΓ1 and Γ2 are isomorphic.
Recall that a group is callednilpotent if any two elements of coprime order commute. Set
nilG(x) ={y∈G | ⟨x,y⟩is nilpotent}and nil(G) =
⋂
x∈G
nilG(x).
Thenon-nilpotent graph ofG, denoted byΓ(G), is the graph whose set of vertices isG\nil(G)
and two verticesa and b are connected by an edge if⟨a,b⟩is not nilpotent. In Figure 7, you
can see the non-nilpotent graph of the symmetric group of degree3.
(1 2)
(2 3)
(1 3)
(1 2 3)
(1 3 2)
Figure 7. The non-nilpotent graph ofS3.
1. Consider the case thatG is D4, S4 or A4.
a) How many connected components does the graphΓ(G) have?
b) IfH is another ﬁnite group such thatΓ(H)≃Γ(G), is it true that|G|=|K|? G≃K?
2. ForG =Dn, describe the graphΓ(G). In particular answer the following questions.
a) How many vertices doesΓ(G) have?
b) How many edges doesΓ(G) have?
c) Is Γ(G) connected? How many connected components does it have?

12 OCTOBER 2021
d) Does every connected component ofΓ(G) have a Hamiltonian circuit?
e) Does every connected component ofΓ(G) have an Eulerian circuit?
f) IfH is another ﬁnite group such thatΓ(H)≃Γ(G), is it true that|G|=|K|? G≃K?
3. Same questions whenG is thegeneralised quaternion groupQ4n of order 4n, wheren≥2:
Q4n =
⣨
x,y
⏐⏐⏐x2n = 1, xn =y2, xy=yx−1⟩
.
4. Same questions whenG =Sn.
5. Same questions whenG =An.
6. Consider non-nilpotent graphs of other groups.
7. Suggest and study additional directions of research.
Email address: oc@itym.org
URL: http://www.itym.org/
