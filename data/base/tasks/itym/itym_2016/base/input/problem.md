PROBLEMS FOR THE 8th INTERNATIONAL TOURNAMENT OF YOUNG
MATHEMATICIANS
JULY 2016, SAINT PETERSBURG (RUSSIA)
Contents
Notation 1
1. Rankings of Teams 1
2. Cutting Segments 2
3. Loose Number Sets 3
4. Suprema of Integer Polynomials 4
5. Composite Polygons 4
6. Diﬀerent Means 5
7. A Colouring Game 6
8. Functional Equations 7
9. Mathematics of Electric Circuits 8
10. Rich Sequences 9
Keywords: 1. combinatorics, probability, series – 2. geometry, intersection – 3. additive
number theory – 4. integer polynomial, approximation – 5. combinatorial geometry, partition
– 6. mean, limit – 7. game, strategy – 8. analysis, functional equation – 9. linear algebra,
circuit, Cayley graph – 10. sequence, Hankel matrix
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
f(x) supremum of a set{f(x) |x∈M}
1. Rankings of Teams
A mathematics tournament is being held in Saint Petersburg withn∈N participating teams
T1, ..., Tn. In the end of the tournament, each team will be ranked according to its rating
(teams can have the same rating). The teams with the highest rating will have rank1, the
teams with the second highest rating will have rank2, and so on. Denote byRn the set of all
possible rankings. In other words,
Rn =
{
(r1,...,r n)∈Nn
⏐⏐⏐⏐for any integer1≤t≤max
k
(rk), there existsi such thatri =t
}
,
Date: March 22, 2016.
1

2 JULY 2016, SAINT PETERSBURG (RUSSIA)
where ri is the rank of the teamTi.
1. Letan be the number of elements inRn and puta0 = 1. Find a recurrent formula foran in
terms ofa0,a 1,...,an−1.
2. Letσ = (s1,...,s n) be a permutation of{1,...,n}. Find the cardinality of the subset
P(σ) :={(r1,...,r n)∈Rn |for any 1≤i<j ≤n, one hasri <r j if and only ifsi <s j}.
3. Show that for every real numberx with|x|suﬃciently small, one has
∞∑
n=0
an
n!xn = 1
2−ex.
4. Denote byMn the sum of all possible last ranks, that is
Mn =
∑
(r1,...,rn)∈Rn
max(r1,...,r n)
and letM0 = 0. Compute the series
∞∑
n=0
Mn
n! xn.
5. Letρn = (X1,...,X n) be a random element ofRn chosen uniformly. Study the behaviour of
E [max(ρn)], that is the expected value of the rank of a team with the lowest rating, asn→∞.
6. Study the behaviour of E [X1], that is the expected value of the rank of the teamT1, as
n→∞.
7. Denote byft(ρn) the number of teams with rankt: ft(ρn) = #{1≤i≤n |Xi =t}.
a) Letk be a positive integer. Findlimn→∞P [f1(ρn) =k], that is the limit of the probability
that exactlyk teams have rank1.
b) How doesE [f1(ρn)] behave asn→∞(the expected number of teams ranked ﬁrst)?
c) How doesP [X1 = 1] behave asn→∞(the probability that the teamT1 is ﬁrst)?
8. Same questions fort = 2, 3, etc.
9. Denote by(X′
1,...,X′
n) the coordinates ofρn ordered in non-increasing order. Lets∈]0, 1[
be a ﬁxed real number. Study the behaviour of the random variableX′
⌊sn⌋as n→∞, where
⌊y⌋denotes the integer part of a real numbery.
10. Study other properties ofρn. Suggest and investigate additional directions of research.
2. Cutting Segments
Let A and B be two bounded domains in the real plane. We suppose that eitherB⊆A or
B∩A = ∅. For positive integersm andn, letA1, ..., Am andB1, ..., Bn be some points on
the boundaries of A and B respectively. We say that a segmentAiBj is cutting if it contains
an inner point of the domainB (in other words, it is dividingB into parts, at least two of
which have nonzero area). Denote byCutB(A1...Am,B 1...Bn) the set of cutting segments.
We would like to ﬁnd all possible values of the cardinality of this set, and in particular its
minimum and maximum, in the following cases:
(i) the points(Ai) and (Bj) are ﬁxed on the respective boundaries, and the domainB can
ﬂoat (move and rotate) strictly inside the domainA;
(ii) the points(Ai) and (Bj) are ﬁxed on the respective boundaries, and the domainB can
ﬂoat (move and rotate) strictly outside the domainA;
(iii) the domains A and B are ﬁxed as well as the points(Ai) on the boundary ofA, and
the points (Bj) can ﬂoat on the boundary ofB.

PROBLEMS FOR THE 8th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
1. Let A =A1...Am be a regularm-gon and B =B1...Bn be a regularn-gon.
a) What area may the polygonB have so that it could be placed strictly insideA?
b) Suppose B lies strictly inside A. What minimum and maximum number of cutting
segments can there be (cf. Figure 1)?
c) Determine CutB(A1...Am,B 1...Bn) in the case (i), depending on the size and the
position of B within A.
d) Consider the case (ii).
e) Consider the case (iii).
A1
A2
A3
B1
B2
B3
A1
A2
A3
B1
B2
B3
Figure 1. Two examples where A and B are triangles in the case (i), and
|CutB(A1A2A3,B 1B2B3)|is equal to 0 and 3.
2. Study the problem for other convex polygons.
3. Study the problem for non-convex polygons. Start withA convex and B non-convex.
4. Study the problem whenA and B are circles. Start with the case (i) and suppose that the
points divide the respective circumferences into arcs of equal length (equidistribution).
5. Study the problem whenA and B are ellipses.
6. Generalise to higher dimensionsN≥3. In particular, study the problem whenA and B are
a) N-dimensional simplexes;
b) N-dimensional balls.
7. Suggest and investigate other directions of research.
3. Loose Number Sets
We say that a set of integers isloose, if it does not contain four diﬀerent numbersa < b <
c < dsuch thata +d = b +c. Denote by P (n) the maximal number of elements in a loose
subset of the set{1, 2,...,n}. We are interested in calculatingP (n) for largen or ﬁnding lower
and upper bounds.
1. Compute P (n) for smalln up to 10.
2. Prove that limn→∞
P (n)
n = 0.
3. Try to ﬁnd best possible upper and lower bounds forP (100) and P (2016).
4. Is it true that limn→∞
P (n)
nε = 0 for
a) ε = 1/2,

