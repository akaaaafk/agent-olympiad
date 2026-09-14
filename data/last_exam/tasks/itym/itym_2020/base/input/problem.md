PROBLEMS FOR THE 12th INTERNATIONAL TOURNAMENT OF
YOUNG MATHEMATICIANS
OCTOBER – NOVEMBER 2020
Contents
Notation 1
1. Cutting into Pieces 1
2. Coding Functions 2
3. Two Types of Functions 3
4. A Glass of Juice 4
5. Multiplication Tables 4
6. Sequences from Rooted Trees 5
7. Families of Subsets 6
8. Primes with Special Properties 7
9. Convergence of Means 8
10. An Electrical Network Problem 9
Keywords: 1. plane geometry, combinatorics – 2. injectivity, polynomials – 3. integrals,
inequalities – 4. solids, volume – 5. number theory, algorithms – 6. trees, sequences – 7. set
theory, combinatorics – 8. primes, number bases – 9. real analysis, means – 10. graphs, metric
spaces
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Zn ={0, 1,...,n−1}ring of residue classes modulon
Z, Q, R, C sets of integer, rational, real and complex numbers
Rn n-dimensional real space
]a,b [ and [a,b ] open and closed interval froma to b
[ [a,b ] ] set of integers froma to b
Z[i] ring of Gaussian integersZ[i] ={a +bi|a,b∈Z}
diam(G) diameter of a graphG
#M or|M| cardinality of a setM
M×N Cartesian product of two sets or graphsM and N
M∪N,M \N,M \N union, intersection and diﬀerence of two setsM and N
M△N symmetric diﬀerence of two setsM and N
1. Cutting into Pieces
Let n be a positive integer.
1. An n×n square is cut inton congruent pieces along the grid lines. (Two pieces are called
congruent if one can be obtained from another by rotation or reﬂection.) What could the total
length of the cuts be?
2. An a×b rectangle is cut inton congruent pieces along the grid lines, wheren divides ab.
What could the total length of the cuts be?
©International Tournament of Young Mathematicians. This work is licensed under a “CC BY-SA 4.0” license.
Date: September 2, 2020.
1

2 OCTOBER – NOVEMBER 2020
3. An n×n square is cut along the grid lines inton pieces with the same area. What are the
minimum and maximum total lengths of the cuts?
Figure 1. A 5×5 square is cut into 5 pieces with the same area, and the total
length of the cuts is 16.
4. Let a and b be positive integers such thatab is divisible byn. An a×b rectangle is cut
along the grid lines inton pieces with the same area. What are the minimum and maximum
total lengths of the cuts?
5. LetP be a polygon in the real plane. Suppose that it is cut inton pieces with the same area
so that every cut is parallel to a side ofP (the side doesn’t have to be the same for diﬀerent
cuts). Denote byl(P,n ) and u(P,n ) the minimum and maximum possible total lengths of the
cuts respectively. Find or estimate the values ofl(P,n ) and u(P,n ) when
a) P is a rectangle;
b) P is a regular polygon.
6. Finally, suppose that cuts are arbitrary straight lines (not necessarily parallel to sides).
Denote byL(P,n ) and U (P,n ) the minimum and maximum possible total lengths of the cuts
of a shapeP into n pieces with the same area. Find or estimate the values ofL(P,n ) and
U (P,n ) when
a) P is a rectangle;
b) P is a regular polygon;
c) P is a circle;
d) P is another shape of your choice.
7. Suggest and investigate additional directions of research.
2. Coding Functions
We will say that a functionf :A→B is coding, or thatf codes the setA, if it is injective:
f (x)̸=f (y) for any distinctx,y∈A.
Let n and k≥n be positive integers.
1. Find alla,b∈Zn for which the linear functionf (x) = ax +b codes the setZn.
2. Find alla,b,c ∈Zn for which the quadratic functionf (x) = ax2 +bx +c codes Zn.
3. Give examples and ﬁnd properties of polynomials of degreed≥3 which are coding functions
from Zn to Zn.
4. More generally, letP (x) = adxd +···+a1x +a0 be a polynomial of degreed with integer
coeﬃcients. When are the valuesP (0),P (1),...,P (n−1) pairwise distinct modulok?
5. Find necessary and/or suﬃcient conditions for a polynomialP (x) = adxd +···+a1x +a0
with coeﬃcients inZn to code the setZn[i] =
{
x +y√−1 |x,y∈Zn
}
.

