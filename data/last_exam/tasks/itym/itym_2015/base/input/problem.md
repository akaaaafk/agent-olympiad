PROBLEMS FOR THE 7th INTERNATIONAL TOURNAMENT OF YOUNG
MATHEMATICIANS
JULY 2015, SOFIA (BULGARIA)
Contents
Notation 1
1. A Laser Machine 1
2. Maximal Minimal Triangles 2
3. Coloured Circles 3
4. Simple Paths in Grids 4
5. A Recursive Sequence 4
6. Critical Points 5
7. Chain Stores 5
8. A Diophantine Equation 7
9. Framing Matrices 7
10. Polynomial Groups 8
Keywords: 1. geometry, optimisation – 2. combinatorial geometry, maximum/minimum
problem – 3. colouring, set theory – 4. graph theory, probability – 5. recursive sequence,
convergence – 6. analysis, critical point – 7. optimisation, integral – 8. number theory,
Diophantine equation – 9. linear algebra, matrix – 10 algebra, group.
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Zn ={0, 1,...,n−1}ring of residue classes modulon
Z, Q, C sets of integer, rational and complex numbers
Cn n-dimensional complex space
Fq ﬁnite ﬁeld of sizeq =pk
GL(n,K ) group of invertiblen×n matrices over a ﬁeldK
gcd(x1,...,xn) greatest common divisor ofx1,...,xn
|x| absolute value ofx
#M or|M| cardinality of a setM
f (n)≪g(n) one hasf (n)≤g(n) for suﬃciently largen
1. A Laser Machine
A metallic chip of shapeP is put inside a unitary disk in the real plane. An engineer designed
a machine that can move both ways around the disk on its circumference, can emit a laser beam
of widthw in any desired direction and can read whether or not the beam hit the chip.
The engineer wants to determine a characteristicσ of the chip with an error at mostε> 0.
1. Denote byN (P ) the minimal number of laser beams that the machine must emit in order
to accomplish the engineer’s goal. FindN (P ) or give an upper bound in the situations below
(the cases A, B, C and D are independent of each other). Start withε = 1
3, 1
4, 1
10.
Date: March 19, 2015.
1

2 JULY 2015, SOFIA (BULGARIA)
A1) P is a circle; C1) σ is the diameter ofP;
A2) P is a convexn-gon; C2) σ is the perimeter;
A3) P is an arbitrary convex shape; C3) σ is the area;
A4) P is not convex; C4) σ is another characteristic;
B1) P contains the center of the disk; D1) w is negligible;
B2) P doesn’t contain the center of the disk; D2)w is not negligible.
Figure 1. P is a convex pentagon and contains the center of the disk.
2. Now, instead of minimisingN (P ), the engineer would like to minimise the total lengthL(P )
of the path that the machine must run on the circumference to determineσ with an error at
mostε> 0. FindL(P ) or give an upper bound in the situations of the question 1.
3. Construct algorithms and write programs optimisingN (P ) and L(P ) for a givenP.
4. Suggest and study other directions of research.
2. Maximal Minimal Triangles
Let D be a convex domain in the plane with area 1. Let Pn be an arbitrary set of n
distinct points inside or on the boundary ofD. Finally, letMin (Pn) be the minimal area of
n(n−1)(n−2)/6 triangles formed by three ofn points ofPn.
A
B
C
D
Figure 2. A setP4 ={A,B,C,D }with Min (P4) = area(ABC ).
We are interested for the maximum ofMin (Pn), whenD is ﬁxed. Denote this number by
MaxPnMin (Pn). In other words,MaxPnMin (Pn) = a if there exists a conﬁgurationPn of n
points insideD such that any triangle formed by 3 of these points has area at leasta, and this
is the maximala for which we can say this. In fact, it is possible to prove that the maximum
is always achieved.
1. Determine MaxPnMin (Pn) in the following cases:
a) D is a triangle (can be assumed to be equilateral) andn = 4;
b) D is a square andn = 5;
c) D is a triangle andn = 5.

