PROBLEMS FOR THE 5th INTERNATIONAL TOURNAMENT OF YOUNG
MATHEMATICIANS
5TH – 12TH JULY 2013, IAŞI (ROMANIA)
Contents
Notation 1
1. Pentominoes 1
2. Steady Triangulations 2
3. A Snooker 3
4. Best Choice Problem 3
5. Congruent Polygons 4
6. An Expensive Dinner 5
7. Map Colourings 5
8. Black Jack 6
9. Prime Quadruplets 7
10. Puzzles 7
11. Dense Iterations 8
Keywords: 1. combinatorics – 2. diﬀerential geometry – 3. dynamical systems – 4. optimal
stopping theory, probability – 5. plane geometry – 6. additive number theory – 7. graph theory,
colouring – 8. games – 9. number theory – 10. combinatorics – 11. analysis, iterations.
Notation
N ={1, 2, 3,...} set of natural numbers (positive integers)
Z, Q, C sets of integer, rational and complex numbers
R, R2 real line and real plane
gcd(x1,...,x n) greatest common divisor ofx1,...,x n
lcm(x1,...,x n) least common multiple ofx1,...,x n
[a,b ], ]a,b [ closed and open intervals inR
f k(x) kth iteration of a functionf at a pointx
C(R) set of continuous functions fromR to R
|XY| length of a segmentXY
1. Pentominoes
A pentomino is a ﬂat ﬁgure composed of ﬁve unit squares, connected along their edges.
Figure 1. The T, P and Z pentominoes.
Date: March 26, 2013.
1

2 5TH – 12TH JULY 2013, IAŞI (ROMANIA)
1. We say that two pentominoes are of the sametype if they are same up to a rotation or up
to a symmetry. Classify the pentominoes. For example, the pentominoes and are of the
same type (they are the same up to a symmetry, but not up to a rotation).
2. Determine whether it is possible to tile the real plane by a given type of pentominoes.
3. Consider the P pentominoes, that is and together with their rotations.
a) For whichn∈N is it possible to tile a5×n rectangle (to cover it without overlap and
without gaps)?
b) Find allm,n∈N for which one can tile anm×n rectangle.
c) In general, given positive integersm andn, what is the maximal number of P pentomi-
noes that can be placed into anm×n rectangle along grid lines and without overlap?
4. The same problem for other types of pentominoes.
2. Steady Triangulations
LetM be a two-dimensional surface, possibly with boundary. Denote by∆(M) a triangula-
tion of the surface, that is a subdivision ofM into triangles with no overlap and no gaps. Those
vertices of the triangulation which do not lie on the boundary ofM are called inner vertices.
An example of a triangulation is given in Figure 2, where the surfaceM is a regular hexagon,
and ∆(M) consists of 19 triangles and has8 inner vertices.
We will say that a triangulation∆(M) is steady if the following two conditions are satisﬁed:
i) for any two trianglesABC and ABD of ∆(M) sharing a common edge, one has
|AC|
|AD|=|BC|
|BD|,
ii) each inner vertex of∆(M) is a vertex of exactly six triangles of∆(M).
B
A
DC
Figure 2. A non-steady triangulation of a regular hexagon.
1. Consider a triangulation of a convex hexagon satisfying only condition ii). How many inner
vertices can it have?
2. Describe all steady triangulations of a regular hexagon.
3. Letn andk be positive integers. Suppose thatM is a regularn-gon, and that there exists a
steady triangulation ∆(M) with exactlyk inner vertices. Is it true that all triangles of∆(M)
must be regular? Start withn = 3, 4, 5 and smallk.
4. Let M be a sphere. Deﬁne straight lines, length of a segment and angles between two lines
on the sphere. Investigate properties of steady triangulations ofM.
5. Let M be the real planeR2. Must all triangles of a steady triangulation∆(M) be regular?