4 JULY 2016, SAINT PETERSBURG (RUSSIA)
b) ε = 1/3,
c) anyε> 0?
5. We call a sequencevery loose if it contains neither four diﬀerent numbersa < b < c < d
such thata +d = b +c, nor triplesa < b < csuch thata +c = 2b. Denote by Q(n) the
maximal number of elements in a very loose subset of the set{1, 2,...,n}. How the answers
to the above questions change forQ(n)?
6. Suggest and investigate generalisations.
Note. If you use computer programs, then please provide the full source codes and all necessary
instructions so that other participants and the jury members are able to reproduce your results.
4. Suprema of Integer Polynomials
Let D(a,r ) :={z∈C | |z−a|≤r}be the closed disk of radiusr∈R+ centred ata∈C
in the complex plane. Denote byc =c(a,r ) the largest real number such that for any nonzero
polynomial P∈Z[z] with integer coeﬃcients, one has
sup
z∈D(a,r)
|P (z)|≥cn,
where n is the degree ofP.
1. Find c( 1
2, 1
2) or give lower and upper bounds.
2. Find c(a,r ) or give lower and upper bounds, whena∈Q.
3. Estimatec(a,r ) whena is a quadratic number, that isua2 +va +w = 0 for someu,v,w ∈Z
and u̸= 0.
4. Study the general case.
5. Suggest and study additional directions of research.
5. Composite Polygons
Let ℓbe a line in the real plane. We will say that a polygonP is divisible by ℓif there exist
two ﬁnite families of linesF1 and F2 in the plane such that
– the lines inF1 are parallel toℓ,
– the lines inF2 are orthogonal toℓ,
– the polygonP is divided byF1 and F2 into parts – each part is either a rectangular
triangle or a rectangle.
We will also say thatP is divisible by a segment s if it is divisible by the line containings.
Finally, a polygon will be calledcomposite if it is divisible by at least one line.
1. Given a triangle, describe all lines by which it is divisible.
2. Given a convex quadrilateral, describe all lines by which it is divisible.
3. Give a criterion for a non-convex quadrilateral to be composite.
4. A polygon isobtuse if all its angles are greater thanπ/2. Does there exist an obtuse convex
pentagon which is
a) not divisible by at least one of its sides?
b) not divisible by all its sides?
c) not composite?