PROBLEMS FOR THE 7th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
2. Consider the case thatD is bounded by a circle (or an ellipse),n is arbitrary.
3. Consider the case thatD is a triangle andn> 5.
4. Consider other types of domainsD.
5. One can also evaluate the expressionMinDMaxPnMin (Pn), whereD belongs to a certain
class of convex domains with area 1, for example, the set of all quadrilaterals. In other words,
MinDMaxPnMin (Pn)≥a, if for anyD within a given class there exists a conﬁguration ofn
points insideD, such that any triangle formed by 3 of these points has area greater than or
equal toa.
6. Study the problem whenD is a convex polygon andPn contains all vertices ofD plus a
ﬁxed number of inner points. One may start with the case thatPn is the set of vertices ofD.
7. Suggest and investigate generalisations to three dimensions.
3. Coloured Circles
Letn andk be positive integers. Two high school students Clara and Carl play the following
games.
1. In the beginning, Clara hasn closed segments. She puts them one by one on a line in such
a way that no point of the line is covered by more thank segments. Carl colours incoming
segments so that any two intersecting segments have diﬀerent colours (two segments are said
to be intersecting if they have at least one point in common including the endpoints). Denote
by C1(n,k ) the minimum number of colours that Carl would need to successfully colour alln
segments regardless of how Clara plays. FindC1(n,k ) or give lower and upper bounds in the
following cases:
a) the length of each segment is the same;
b) the segments are arbitrary.
Figure 3. C2(3, 2) = 3.
2. Clara hasn closed circles. She puts them one by one on a plane in such a way that no point
of the plane is covered by more thank circles. Carl colours incoming circles so that any two
intersecting circles have diﬀerent colours (touching circles are also intersecting – at one point).
Denote byC2(n,k ) the minimum number of colours that Carl would need to successfully colour
alln circles regardless of how Clara plays. FindC2(n,k ) or give lower and upper bounds in the
following cases:
a) the radius of each circle is the same;
b) the circles are arbitrary.
3. In the same manner, one can deﬁne a functionCd(n,k ) for ad-dimensional game. Determine
relations betweenCd(n,k ) when d varies. For example, what islimd→∞Cd(n,k )?
4. Suggest and study other directions of research. For example, consider other types of ﬁgures.

4 JULY 2015, SOFIA (BULGARIA)
4. Simple Paths in Grids
Consider an undirected graphG. LetV be the set of its vertices, andE the set of its edges.
A path of length k is a sequence of distinct edges(v0,v 1), (v1,v 2), ..., (vk−1,vk)∈E. We say
that a path issimple if its vertices are distinct.
1. Let n and k be positive integers. Consider ann×n grid, which is a graph with(n + 1)2
vertices and 2n(n + 1) edges. Denote byDn(k) the minimum number of edges that one should
delete in this graph, so that the obtained graph wouldn’t have a simple path of lengthk. For
example, Dn(1) = 2n(n + 1). Find a formula forDn(k) or estimate it.
Figure 4. D3(2)≤16 (the dashed edges are deleted).
2. Suppose that edges of then×n grid are deleted randomly: for each edge, one tosses a coin
to determine whether it should be deleted. Denote byPn(k) the probability that the obtained
graph has no simple path of lengthk. FindPn(k) or estimate it.
3. Investigate a 3-dimensional generalisation.
4. Formulate and study an analogous problem for triangular grids.
5. Formulate and study an analogous problem for hexagonal grids.
6. Suggest other directions of research.
5. A Recursive Sequence
LetA be a subset of[0, 1]. We takeu0∈[0, 1] and deﬁne a sequence(un) by recursion in the
following manner:un+1 is the proportion of terms amongu0,u 1,...,un which belong toA. In
other words, forn≥0 one has
un+1 = #{i |0≤i≤n and ui∈A}
n + 1 .
1. Does the sequence(un) converge? Study the following cases:
a) A = [a, 1] where 0<a< 1;
b) A = [0,a ] where 0<a< 1;
c) A = [a1,b 1]∪[a2,b 2]∪···∪[ak,bk] with k∈N and 0≤a1 <b 1 <···<a k <b k≤1;
d) A is arbitrary.
2. DenoteℓA(u0) = limn→∞un if the sequence converges, and letL0(A) be the set of possible
valuesℓA(u0) when u0 varies in [0, 1]. Find L0(A) for the cases of the question1.
3. LetN be a non-negative integer. Assume that one chooses real numbersu0,u 1,...,uN from
the interval[0, 1], and constructs a sequence by using the recurrence relation above forn≥N.
Do the results of the question1 still hold?

