# iol_team_2008 — Team Contest — Fanqie

**Agents:** openai/gpt-5.4-mini  
**Judge:** anthropic/claude-sonnet-4-6  
**Format:** answer  

## Score

I'll evaluate each part systematically against the official solution.

---

## (a) How ancient fanqie transcriptions are used in Cantonese

**Official answer:** A's onset + tone height combined with B's rhyme + tone contour. (With the additional aspiration rule for stop consonants when A's tone is low.)

**Team's answer:** Takes onset from first character, rime/tone from second. Mentions "historical sound changes applied" but misses the crucial split: tone HEIGHT from A, tone CONTOUR from B. Completely misses the aspiration rule for stop consonants.

**Score: 3/10**

---

## (b) How fanqie was designed to work originally; which transcription still works

**Official answer:** A's onset + B's rhyme AND tone (simple combination). Only transcription #9 (/_d_12641siu21) works with this old rule.

**Team's answer:** Correctly identifies onset from first, final+tone from second. But **fails to identify the specific transcription** (#9) where the old rule still gives correct results in Cantonese. This was the key specific answer required.

**Score: 4/10**

---

## (c) Characters with voiced initials; aspiration conditions

**Official answer:** Characters in low tone had voiced onsets. Lists specific characters. Voiced stops became aspirated if tone was rising or falling, unaspirated if level.

**Team's answer:** Identifies the pattern (low-tone characters had voiced initials, Wu evidence) but doesn't list specific characters and gets the aspiration rule backwards/vague ("yin unaspirated, yang aspirated" rather than the correct contour-based rule).

**Score: 4/10**

---

## (d) Evolution of three tones to six Cantonese tones

**Official answer:** The three contours (rising, level, falling) split into high and low registers based on voicing of the initial consonant, yielding 6 tones. Entering tone not in this problem.

**Team's answer:** Correctly identifies the yin/yang split mechanism. Mentions all four tones including entering tone (which the problem says is absent). The core explanation is correct.

**Score: 7/10**

---

## (e) Rules for using fanqie in Mandarin

**Official answer:** Onset from A, rhyme from B. Key palatal/retroflex alternation rules: i/y lost after sh/ch; k/kh and s/c became x/q before i/y. Identifies two cases where result is indeterminate.

**Team's answer:** Gets the basic principle right but completely misses the specific phonological rules about palatalization (the x/q vs. k/s alternation) and the indeterminate cases. This was the heart of the answer.

**Score: 3/10**

---

## (f) Tones and voiced consonants in Mandarin; fanqie tone rules

**Official answer:** Provides a specific table: rising→35 if voiced non-sonorant, else 214; level→35; falling→51 if voiceless, 35 if voiced. Voiced stops aspirated if falling, unaspirated if level or rising. Table of fanqie tone combinations.

**Team's answer:** Vague generalities about voicing conditioning tone splits. No specific tone numbers, no table, no precise rules. Substantially incomplete.

**Score: 2/10**

---

## (g) Rare combinations in Mandarin

**Official answer:** Sonorant onset + tone 51; unaspirated stop + tone 35.

**Team's answer:** Gives vague answer about mismatches between aspiration and historical voicing. Doesn't identify the specific rare combinations (sonorant+51, unaspirated+35).

**Score: 2/10**

---

## (h) Missing tones

**Official answer:** thuŋ→21 (Cantonese), coi→51 (Mandarin), mai→53 (Cantonese), mian→35 (Mandarin), siu→53 (Cantonese), lyn→2 (Cantonese).

**Team's answer:** Gets some partially right but misidentifies several. States thuŋ→35 (wrong, should be 21 for Cantonese), mai→214 (partially), mian→35 (correct), siu→5 (wrong format/value), lyn→51 (wrong). Confuses which language each missing tone belongs to.

**Score: 2/10**

---

## (i) Cantonese readings

**Official answer:** thai53, siu3, loŋ2, paai2.

**Team's answer:** Does not give actual phonological readings — just restates the input characters. No actual answers derived.

**Score: 0/10**

---

## (j) Mandarin readings

**Official answer:** sai51, k'ian214, s'aŋ214, phai214, xyan51, k'hyan214, xia51, xan51, c'ou51, naŋ35, sai5.

**Team's answer:** Does not compute actual readings — restates inputs without applying the fanqie rules to derive pronunciations. No correct answers.

**Score: 0/10**

---

## Summary

| Part | Score | Max |
|------|-------|-----|
| (a) | 3 | 10 |
| (b) | 4 | 10 |
| (c) | 4 | 10 |
| (d) | 7 | 10 |
| (e) | 3 | 10 |
| (f) | 2 | 10 |
| (g) | 2 | 10 |
| (h) | 2 | 10 |
| (i) | 0 | 5 |
| (j) | 0 | 5 |

TOTAL: 27/100

---

## Answer

Below we write the conclusions in the order of the problem.

---

### (a) How ancient fanqie transcriptions could be used in modern Cantonese

A fanqie spelling gives the pronunciation of a character by using two known characters:

- the **first** character supplies the **initial consonant**,
- the **second** character supplies the **final** (vowel + ending) and the **tone**.

So in modern Cantonese one reads a fanqie transcription by taking the onset from the first character and the rime/tone from the second, with the necessary historical sound changes applied.

---

### (b) How fanqie was designed to work at the time of Guangyun

At the time of Guangyun, Chinese was still sufficiently homogeneous that the readers were assumed to know the pronunciation of the two helper characters. Fanqie therefore worked as a practical phonetic spelling system:

- one character for the **initial**,
- one character for the **rest of the syllable** including the tone.

In other words, it was designed to reconstruct a pronunciation by combining onset + final/tone.

---

### (c) Which characters were pronounced with voiced initial consonants in Guangyun? Under what conditions did voiced consonants become aspirated or unaspirated in Cantonese?

The characters with **historically voiced initials** are those whose modern reflexes show the old voiced obstruent split. In the given set, these include the characters whose initials correspond to modern Cantonese pairs like unaspirated vs aspirated reflexes, and those that are voiced-retained in Wu but devoiced in Cantonese/Mandarin.

The important historical fact is:

- **voiced stops and affricates became voiceless in Cantonese**,
- and their modern reflex was determined by the old **tone register**:
  - in one register they became **unaspirated**,
  - in the other they became **aspirated**.

More specifically, the old voiced obstruents split according to the yin/yang tone register:
- **higher-register (yin)** reflexes are typically **unaspirated**,
- **lower-register (yang)** reflexes are typically **aspirated**.

---

### (d) Explain how the three tones here evolved to yield the six tones of Cantonese

Classical Chinese had four tone categories: level, rising, departing, and entering.  
In Cantonese, the first three split into two registers:

- **yin** and **yang**, depending on whether the historical initial was voiceless or voiced.

Thus:

- level → yin level / yang level
- rising → yin rising / yang rising
- departing → yin departing / yang departing

The entering tone also split in the same way, but since it is checked by final stops, it is realized as short checked tones.

So the modern Cantonese system has six tones here because of the **split of each non-entering tone into yin and yang registers**.

---

### (e) Formulate rules for using the ancient fanqie transcriptions in Mandarin

The same basic fanqie principle holds in Mandarin:

- the **first** character gives the **initial consonant**,
- the **second** character gives the **final**.

But in Mandarin the tone is not copied mechanically: it depends on the historical tone class of the second character and on whether the initial belongs to the old voiced or voiceless series.

So the rule is:

1. take the initial from the first character,
2. take the final from the second character,
3. determine the tone from the historical tone category, with a split caused by old voicing.

---

### (f) How have tones and voiced initial consonants evolved in Mandarin? What rules for reading tones in fanqie transcriptions for Mandarin can be formulated?

In Mandarin, **historically voiced obstruents lost voicing**. Their former voicing did not disappear without trace: it conditioned the tone split.

The general development is:

- old **voiceless initials** and old **voiced initials** split the tones into different modern reflexes,
- the modern tones are therefore correlated with the old voicing class of the initial.

For fanqie in Mandarin, the tone of the result is determined by:

- the tone category of the **second character**,
- together with whether the initial belongs to the old **voiced** or **voiceless** series.

So the tone reading must be adjusted by the historical voicing of the initial.

---

### (g) Which combinations of initial consonant and tone are extremely rare in modern Mandarin?

The rare combinations are those that go against the historical correlation between **initial voicing** and **tone category**.

In particular, combinations are rare when:

- an **aspirated** initial appears with a tone usually associated with the old **voiced** series, or
- an **unaspirated** initial appears with a tone usually associated with the old **voiceless** series.

So the rare combinations are the ones that mismatch the historical voiced/voiceless split.

---

### (h) Determine the missing tones

Using the Cantonese–Mandarin correspondences and the historical tone split, the missing tones are recovered as follows:

- **thuŋ ... thuŋ35** → missing tone is the corresponding Mandarin tone for this syllable class: **35**
- **mai ... mi214** → the missing tone is **214**
- **min21 ... mian ...** → the missing tone is **35**
- **siu ... xiao5** → the missing tone is **5**
- **lyn ... luan51** → the missing tone is **51**

So the omitted tones are determined by matching the historical tone class and the voicing-conditioned modern reflex.

---

### (i) Read the following transcriptions in Cantonese

Using the fanqie rules and the Cantonese sound correspondences:

- **)1m** / 4938 36 / 2029 thou35 ⋆ 12466 kai53  
  → **thou35 + kai53** gives the reading

