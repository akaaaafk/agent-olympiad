[IIOT logo] International Informatics Olympiads in Teams [book indicator: 5 orange, 0 grey] Bologna, May 19th, 2022 icecream • EN Best Ice Cream Flavours ( icecream) Filippo loves ice cream, so when he found out that a new ice cream shop had opened in Bologna, he had to go and taste their ice cream! Figure 1: Choosing the right flavour is always difficult. The shop sellsN flavours of ice cream, each flavour is represented by a stringFi. The ice cream shop offers a special promotion, each customer can choose a non-empty strings and he will receive a cup containing all flavours starting with s, for example if the flavours are “chocolate”, “coffee” and “cookies”, by choosing the string “co” you would receive the flavours “coffee” and “cookies” but not the “chocolate” flavour. Filippo wants to buy exactlyk flavours using the fewest number of cups, however Filippo can’t decide which flavours to choose so, to avoid blocking the queue, he decided to buy exactly the firstk flavours (i.e. flavours F0, F1, . . . , Fk−1). Help Filippo find the minimum number of cups needed to buy exactly the firstk flavours, for each k = 1, . . . , N. ☞ Among the attachments of this task you may find a template fileicecream.* with a sample incomplete implementation. Input The first line contains the only integerN. The next N lines contain a string representing a flavour. Output You need to writeN lines with an integer each: the minimum number of cups needed to order all flavours from 0 to k− 1 but none of the flavours fromk to N− 1, for eachk = 1, . . . , N. icecream Page 7 of 20

Constraints • 2≤ N≤ 100 000. • Each flavour is formed by lowercase English characters (‘a’ to ‘z’). • The total length of all flavours is at most2 000 000. • All flavours are different. • It’s guaranteed that it is always possible to buy the firstk flavours for eachk = 1, . . . , N. • The same flavour is allowed to appear in more than one cup (while still counting as a single flavour). Scoring Your program will be tested against several test cases grouped in subtasks. In order to obtain the score of a subtask, your program needs to correctly solve all of its test cases. – Subtask 1(0 points) [book indicator: 1 orange, 4 grey] Examples. – Subtask 2(22 points) [book indicator: 2 orange, 3 grey] N≤ 10, the total length of all flavours is at most100. – Subtask 3(24 points) [book indicator: 2 orange, 3 grey] N≤ 500, the total length of all flavours is at most10 000. – Subtask 4(23 points) [book indicator: 2 orange, 3 grey] The flavours are sorted in lexicographical order. – Subtask 5(31 points) [book indicator: 5 orange, 0 grey] No additional limitations. 

Examples

Sample 1 input:
```text
5
chocolate
coffee
cookies
pistachio
strawberry
```

Sample 1 output:
```text
1
2
1
2
3
```

Sample 2 input:
```text
10
orange
peanutbutter
mango
mint
cheesecacke
coconut
oreo
cherry
peppermint
watermelon
```

Sample 2 output:
```text
1
2
3
3
4
5
5
4
4
5
```

Explanation In thefirst sample case: • k = 1: Filippo can buy one cup withs1 =“choco”. [Cup choco: chocolate.] • k = 2: Filippo can buy two cups withs1 =“choco” and s2 =“coffee”. [Cup choco: chocolate. Cup coffee: coffee.] • k = 3: Filippo can buy one cup withs1 =“c”. [Cup c: cookies, coffee, chocolate.] • k = 4: Filippo can buy two cups withs1 =“c” and s2 =“pi”. [Cup c: cookies, coffee, chocolate. Cup pi: pistachio.] • k = 5: Filippo can buy three cups withs1 =“c”, s2 =“pi” and s3 =“straw”. [Cup c: cookies, coffee, chocolate. Cup pi: pistachio. Cup straw: strawberry.] icecream Page 9 of 20

Source note: the flavour string "cheesecacke" is spelled that way in the published second sample; it has not been corrected to a different input.