PROBLEMS FOR THE 12th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
6. Let ζ∈C be an nth root of unity, that is, a solution of the equation xn = 1 . Find
necessary and/or suﬃcient conditions for a polynomialP (x) = adxd +···+a1x +a0 with
integer coeﬃcients to code the set
{
ζ,ζ2,...,ζn
}
. Start withd = 1, 2, 3.
7. Suggest and investigate further directions of research.
3. Two Types of Functions
Letf be a function deﬁned and continuous on a interval[a,b ], wherea,b∈R anda<b . We
will say thatf is a function ofﬁrst typeif, for allx∈[a,b ], the following inequality holds:
f (x)≤
b
a
f (s)ds.
We will say thatf is a function ofsecond typeif, for allx∈[a,b ], one has:
f (x)≤
x
a
f (s)ds.
1. Find allc∈R for which the functionf (x) = x +c is a) of ﬁrst type; b) of second type.
2. Find allc∈R for which the functionf (x) = cx−x2 is a) of ﬁrst type; b) of second type.
3. Is it true that any function of second type is also of ﬁrst type?
4. Give examples and ﬁnd properties of functions of ﬁrst type which are not of second type?
5. Find all reala and b for whichf (x) = sin x is a function a) of ﬁrst type; b) of second type.
6. Is it true that any diﬀerentiable function of second type is a solution of the following system
of inequalities



f′(x)≤f (x), for allx∈[a,b ];
f (a)≤0.
Is the converse true?
7. Determine the polynomials of degreen∈N which are functions a) of ﬁrst type; b) of second
type.
8. Find necessary and/or suﬃcient conditions for a function to be a) of ﬁrst type; b) of second
type.
9. Give examples of functionsf (x,y ) deﬁned and continuous on[0, 1]×[0, 1] such that, for all
x, y∈[0, 1], one has
a) f (x,y )≤
∫∫
[0,1]×[0,1]
f (t,s )dtds.
b) f (x,y )≤
∫∫
[0,x]×[0,y]
f (t,s )dtds.
10. Investigate an analogous problem for functions that are not necessary continuous but
Riemann integrable, Lebesgue integrable, etc.

4 OCTOBER – NOVEMBER 2020
4. A Glass of Juice
A mathematician ordered a glass of juice. Leta and b be positive real numbers. Consider
the following glasses (the wall of the glass in the ﬁrst four cases is a solid of revolution of a
curvef (x,z ) = 0 around thez-axis):
a) cylinder: f (x,z ) = x−a and 0≤z≤b;
b) cone: f (x,z ) = z−ax and 0≤x≤b;
c) hemisphere: f (x,z ) = z−
√
a2−x2 and 0≤x≤a;
d) parabola: f (x,z ) = z−x2 and 0≤x≤b;
e) a rightn-prism with heightb and a regularn-gon with sidea as its bases;
f) an upturned rightn-pyramid with heightb and a regularn-gon with sidea as its base.
In the beginning, the glass was full of juice. Denote byV the volume of juice in it. While
delivering the glass, the waiter took a misstep so that the glass made an angleαwith its initial
position. Hence, some juice was spilled (see Figure 2).
x
z
a
b
x
z
α
Figure 2. Juice was spilled from a cylinder glass.
1. For givena, b, n and a form of the glass above, does the volume of the remaining juice
depend only onα?
Denoteby V (α)thevolumeoftheremainingjuice. Fortheaboveglasses, answerthefollowing
questions.
2. Let α= 30◦, a = 1 and b = 3. Find all possible values ofV (α)/V.
3. Let V (α)/V = 1/2, a = 1 and b = 3. Find all possible values ofα.
4. Try to ﬁnd a formula or all possible values ofV (α)/V in terms ofa, b, n and α.
5. Introduce other types of glasses and study the problem for them.
5. Multiplication Tables
Let n and k≥2 be positive integers. Then-multiplication table of dimensionk is the set of
all integers obtained as a product ofk integers between 1 and n.
For a positive integerm, we deﬁne
ak(m,n ) = #


(x1,x 2,...,xk)∈[ [1,n ] ]k
⏐⏐⏐⏐⏐⏐
k
i=1
xi =m


,
where [ [1,n ] ] ={1,...,n}.
1. Let αbe a positive integer andp be a prime number, determineak(pα,n )