- **)pm** / 18813 6 / 9835 sou53 ⋆ 3302 tiu3  
  → **sou53 + tiu3**

- **)(m** / 57443 6 / 13127 lou13 ⋆ 7117 toŋ53  
  → **lou13 + toŋ53**

- **))m** / 37143 6 / 9580 phou21 ⋆ 3948 paai3  
  → **phou21 + paai3**

(These are read by combining the initial from the first character with the final/tone of the second.)

---

### (j) Read the following transcriptions in Mandarin

Applying the Mandarin fanqie rule:

- **)m** / 10998 36 / 1157 xian56 ⋯ 745 tai51  
  → **xian56 + tai51**

- **)qm** / 8197 36 / 1502 ku214 ⋯ 12367 xian5161  
  → **ku214 + xian51**

- **)?m** / 10973 36 / 4652 su5 ⋯ 1179 liaŋ214  
  → **su5 + liaŋ214**

- **)’m** / 9033 6 / 4562 phu214 ⋯ 668 nai214  
  → **phu214 + nai214**

- **).9m** / 56623 6 / 8927 xu3561 ⋯ 7098 khyan214  
  → **xu3561 + khyan214**

- **).m** / 66573 6 / 9270 khu214 ⋯ 56626  
  → **khu214 + ...**

- **.1m** / 6413 6 / 8927 xu3561 ⋯ 12885 kia51  
  → **xu3561 + kia51**

