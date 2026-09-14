PROBLEMS FOR THE 6th INTERNATIONAL TOURNAMENT OF YOUNG
MATHEMATICIANS
JULY 2014, BREMEN (GERMANY)
Contents
Notation 1
1. Poles of Polygons 2
2. Free Subsets 2
3. A Recursive Sequence 3
4. Binary Matrices 3
5. An Egyptian Game 4
6. Ridges of Functions 4
7. Decimal Representations 5
8. Cycles in a Permutation Group 5
9. An Equation inZn 6
10. Reﬂexive Polynomials 6
11. Points, Lines and Planes 7
Keywords: 1. geometry, polygon – 2. additive number theory – 3. analysis, recursive
sequence – 4. linear algebra, matrix norm – 5. Egyptian fraction, inequality – 6. analysis,
continuous function – 7. Diophantine approximation, algebraic number – 8. permutation
group, cycle – 9. number theory, residue class – 10. polynomial over a ﬁnite ﬁeld, permutation
– 11. combinatorial geometry.
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Z, Q, C sets of integer, rational and complex numbers
R, R2, R3 real line, real plane and 3-dimensional real space
gcd(x1,...,x n) greatest common divisor ofx1,...,x n
Zn ={0, 1,...,n−1}ring of residue classes modulon
Z∗
n group of invertible elements ofZn
Fq ﬁnite ﬁeld of sizeq =pk
Fq[X1,...,X n] polynomial ring in symbolsX1,...,X n over Fq
Sn symmetric group of degreen
GL(n, R) group of invertiblen×n matrices over R
M×N direct product of two sets or two groupsM and N
M n set ofn-tuples of elements of a setM
G ⋊H, Gwr H semidirect product and wreath product of groupsG and H
|M|or #M cardinality of a setM
|XY| length of a segmentXY
φ(n) Euler’s totient function
log(x) natural logarithm ofx
∥A∥p p-norm of a matrixA
lim sup
n→+∞
xn limit superior of a sequence(xn), lim sup
n→+∞
xn = limn→+∞
(
sup
m≥n
xm
)
Date: April 13, 2014.
1

2 JULY 2014, BREMEN (GERMANY)
1. Poles of Polygons
Let n≥3 and k≥2 be positive integers. LetA =A1A2...An be a convex polygon in the
real plane R2⊆Rk. Denote by Polek(A) the set of pointsP∈Rk for which it is possible to
construct aplane polygon with side lengths|PA 1|,|PA 2|, ..., |PA n|. (Here some lengths can
be zero, the order of sides is arbitrary, non-convex polygons are accepted, sides must not have
inner intersections.) The setPolek(A) will be called thepole of A of dimensionk.
A1
A2 A3
A4
P
|PA 1|
|PA 3||PA 2|
|PA 4|
Figure 1. A pointP belonging to the pole of a trapezoidA1A2A3A4.
1. Show that Pole2(A) = R2 for the following polygons:
a) an isosceles trapezoid, see Figure 1;
b) a regular polygon (n≥4);
c) a polygon with equal angles (n≥4).
2. Describe the poles of dimension2 of convexn-gons. Start with small values ofn.
3. Suppose that the vertices ofA are integer points (i.e. their coordinates are integer). Take
a pointP∈Polek(A) with integer coordinates. Does there exist a polygon with side lengths
|PA 1|,|PA 2|, ..., |PA n|whose vertices are also integer points? First, considerk = 2, 3.
4. Denote by CPolek(A) the subset of pointsP∈Rk for which there exists aplane convex
polygon with side lengths|PA 1|,|PA 2|, ..., |PA n|. It will be called theconvex poleof A of
dimension k. Describe convex poles of dimension2.
5. Givenn and k, is it true thatCPolek(A) = Pole k(A) for any convexn-gon A?
6. Describe the poles and the convex poles of dimension3. Start with small values ofn.
7. Investigate the problem whenk≥4.
2. Free Subsets
Let m, n and k≤m be positive integers. A subsetB⊆{1, 2,...,n}will be called (k,m )-
free if m cannot be presented as a sum of at mostk distinct elements ofB. For example, the
set{1, 2, 3, 4,a≥5}is (3, 10)-free if and only ifa≥11. Denote by f (k,m,n ) the maximum
cardinality of a(k,m )-free subset.
1. Study properties off (k,m,n ) such as monotonicity, divisibility by a given prime, etc.
2. Give lower and upper bounds of the function. Start with small values ofk.
3. Evaluate an asymptotic behaviour.
4. Find an exact formula.
5. Investigate the functiong(k,m,n ) obtained by replacing “at mostk distinct elements” in
the statement of the problem with “exactlyk distinct elements”.