PROBLEMS FOR THE 7th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
4. Let LN (A) be the set of all possible limitslimn→∞un in the question3 and
L∞(A) :=
⋃
N≥0
LN (A).
For a given setB, does there existA such that L∞(A) = B? Consider the following cases:
a) B ﬁnite; b) B = [0, 1]; c) B = Q∩[0, 1]; d) B is an arbitrary subset of[0, 1].
5. Let A be now a subset of[0, 1]2. Study the convergence of sequences(un) such that
un+1 = #{i |0≤i≤n and (ui,un−i)∈A}
n + 1 .
Start withA = [0,a ]×[0,b ].
6. Critical Points
A critical point of a diﬀerentiable functionf is any valuex in its domain wheref′(x) = 0 .
Consider the following function
F (x) =
n∑
i=1
ci
Pi(x),
where n is a positive integer,ci are nonzero real constants andPi(x) are distinct polynomials
with real coeﬃcients. The functionF is deﬁned everywhere inR except for the real zeros of
the polynomials. Suppose that it is non-constant.
We would like to estimate the numberN (F ) of distinct real critical points ofF.
1. Suppose that the polynomials are linear,Pi(x) = x +ai where ai∈R. Describe the set of
possible values ofN (F ) when n is ﬁxed and
a) the numbersai and ci may vary;
b) the numbersai are ﬁxed but the numbersci may vary;
c) the numbersci are ﬁxed but the numbersai may vary.
2. Let Pi(x) = x2 +aix +bi be quadratic polynomials withai,bi∈R and a2
i < 4bi for alli
form 1 to n.
a) EstimateN (F ). Is it true thatN (F )≤2n−1?
b) Find all possible values ofN (F ) for a ﬁxedn.
3. Investigate the problem for polynomials of higher degrees.
7. Chain Stores
Let f be a piecewise continuous function on an interval[a,b ] such that
b
a
f (x)dx = 1. One
can imagine that the interval is a street and the functionf is the population density. The latter
means that the number
t
s
f (x)dx≤1, where a≤s≤t≤b, gives the proportion of people
living in the part[s,t ] of the street. Merchants place chain stores in the street.
1. Suppose that there is only one merchant who is building hisn stores in such a way that the
inhabitants of the street could shop as comfortably as possible. In other words, he is trying to
minimise the following integral
b∫
a
dist(x,S )f (x)dx,

6 JULY 2015, SOFIA (BULGARIA)
over subsetsS⊂[a,b ] of n points, whereS corresponds to the locations of the stores. Here
dist(x,M ) denotes the distance of a point to the subset. What are the optimal conﬁgurations
of the stores if
a) f (x)≡1
b−a ? b) f (x) =−2
b−a|2x−(a +b)|+ 2 ?
Start withn = 1, 2, 3, 4.
2. Consider other functionsf. Try to construct a general theory by ﬁnding regularities.
3. Let Sopt be an optimal set ofn stores. Estimate the integral
b
a
dist(x,Sopt)f (x)dx.
4. Let us modify the problem. Suppose that the merchant is not able to build all his stores at
once, and proceeds successively so that after each step, the inhabitants would ﬁnd the locations
of existing stores the most comfortable. How should the merchant place the stores? Start with
the functions in 1a) and 1b). Compare the result withSopt when n grows.
5. Suppose that there are two merchantsM1 and M2. One after another, they successively
build their stores in the street (ﬁrstM1 places a store, thenM2 places a store, then againM1,
etc.). Each merchant would like that, after each turn he plays, his stores be closer to as much
people as possible and at the same time were comfortably located. More precisely, assume it is
the turn ofM1 to build a store (the deﬁnitions are symmetric forM2). Denote byS1⊂[a,b ]
the locations of the stores ofM1 including the potential one, andS2⊂[a,b ] the locations of
the stores ofM2 at the moment. ThenM1 wants to maximise the following integral
∫
E1
(l1(x)−dist(x,S 1))f (x)dx,
where E1⊂[a,b ] is the subset of points which are closer toS1 than toS2, that is
E1 ={x∈[a,b ] |dist(x,S 1)>dist (x,S 2)}.
The setE1 being a union of intervals,l1(x) denotes the length of the interval which containsx.
Describe optimal conﬁgurations of stores.
6. Suppose that an inhabitant always goes to the closest store. Is it true that the ratio of the
numbers of customers of the merchants tends to 1 as the total number of stores grows?
7. Suppose now that an inhabitant at pointx always shops in a store of that merchantMi
for which the sumρ(x,Si) = ∑
y∈Si
1
(x−y)2 is maximal. Each merchantMi in his turn wants to
maximise the integral

Ei (li(x)−dist(x,Mi))f (x)dx, where
Ei ={x∈[a,b ] |ρ(x,Mi)>ρ(x,Mj), i̸=j},
and li(x) is the length of the (maximal) interval fromEi which containsx. Investigate this
situation.
8. Generalise and study the problem in the case where there are more than two merchants.
9. Extend the problem to a circle in the real plane, a ball or a sphere inR3. Construct optimal
conﬁgurations for small values ofn (total number of stores).
10. Construct a continuous time model, in which every merchant gets a proﬁt proportionally
to the number of customers. That proﬁt is then invested in building new stores (the cost of a
store and the time to build it are equal for everybody). Suppose that one merchant started his
business well before all others. Will he be able to monopolise the region?