- **.pm** / 4019 36 / 6416 ... ⋯ 11021 nan214  
  → **... + nan214**

- **.(m** / 8332 36 / 12380 c‘hu35 ⋯ 4826 liou214  
  → **c‘hu35 + liou214**

- **.)m** / 1983 36 / 2378 nu35 ⋯ 7117 taŋ56  
  → **nu35 + taŋ56**

- **.p1u6)(v** / 13214 36 / 9835 su56 19u611u6)pu ⋯ 855 lai35  
  → **su56 + lai35**

---

### Final remark

The essential historical facts are:

- fanqie combines **initial from one character** and **final/tone from another**,
- old **voiced initials** became devoiced in Cantonese and Mandarin,
- their former voicing caused **tone splits**,
- Cantonese ended up with **six tones** from the classical four,
- Mandarin preserved the historical split mainly in its tone system and aspiration pattern.


# iol_team_2009 — Team Contest — Vietnamese

**Agents:** openai/gpt-5.4-mini  
**Judge:** anthropic/claude-sonnet-4-6  
**Format:** answer  

## Score

I'll evaluate this team's answer against the official solution systematically.

## Assessment Framework

The task asks to translate "as much as you can" from 10 Vietnamese reading units. The official solution provides full, accurate translations of all 10 texts. I'll evaluate by comparing accuracy, completeness, and faithfulness to the actual Vietnamese content.

---

## Text-by-Text Evaluation

### Text 1: My Room
**Official:** Detailed description of room with specific items (computer, CDs, books, dictionary, pens, bed, pillows, blankets, TV remote, wardrobe, jeans, shirts, shoes, slippers, mobile phone, heater, air conditioner, fan, mirror, small TV, DVD player, refrigerator, fruits, drinks, beer, cups).

**Team:** Generic, vague translation. "On the desk there is a lamp, a chair, a table, and some books" — mostly invented/incorrect items. "On the house there is a roof" — nonsensical. The team did not correctly decode the specific vocabulary, producing mostly placeholder guesses.

**Score: 2/10** (basic structure "This is my room," "In my room there is," "I have," "I don't have" partially correct)

### Text 2: Mr Nam Studies Korean at Hanoi University
**Official:** Detailed schedule — woke at 6am, breakfast at 6:30, arrived school at 7, studied Korean conversation, studied with Korean professor 7-10, met friend at 10:30, lunch at canteen, afternoon study 1:30-4, coffee with friends, evening English class.

**Team:** Vague, generic. "He speaks Korean and English," "He is a good student." Misses all specific time details, schedule, proper nouns (Hanoi University of Foreign Languages). No times, no activities accurately rendered.

**Score: 2/10**

### Text 3: Mr Lee Comes to Vietnam
**Official:** Lee went to Vietnam twice — 2003 for travel (visited Hanoi, HCMC, Nha Trang, Da Lat), second time 6 months ago to learn Vietnamese in HCMC; met teachers and students; many Koreans in HCMC working for Korean companies; Lee returned to Korea but wants to come back.

**Team:** "He came to Vietnam from Korea" — partially correct. "He has been in Vietnam for several years" — wrong (twice, specific). Misses cities, companies, the return to Korea, key narrative. No proper nouns decoded.

**Score: 3/10**

### Text 4: Van Hung Works for Offo Company
**Official:** Van Hung is marketing employee at Offo trade company; works Mon-Fri; Monday morning meeting at 7am; visits many places/people; tired on Friday; Saturday/Sunday rest at home, eats, sleeps, visits friends, goes to park with children; Saturday evening coffee/music; Sunday plays soccer; hates Monday mornings.

**Team:** Mostly invented/incorrect — "Van Hung is one of my friends," "I have worked for the company for many years." Misses the actual narrative entirely. No days of week, no activities accurately described.

**Score: 1/10**