PROBLEMS FOR THE 6th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
3. A Recursive Sequence
Let θbe a real number. Consider the sequence given by the following recurrent relation:
a1 = 1 and an = 1−θ·
n−1∑
k=1
ak
k log(n+1−k) for n≥2.
1. If the limit of the sequence(an) exists, what is it equal to?
2. Show that limn→∞an exists when 0≤θ <1. Consider also the caseθ <0.
3. Investigate the caseθ≥1.
4. Study other recursive sequences by replacing the denominator in the relation above by the
expression kr(log(n+1−k))s, wherer and s are positive real numbers.
4. Binary Matrices
Let n and k≤n be positive integers. Denote by GL(n, R) the group of invertiblen×n
matrices with real entries. A matrixA∈GL(n, R) will be calledk-binary if it has the following
property: in each column, exactlyk entries are equal to1 and all other entries are zeros.
Let p be a positive integer. Thep-norm∥x∥p of a vectorx = (x1,...,x n)∈Rn is
∥x∥p =
( n∑
i=1
|xi|p
)1/p
,
and thep-norm∥A∥p of a matrixA∈GL(n, R) is deﬁned as
∥A∥p = sup
x̸=0
∥Ax∥p
∥x∥p
.
1. Calculate the number ofk-binary matricesA∈GL(n, R). What is the maximum determi-
nant of ak-binary matrix of dimensionn?

)))
1 0 1 1
0 0 1 0
1 1 0 0
0 1 0 1
(
(
Figure 2. A 2-binary matrix of dimension 4.
2. What are the minimum and maximum norms∥A∥p of ak-binary matrix of dimensionn?
3. Find lower and upper bounds on the norm∥A−1∥p of the inverse of ak-binary matrix of
dimension n.
4. Givenk and p, denote byPn(τ) the probability that, for ak-binary matrixA∈GL(n, R),
one has the inequality∥A−1∥p≤nτ.Does there exist a real numberτ> 0 such that
lim sup
n→+∞
Pn(τ)> 0 ?
5. Do there exist real constantsα> 0 and τ> 0 depending onk and p such that
∥A−1∥p≤α·nτ,
for anyn and anyk-binary matrixA∈GL(n, R)? Start withk = 1, 2, 3, 4 and p = 1, 2.

4 JULY 2014, BREMEN (GERMANY)
5. An Egyptian Game
Let n be a positive integer and letE⊆N be an inﬁnite set of positive integers. Alice and
Bob are playing the following game. First, Alice choosesn numbers a1 < a2 < ... < an from
the setE. After that Bob also choosesn numbersb1 <b 2 <...<b n fromE (the same numbers
may be chosen both by Alice and Bob). Bob wins if one of the next conditions is satisﬁed:
1<
n∑
k=1
1
bk
<
n∑
k=1
1
ak
or
n∑
k=1
1
ak
≤1.
Otherwise, it is Alice who wins. Denote byG(E)⊆N the set of those positive integersn for
which Alice has a winning strategy.
1. Find G(E) in the following cases:
a) E ={2k|k∈N∪{0}};
b) E = N;
c) E = 3·N;
d) E ={p|p is prime}.
2. Which subsets ofN can be presented asG(E) for someE.
3. Is there a sequence of inﬁnite sets(Ei)i∈N such thatEi+1 = G(Ei), for alli∈N?
4. Alice and Bob decided to change the conditions: Bob wins if and only if
1>
n∑
k=1
1
bk
>
n∑
k=1
1
ak
or
n∑
k=1
1
ak
≥1.
Show that for alln, Alice has a winning strategy.
5. We say that Alice has alazy winning strategyin the latter game if there exists an inﬁnite
subset L⊆E such that, by choosing then smallest numbers ofL, Alice wins for alln∈N.
Determine whether Alice has a lazy winning strategy, whenE is as in 1a)-d).
6. Suggest and study additional directions of research.
6. Ridges of Functions
Let X be a set andf :X→X be a function. Thepreimagef−1(x) of a pointx∈X is the
set of all pointsy∈X such thatf (y) = x. Theridge of the functionf is the set of cardinalities
of the preimagesf−1(x),
ridge(f ) =
{
#f−1(x) |x∈X
}
.
If the preimage ofx is inﬁnite, then we put#f−1(x) =∞.
1. TakeX = R. We are interested in the ridges of continuous functionsf : R→R.
a) Find all integersn such thatridge(f ) ={n}for a continuous functionf.
b) Canridge(f ) contain only even integers?
c) Describe subsets ofN∪{0,∞}which are ridges of polynomials.
d) Describe subsets ofN∪{0,∞}which are ridges of continuous functions.
2. The same questions whenX = [0, 1].
3. An analogous problem forX = R2.
4. Consider other setsX.