PROBLEMS FOR THE 8th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
A
B
C
D
Figure 2. A convex quadrilateralABCD divisible by its sideAD.
5. In how many parts can a composite obtuse convex pentagon be divided by a lineℓ, if
a) ℓcontains a side?
b) ℓis neither parallel nor orthogonal to any of the sides?
6. Study the divisibility of non-convex and non-obtuse pentagons.
7. Consider other polygons. Describe compositen-gons whenn> 5.
8. Suggest and study additional directions of research. One could also try to extend the notion
of divisibility toα-divisibility whereα is the angle between familiesF1 and F2.
6. Diﬀerent Means
Let M and N be two real-valued functions deﬁned in the domainR+×R+. Given any
positive real numbersa and b, one can construct two sequences(an) and (bn) satisfying the
following recurrence relations
an =M(an−1,b n−1) and bn =N(an−1,b n−1),
where a0 = a, b0 = b and n∈N. If the limits limn→∞an and limn→∞bn exist and coincide for all
a,b∈R+, then the function
M⊗N(a,b ) := limn→∞an = limn→∞bn
is well-deﬁned inR+×R+. We will call it themean-product of M and N.
1. Consider two classical functions – the arithmetic meanA(a,b ) = a+b
2 and the harmonic mean
H(a,b ) = 2
1
a + 1
b
. For anya,b∈R+ andn∈N, takean =A(an−1,b n−1) andbn =H(an−1,b n−1)
with a0 =a and b0 =b.
Prove that the sequences(an) and (bn) converge to the same limit. DetermineA⊗H. Is it
a symmetric function, that isA⊗H(a,b ) =A⊗H(b,a )?
2. Let G(a,b ) =
√
ab be the geometric mean.
a) Show that the functionsA⊗G and H⊗G are well-deﬁned inR+×R+.
b) Prove that
A⊗G(a,b ) =π

2
∞∫
0
1∑
(x2 +a2)(x2 +b2)
dx
(
(
−1
.
c) Find a formula forH⊗G.
3. Consider a Hoelder mean
Hp(a,b ) =
p
∫
ap +bp
2 ,

6 JULY 2016, SAINT PETERSBURG (RUSSIA)
where p ̸= 0 is an arbitrary real number. Investigate the following functions (if they are
well-deﬁned, then ﬁnd a formula or a Taylor expansion):
a) Hp⊗G;
b) Hp⊗Hq, for any real nonzerop and q;
c) Hp[λ]⊗Hq[µ], where 0<λ,µ<2 and Hp[t](a,b ) =
p
∑
t·ap+(2−t)·bp
2 .
4. One can instead construct the sequences(an) and (bn) as follows:
an =M(an−1,b n−1) and bn =N(an,b n−1),
where n∈N, a0 = a and b0 = b. If the limits limn→∞an and limn→∞bn exist and coincide for all
positive a and b, then one can deﬁne theArchimedes mean-product of M and N,
M⊗AN(a,b ) := limn→∞an = limn→∞bn.
Investigate the following functions (if well-deﬁned, ﬁnd a formula or a Taylor expansion):
a) Hp⊗AHp;
b) Hp⊗AG;
c) Hp⊗AHq;
d) Hp[λ]⊗AHq[µ], where 0<λ,µ<2.
5. Consider other means: Lehmer means
( ap+bp
ap−1+bp−1
)1
p
, Stolarsky means
(ap−bp
p(a−b)
) 1
p−1
, weighted
versions of means and their convex combinations.
6. Find criteria for a mean-product to be continuous, symmetric, smooth, analytic, homoge-
neous, etc.
7. Try to generalise results to means of more than two variables.
7. A Colouring Game
Alice and Bob play a game on a circle of circumference 1. Initially, the circle is completely
white. In each step, one player picks a real numbert∈[0, 1] and the other chooses an arc of
length t. All white points in the chosen arc become black and all black points become white.
The players pick numbers alternately, starting with Alice. The game stops aftern steps, where
n∈N is given in advance. In the end, Alice’s gain, denoted byGA, is the proportion of points
which are white. Bob’s gain, denoted byGB, is the proportion of points which are black.
Figure 3. An example withn = 3. Alice pickst = 1/6 and Bob chooses an arc
on the right. Then he pickst = 1/2 and Alice chooses an arc on the top. Finally
Alice pickst = 1 and Bob chooses the entire circle. HereGA =GB = 1
2.
1. Depending onn, does there exist a strategy allowing Alice to ensure a gain at least1
2? And
what about Bob?
2. What maximal gain can Alice ensure? Start withn = 2, 3, 4.
In the next two questions, the game is on the segment[0, 1] which is initially white. In each
step, a player picks a real0≤t≤1 and the other player chooses a subinterval of lengtht