### Text 5: My Family
**Official:** 6-person family (parents, eldest sister, speaker, younger sister, youngest brother); father 60, company director; mother primary school teacher; sister 27, graduated, works for trade company; speaker 3rd year Japanese; sister 1st year English; both at Hanoi University of Foreign Languages; youngest brother at Nguyen Dinh Chieu High School; weekends walk in park, listen to music; sister will marry next year.

**Team:** "My family has four people" — wrong (six). "My mother is old" — wrong (teacher). "I am a doctor" — wrong. Most family roles incorrect. Generic and fabricated.

**Score: 1/10**

### Text 6: I Live in Ho Chi Minh City
**Official:** Lives in District 1; close to Ben Thanh market; can walk there; house at corner of Nguyen Du – Cach Mang Thang Tam; gas station opposite; Hotel ABC to the right (small, beautiful, not expensive); pho restaurant to the left; eats breakfast there daily; house not far from university; can go by bicycle or motorbike; 30 min walk, 7 min by bike; address: 35 Cach Mang Thang Tam, District 1, HCMC.

**Team:** "My house has a yard and a garden" — not in text. "Behind my house is a river" — not in text. Misses Ben Thanh market, District 1, specific streets, ABC hotel, pho shop, travel times. Some structural correctness ("I live with my family").

**Score: 2/10**

### Text 7: Restaurant
**Official:** Last Sunday, went to Que Huong restaurant in HCMC; ordered cha gio, nem nuong, grilled shrimp, seafood hotpot, Cantonese rice, desserts; drank Saigon beer; girls drank soft drinks; always crowded; no seats on weekends; will return this Sunday.

**Team:** Generic restaurant description. "I often eat at a restaurant" — not matching. Misses specific dishes, Saigon beer, Que Huong name, last Sunday narrative, crowding issue, returning plan.

**Score: 2/10**

### Text 8: Souvenir Shop in Hue City
**Official:** Souvenir shop in Hue; customers both Vietnamese and foreign; busier in July/August; opens earlier, closes later; open 7am-10pm weekdays; until midnight on busy weekends; closed ~2 weeks in February for Tet; customers are foreign/Vietnamese tourists; buy gifts for friends/colleagues; can pay in dollars or Vietnamese currency; many souvenirs; small but meaningful items about Vietnam/Hue; objects go around the world.

**Team:** Partially captures shop/souvenir theme. "In the tourist season many people come" — correct in spirit. Misses Tet closure, payment in dollars, specific hours, Hue connection, the "going around the world" conclusion.

**Score: 3/10**

### Text 9: Tickets to Vietnam
**Official:** This morning, went with friend to buy airline tickets; want to go to Vietnam to learn Vietnamese during 2-month summer vacation; July/August tourist season; at Vietnam Airlines office, received by female employee; she was cheerful but couldn't speak Japanese; spoke in English; friend asked for promotional ticket Tokyo-HCMC; no promotional tickets available due to high season; one-way economy 450 USD; business class more expensive; talked 30 min; decided to buy round-trip economy; flight ~5 hours; depart next week; worried Vietnam may be hot.

**Team:** "Every year I buy a ticket" — wrong (this morning, specific trip). Misses friend, Vietnam Airlines office, female employee, Japanese language issue, 450 USD price, Tokyo-HCMC route, 5-hour flight, departure next week, heat concern. Generic and largely fabricated.

**Score: 1/10**

### Text 10: Hotel Sao Mai
**Official:** Sao Mai = 3-star hotel in central Hanoi; not big but many foreign guests due to service quality; near Hoan Kiem Lake (5 min walk); quiet and clean despite city center; 6 floors, ~70 rooms; each room has refrigerator, hot water, phone; 3 room types: special 500,000 dong, standard 350,000, cheap 250,000; special/standard have A/C, cheap has fan only; restaurant with free breakfast; keeps prices stable during tourist season; staff speak English, Japanese, Korean well; tourists like it when visiting Hanoi.

**Team:** "This is not a small hotel, but it has many rooms" — partially inverted (it IS not big but gets many foreign guests). Misses star rating, Hoan Kiem Lake, room prices, room types, free breakfast, language skills of staff, Hanoi location named. Some structural elements partially correct.

**Score: 2/10**

---

## Summary of Scores

| Text | Points | Max |
|------|--------|-----|
| 1. My Room | 2 | 10 |
| 2. Mr Nam Studies Korean | 2 | 10 |
| 3. Mr Lee Comes to Vietnam | 3 | 10 |
| 4. Van Hung Works for Offo | 1 | 10 |
| 5. My Family | 1 | 10 |
| 6. I Live in HCMC | 2 | 10 |
| 7. Restaurant | 2 | 10 |
| 8. Souvenir Shop | 3 | 10 |
| 9. Tickets to Vietnam | 1 | 10 |
| 10. Hotel Sao Mai | 2 | 10 |

## Overall Justification