PROBLEMS FOR THE 6th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
7. Decimal Representations
Let α = (an)n∈N be a sequence of positive integers. We denote byD(α) the real number
0,a 1a2...an...with the decimal representation obtained by writing successively all the terms of
the sequence α. For example,D(α) = 0, 1234567891011...when α is the sequence of successive
positive integers.
1. Determine whether the numberD(α) is rational or irrational, ifα is
a) the sequence of successive positive integers:1, 2, 3, 4, 5,...;
b) the sequence of successive prime numbers:2, 3, 5, 7, 11,...;
c) the Fibonacci sequence:a1 = 1, a2 = 1 and an =an−1 +an−2 for n> 2.
2. Find suﬃcient and/or necessary conditions onα for the numberD(α) to be rational.
3. In the examples 1a)-c) above, isD(α) algebraic or transcendental?
4. Letf : N→N be a permutation of the set of positive integers,i.e. f is a bijection. Denote
by αf the sequence (f (n))n∈N. Determine permutationsf for which the numberD(αf ) is
a) rational;
b) algebraic;
c) transcendental.
5. Consider other sequencesα, and determine whetherD(α) is algebraic or transcendental.
6. Find suﬃcient and/or necessary conditions onα for the numberD(α) to be algebraic.
8. Cycles in a Permutation Group
Denote bySn the group of permutations of the set{1, 2,...,n}. LetG be a subgroup ofSn.
Introduce the set
C(G) ={s∈G |s is a cycle of lengthn}.
We would like to know whether the following inequality is correct:
|C(G)|
|G|≤φ(n)
n , (1)
where φ(n) is the Euler’s totient function.
1. Show that ifG =⟨s⟩is a cyclic group generated by a cycles of lengthn, then one has the
equality in (1).
2. Check the inequality whenG is a direct productCa×Cb, a semidirect productCa ⋊Cb or
a wreath productCa wr Cb of two cyclic groups of ordersa and b.
3. Describe all permutation subgroups for which the equality holds.
4. Check the inequality for primitive permutation subgroups.
5. Is the inequality correct for any subgroup ofSn?
6. More generally, let2≤k≤n be a positive integer. Consider the following set:
Ck(G) ={s∈G |s is a cycle of lengthk}.
Suggest an upper bound for the density|Ck(G)|/|G|depending onk andn. Adapt and answer
the previous questions. You may start with small values ofk and n.