PROBLEMS FOR THE 8th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
within [0, 1]. The white points in the subinterval become black and vice-versa. The gains are
deﬁned in a similar manner.
0 1 0 1 0 1 0 1
Figure 4. An example withn = 3. Alice picks t = 1/3 and Bob chooses a
subinterval on the left. Then he pickst = 1/2 and Alice chooses a subinterval on
the right. Finally, Alice choosest = 1 and Bob chooses the entire segment[0, 1].
As a resultGA =GB = 1
2.
3. What is the maximal gain that Alice can ensure (as a function ofn)?
4. Find the maximal gains that Alice and Bob can ensure if they are only allowed to pick real
numberst which are
a) of the form1
k with k∈N;
b) not greater than1
2.
5. Now, the game is on the segment[0, 1] with 3 colours: white, blue and red. All white points
in a chosen subinterval become blue, all blue points become red and all red points become
white. Bob’s gain is the proportion of white and blue points, Alice’s gain is the proportion of
red points. Find the maximal gain that Alice can ensure aftern steps.
6. Suggest and study additional directions of research.
8. Functional Equations
Let ]a,b [ be a non-empty open interval of the real line witha,b∈R∪{−∞, +∞}. We would
like to investigate equations of the form
f(f(x)) =g(x),
where f and g are two real-valued functions deﬁned on the interval]a,b [.
1. Given thatg(x) =ex, does the equation have a solutionf which is
a) continuous?
b) diﬀerentiable (twice diﬀerentiable, etc.)?
c) analytic?
d) presentable as a power series convergent in]a,b [?
Start with the case]a,b [= R.
2. Analoguous questions when
a) g(x) =x2 +px +q with p,q∈R;
b) g(x) is a polynomial of degreen> 2.
3. Solve the equationf(f(x)) =f′(x) for a continuously diﬀerentiable functionf : ]a,b [→R.
4. Investigate the equationsf(f(x)) =
 b
af(t)dt and f(f(x)) =
 x
a f(t)dt, wheref : [a,b ]→R
is a) continuous; b) Riemann integrable; c) Lebesgue integrable.
5. Let M be a bounded closed interval [a,b ] or the entire R. We say that a continuous
function g : M →R is a k-square if there exists a continuous functionf : M →R such
that g(x) = f(f(x)) for allx∈M. Determine the density ofk-squares in the setC(M) of
continuous functions onM for diﬀerent topologies.
6. Suggest and study other directions of research.