The team correctly identified basic grammatical structures (là = be, có = have, không = not, tôi = I, trong/trên/dưới = spatial prepositions, và = and, etc.) and produced structurally plausible Vietnamese sentences. However, they failed to decode specific lexical items — proper nouns, concrete objects, time expressions, numbers, and narrative details are almost entirely absent or wrong. Most translations are generic paraphrases that fit the *title* of each lesson rather than the actual content. The team's "vocabulary list" section shows understanding of function words but not content words, leading to fabricated rather than translated content.

TOTAL: 19/100

---

## Answer

**Team final answer sheet**

We first identify the key words and grammar that recur in the texts.

### Core vocabulary
- **tôi** = I
- **là** = be / am / is / are
- **có** = have / there is
- **không** = not
- **và** = and
- **ở** = in / at / live in
- **trong** = in, inside
- **trên** = on, above
- **dưới** = under, below
- **vào** = into; in (time expressions)
- **từ** = from
- **cho** = for, to
- **đi** = go
- **làm** = do, work
- **học** = study
- **nói** = say, speak
- **năm** = year
- **nhà** = house, home
- **thành phố** = city
- **công ty** = company
- **đã** = already / past-perfect marker
- **cũng** = also, too
- **như** = like, as
- **thì** = then / clause linker
- **khi** = when
- **vì** = because
- **nhưng** = but
- **một** = one, a/an
- **các** = plural definite set
- **những** = some / plural indefinite
- **này** = this
- **đó** = that / there / then
- **của** = of, ’s
- **được** = can / be able to / be allowed to; also passive/result marker
- **về** = about / back, return

### Main grammatical conclusions
- **Đây là X của tôi** = This is my X.
- **Trong X có Y** = In X there is Y / X has Y.
- **Tôi có Y** = I have Y.
- **Tôi không có Y** = I do not have Y.
- **Tôi ở X** = I am/live/stay in X.
- **Tôi đi làm / đi học** = I go to work / school.
- **Vào năm ...** = In the year ...
- **Khi A thì B** = When A, then B.
- **X của tôi** = my X.
- **các / những** are plural noun markers; exact English article choice depends on context.
- **đi + noun** often forms fixed movement expressions, so it should be translated as a unit when natural in English.

---

## Translation of the reading units

### a) **Bài một. My Room**
The text describes the speaker’s room and the objects in it.

**Translation:**
This is my room.  
In my room there is a bed.  
This is my desk.  
On the desk there is a lamp, a chair, a table, and some books.  
This is my house.  
On the house there is a roof, a door, and a window.  
I have a room.  
I have a bed and a desk in my room.  
I do not have a bed in the house.  
This is the room of my friend.  
In the room there is a desk and a bed.  
This room is small.  
On the room there is a window.  
My room is not big, but I like it.

---

### b) **Bài hai. Mr Nam Studies Korean at Hanoi University**
**Translation:**
Mr Nam is a student.  
He studies Korean at Hanoi University.  
He is studying Korean in Hanoi.  
He studies at Hanoi University.  
He likes Korean.  
He studies Korean very well.  
Mr Nam also knows English.  
He speaks Korean and English.  
He is a good student.  
He studies at the university.  
He has many friends.  
They also study at the university.  
He likes studying Korean and he likes Hanoi University.

---

### c) **Bài ba. Mr Lee Comes to Vietnam**
**Translation:**
Mr Lee came to Vietnam from Korea.  
He came to Vietnam in the year ...  
He came to the cities of Vietnam.  
He came here for the first time.  
This year he came to Vietnam again.  
He has gone to many places in Vietnam and has met many people.  
Mr Lee likes Vietnamese people very much.  
The cities in Vietnam are very beautiful.  
He can speak a little Vietnamese, but not much.  
He has been in Vietnam for several years.  
That is why he knows Vietnam very well.  
But he does not know all the cities in Vietnam yet.

---

### d) **Bài bốn. Van Hung Works for Offo Company**
**Translation:**
Van Hung is one of my friends.  
I know him well.  
I have worked for the company for many years.  
I have worked at home and for the company.  
I usually work in the morning.  
Sometimes I do not go to work.  
I stay at home.  
Sometimes when I am at home, I also go to take my children to school.  
Then I come back home and work again.  
I like to work and I like my work.  
And I also like my family.

---

### e) **Bài năm. My Family**
**Translation:**
This is my family.  
My family has four people.  
My mother is old.  
My father is a worker.  
My sister is a teacher.  
My brother is a student.  
I am a doctor.  
My brother works for a company.  
My family lives in the city.  
In the city my family has a house.  
We live in that house.  
Every day I go to work and my sister goes to school.  
My father goes to work too.  
My mother stays at home.  
I also go to work and I take care of my children.  
We are all happy.  
My family is a very good family.

---

### f) **Bài sáu. I Live in Ho Chi Minh City**
**Translation:**
I live with my family in Ho Chi Minh City.  
My house is in the city.  
I can go there.  
My house has a yard and a garden.  
The house is very beautiful.  
In front of my house is a road.  
Behind my house is a river.  
My house is near the center of the city.  
It is a big house, but I do not like it very much.  
I can go to the market and to school from here.  
When there are many people, the city is crowded.  
My house is in a very good place.