PROBLEMS FOR THE 12th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
2. Find bounds forak(m,n ).
3. Find the following limits:
a) limn→∞
1
n
∑n
m=1ak(m,n );
b) limn→∞
1
nk
∑nk
m=nak(m,n ).
Denote byMk(n) the cardinality of then-multiplication table of dimensionk. For a sequence
of integersX ={xi}∞
i=0, denote byMk(X,n ) the number of integers inX which appear in the
n-multiplication table of dimensionk.
4. Determine limn→∞
Mk(n)
nk .
5. Estimate (ﬁnd bounds and an asymptotic) the values ofMk(X,n ) and limn→∞
Mk(X,n)
#(X∩[ [1,n] ])k in
the following cases:
a) X is the sequence of prime numbers;
b) X = N and k = 2;
c) X ={ir}i∈N where r is a positive integer;
d) X is a geometric progression withx0 = 1;
e) X is an arithmetic progression with the common diﬀerence being a prime number.
6. Find bounds and an asymptotic forMk(n).
7. Given k, m and the prime decomposition ofm, determine time complexity for ﬁnding the
minimum integern≥1 such thatak(m,n )≥1.
8. Suggest and study additional directions of research.
6. Sequences from Rooted Trees
LetT be a ﬁnite rooted tree withn leafs. Deﬁne the sequenceS(T ) = (a1,...,an) as follows.
•Choose a path from the rootr to one of its leafsx1, and deﬁnea1 = 0.
•Choose a new leafx2, so that the the number of common edges in the path fromr to
x1 and the path formr to x2 is minimal, and deﬁnea2 this number of common edges.
•Choose the leafsx3,x 4,...,xn in the same way recursively: for2≤i≤n−1, we take
xi+1 such that the path fromr to xi+1 minimises the total number of common edges
(counted multiple times if necessary) with the path fromr tox1, the path fromr tox2,
..., the path form r ot xi.
For example, for the tree in Figure 3, we can havex1 = 2, x2 = 4, x3 = 1, x4 = 5, x5 = 3,
and its sequence isa1 = 0, a2 = 0, a3 = 1, a4 = 2, a5 = 2.
r
1 2 3 4 5
Figure 3. Example of a rooted tree.

6 OCTOBER – NOVEMBER 2020
1. Prove that the sequenceS(T ) depends only on the treeT and not on the choice of leafs,
that isS(T ) is well deﬁned.
2. Calculate or describe the sequenceS(T ) when T is
a) the tree in Figure 4;
b) a full binary tree, that is any non-leaf vertex has exactly two children;
c) a full k-ary tree, that is any non-leaf vertex has exactlyk children;
d) a tree with all the vertices at the same distanceh from the root having the same degree
dh, for a given sequence of positive integersd1,d 2,....
r
1 2 3 4 5 6 7 8 9
Figure 4. Another example of a rooted tree.
3. Is it true that ifS(T ) = S(T′), thenT and T′are isomorphic?
4. Let B = ( b1,b 2,...) be a ﬁnite sequence of non-negative integers. Does the equation
S(T ) = B, whereT is a ﬁnite tree, have a solution? Give necessary and suﬃcient conditions
on B.
5. Estimate (give lower and upper bounds) and ﬁnd properties of the last terman of the
sequence S(T ), depending on the degrees of the vertices ofT or other characteristics ofT.
It is also possible to deﬁne the sequenceS(T ) for a treeT of inﬁnite height – instead of
choosing leafs, one might consider inﬁnite paths starting at the root.
6. Formulate and answer the previous questions for inﬁnite trees. Also, in the question 3,
investigate the case of a tree with each vertex having at least two descending edges.
7. Suggest and work on other directions of research.
7. Families of Subsets
Let m and n be positive integers, and letF ={F1,F 2,...,Fm}be a family ofm subsets of
the set [ [1,n ] ] ={1,...,n}.
1. In this question suppose thatm is odd.
a) Find the maximum possible value ofm (in terms ofn) for which there exists a family
F with the property: for all1≤i≤m, there are exactlym−1
2 indices j̸=i such that
|Fi\Fj|> 0.
b) Fix a positive integerk. Find the maximum possible value ofm (in terms ofn and k)
for which there exists a familyF with the property: for all1≤i≤m, one has|Fi|=k
and there are exactlym−1
2 indices j̸=i such that|Fi\Fj|> 0.