8 JULY 2016, SAINT PETERSBURG (RUSSIA)
9. Mathematics of Electric Circuits
An electric circuit can be viewed as an undirected weighted graph without loops and with
multiple edges, where the weight of each edge is the resistance of the corresponding circuit
element. Given such graphΓ, we are interested in measuring the resistanceRij between any
pair of verticesvi and vj of the graph. A well-known method consists in connecting a unit
current source between the vertices, and applying Kirchhoﬀ’s circuit laws and Ohm’s law in
order to ﬁnd the potentials at all vertices (see Figure 5). The resistanceRij will then be the
diﬀerence of potentials atvi and vj.
v1 v2
v3v4
r12
r14
r23
r34
r24
1
Figure 5. Connecting a unit current source between the verticesv1 and v3.
1. Let rij be the resistance (weight) of the edge connecting verticesvi,v j ∈Γ. We denote
rij =∞(or rather 1/rij = 0) if there is no edge between these two vertices. Using Kirchhoﬀ’s
laws deﬁne a system of linear equations that allows to compute the resistanceRij between any
two verticesvi,v j in terms of the weightsrij.
2. Assumethatthegraphisbuiltfromtheedgesofapolyhedroninan N-dimensionalEuclidean
space and the resistance of any edge is exactly 1 ohm. Compute the resistance between opposite
vertices for the following polyhedrons:
a) a regular polygon in the real plane;
b) a cube in the 3-dimensional Euclidean space;
c) an octahedron in the 3-dimensional Euclidean space;
d) an icosahedron in the 3-dimensional Euclidean space;
e) a cube in theN-dimensional Euclidean space.
3. Assume that you can vary the resistance of each edge in a given interval[a,b ]. What are
the maximal and minimal resistances that you can get between two opposite vertices for the
above graphs?
4. Let Sn be the symmetric group of degreen, and letT ⊂Sn be the set of transpositions
(1 2), (2 3), ..., (n−1n). The Cayley graph associated with(Sn,T ) is deﬁned as the undirected
graph havingn! vertices corresponding to the permutations inSn and such that there is an
edge between verticesσ,τ∈Sn if and only ifτσ−1∈T.
Assuming that each edge of this graph has resistance 1 ohm, compute the resistance between
the following two “opposite” permutations:
(
1 2 3 ···n−1 n
1 2 3 ···n−1 n
)
and
(
1 2 3 ···n−1 n
n n−1 n−2 ···2 1
)
.
5. Consider other groupsG and their generators.
6. Suggest and study additional questions.

PROBLEMS FOR THE 8th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 9
10. Rich Sequences
Let (ai) be a sequence over a setS, that is the terms of the sequence are elements ofS. An
(i,n )-order Hankel matrix of the sequence is the followingn×n matrix:
Hi,n=

))))
ai ai+1 ... ai+n−1
ai+1 ai+2 ... a i+n
... ... ... ...
ai+n−1 ai+n ... ai+2n−2
(
(
.
An inﬁnite sequence(ai)i≥1 is said to berich if, for all positive integersi andn, the determi-
nant|Hi,n|is nonzero. A ﬁnite sequence(ai)1≤i≤N is rich if the determinant|Hi,n|is nonzero
for all positive integersi and n such thati + 2n−2≤N.
1. Let S be a subset ofZ of cardinality 2.
a) Show that there exist no inﬁnite rich sequences overS.
b) What is the maximum length of a rich sequence overS?
c) Describe all rich sequences whenS ={1, 2}.
2. Let S be a subset ofZ of cardinality 3.
a) Construct ﬁnite rich sequences whenS ={1, 2, 3}.
b) Is there an inﬁnite rich sequence overS?
3. Investigate the existence of inﬁnite rich sequences whenS⊂Z is a subset of cardinality
more than 3.
4. Consider the inﬁnite sequence(ai)i≥1 over the set{1, 2, 3, 4}such that the inﬁnite word
a1a2a3...is invariant under the transformation1↦→12, 2↦→23, 3↦→14, 4↦→32. The ﬁrst
sixteen terms of the sequence are 1, 2, 2, 3, 2, 3, 1, 4, 2, 3, 1, 4, 1, 2, 3, 2. Is the sequence
(ai)i≥1 rich?
5. Investigate the existence of inﬁnite rich sequences and construct ﬁnite rich sequences, when
S is a subset of a ringZm of residues modulom.
6. Investigate the existence of inﬁnite rich sequences and construct ﬁnite rich sequences, when
S is a subset of a ﬁnite ﬁeldFq of sizeq =pk, wherep is prime.
7. Suggest and study additional questions.
E-mail address : oc@itym.org
URL: http://www.itym.org/