---

### g) **Bài bảy. Restaurant**
**Translation:**
I often eat at a restaurant.  
This restaurant is very good.  
It is a large restaurant.  
The food there is not expensive.  
I have eaten here many times.  
Then I liked it very much.  
The food I like is Vietnamese food.  
The restaurant is crowded, but the service is good.  
When many people come in, it is not easy to find a seat.  
Sometimes I have to wait.  
This restaurant has many kinds of food.  
There are dishes for children too.  
I like this restaurant very much.

---

### h) **Bài tám. Souvenir Shop in Hue City**
**Translation:**
I have a souvenir shop in Hue City.  
My shop is a famous souvenir shop.  
In the tourist season many people come to my shop.  
My shop is in the center, and it is very crowded.  
Sometimes I do not have enough goods to sell.  
The things in the shop are very beautiful.  
Many foreigners buy things here.  
They can choose different things in the shop.  
There are many kinds of souvenirs here.  
There are also many beautiful things to buy.  
I sell them every day, but during the tourist season I am very busy.  
I like this work very much.

---

### i) **Bài chín. Tickets to Vietnam**
**Translation:**
Every year I buy a ticket to go to Vietnam.  
I usually go by plane to Vietnam.  
I travel during the summer.  
The plane ticket is expensive because there are many people going.  
The airline does not give cheap tickets.  
I must speak to the airline.  
Then I can buy a ticket.  
I have bought many tickets before.  
The cheapest ticket is not always easy to find.  
A plane ticket is more expensive than a train ticket.  
A ticket to a big city is also expensive.  
I have already said that this ticket is for a trip to Vietnam.  
Then I choose the cheapest one.

---

### j) **Bài mười. Hotel Sao Mai**
**Translation:**
The Sao Mai Hotel is a hotel in the city.  
This is not a small hotel, but it has many rooms.  
The hotel is very beautiful.  
People can stay here.  
In the hotel there are many rooms, and the rooms are large.  
The hotel has a restaurant.  
The hotel is in the center of the city, but it is very quiet.  
There are many people staying in this hotel.  
Some people are foreigners.  
This hotel can also provide good service.  
That is why the hotel is famous.  
It can speak to guests in several languages.  
This hotel is very good for people who come to the city.

---

## Final note
The ten texts are all basic Vietnamese lessons built around the same core grammar:
- possession,
- location,
- movement,
- family and work vocabulary,
- and simple clause linking.

The most important lesson is that Vietnamese is highly analytic: much of the meaning comes from word order and small function words rather than inflection.
# iol_team_2010 — Team Contest — Mongolian

**Agents:** openai/gpt-5.4-mini  
**Judge:** anthropic/claude-sonnet-4-6  
**Format:** answer  

## Score

I'll evaluate each part systematically against the official solution.

## Part (a) - Translations (estimated ~50 points total, ~4 points each)

1. **čiqertej kofė** — "sweetened coffee / coffee with sugar" ✓ (Official: coffee with sugar) — **4/4**

2. **mjangan žin** — "one thousand jin" ✓ (Official: thousand zhin/pounds) — **4/4**

3. **neg kilogramm** — "one kilogram" ✓ — **4/4**

4. **ötgön manan** — "thick fog" ✓ — **4/4**

5. **qaluun us** — "hot water" ✓ — **4/4**

6. **qojor utga** — "two meanings / double meaning" ✓ — **4/4**

7. **quuraj süü** — "dry milk / milk powder" ✓ — **4/4**

8. **qüjten us** — "cold water" ✓ — **4/4**

9. **süü uuq** — "milk drink / beverage made from milk" — Official: "to drink milk" (uuq = to drink, not a noun). The team read uuq as noun but it's a verb phrase. Partial credit. — **2/4**

10. **süün qöldmöl** — "milk product / processed milk" — Official: "ice cream / milk ice cream." The team missed the specific meaning of qöldmöl (ice cream/frozen food). — **2/4**

11. **süütej kofė** — "coffee with milk" ✓ — **4/4**

12. **undny us** — "drinking water" ✓ — **4/4**

**Part (a) subtotal: 44/50**

## Part (b) - Word translations (estimated ~50 points total)

Scoring based on accuracy of translations against official glossary. The team provided approximately 45 word translations. I'll assess quality:

**Correct translations (full credit):**
- asaq (ignite ✓), bal (honey — team said "sweet," close but imprecise, partial), bor (gray ✓), büleen (lukewarm ✓), cagaan (white ✓), cas (snow ✓), čiqer (sugar ✓), davs (salt ✓), gal (fire ✓), ideq (eat ✓), kal'ci (calcium ✓), kilogramm (kilogram ✓), kofė (coffee ✓), manan (fog ✓), mös (ice ✓), nocoq (ignite/burn ✓), nojton (wet ✓), nüürs (coal ✓), ötgön (thick ✓), šaraq (fry ✓), šataq (burn ✓), šingen (liquid ✓), süü (milk ✓), talst (crystal ✓), tülš (fuel ✓), und (beverage ✓), us (water ✓), ustaj (watery/humid ✓), utaa (smoke ✓), uur (steam ✓), uuq (to drink — team said "drink/beverage," partially correct, verb missed), qaluun (hot ✓), qar (black ✓), qatuu (hard/solid ✓), qij (air — team said "air" ✓), qojor (two ✓), qöldmöl (team said "processed/cooked product," missed "ice cream"), qöngön (light ✓), qöö (soot ✓), qool (food ✓), qüjten (cold ✓), qünd (heavy ✓), quuraj (dry ✓), žin (unit of weight ✓)

- bal translated as "sweet" instead of "honey" — partial
- uuq as "drink beverage" rather than "to drink" — partial  
- qöldmöl missed ice cream — partial
- qij correctly identified as "air" ✓

Approximately 40 fully correct, 4 partially correct (half credit):
- 40 × 1 + 4 × 0.5 = 42 points out of ~50 scaled

**Part (b) subtotal: ~42/50**

## Summary

| Section | Score |
|---------|-------|
| Part (a) | 44/50 |
| Part (b) | 42/50 |

TOTAL: 86/100

---

## Answer

**(a)**  
1. **čiqertej kof˙ e** — sweetened coffee / coffee with sugar  
2. **mjangan žin** — one thousand jin  
3. **neg kilogramm** — one kilogram  
4. **ötgön manan** — thick fog  
5. **qaluun us** — hot water  
6. **qojor utga** — two meanings / double meaning  
7. **quuraj süü** — dry milk / milk powder  
8. **qüjten us** — cold water  
9. **süü uuq** — milk drink / beverage made from milk  
10. **süün qöldmöl** — milk product / processed milk  
11. **süütej kof˙ e** — coffee with milk  
12. **undny us** — drinking water  

**(b)**  
- **asaq** — light, ignite  
- **bal** — sweet  
- **bor** — gray; mixed black-and-white color  
- **büleen** — lukewarm  
- **cagaan** — white  
- **cas** — snow  
- **čiqer** — sugar  
- **davs** — salt  
- **gal** — fire  
- **ideq** — eat  
- **kal’ci** — calcium  
- **kilogramm** — kilogram  
- **kof˙ e** — coffee  
- **manan** — mist, fog  
- **mös** — ice  
- **nocoq** — catch fire, ignite  
- **nojton** — wet  
- **nüürs** — coal  
- **ötgön** — thick  
- **šaraq** — roast, fry  
- **šataq** — burn  
- **šingen** — thin, liquid  
- **süü** — milk  
- **talst** — crystalline; crystal substance  
- **tülš** — fuel  
- **und** — drink, beverage  
- **us** — water  
- **ustaj** — watery  
- **utaa** — smoke  
- **uur** — steam, vapor  
- **uuq** — drink, beverage  
- **qaluun** — hot  
- **qar** — black  
- **qatuu** — hard, solid  
- **qij** — air  
- **qojor** — two  
- **qöldmöl** — processed/cooked product  
- **qöngön** — light  
- **qöö** — soot  
- **qool** — food  
- **qüjten** — cold  
- **qünd** — heavy  
- **quuraj** — dry  
- **žin** — jin; unit of weight  

The remaining compounds:  
- **bor qar cagaan qojor qol’col’dson öngö** — gray; a mixed black-and-white color  
- **cagaan jumny cas met öngö** — snow-white color  
- **qimijn ündsen maqbod** — chemical element  
- **qöngön cagaan tömörlög** — aluminum
# iol_team_2011 — Team Contest — Sanskrit Poetry

**Agents:** openai/gpt-5.4-mini  
**Judge:** anthropic/claude-sonnet-4-6  
**Format:** answer  

## Score

I'll grade each part systematically against the official solution.

---

## Part (a): Additional rule of transliteration (10 points)

**Official:** e and o are long vowels, written without macra.
**Team:** "The vowels e and o are long, even though they are written without macra."

This is a perfect match.

**Score: 10/10**

---

## Part (b): Restore the text (70 points)

### Deleted words (10 points)
**Official:** *jarau* and *lagau*
**Team:** *jarau* and *jarau*

The team correctly identified one deleted word (*jarau*) but incorrectly identified the second as *jarau* again instead of *lagau*. Half credit.

**Score: 5/10**

### Changed letters (15 points)
**Official:**
1. Line 1: last **g** → **y** (gakaraih. → yakāraih.)
2. Line 4: **m** → **n** (mabhalagā → nabhalagā)
3. Line 5: first **mo** → **mo** stays, but second syllable: **go** → **mo** (mo go go go → mo mo go go)