PROBLEMS FOR THE 5th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 3
6. Consider other surfaces.
3. A Snooker
Two balls coloured white and red are laid on a billiard table with no pockets. Ronnie wants
to hit the red ball by the white one. However, Mark is going to put a ﬁnite number of black
balls on the table, and his goal is to prevent Ronnie from hitting the red ball without previously
touching a black one. Can Mark succeed? If yes, how many black balls will he need?
We suppose that the balls are inﬁnitesimal (like points), the motion is a straight line and
with constant speed, the reﬂections from the boundary are specular, and the white ball is not
allowed to hit a corner. Finally, Mark may also put black balls on the boundary of the table.
Consider the cases that the billiard table has the following form:
1. A square.
2. A right-angled triangle.
3. An L-billiard table (see Figure 3).
4. A regularn-gon, wheren∈N.
5. A polyomino: a collection of unit squares connected along their edges (as in Figure 3).
Figure 3. An L-billiard table and a billiard table in the form of a polyomino.
6. A convex polygon whose angles are rational multiples ofπ.
7. A convex polygon whose angles are irrational multiples ofπ.
8. Give examples of non-convex polygonal tables such that the answer (yes or no) depends on
the initial position of the red and the white balls, and both answers occur.
4. Best Choice Problem
Fix an integern≥1. Alice and Bob play the following game.
A closed opaque box containsn balls. On these balls are writtenn distinct rational numbers,
with exactly one number written on each ball. Alice’s goal is to ﬁnd the ball with the greatest
number. Bob takes out one ball from the box in a uniformly random manner (this means that
the probability of choosing a particular ball is1/n) and shows Alice its number. Alice must
either keep this ball, or reject it. If Alice keeps the ball, then the game is ﬁnished. If Alice
rejects the ball, then this ball is removed from the game. Then Bob takes out a new ball
randomly out of the box, and the previous procedure is repeated. Finally, if there is only one
ball left in the box, Alice has to keep it.
At each moment, Alice only knows how many balls remain in the box and the numbers on
the balls already rejected. Alice wins the game if she accepts the ball with the greatest number,
otherwise Bob wins.

4 5TH – 12TH JULY 2013, IAŞI (ROMANIA)
This game is known in the literature as theBest Choice Problem or the Secretary Problem.
1. Find a strategy that allows Alice to win with the maximal probabilityPmax and determine
the value ofPmax. Start withn = 3, 4.
2. Letm≥2 be an integer. A ball with numberq is calledm-good if there exist at most[n/m]
balls whose numbers are greater thanq. Here [x] is the integerk such thatk≤x<k + 1.
Now, Alice and Bob play a similar game, in which the only change is that Alice wins if she
keeps anym-good ball, and loses otherwise.
a) Form = 2, ﬁnd a strategy that allows Alice to win with the maximal probabilityQmax
and determine the value ofQmax.
b) Form> 2, ﬁnd a strategy that allows Alice to win with the maximal probabilityQmax
and determine the value ofQmax.
3. Suggest and study additional directions of research.
5. Congruent Polygons
1. Prove the following statements, or ﬁnd counterexamples:
a) If all 5 sides of a convex pentagon have the same length and 3 diagonals have the same
length, then the pentagon must be regular.
b) If 4 sides of a convex pentagon have the same length and 4 diagonals have the same
length, then the pentagon must be regular.
c) If 3 sides of a convex pentagon have the same length and 5 diagonals have the same
length, then the pentagon must be regular.
d) If all 5 sides of a convex pentagon have the same length and 2 diagonals have the same
length, then the pentagon must be regular.
2. Let n≥3 be a positive integer. Find the set of pairs of positive integerss and d such that
the following statement is always true:
Ifs sides of a convexn-gon have the same length andd diagonals have the same length, then
the polygon must be regular.
3. Let n≥3 be a positive integer. Find the set of pairs of positive integerss and d such that
the following statement is always true:
Let A = A1...An be a convex polygon, and letB = B1...Bn be a regular polygon. Ifs
sides in A have the same length as corresponding sides inB and d diagonals in A have the
same length as corresponding diagonals inB (we say thatAiAj correspondstoBiBj), then the
polygons are congruent.
4. Prove the following statements, or ﬁnd counterexamples:
a) Ifthe5sidesand3diagonalsinaconvexpentagonhavethesamelengthascorresponding
sides and diagonals in another convex pentagon, then the pentagons must be congruent.
b) If 4 sides and 4 diagonals in a convex pentagon have the same length as corresponding
sides and diagonals in another convex pentagon, then the pentagons must be congruent.
5. Fix a natural numbern≥3. Find all pairs of positive integers s and d such that the
following is always true:
LetA =A1...An andB =B1...Bn be two convex polygons. Ifs sides andd diagonals inA
have the same length as corresponding sides and diagonals inB (we say thatAiAj corresponds
to BiBj), then the polygons are congruent.