PROBLEMS FOR THE 12th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
2. Given positive integersm, n and s, what maximum number of pairs (Fi,Fj) such that
|Fi△Fj|=s could there be for a familyF? Start withs = 1. HereA△B = (A\B)∪(B\A)
denotes thesymmetric diﬀerenceof A and B.
3. Fix ε∈]0, 1[ and letn be suﬃciently large.
a) Prove that there exist an integerk, depending onn and ε, and a familyF with m >
(1 + 0.1ε2)n such that
|Fi|=k and |Fi\Fj|<εk, for all 1≤i̸=j≤m. (1)
b) The same question form> (1 + 0.4ε2)n.
c) Could you replace the constant0.4 by a larger one?
d) Give an upper bound (in terms ofn andε) form such that there exist a positive integer
k and a familyF satisfying (1).
4. Givenn, ﬁnd the maximum possible value ofm for which there exists a familyF with the
following property:
a)|Fi|≡a (mod 2) and|Fi\Fj|≡b (mod 2) for all distincti,j ∈[ [1,m ] ]. Consider the
cases (a,b ) = (0, 0), (0, 1), (1, 0) and (1, 1) separately.
b)|Fi|≡a (mod 3) and|Fi\Fj|≡b (mod 3) for all distincti,j ∈[ [1,m ] ]. Consider the
cases (a,b ) = (0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1) and (2, 2) separately.
c)|Fi|̸≡0 (mod 6) and|Fi\Fj|≡0 (mod 6) for all distincti,j ∈[ [1,m ] ].
5. Suggest and study additional directions of research.
8. Primes with Special Properties
For positive integersx and b, denote byAb(x) the product of the digits ofx in its baseb
representation, and deﬁnerb(x) to be the integer obtained by writing the digits ofx in its base
b representation in the reverse order. For example,A10(1729) = 126 , r10(1729) = 9271 and
A3(1729) = 0, r3(1729) = 1001012 3.
Let p1 = 2, p2 = 3, p3 = 5, ...be the sequence of prime numbers. A primepn is called
b-product-likeifAb(pn) has the same baseb representation asn. A primepn is calledb-mirror-
like if rb(pn) = prb(n). For example, 73 is both 10-product-like and 10-mirror-like, since it is
the 21st prime number,7·3 = 21 and 37 is the 12th prime number.
1. a) Prove that73 is the only prime which is both10-product-like and 10-mirror-like.
b) Determine all primes which are both9-product-like and 9-mirror-like.
c) Consider other basesb.
2. a) Classify all primespn which are 10-product-like.
b) The same question for any baseb.
3. a) Are there inﬁnitely many10-mirror-like primes?
b) If yes, estimate the number of the10-mirror-like primes not exceedingx, wherex∈N.
If not, give an upper bound for the10-mirror-like primes and try to classify them.
4. Given a positive integerℓ, classify all primespn such that|A10(pn)−n|=ℓ, if
a) ℓ= 1;
b) ℓ>1.
5. Suggest and study additional directions of research.

8 OCTOBER – NOVEMBER 2020
9. Convergence of Means
Consider a sequencex ={xn}∞
n=1 of positive real numbers. DenoteAk(x,n ) = xn+1+···+xn+k
k
and Gk(x,n ) = k√xn+1·...·xn+k. We will study the sequences
Ak(x) ={Ak(x,n )}∞
n=1 and Gk(x) ={Gk(x,n )}∞
n=1.
1. Assume that the sequenceA2(x) has a limit. Is it true that:
a) the sequence{xn}∞
n=1 also has a limit?
b) the sequenceA3(x) has a limit? If yes, may it be diﬀerent from the limit ofA2(x)?
c) the sequenceG2(x) has a limit? If yes, may it be diﬀerent from the limit ofA2(x)?
2. Suppose that for some ﬁxedk≥3 the sequenceAk(x) has a limita> 0.
a) Does this imply convergence of sequences Al(x), Gl(x) for various l ≥1? If they
converge, what could be the possible values of their limits?
b) Answer the same question for sequences A∞(x) = {An(x,n )}∞
n=1 and G∞(x) =
{Gn(x,n )}∞
n=1. Is it possible thata is not alimiting pointfor{xn}∞
n=1 (that is{xn}∞
n=1
does not contain subsequences converging toa)?
c) What are possible limiting points of the sequences in a) and b)?
d) Assume that for somek and l greater than 1 or equal to∞the sequencesAk(x) and
Gl(x) converge to the same limita > 0. Does this imply that the sequence{xn}∞
n=1
also converges to the same limit?
3. Let f : ]0, +∞[→]0, +∞[ be an arbitrary function. Let R and T stand for any of the
symbols Ak and Gl. For any sequencex ={xn}∞
n=1 we shall assume thatA1(x) = G1(x) = x.
Finally, byf (x) we denote the new sequence{f (xn)}∞
n=1.
We say that the functionf is (R,T )-continuous, if for any sequencex of positive real numbers
and anya> 0 the condition limn→∞R(x) = a implies limn→∞T (f (x)) = f (a). Note that for
R =T =A1 this deﬁnition coincides with the standard deﬁnition of continuous functions.
a) Check which elementary functions (polynomials, trigonometric polynomials,exp(x),xα)
are (R,T ) continuous for variousR and T.
b) Do the theorems of Bolzano1and Weierstrass2generalise to(R,T )-continuous functions?
c) Is composition of two(R,T )-continuous functions also(R,T )-continuous?
d) Can an(R,T )-continuous non-constant function be periodic?
e) Investigate which other statements on continuous functions generalise or do not gener-
alise to (R,T )-continuous functions?
f) Investigate the relationship between classes of(R,T )-continuous functions for various
R and T.
g) Determine the cardinality (cardinal number) of the set of(R,T )-continuous functions.
4. Let a(x,y ) = x+y
2 and g(x,y ) =√xy be the standard arithmetic and geometric means for
x,y > 0. Let 0<p<q be two ﬁxed real numbers. Solve the functional equations
f (a(x,p )) +f (a(x,q )) = f (x) (A)
f (g(x,p )) +f (g(x,q )) = f (x) (B)
by ﬁnding all functionsf deﬁned on[p,q ], satisfying (A) and/or (B), which are
a) continuous;
b) periodic;
c) diﬀerentiable at least one time;
d) diﬀerentiable at least two times.
1Bolzano theorem. If a continuous function deﬁned on an interval takes both positive and negative values,
then it must be 0 at a point.
2W eierstrass theorem. A continuous function on a closed and bounded interval attains its extreme values.