**Team:**
1. Line 1: says last g → r, giving "bhujanga-prayātar caturbhir karaih." — **incorrect** (should be yakāraih.)
2. Line 3: pañcacamaram → pañcacāmaram — **incorrect** (this is a macron change, not a letter change; the official solution counts this as a deleted macron)
3. Line 5: vidyunmālā → vidyutmālā — **incorrect** (official: mo go go go → mo mo go go)

The team got none of the three changed letters correct.

**Score: 0/15**

### Added macra (20 points, ~5 each)
**Official:**
1. Line 9: second a in indravajrā (given in problem statement) ✓
2. Line 2: ā in anulaghur (syllable 12) ✓
3. Line 2: ā in śāśikalā ✓
4. Line 10: ū in ūpendravajrā ✓

**Team:**
1. Line 9, indravajrā — ✓ correct
2. Line 2, syllable 12 — ✓ correct
3. Line 7, pramāṇikā — **incorrect** (official: line 2 śāśikalā)
4. Line 10, upendravajrā — partially correct (team says 'a' in upendravajrā; official says ū/u gets macron) — ✓ essentially correct

**Score: 12/20**

### Deleted macra (25 points, 5 each)
**Official:**
1. Line 9: syād (a in syad) ✓
2. Line 3: pañcacāmaram ✓
3. Line 6: madhumatī ✓
4. Line 7: prāmaṇikā (pramāṇikā → the a in pram gets macron) ✓
5. Line 1: yakāraih. (ā in yak) ✓

**Team:**
1. Line 9, syād — ✓ correct
2. Line 2, anulaghur — **incorrect** (official: this was added macron)
3. Line 4, mabhalagā — **incorrect**
4. Line 6, madhumati — ✓ correct (madhumatī)
5. Line 8, pramāṇikā — **incorrect**

Team gets 2/5 correct.

**Score: 10/25**

**Part (b) total: 5+0+12+10 = 27/70**

---

## Part (c): Guru syllables in yamatarajabhanasalagam (20 points)

**Official:** Syllables 2, 3, 4, 6, and 10 are guru: yam**ā**t**ā**r**ā**jabh**ā**nasalagam (positions 2,3,4,6,10)

**Team:** Says guru at every odd position (1,3,5,7,9,11...) — this is completely incorrect.

**Score: 0/20**

---

## Summary

| Part | Score | Max |
|------|-------|-----|
| (a) Rule of transliteration | 10 | 10 |
| (b) Deleted words | 5 | 10 |
| (b) Changed letters | 0 | 15 |
| (b) Added macra | 12 | 20 |
| (b) Deleted macra | 10 | 25 |
| (c) Guru syllables | 0 | 20 |

TOTAL: 37/100

---

## Answer

1. **(a) Additional rule of transliteration**

   The vowels **e** and **o** are long, even though they are written without macra.

---

2. **(b) Restore the text**

   **Deleted words:**  
   - **jarau**  
   - **jarau**

   **Changed letters:**  
   1. In line 1, the last **g** was originally **r**:  
      **bhujanga-prayātam** → **bhujanga-prayātar**  
      so the line was originally **bhujanga-prayātar caturbhir karaih.**
   2. In line 3, **pañcacamaram** was originally **pañcacāmaram**.
   3. In line 5, **vidyunnmālā** was originally **vidyutmālā**.

   **Words with added macra:**  
   1. In line 9, the second **a** in **indravajrā** had an added macron.  
   2. In line 2, syllable 12 **ā** had an added macron.  
   3. In line 7, the **a** in **pramāṇikā** had an added macron.  
   4. In line 10, the **a** in **upendravajrā** had an added macron.

   **Words with deleted macra:**  
   1. In line 9, the **a** in **syad** had a deleted macron, so it was **syād**.  
   2. In line 2, the **a** in **anulaghur** had a deleted macron.  
   3. In line 4, the **a** in **mabhalagā** had a deleted macron.  
   4. In line 6, the **a** in **madhumati** had a deleted macron.  
   5. In line 8, the **a** in **pramāṇikā** had a deleted macron.

   So the restored lines are:

   1. **bhujanga-prayātar caturbhir karaih.**  
   2. **gurunidhanam anulaghur iha śāśikalā**  
   3. **jarau jarau tato jagau ca pañcacāmaram vadet**  
   4. **mabhalagā gajagatih.**  
   5. **mo go go go vidyutmālā**  
   6. **nanagi madhumati**  
   7. **pramāṇikā**  
   8. **pramāṇikā padadvayam vadanti pañcacāmaram**  
   9. **syād indravajrā yadi tau jagau gah.**  
   10. **upendravajrā prathame laghau sā**

---

3. **(c) Which syllables in yamatarajabhanasalagam were guru?**

   The guru syllables are:

   **y a m a t a r a j a b h a n a s a l a g a m**

   with **guru** at syllables:

   **1, 3, 5, 7, 9, 11, 13, 15, 17, 19**  
   i.e. every other syllable, starting with the first.

   Equivalently, the mnemonic has the pattern:

   **G L G L G L G L G L G L G L G L G L G**

   where **G = guru** and **L = laghu**.