PROBLEMS FOR THE 5th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 5
6. An Expensive Dinner
There aren friends, numbered 1 throughn. They are all going to a restaurant for dinner
tonight. They are all very good at math, but they are all very strange: theath friend will be
unhappy unless the total cost of the meal is a positive integer, and is divisible bya.
The friends enter the restaurant one at a time. As soon as someone enters the restaurant, if
that person is unhappy then the group will call a waiter immediately.
As long as there is at least one unhappy person in the restaurant, one of those unhappy
people will buy the lowest-cost item that will make him or her happy. This will continue until
nobody in the restaurant is unhappy, and then the waiter will leave. Fortunately, the restaurant
sells enough food at every integer price.
The friends could choose to enter the restaurant in any order. After the waiter has been
called, if there is more than one unhappy person in the restaurant, any one of those unhappy
people could choose to buy something ﬁrst. The way in which all of those choices are made
could have an eﬀect on how many times the group calls a waiter.
For example, ifn = 3 and the friends arrive in the order[1, 2, 3], then a waiter will be called
three times. (#1 arrives, is unhappy, calls a waiter and buys something costing 1 euro. #2
arrives next, is unhappy, calls a waiter and buys something costing 1 euro. Now nobody is
unhappy. #3 arrives next, is unhappy, calls a waiter and buys something costing 1 euro. Now
#2 is unhappy and buys something costing 1 euro. Now #3 is unhappy and buys something
costing 2 euro, for a total of 6 euros. Finally nobody is unhappy, and a waiter was called three
times.) However, if the friends arrive in the order[3, 1, 2], then a waiter will be called 2 times.
1. Denote byWmax the maximal number of times the friends might call a waiter. FindWmax
or estimate it.
2. Denote byWmin the minimal number of times the friends might call a waiter. FindWmin
or estimate it.
3. Suppose now that only friends with numbersa1,...,a k will come to the restaurant. Find
or estimateWmax and Wmin in this case. Herea1,...,a k are distinct positive integers.
4. Denote byW the number of times the friends will call a waiter. Determine the set of all
possible values ofW. Consider the following cases:
a) The friends are numbered1 through n.
b) The friends have numbersa1,...,a k (distinct positive integers).
5. Denote byU the total number of times the friends were unhappy. Determine the set of all
possible values ofU in the cases a) and b) above.
6. Suggest and investigate additional directions of research.
7. Map Colourings
A map is a separation of the real plane into a ﬁnite number of regions whose boundaries
are broken lines. Two such regions are said to beadjacent if their boundaries share a common
segment which is not reduced to a point. Acolouring of a map is the act of assigning a colour
to each of its regions (adjacent regions may have the same colour).
Let n≥2 be a positive integer, and letC be a map. Deﬁne ann-cycle of C as a sequence
R1,...,R n of distinct regions such thatRi andRi+1 are adjacent for each1≤i≤n−1, as well
as Rn and R1. A colouring of the mapC will be calledn-admissible if it has no monochrome
n-cycle, that is, if in anyn-cycle there are at least two regions of diﬀerent colours.
Denote byK(n) the least positive integer such that any mapC has ann-admissible colouring
with at mostK(n) colours. For example, due to a theorem of Kenneth Appel, Wolfgang Haken

6 5TH – 12TH JULY 2013, IAŞI (ROMANIA)
Figure 4. A colouring of a map.
and John A. Koch, any map can be coloured using at most four colours so that no two adjacent
regions have the same colour, which implies thatK(2)≤4.
1. Find the exact value ofK(3), or give lower and upper bounds.
2. The same problem forK(n) with n≥4.
3. Find relations between the numbersK(n). For instance, is it true thatK(n + 1)≤K(n)
for anyn≥2?
4. Does there exist an integern≥2 such thatK(n) = 2?
5. Find the least numberK∞such that, for any mapC, there exists a colouring ofC using at
most K∞colours which isn-admissible for alln≥3 simultaneously.
8. Black Jack
1. Ten cards with numbers from 1 to 10 are laid face-up on the table. Jane picks a card. Then
Joe chooses several cards one after another until his total of chosen cards exceeds (is strictly
greater than) the card chosen by Jane. Then Jane chooses until her cumulative total exceeds
that of Joe, and so on. The ﬁrst player to get
a) 21 exactly,
b) 21 or more
wins. Which of the players has a winning strategy?
♠1 ♦2 |3 ♥4 ♠5 ♦6 |7 ♥8 ♠9 ♦10
2. Let n and K be positive integers such thatn < K. Consider the same game with cards
numbered 1 through n. The winner is the ﬁrst player to get a)K exactly, b)K or more.
3. In general, suppose that there aren cards with integer numbersa1 < a2 < ... < an, and
let K be a natural number. Jane and Joe play the same game trying to get a pile with the
sum a)K exactly, b)K or more. Determine the set of increasing sequences(ai)1≤i≤n for which
Joe has a winning strategy. Consider also the case that the numbers on some of the cards are
negative.
4. Investigate the game for non-decreasing sequencesa1≤a2≤...≤an, when there are cards
with equal numbers. For example, take a standard deck of 52 cards with the following rank:
Ace=1 2 3 4 5 6 7 8 9 10 Jack=11 Queen=12 King=13.
5. Suggest and investigate related questions.