6 JULY 2014, BREMEN (GERMANY)
9. An Equation inZn
Consider the ring Zn of residues modulo a positive integern. Denote by Z∗
n the subset of
invertible elements, one hasZ∗
n ={x∈Zn |gcd(x,n ) = 1}.
Let p be an odd prime number. We want to study the equation
x +x−1 +y +y−1 =t,
where x,y∈Z∗
p and t∈Zp. Denote byNp(t) the number of its solutions(x,y ) for a givent.
1. Let A ={x +x−1|x∈Z∗
p}. What are the cardinalities ofA and the sets
A +A ={a +b|a,b∈A}and A·A ={a·b|a,b∈A}?
2. Find Np(0). For small values ofp, give an explicit formula ofNp(t) depending ont.
3. Describe mapsf :t↦→at+b
ct+d under whichNp is invariant, that is,Np(t) = Np(f (t)):
a) Find alla∈Z∗
p and b∈Zp such thatNp(t) = Np(at +b) for anyt∈Zp.
b) Determineb∈Z∗
p such thatNp(t) = Np(bt−1) for anyt∈Z∗
p.
c) Consider other mapsf.
4. Study an analogous problem for the ringZpk where p is a prime andk∈N.
5. Generalize results toZn for any integern.
10. Reﬂexive Polynomials
Let n and k be positive integers,p be a prime number andq = pk. Denote by Fq a ﬁnite
ﬁeld of sizeq, and let R = Fq[X1,...,X n] be the ring of polynomials in symbolsX1,...,X n
over the ﬁeldFq.
1. Is it true that for any permutationσ : Fn
q →Fn
q of the set Fn
q , there exists ann-tuple of
polynomials (P1,...,P n)∈Rn such that
(P1(x1,...,x n),...,P n(x1,...,x n)) = σ(x1,...,x n), for allx1,...,x n∈Fq ? (2)
Start withn = 1, 2 and k = 1, 2.
An element P = ( P1,...,P n) ∈Rn is called a reﬂexive mapif there exists an element
Q = (Q1,...,Q n)∈Rn such that the compositionP◦Q is the identity map(X1,...,X n),
that is,
(P1(Q1,...,Q n),...,P n(Q1,...,Q n)) = (X1,...,X n).
For instanceP = (X +Y 2,Y )∈(Fq[X,Y ])2 is a reﬂexive map, its inverse isQ = (X−Y 2,Y ).
2. Suppose thatp is odd. Find all permutationsσ of the setFn
q which are induced by a reﬂexive
map P = (P1,...,P n)∈Rn, i.e. one has the equality (2). Start withn = 1, 2 and k = 1, 2.
Note that for example the element(X q,Y )∈(Fq[X,Y ])2 is not a reﬂexive map, even though
it induces a bijection ofF2
q.
3. The same problem whenp = 2. In particular, does there exist anodd permutation of Fn
q
that is induced by a reﬂexive map?

PROBLEMS FOR THE 6th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
11. Points, Lines and Planes
Let N points be given in the spaceR3, not all on the same plane and also not all lying on
two lines. Denote byL the number of lines passing through at least two of these points, and
let P be the number of planes containing at least three of the points.
1. For smallN, what values can the expressionN−L +P take?
2. Is it true thatN−L +P≥0 for suﬃciently largeN?
3. Suppose that no three points are collinear. Is it true thatN−L +P≥2 for any suﬃciently
large N? When does the equality hold?
N = 4
L = 6
P = 4
Figure 3. A conﬁguration of points withN−L +P = 2.
4. Determine the set of possible values of the expressionN−L +P for a givenN. Distinguish
the general situation and the case that no three points are collinear.
E-mail address : organizers.itym@gmail.com
URL: http://www.itym.org/