PROBLEMS FOR THE 7th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
8. A Diophantine Equation
1. Denote byf (n) the number of solutions of the equation
xyz +x +y =n
in positive integersx,y,z . Find all realε> 0 such thatf (n)≪nε. The notationf (n)≪g(n)
means thatf (n)≤g(n) for suﬃciently largen.
2. Let a and b be integers. Denote byf (a,b ) the number of solutions of the equation
xyz +a(x +y) = b
in positive integersx,y,z . Find all realε> 0 such that
f (a,b )≤|ab|ε
whenever|a|or|b|is greater than some constantN (ε). EstimateN (ε).
3. Suggest and investigate other generalisations and directions of research.
9. Framing Matrices
Consider ann-dimensional vector spaceKn over a ﬁeldK. A collectionF of vectors is said
to be in general position if anyn vectors fromF are linearly independent overK. Note that
by deﬁnition ifn> 1 and F contains two copies of a vector, then it is not in general position.
Let A and B be n×n matrices with entries fromK. The pair (A,B ) will be calledframing
if there exists a vectorv∈Kn for which the collection
F =
(
AkBℓ·v
)
, where 0≤k <ord(A) and 0≤ℓ<ord(B) are integers,
is in general position. Theorder of a matrix, denoted byord(C), is the least naturalm such
that Cm is the identity matrix (by conventionord(C) = +∞if no suchm exists). Note that
the collectionF is ﬁnite if and only if both matricesA and B are of ﬁnite order.
1. Let K = C andλ = exp
(2π√−1
n
)
. Consider the following matrices
A =


λ0 0
λ1
...
0 λn−1
(

and B =


0 1 0
...
0 1
1 0 0
(

,
that isA : (x1,x 2,...,xn)↦→(x1,λx2,...,λn−1xn) and B : (x1,x 2,...,xn)↦→(x2,...,xn,x 1).
The collectionF constructed above consists ofn2 vectors.
a) Show that whenn is prime, the pair(A,B ) is framing.
b) Is there anyn for which (A,B ) is not framing?
c) Find alln for which (A,B ) is framing.
2. Consider other pairs of matrices. In particular, investigate the following situations:
a) Both matrices are diagonal.
b) One of the matrices is not invertible.
c) One of the matrices is of inﬁnite order.
3. Find framing pairs of matrices whenK = R.
4. Find framing pairs of matrices whenK is a ﬁnite ﬁeld. Start withK = Fp wherep is prime.

8 JULY 2015, SOFIA (BULGARIA)
10. Polynomial Groups
Let Fp be a ﬁnite ﬁeld wherep is prime. Consider the following set of polynomials overFp
Gn(p) =
{
x +a2x2 +···+anxn |ai∈Fp
}
.
1. Show thatGn(p) is a group under the operation of composition of functions moduloxn+1.
For example, the product of the elementsP =x +x2 and Q =x +x3 in G4(p) is
P◦Q = (x +x3) + (x +x3)2 =x +x2 +x3 + 2x4.
2. Find all pairs(n,p ) for which the groupGn(p) is abelian.
3. Is the groupGn(p) two-generator?
4. Denote byF (n,p ) the number of generating pairs of the groupGn(p). EstimateF (n,p ) by
giving lower and upper bounds.
5. Let (P1,P 2) be an arbitrary pair of elements inGn(p). Consider the following operations:
(A) interchangeP1 and P2, that is(P1,P 2)↦→(P2,P 1);
(B) replacePi byP−1
i , that is(P1,P 2)↦→(P−1
1 ,P 2) or (P1,P−1
2 );
(C) replacePi byPi◦Pj or Pj◦Pi, wherei̸=j, for example(P1,P 2)↦→(P1,P 1◦P2).
Write (P1,P 2)∼(Q1,Q 2)ifthepair (Q1,Q 2)canbeobtainedfromthepair (P1,P 2)byapplying
any ﬁnite sequence of operations (A)–(C). All pairs of elements inGn(p) are thus divided into
equivalence classes, denote byN (n,p ) the number of these classes.
Estimate N (n,p ). Start withn = 2, 3, 4.
6. Describe normal subgroups ofGn(p).
7. Study other properties of groupsGn(p).
E-mail address : oc@itym.org
URL: http://www.itym.org/