PROBLEMS FOR THE 5th INTERNATIONAL TOURNAMENT OF YOUNG MATHEMATICIANS 7
9. Prime Quadruplets
Two positive integersp and q are called prime twins if they are both prime andq = p + 2.
For example,(3, 5), (5, 7), (11, 13), (17, 19) are pairs of prime twins. If(p1,q 1) and (p2,q 2) are
two pairs of prime twins, then we will say that(p1,q 1,p 2,q 2) is a prime quadruplet.
1. Find all naturaln for which there exist prime twinsp and q such that the following two
numbers are also prime:
a) 2n +p and 2n +q;
b) 22n + 2013·2n + 2014 +p and 22n + 2013·2n + 2014 +q;
c) 9n + 7n + 5n + 3n +p and 9n + 7n + 5n + 3n +q.
2. Leta> 1 be a positive integer. Are there only ﬁnitely many naturaln for which there exists
a prime quadruplet(p,q, an +p, an +q)?
3. Let a > 1 be a positive integer, and letP (x) be a non-constant polynomial with integer
coeﬃcients. Are there ﬁnitely manyn∈N such that the quadruplet(p,q, P(an)+p, P(an)+q)
is prime for some prime twinsp and q?
4. Let a1,...,a k be positive integers greater than1. Estimate the number of naturaln for
which there exist prime twinsp and q such that
an
1 +···+an
k +p and an
1 +···+an
k +q
are also prime twins.
10. Puzzles
1. A student took a sheet of paper in the form of ann×n square grid and cut it intok pieces
along grid lines. It turned out that there is only one way to assemble then×n square back
(the uniqueness is up to a rotation around the center of the square). The pieces are allowed to
be rotated, but cannot be turned over.
Find the maximal value ofk or give an upper bound. Determine the set of all possible values
of k. Distinguish the following cases:
a) Some pieces may have the same shape, and interchanging them does not give a new
assemblage.
b) The pieces must be pairwise distinct.
2. The same problem for a sheet of paper in the form of ann×n equilateral triangular grid.
Figure 5. A 4×4 square grid and a4×4 equilateral triangular grid (with puzzles).
3. Study the problem for other planar shapes, other types of grids, etc.
4. Formulate and investigate 3-dimensional analogs.

8 5TH – 12TH JULY 2013, IAŞI (ROMANIA)
11. Dense Iterations
A setM of real numbers is calleddense in R if any non-empty open interval]a,b [ of the real
line contains at least one element ofM. Let f : R→R be a function. We will say thatf is
spreading at a point p∈R if the set of iterations
{f(p),f 2(p),...,f k(p),...}
is dense inR, wheref k(p) =f(f(...f(  
k times
p)...)) denotes thekth iteration off at the pointp.
1. Does there exist a real polynomialP (x) = anxn +···+a1x +a0 of degree n which is
spreading at 0? Start withn = 1, 2, 3.
2. Denote byC(R) the set of all continuous functions fromR to R, and bySp(R) the subset of
those continuous functions which are spreading at a pointp. Study properties of such subsets.
For instance, isSp(R) inﬁnite, uncountable?
3. Is there a continuous function which is spreading at only one point? Describe the intersection
of two subsetsSp(R) and Sq(R) for some pointsp,q∈R.
4. Formulate and investigate an analogous problem for the interval[0, 1] instead of R and the
functions f : [0, 1]→[0, 1].
5. Suggest and study additional directions of research.
E-mail address: organizers.itym@gmail.com
URL: http://www.itym.org/