PROBLEMS FOR THE 12th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 9
5. Consider other modiﬁcations of the equations (A) and (B).
10. An Electrical Network Problem
Let G be an undirected connected graph without loops and multiple edges. For any two
vertices u and v of the graph, denote byd(u,v ) the shortest path distance betweenu and v.
The diameter of the graph, denoted by diam(G), is the maximal value ofd(u,v ) over all pairs
of verticesu and v. One can consider an electrical circuit associated with the graphG and
deﬁne the eﬀective resistanceR as follows. Suppose that each edge corresponds to a 1 Ohm
resistor, and connect a unit current source fromu to v (see Figure 5). Theeﬀective resistance
R(u,v ) is then the diﬀerence of the potentials atu and v.
v
u
1 Ohm
1 Ohm
1 Ohm
1 Ohm
1 Ohm1
Figure 5. Connecting a unit current source between the verticesu and v.
1. Let VG be the set of vertices of the graphG. A functionρ:VG×VG→[0, +∞[ is called a
metric on G if the following properties hold:
i) ρ(u,v ) = 0 if and only ifu =v;
ii) ρ(u,v ) = ρ(v,u ) for anyu,v∈VG (symmetry);
iii) ρ(u,v )≤ρ(u,w ) +ρ(w,v ) for anyu,v,w ∈VG (triangle inequality).
Prove that the eﬀective resistanceR is a metric onG.
2. Is it true that R(u,v ) is maximal for some vertices u and v with d(u,v ) = diam(G)?
Investigate this question for the following graphs.
a) G =Pn×Pn, wherePn is a path onnvertices (‘×’ denotes Cartesian product of graphs).
b) G =Cn×Cn, whereCn is a cycle onn vertices.
c) G =Pn
2 is the graph of ann-dimensional hypercube.
d) G = An is the graph of the permutohedron of ordern. The permutohedronAn is a
polytope in Rn, the vertices of which are formed by permuting the coordinates of the
vector (1, 2,...,n ), and two vertices(a1,...,an) and (b1,...,bn) are connected if and
only if one is obtained form the other by interchanging the numbersi andi + 1for some
1≤i≤n−1.
e) G is an arbitrary undirected connected graph.
3. For the above graphs, determine whetherR(u,v ) attains its minimum for some verticesu
and v such thatd(u,v ) = 1.
4. We say that the eﬀective resistance ismonotonous with respect to the shortest path distance
if the inequalityd(u,v ) < d(u′,v′) implies the inequalityR(u,v )≤R(u′,v′), for any pairs of
vertices (u,v ) and (u′,v′). Investigate this monotonicity property for the above graphs.
5. Suggest and investigate additional directions of research.

10 OCTOBER – NOVEMBER 2020
Email address: oc@itym.org
URL: http://www.itym.org/
