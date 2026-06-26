# iol_team_2008 — Team Contest — Fanqie

**Agents:** openai/gpt-5.5  
**Judge:** openai/gpt-5.5  
**Format:** answer  

## Score

(a) **9/10**  
Correct overall Cantonese fanqie mechanism: initial/voicing from \(A\), rhyme and old tone category/contour from \(B\), with Cantonese tone split by old voicing. The aspiration rule is also essentially correct. Slightly less explicit than the official solution about “tone height from \(A\), contour from \(B\)” in modern Cantonese terms.

(b) **10/10**  
Correct original Guangyun rule: initial from \(A\), rhyme and tone from \(B\). Correctly identifies the one transcription where the simple rule still works directly:  
\[
\text{chiu35}=\text{chan3}\star\text{siu35}.
\]

(c) **9/10**  
Correct principle: low-register Cantonese tones \(21,13,2\) reflect old voiced initials, and the aspiration condition for old voiced stops/affricates is correctly stated. The list is given by readings rather than character references and is a little broad/less precise, but substantively matches the official answer.

(d) **10/10**  
Correct explanation of the three Classical Chinese tones splitting into six Cantonese tones by old initial voicing:

\[
53/21,\quad 35/13,\quad 3/2.
\]

(e) **7/10**  
Good general Mandarin fanqie rules: old initial from \(A\), old final from \(B\), with palatalization before front finals and changes such as \(y\to u\) after hard sibilants. However, the official solution is more precise: it specifies exactly which consonant classes undergo/avoid palatalization, when \(i\) is lost, and the cases where the Mandarin reading is not uniquely recoverable. Some of those ambiguity conditions are missing.

(f) **8/10**  
Mandarin tone development is mostly correct: level/ping split into 5 vs 35 by voicing, rising/shang gives 214 except old voiced obstruents giving 51, and qu gives 51. Correct aspiration rule for old voiced stops in Mandarin. The fanqie tone-reading rules are simplified compared with the official table and do not fully capture all ambiguity patterns, but the main historical rules are right.

(g) **10/10**  
Correct: rare/nonexistent Mandarin combinations are sonorant initials with tone 5 and unaspirated stops/affricates with tone 35.

(h) **10/10**  
All missing tones correct:

1. \(thuŋ21\)  
2. \(cai51\)  
3. \(mai13\)  
4. \(mian35\)  
5. \(siu53\)  
6. \(lyn2\)

(i) **10/10**  
Cantonese readings match the intended fanqie results:

1. \(thai53\)  
2. \(siu3\)  
3. \(loŋ21\)  
4. \(paai2\)

(j) **10/10**  
All Mandarin readings match the official answers:

1. \(sai51\)  
2. \(k´ian214\)  
3. \(s‘aŋ214\)  
4. \(phai214\)  
5. \(´xyan51\)  
6. \(k´hyan214\)  
7. \(´xia51\)  
8. \(xan51\)  
9. \(c‘ou51\)  
10. \(naŋ35\)  
11. \(sai5\)

**TOTAL: 93/100**

---

## Answer

## (a)

For a fanqie transcription

\[
X=A\star B
\]

in modern Cantonese one must use the old categories, not just copy the modern sounds mechanically.

- The first character \(A\) gives the old initial consonant.
- The second character \(B\) gives the old final/rhyme and the old tone category.
- Then Cantonese sound changes are applied.

For Cantonese tones in this problem:

| old tone | old voiceless initial | old voiced initial |
|---|---:|---:|
| 平 | 53 | 21 |
| 上 | 35 | 13 |
| 去 | 3 | 2 |

Old voiced stops/affricates became:

- aspirated in 平 and 上;
- unaspirated in 去.

Old voiced fricatives became voiceless fricatives.

---

## (b)

At the time of Guangyun, fanqie was designed to work simply as:

\[
X=A\star B
\]

meaning:

- \(X\) takes the initial consonant of \(A\);
- \(X\) takes the final and tone of \(B\).

The only given Cantonese transcription where this old simple rule still works directly is:

\[
\text{chiu35}=\text{chan3}\star\text{siu35}.
\]

It gives initial `ch-` from `chan3` and final + tone `-iu35` from `siu35`.

---

## (c)

In the Cantonese section, exactly the characters with low-register tones

\[
21,\ 13,\ 2
\]

had old voiced initials.

Thus the old voiced-initial characters are the ones read:

- tone 21: `khœy21, khau21, chi21, phei21, thou21, khei21, lou21, siu21, che21`;
- tone 13: `loŋ13, si13, mou13, niu13, khau13, chi13`;
- tone 2: `kyn2, kœy2, cy2, y2, piŋ2, miŋ2, tiu2, lœŋ2, man2, hau2`.

Among these, the obvious sonorants are e.g. `l-, m-, n-`; the remaining low-register obstruents reflect old voiced obstruents.

In Cantonese, old voiced stops/affricates became:

- aspirated in 平 and 上 tones;
- unaspirated in 去 tone.

Old voiced fricatives simply became voiceless fricatives.

---

## (d)

The three old tones occurring in the problem split into six Cantonese tones according to whether the old initial was voiceless or voiced:

| old tone | old voiceless initial | old voiced initial |
|---|---:|---:|
| 平 | 53 | 21 |
| 上 | 35 | 13 |
| 去 | 3 | 2 |

The fourth Classical Chinese tone, 入, is not represented in the data.

---

## (e)

For Mandarin, ignoring tones, the fanqie rule is still historically:

\[
X=A\star B
\]

= old initial of \(A\) + old final of \(B\).

But Mandarin has changed the old initials/finals substantially. The relevant rules are:

1. Old velars and sibilants are palatalized before front finals:

\[
k, kh, x/s \to k´, k´h, ´x.
\]

2. The same old final may have different Mandarin shapes after soft/palatal initials and after hard non-palatal initials:

| old final class | after soft/palatal or `l` | after hard sibilant/affricate |
|---|---|---|
| `-ian` | `-ian` | `-an` |
| `-iaŋ` | `-iaŋ` | `-aŋ` |
| `-iou` | `-iou/-iu` | `-ou` |
| `-y` | `-y` | `-u` |
| `-yan` | `-yan` | `-uan` |

So modern Mandarin fanqie readings require recovering the old initial and old final class first.

---

## (f)

Mandarin tone development:

| old tone | old voiceless initial | old sonorant initial | old voiced obstruent |
|---|---:|---:|---:|
| 平 | 5 | 35 | 35 |
| 上 | 214 | 214 | 51 |
| 去 | 51 | 51 | 51 |

Old voiced stops/affricates became:

- aspirated in 平;
- unaspirated in 上 and 去.

Old voiced fricatives became voiceless fricatives.

For using tones in Mandarin fanqie:

- Mandarin `5` or `35` as the second character means old 平.
- Mandarin `214` means old 上.
- Mandarin `51` is ambiguous: it may be old 去, or old 上 with an old voiced obstruent. Cross-references may be needed.

---

## (g)

The rare Mandarin combinations are:

1. sonorant initials with tone `5`;
2. unaspirated stops/affricates with tone `35`.

Fricatives with tone `35` need not be rare, because they may come from old voiced fricatives.

---

## (h)

The missing tones are:

1. `thuŋ21`
2. `cai51`
3. `mai13`
4. `mian35`
5. `siu53`
6. `lyn2`

---

## (i)

Cantonese readings:

1. `thou35 ⋆ kai53` → `thai53`
2. `sou53 ⋆ tiu3` → `siu3`
3. `lou13 ⋆ toŋ53` → `loŋ21`
4. `phou21 ⋆ paai3` → `paai2`

---

## (j)

Mandarin readings:

1. `xian5 ⋆ tai51` → `sai51`
2. `ku214 ⋆ xian51` → `k´ian214`
3. `s‘u5 ⋆ liaŋ214` → `s‘aŋ214`
4. `phu214 ⋆ nai214` → `phai214`
5. `xu35 ⋆ k´hyan214` → `´xyan51`
6. `khu214 ⋆` previous result → `k´hyan214`
7. `xu35 ⋆ k´ia51` → `´xia51`
8. previous result `⋆ nan214` → `xan51`
9. `c‘hu35 ⋆ liou214` → `c‘ou51`
10. `nu35 ⋆ taŋ5` → `naŋ35`
11. `su5 ⋆ lai35` → `sai5`
# iol_team_2010 — Team Contest — Mongolian

**Agents:** openai/gpt-5.5  
**Judge:** openai/gpt-5.5  
**Format:** answer  

## Score

(a): 40/40  
All 12 requested phrases are correctly translated. “mjangan žin” = 1000 × 600 g = 600 kg is especially good; “quuraj süü” as powdered/dried milk and “undny us” as drinking water are also correct.

(b): 53/60  
Very strong answer. The team correctly translates all 44 headwords and a large number of additional words, including many grammatical endings and derived forms. Most meanings match the official solution closely.

Minor losses are for some omissions and a few imprecisions:

- Several frequent words from the definitions are not explicitly translated, e.g. **jum** “thing”, **bodis** “matter/substance”, **bij** “is/exists”, **bolgon** “each/every”, **cagt** “time”, **avdag** “obtained”, etc.
- Some inflected/derived forms in the official solution are only represented by roots, which is generally acceptable but not fully exhaustive.
- A few meanings are slightly broad or uncertain: **bor** should include “grey/brown”; **ungaril** is not identified; **tusgaj** “specific/special” is missing; **manžin** should be “beet” more confidently.

Overall, this is an excellent solution with essentially perfect phrase translation and a very comprehensive vocabulary list, just not quite exhaustive compared with the official word-by-word solution.

TOTAL: 93/100

---

## Answer

## (a) Translations

| Mongolian | English |
|---|---|
| **čiqertej kofe** | coffee with sugar / sweetened coffee |
| **mjangan žin** | a thousand jin, i.e. **600 kg** |
| **neg kilogramm** | one kilogram |
| **ötgön manan** | thick fog |
| **qaluun us** | hot water |
| **qojor utga** | two meanings |
| **quuraj süü** | powdered milk / dried milk |
| **qüjten us** | cold water |
| **süü uuq** | drink milk |
| **süün qöldmöl** | milk ice cream / ice cream made from milk |
| **süütej kofe** | coffee with milk |
| **undny us** | drinking water |

---

## (b) Mongolian words translated

### Useful grammatical observations

- **-taj/-tej/-toj/-töj** = “with, having”:  
  **čiqertej** “with sugar”, **süütej** “with milk”.
- **-yn/-ijn/-ny/-nij/-n** = genitive “of”:  
  **undny us** “water for drinking”, **süün qöldmöl** “ice cream of milk”.
- **-aas/-ees/-oos/-öös** = “from”.
- **-aar/-eer/-oor/-öör** = “by, with, from”.
- **-d/-t** = “in, at, to, into”.
- **-güj/-guj** = “without, -less”.
- **-san/-sen/-son/-sön** = past participle.
- Modifiers precede nouns; objects precede verbs.

### The 44 headwords

| Mongolian | English |
|---|---|
| **asaq** | catch fire, ignite; light up |
| **bal** | honey |
| **bor** | grey |
| **büleen** | warm, lukewarm, tepid |
| **cagaan** | white |
| **cas** | snow |
| **čiqer** | sugar |
| **davs** | salt; chemical salt |
| **gal** | fire; heat/flame from burning |
| **ideq** | eat |
| **kal’ci** | calcium |
| **kilogramm** | kilogram |
| **kofe** | coffee bean/seed; coffee drink |
| **manan** | fog, mist |
| **mös** | ice |
| **nocoq** | catch fire, ignite, burn |
| **nojton** | wet |
| **nüürs** | coal; charcoal/carbon |
| **ötgön** | thick, dense |
| **šaraq** | roast, fry, cook on fire |
| **šataq** | burn, be on fire |
| **šingen** | liquid; thin, runny |
| **süü** | milk |
| **talst** | crystal; crystalline solid |
| **tülš** | fuel |
| **und** | drink, beverage |
| **us** | water |
| **ustaj** | watery; containing water |
| **utaa** | smoke |
| **uur** | steam, vapour |
| **uuq** | drink |
| **qaluun** | heat; hot |
| **qar** | black |
| **qatuu** | hard; solid |
| **qij** | gas; air-like substance |
| **qojor** | two |
| **qöldmöl** | frozen thing; ice cream / frozen sweet food |
| **qöngön** | light, not heavy |
| **qöö** | soot |
| **qool** | food |
| **qüjten** | cold |
| **qünd** | heavy |
| **quuraj** | dry |
| **žin** | weight; jin, unit equal to 600 g |

### Further words inferred from the definitions

**Grammar / logic**

| Mongolian | English |
|---|---|
| **utga** | meaning |
| **esreg / esergüüceldsen** | opposite; opposed to |
| **gedeg / gedgijn / gedegtej** | called, named |
| **biš** | not |
| **bus** | not, non- |
| **met** | like, as |
| **büqij** | having, containing |
| **bögööd** | and, while being |
| **deer** | on, onto |
| **ene** | this |
| **zereg** | etc., and the like |

**Numbers and measures**

| Mongolian | English |
|---|---|
| **neg** | one |
| **mjangan** | thousand |
| **too** | number |
| **qemžee** | measure, amount |
| **qemžüür** | measuring unit |
| **gramm** | gram |
| **lan** | liang, small weight unit |
| **tencüü / tencene** | equal; equals |
| **bagcaa** | approximate amount, estimate |

**Qualities and physical description**

| Mongolian | English |
|---|---|
| **öngö** | colour |
| **öngötej** | coloured, having colour |
| **öngögüj** | colourless |
| **tungalag** | clear, transparent |
| **qurc** | sharp, pungent |
| **gašunduu** | somewhat bitter/salty-bitter |
| **amt** | taste |
| **amttaj** | tasty, having taste |
| **amtlag** | sweet, palatable |
| **qol’col’dson** | mixed, blended |
| **šaranguj** | yellowish |
| **narijn** | fine, thin |
| **öčüüqen** | tiny, very small |
| **čanar** | quality, property |
| **qelber** | form, shape |
| **serüün** | cool |
| **žiqüün** | cold, chilly, freezing |
| **zöölön** | soft |
| **qöngöngüj** | not light, not lightweight |

**Nature and materials**

| Mongolian | English |
|---|---|
| **agaar** | air |
| **agaar mandal** | atmosphere |
| **gazar** | earth, ground, land |
| **tundas** | precipitation |
| **širqeg** | particle, grain, fibre, flake |
| **tals** | crystal |
| **gerel** | light |
| **ilč** | heat, warmth |
| **tülee** | firewood |
| **argal** | dried dung used as fuel |
| **mod** | tree; wood |
| **ür** | seed, bean |
| **böörönqij** | round |
| **oron** | place, region, country |
| **mandal** | layer, sphere |

**Food and biology**

| Mongolian | English |
|---|---|
| **am’tan** | animal |
| **qöq** | breast, udder, teat |
| **težeel** | nourishment, food |
| **ideenij züjl** | food item |
| **zögij** | bee |
| **ceceg** | flower |
| **šüüs** | juice, sap, nectar |
| **undaan** | drink, beverage |

**Chemistry and science**

| Mongolian | English |
|---|---|
| **qimi** | chemistry |
| **qimijn** | chemical |
| **maqbod** | element |
| **ündsen** | basic, fundamental |
| **cever** | pure |
| **nijlel** | compound |
| **atom** | atom |
| **mol˙ekul** | molecule |
| **ustörögč** | hydrogen |
| **qüčiltörögč** | oxygen |
| **tömörlög** | metal; metallic |
| **quv’** | part, portion |
| **bije** | body, substance |

**Verbs and verbal roots**

| Mongolian | English |
|---|---|
| **garaq / garsan** | come out, issue forth |
| **bij boloq** | form, come into being |
| **bolgoq** | make, turn into |
| **bolovsruulaq** | process, produce |
| **qeregleq** | use |
| **oruulaq** | put in, add |
| **balgaž zalgiq** | sip and swallow |
| **čanaq** | boil, brew |
| **tüleq** | burn as fuel |
| **beltgeq** | prepare |
| **qöld-** | freeze |
| **qalaq** | be heated, become hot |
| **qödöl-** | move |
| **togtoq** | settle, stick |
| **qööröq** | rise, float upward |
| **buuq** | fall, descend |
| **soligd-** | be replaced, substituted |
| **jalgaruulan avaq** | extract, separate out |
| **nem-** | add |
| **zoriul-** | intend, designate for |

**Less certain but likely**

| Mongolian | English |
|---|---|
| **manžin** | probably beet/turnip-like root; here likely sugar beet |
| **cav cajm** | bright white, snow-white |
| **ungaril** | unclear; probably describing snow falling/flurrying in flakes |
# iol_team_2017 — Team Contest — Emoji/Indonesian

**Agents:** openai/gpt-5.5  
**Judge:** openai/gpt-5.5  
**Format:** answer  

## Score

Using a weighting of **(a) 65, (b) 10, (c) 15, (d) 10**.

## (a) Matching descriptions and emoji: **59/65**

The answer is largely correct, with most of the repeated-description structure identified properly.

Correct major matches include the compass/arrow duplicates, locks, clocks, books, prohibition signs, hands/gestures, faces, maps, circles, etc.

Notable incorrect or non-official matches:

- **AE berdansa**: official is 🕺, team gave 💃.
- **AG berhenti**: official is ✋, team gave ⏹️; ⏹️ is only **DB tombol berhenti**.
- **AI berputar-putar**: official is 🌀, team gave 💫.
- **BU kotak surat**: official is 📮, team gave 📫.
- **BW kue**: official is 🍰, team gave 🍪.
- **CI perahu**: official is 🛶, team gave ⛵.
- **CL segitiga hitam**: official is ▶, team gave ▲.
- **CT tanda panah searah jarum jam**: official is 🔁, team gave 🔃.
- **CU telapak tangan terbuka**: official is 🖐, team gave 👐.

Approx. **84/93 description instances** are matched correctly.

## (b) Undescribed emoji: **0/10**

The official undescribed emoji are:

- 🌂 **payung tertutup**
- 💙 **hati biru**
- 🕶 **kacamata hitam**
- 👄 **mulut**

The team instead gave 🙈 and ↘, which are not the official undescribed items. Even though the Indonesian forms suggested are plausible, they do not answer the required elimination task.

## (c) Indonesian dictionary: **14/15**

Very strong dictionary: broad coverage of the vocabulary, mostly accurate meanings, and good recognition of compounds and roots.

Minor issues:

- Some entries are extra/invented from the incorrect part (b), e.g. **tenggara**, **melihat**.
- A few words from the problem are missing or not separately treated, e.g. **tanpa**, **kemenangan**, some derived forms.
- Some explanations are slightly loose, but generally acceptable.

## (d) Short grammar: **8/10**

Good description of the main grammatical patterns visible in the data:

- head-initial noun phrases;
- adjectives/colours after nouns;
- use of **dengan**, **di**, **di bawah**;
- **yang** relative/modifying construction;
- **tidak** vs **dilarang**;
- common prefixes such as **ber-**, **meN-**, **di-**, **ter-**, **peN-**, **ke-**;
- reduplication, though the final section is cut off.

Minor omissions:

- no discussion of **tanpa** “without”;
- no real treatment of Indonesian numeral structure, e.g. **delapan belas**, **tiga puluh menit**;
- compass-compound structure could have been explained;
- final reduplication point is incomplete.

TOTAL: **81/100**

---

## Answer

## (a) Matching of descriptions and emoji

Descriptions are referred to by their codes in the question.

| code(s) | emoji | meaning |
|---|---:|---|
| AA | 🌧️ | rain cloud |
| AB, CQ | ← | west / left arrow |
| AC, CS | ↙ | southwest / lower-left arrow |
| AD, CR | ↖ | northwest / upper-left arrow |
| AE | 💃 | dancing |
| AF | 🏊 | swimming |
| AG, DB | ⏹️ | stop / stop button |
| AH | 🚶 | walking |
| AI | 💫 | spinning/dizzy |
| AJ | 🌐 | globe with meridians |
| AK | 🤾 | handball |
| AL | 📕 | closed red book |
| AM | 📖 | open book |
| AN | ♻️ | recycling |
| AO | 🔞 | no one under 18 |
| AP | 🚫 | prohibited |
| AQ | ⛔ | no entry |
| AR | 🚭 | no smoking |
| AS | no-U-turn sign | no U-turn |
| AT | 👀 | eyes |
| AU | 〰️ | wavy line |
| AV, CY | 🔓 | open/unlocked lock |
| AW | 🔐 | locked with key |
| AX | 🖤 | black heart |
| AY | 💓 | beating heart |
| AZ | 💘 | heart with arrow |
| BA | ✌️ | victory hand |
| BB | 👌 | OK hand |
| BC | 🙅 | “no” gesture |
| BD | 🤝 | handshake |
| BE | 🕗 | eight o’clock |
| BF | 🕧 | twelve-thirty |
| BG | ⌛ | hourglass |
| BH | 🕚 | eleven o’clock |
| BI | 🕙 | ten o’clock |
| BJ | ⌚ | watch |
| BK | 🕒 | three o’clock |
| BL | 🐾 | animal tracks / paw prints |
| BM | 👣 | footprints |
| BN, CC | 🥉 | third place / bronze medal |
| BO | 🔍 | magnifying glass |
| BP | 👓 | glasses |
| BQ | 🗣️ | speaking head |
| BR | 🚇 | underground train / metro |
| BS | ⬛ | black square |
| BT | 📥 | inbox tray |
| BU | 📫 | mailbox |
| BV | 🏁 | chequered flag |
| BW | 🍪 | cookie/cake |
| BX | 🎂 | birthday cake |
| BY | 🔵 | blue circle |
| BZ | ⚫ | black circle |
| CA | 🔴 | red circle |
| CB | 🕵️ | detective/spy |
| CD | ☔ | umbrella with raindrops |
| CE | ⛱️ | umbrella on ground |
| CF | 🚷 | no pedestrians |
| CG | 📏 | ruler |
| CH | 📐 | triangular ruler |
| CI | ⛵ | boat/sailboat |
| CJ | 🚤 | speedboat |
| CK | 🗺️ | world map |
| CL | ▲ | black triangle |
| CM | 💌 | love letter |
| CN, CZ | → | east / right arrow |
| CO, DA | ↗ | northeast / upper-right arrow |
| CP | 🔄 | counterclockwise arrows |
| CT | 🔃 | clockwise arrows |
| CU | 👐 | open hands |
| CV | ✋ | raised open palm, fingers together |
| CW | 🙊 | not speaking / speak-no-evil |
| CX | 🙉 | not hearing / hear-no-evil |
| DC | ⏩ | fast-forward button |
| DD | ◀️ | reverse/back button |
| DE | ⏪ | fast reverse button |
| DF | ▶️ | play button |
| DG | 🔁 | repeat button |
| DH | 😎 | face with sunglasses |
| DI | 🙄 | face with eyes upward |
| DJ | 😮 | face with open mouth |
| DK | 🤐 | face with tightly closed/zippered mouth |
| DL | 🤕 | face with head bandage |
| DM | 😶 | face without mouth |
| DN | 🙃 | upside-down face |
| DO | 😭 | sobbing/loudly crying face |

Duplicate descriptions occur for:

- ←: **barat**, **tanda panah kiri**
- →: **timur**, **tanda panah kanan**
- ↖: **barat laut**, **tanda panah kiri atas**
- ↗: **timur laut**, **tanda panah kanan atas**
- ↙: **barat daya**, **tanda panah kiri bawah**
- ⏹️: **berhenti**, **tombol berhenti**
- 🔓: **gembok terbuka**, **tidak terkunci**
- 🥉: **juara ketiga**, **medali perunggu**

---

## (b) Emoji not described at all

By elimination and by analogy with the other sets, the undescribed emoji are:

| emoji | Indonesian description |
|---|---|
| 🙈 | **tidak melihat** “not seeing / see-no-evil” |
| ↘ | **tenggara** “southeast”; also **tanda panah kanan bawah** “lower-right arrow” |

---

## (c) Indonesian dictionary

| Indonesian | English |
|---|---|
| arah | direction |
| atas | above, upper |
| awan | cloud |
| bawah | below, lower, under |
| barat | west |
| barat daya | southwest |
| barat laut | northwest |
| belas | teen, as in *delapan belas* “eighteen” |
| berbicara | speak |
| berdansa | dance |
| berdebar-debar | beat, throb |
| berenang | swim |
| bergelombang | wavy |
| berhenti | stop |
| berjalan | walk |
| berputar-putar | spin, turn round and round |
| biru | blue |
| bola | ball |
| bola dunia | globe |
| buku | book |
| cepat | fast |
| cinta | love |
| dansa | dance |
| daur ulang | recycling |
| daya | power; in *barat daya* = southwest component |
| delapan | eight |
| delapan belas | eighteen |
| dengan | with |
| di | in, at, on; also passive prefix in other words |
| di bawah | under, below |
| dilarang | forbidden, prohibited |
| diperban | bandaged |
| dua | two |
| dua belas | twelve |
| dunia | world |
| garis | line |
| gelombang | wave |
| gembok | padlock |
| hati | heart |
| hewan | animal |
| hitam | black |
| hujan | rain |
| isyarat | gesture, sign |
| jabat tangan | handshake |
| jalan | walk, road |
| jam | clock, hour |
| jam pasir | hourglass |
| jam tangan | wristwatch |
| jarum jam | clock hand; clockwise direction |
| jari | finger |
| jejak | track, footprint |
| juara | winner, champion |
| kaca | glass |
| kaca pembesar | magnifying glass |
| kacamata | glasses |
| kaki | foot, leg |
| kanan | right |
| kebalikan | opposite, reverse |
| kepala | head |
| kereta | train |
| kereta bawah tanah | underground train, metro |
| ketiga | third |
| kiri | left |
| kotak | box, square |
| kotak-kotak | chequered |
| kotak masuk | inbox |
| kotak surat | mailbox |
| kue | cake, cookie |
| kunci | key; lock |
| laut | sea; in compass words = north component |
| lingkaran | circle |
| masuk | enter |
| mata | eye |
| mata-mata | spy, detective |
| maju | forward |
| medali | medal |
| melihat | see |
| mendengar | hear |
| merah | red |
| meridian | meridian |
| merokok | smoke |
| mulut | mouth |
| mundur | backward, reverse |
| oke | OK |
| panah | arrow |
| pasir | sand |
| payung | umbrella |
| pejalan kaki | pedestrian |
| pembesar | enlarger, magnifier |
| penggaris | ruler |
| perahu | boat |
| perban | bandage |
| perunggu | bronze |
| peta | map |
| peta dunia | world map |
| putar | turn, rotate, play |
| putar balik | turn back, U-turn |
| rapat | tight, close together |
| searah | in the same direction |
| sebelas | eleven |
| segitiga | triangle |
| sepuluh | ten |
| surat | letter, mail |
| tanah | ground, earth |
| tanda | sign, mark |
| tangan | hand |
| tahun | year |
| telapak tangan | palm |
| tenggara | southeast |
| terbalik | upside down |
| terbuka | open |
| terkunci | locked |
| terpanah | pierced/shot by arrow |
| tersedu-sedu | sobbing |
| tertutup | closed |
| tetesan | drops |
| tidak | not |
| timur | east |
| timur laut | northeast |
| tombol | button |
| tiga | three |
| tiga puluh | thirty |
| ulang, ulangi | repeat |
| wajah | face |
| yang | which, that |

---

## (d) Short grammar of Indonesian from the data

1. **Noun phrases are head-first.**  
   The main noun comes first, modifiers follow:
   - **hati hitam** = heart black = “black heart”
   - **lingkaran merah** = circle red = “red circle”
   - **bola dunia** = ball world = “globe”
   - **peta dunia** = map world = “world map”
   - **jam tangan** = clock hand = “watch”

2. **Adjectives and colours follow nouns.**
   - **kotak hitam** “black square”
   - **lingkaran biru** “blue circle”
   - **buku merah tertutup** “closed red book”

3. **Prepositions:**
   - **dengan** = “with”:  
     **payung dengan tetesan hujan** “umbrella with raindrops”
   - **di** = “in/on/at”:  
     **payung di tanah** “umbrella on the ground”
   - **di bawah** = “under”:  
     **di bawah delapan belas tahun dilarang** “under eighteen years prohibited”

4. **Relative/linking word _yang_.**
   Used before a modifying phrase:
   - **hati yang berdebar-debar** “heart that is beating”
   - **hati yang terpanah cinta** “heart pierced by love”

5. **Negation and prohibition.**
   - **tidak** = ordinary “not”:  
     **tidak bicara** “not speak”, **tidak mendengar** “not hear”
   - **dilarang** = “forbidden/prohibited”:  
     **dilarang merokok** “no smoking”, **dilarang masuk** “no entry”

6. **Important prefixes.**
   - **ber-** forms intransitive/activity verbs:  
     **berdansa**, **berenang**, **berjalan**, **berbicara**
   - **meN-** forms active verbs:  
     **mendengar**, **melihat**, **merokok**
   - **di-** forms passives/resultatives:  
     **dilarang**, **diperban**
   - **ter-** marks state/result:  
     **terbuka**, **terkunci**, **terbalik**, **terpanah**
   - **peN-** forms agent/instrument nouns:  
     **penggaris** “ruler”, **pembesar** “magnifier”, **pejalan kaki** “pedestrian”
   - **ke-** forms ordinals:  
     **ketiga** “third”

7. **Reduplication** can mark repetition, intensity, or patterned meaning:
   - **berputar-putar
# iol_team_2018 — Team Contest — Mẽbêngôkre, Xavante and Krĩkatí

**Agents:** openai/gpt-5.5  
**Judge:** openai/gpt-5.5  
**Format:** answer  

## Score

The submitted “answer” contains no actual problem solution (only an API response object with an empty `output` field). Therefore there are no correspondences, matches, translations, or explanations to grade.

- **(a) Xavante–Mẽbêngôkre correspondences:** 0 points — no correspondences provided.
- **(b1) Matching questions and answers:** 0 points — no matches provided.
- **(b2) Translations into English:** 0 points — no translations provided.
- **(c) Translations into English:** 0 points — no translations provided.
- **(d) Translations into Xavante:** 0 points — no translations provided.

TOTAL: 0/100

---

## Answer

{'background': False, 'completed_at': 1781885373, 'created_at': 1781885373, 'error': None, 'frequency_penalty': 0, 'id': 'resp_24328ec3-7cc7-42bc-87f8-faa6e0136bee', 'incomplete_details': None, 'instructions': None, 'max_output_tokens': 8192, 'max_tool_calls': None, 'metadata': {}, 'model': 'openai/gpt-5.5', 'object': 'response', 'output': [], 'parallel_tool_calls': True, 'presence_penalty': 0, 'previous_response_id': None, 'prompt_cache_key': None, 'reasoning': None, 'safety_identifier': None, 'service_tier': 'default', 'status': 'completed', 'store': True, 'temperature': 1, 'text': {'format': {'type': 'text'}}, 'tool_choice': 'auto', 'tools': [], 'top_logprobs': 0, 'top_p': 1, 'truncation': '', 'usage': {'cost': {'currency': 'USD', 'input_cost': 0.04894, 'output_cost': 0.24576, 'total_cost': 0.2947}, 'input_tokens': 9787, 'input_tokens_details': {'cached_tokens': 0}, 'output_tokens': 8192, 'output_tokens_details': {'reasoning_tokens': 8192}, 'total_tokens': 17979}, 'user': None}
# iol_team_2019 — Team Contest — Rhythmic Gymnastics

**Agents:** openai/gpt-5.5  
**Judge:** openai/gpt-5.5  
**Format:** answer  

## Score

### Grading basis
I treated the **29 numbered gaps, 49–77, as equal sub-parts**, since the official solution gives one answer per numbered item. Thus each item is worth \(100/29 \approx 3.45\) points. For score-only items, the mark must match the official mark.

---

## A. Gaps 49–56  
**Team answer:** no reconstruction attempted.  
**Official:** full answers required for all 8 items.

**Score:** 0/8 items = **0.0/27.6**

Brief justification: The team explicitly states that these cannot be reconstructed, so no credit can be awarded against the official solution.

---

## B. Gaps 57–77  

| No. | Team | Official | Result |
|---:|---:|---:|:--|
| 57 | 0.4 | 0.4 | correct |
| 58 | 0.2 | 0.2 | correct |
| 59 | 0.2 | 0.2 | correct |
| 60 | 0.3 | 0.3 | correct |
| 61 | 0.7 | 0.9 | wrong |
| 62 | 0.6 | 0.4 | wrong |
| 63 | 0.3 | 0.2 | wrong |
| 64 | 0.2 | 0.2 | correct |
| 65 | 0.3 | 0.3 | correct |
| 66 | 0.5 | 0.5 | correct |
| 67 | 0.3 | 0.3 | correct |
| 68 | 0.4 | 0.4 | correct |
| 69 | 0.4 | 0.4 | correct |
| 70 | 0.6 | 0.4 | wrong |
| 71 | 0.5 | 0.8 | wrong |
| 72 | 0.3 | 0.4 | wrong |
| 73 | 0.5 | 0.5 | correct |
| 74 | 0.3 | 0.5 | wrong |
| 75 | 0.2 | 0.2 | correct |
| 76 | 0.4 | 0.4 | correct |
| 77 | 0.4 | 0 / — | wrong |

Correct: **13/21**

**Score:** \(13 \times 100/29 = 44.8\) points, equivalently **44.8/72.4** for this section.

---

## C. Scoring principles
No separate official-credit section is given for explanatory principles. The principles stated are partially reasonable but too inaccurate to rescue the wrong numerical answers, especially for risk elements and body difficulties.

**Score impact:** no additional credit.

---

TOTAL: 44.8/100

---

## Answer

## Final Team Answer Sheet

### A. Missing symbolic gaps 49–56

The symbolic notations/images needed for gaps **49–56** are not present in the supplied text, so these gaps cannot be reconstructed from the information shown.

---

### B. Completed scores for gaps 57–77

| No. | Score |
|---:|---:|
| 57 | 0.4 |
| 58 | 0.2 |
| 59 | 0.2 |
| 60 | 0.3 |
| 61 | 0.7 |
| 62 | 0.6 |
| 63 | 0.3 |
| 64 | 0.2 |
| 65 | 0.3 |
| 66 | 0.5 |
| 67 | 0.3 |
| 68 | 0.4 |
| 69 | 0.4 |
| 70 | 0.6 |
| 71 | 0.5 |
| 72 | 0.3 |
| 73 | 0.5 |
| 74 | 0.3 |
| 75 | 0.2 |
| 76 | 0.4 |
| 77 | 0.4 |

---

### C. Scoring principles used

- Ordinary apparatus difficulties are valued by the number and strength of apparatus criteria, such as: without hands, outside visual control, under the leg, while on the floor, during rotation, etc.
- Risk elements with a large throw are scored roughly as:
  - 0.2 for two full rotations;
  - +0.1 for each extra full 360° rotation;
  - +0.1 for change of level/axis;
  - +0.1 for each apparatus criterion at throw, catch, or bounce.
  - Extra 180° rotations do not add value.
- Leaps, balances, and rotations follow fixed difficulty tables; for pivots, only complete extra 360° rotations increase the value.
# iol_team_2021 — Team Contest — Garífuna, Lokono and Kari'ña

**Agents:** openai/gpt-5.5  
**Judge:** openai/gpt-5.5  
**Format:** answer  

## Score

(a) **24/24**  
All marked sentence correspondences 39–62 match the official solution exactly.

(b) **12.5/16**  
Most translations are correct. Main losses:  
- **Háluaha háfuridun óuchaha haruga** mistranslated: should be “They’re trying to go out and fish tomorrow,” not “come back from fishing.”  
- **Ariha hamutina súdara** reversed subject/object: should be “The police saw me.”  
- **¿Ka abu ludin?** should be “With whom did he come?”  
- **¿Ka biribai?** should be “What is your name?”  
Several other answers are acceptable with minor wording differences.

(c) **7.5/12**  
Some forms are correct or close, but several have important grammatical errors:  
- **liri** was needed instead of **tiri** for “your father’s name” and “this man’s name.”  
- Negative “see” forms are not quite correct.  
- **bumutina** was needed for “you killed me,” not **bamutina**.  
- Final sentence should use **póupoutu le** and the correct negative seeing form.  
“This broom is ours” is correct.

(d) **9.6/12**  
Most Lokono correspondences are correct, but **dike** and **donkon** were swapped:  
- official: **dike = ear**, **donkon = to sleep**.  
The sound change is also wrong: official answer is **m > n**, not **r > d**.

(e) **3/14**  
This section is largely incomplete. Some isolated correspondences are correct, e.g. **wügüri/wokory = man**, **bui/amoro = yousg**, **kodibio/tonoro/dunuru = bird**, **horhorho = earth**, **bubada = your nail/claw**, **lígiri/lushiri = his nose**.  
However, most required table cells are missing, and several proposed correspondences are wrong, e.g. **woryi** is “woman,” not “man”; **gimara** is “arrow,” not “moon”; **núgudi/nǘgüra** are not “my liver/liver.”

(f) **12/14**  
Part (i) is completely correct.  
Part (ii): 14 and 15 are correct; 16 is wrong — official: “The stones are on the ground.”  
Part (iii): grammar is mostly right, but **wokory** is Kari’ña, not Lokono; Lokono “man” is **wadili**. Also **Wamithadafa** and **Nashimakafa** were required, not the submitted forms.

(g) **7.5/8**  
Very strong vocabulary list. Nearly all are correct. Main issues:  
- **áluaha** should be “to look for,” not “come/arrive.”  
- **ayawa = to cry** was omitted.  
- **uagu** should be “for” in the official list; “about/on” is only partially acceptable.

**TOTAL: 76/100**

---

## Answer

## (a)

39. **A Y**  
40. **J**  
41. **I**  
42. **A O**  
43. **Q**  
44. **T**  
45. **H**  
46. **G**  
47. **B D**  
48. **B E**  
49. **R**  
50. **Y**  
51. **A G**  
52. **A P**  
53. **B J**  
54. **X**  
55. **M**  
56. **A D**  
57. **U**  
58. **Z**  
59. **A E**  
60. **A A**  
61. **A B**  
62. **K**

---

## (b)

- **Ariengatu núguchu nun nabuidunu muna.** — My mother told me to sweep the house.  
- **Hísieti uwi lun.** — He likes meat.  
- **Nani guríara to.** — This boat is mine.  
- **¿Ka babuserubai?** — What do you want?  
- **Ibidieti nun átirila irumu tau.** — I don’t know how old she is.  
- **Yumbuitibu hamuga anhabu giara.** — You would come if you could.  
- **Áfarati búguchi aban ounli.** — Your father killed a dog.  
- **Háluaha háfuridun óuchaha haruga.** — They will come back from fishing tomorrow.  
- **Nidin aríahai úduraü.** — I went to look for fish.  
- **Nuguya mabuseruntina nuádigimari.** — I myself do not like/want my work.  
- **¿Ka tiri lani señora?** — What is his wife’s name?  
- **Ariha hamutina súdara.** — I see the policemen/soldiers.  
- **¿Ka abu ludin?** — What did he go/leave with?  
- **¿Ka biribai?** — What did you see?  
- **Wagía madüguntiwa guríara.** — We did not make a boat.  
- **Máfaru numutu hiñaru to.** — I did not kill this woman.

---

## (c)

- I don’t know your father’s name.  
  **Ibidieti tiri búguchi nun.**

- They don’t see this place.  
  **Marihatiñu fulasu le.**

- Youpl don’t know this man’s name.  
  **Ibidieti tiri eyeri le hun.**

- This broom is ours.  
  **Wani abuidagülei le.**

- You didn’t kill me.  
  **Máfaru bamutina.**

- We don’t see this boat.  
  **Marihatiwa guríara to.**

---

## (d)

### i.

- **aba** — one  
- **biama / bian** — two  
- **bui** — yousg  
- **dike** — to sleep  
- **diki** — after  
- **donkon** — ear  
- **dukhun** — to see  
- **duna** — arm  
- **farun** — to kill  
- **hiyaro** — woman  
- **khabo** — hand  
- **kuthu** — granny  
- **lira** — that one, masc.  
- **tora** — that one, fem.

### ii.

Earlier Lokono had **\*r**, which changed to **d** in modern Lokono.

---

## (e)

Confident filled cells / correspondences:

- **wokory** — man  
- **woryi** — man  
- **wügüri** — man  
- **bui** — yousg  
- **amoro** — yousg  
- **kodibio** — bird  
- **tonoro** — bird  
- **dunuru** — bird  
- **horhorho** — earth / landform  
- **bubada** — your nail/claw  
- **gimara** — moon  
- **núgudi / nǘgüra** — my liver / liver  
- **lushiri / lígiri** — his nose  
- **duna** — arm  
- **khabo** — hand  
- **kuthu** — granny  

---

## (f)

### i.

1. **B**  
2. **A**  
3. **J**  
4. **M**  
5. **E**  
6. **G**  
7. **F**  
8. **C**  
9. **I**  
10. **L**  
11. **H**  
12. **K**  
13. **D**

### ii.

14. **Lufarufa aba kabadaro tora hiyaro oma.**  
He will kill a jaguar with that woman.

15. **Hushimaku we.**  
Youpl called us.

16. **Horhorho diakoka to shibabe.**  
The landform is on top of the stone.

### iii.

N. The man will listen.  
**Li wokory kanabafa.**

O. We will laugh.  
**Wamithadufa.**

P. They will scream.  
**Nashimakufa.**

Q. There are three men here.  
**Kabun wokorynon yâka.**

---

## (g)

- **abu** — with  
- **ábuna** — sow, plant  
- **achülüra** — arrive  
- **adeira** — find  
- **adüga** — do, make, work  
- **adumureha** — talk, speak  
- **adura** — shoot  
- **áfara** — kill  
- **afeidira** — lose  
- **áfurida** — go out, leave  
- **áluaha** — come, arrive  
- **aluguraha** — sell  
- **anhein** — if, when  
- **anihein** — there is/are; have  
- **anura** — flee  
- **ariha** — see  
- **ariñaha** — tell, say, ask  
- **arüna** — arm  
- **ásura** — finish  
- **áwaha** — call  
- **bugía / buguya** — yousg  
- **ebelura** — enter  
- **eifi** — beans  
- **eiga** — eat  
- **hagía** — they  
- **halaü** — chair  
- **íchiga** — give  
- **irumu** — year  
- **ladüga** — because; doing/making  
- **ligía** — he, that one  
- **nugía / nuguya** — I  
- **ou(n)we** — die  
- **súdara** — soldier, police  
- **sun** — all, every  
- **tugía / tuguya** — she, that one fem.  
- **uagu** — about, concerning, on  
- **úduraü** — fish  
- **umadaü** — friend  
- **un / lun** — to, for  
- **wagía** — we  
- **ya** — here, there
# iol_team_2022 — Team Contest — Manchu

**Agents:** openai/gpt-5.5  
**Judge:** openai/gpt-5.5  
**Format:** answer  

## Score

Part I (a–c): **25/25**  
- (a) All correspondences are exactly correct.  
- (b) All four translations are correct; computing 1216 jin in 56 is acceptable.  
- (c) Manchu script forms are correct.

Part II (d–e): **25/25**  
- (d) All correspondences are exactly correct.  
- (e) All blanks are correctly filled. The wording for (vi) is slightly paraphrased but captures the intended meaning.

Part III (f): **22/25**  
Most answers are correct and written appropriately in Manchu script.  
- 90–92 correct.  
- 93: gives the unit price of chicken meat, but the question asks for the price of 48 liang; should be 4 qian 5 fen. Partial credit only.  
- 94–95 correct.  
- 96: the expected answer refuses to buy a sheep with bad wool; the team instead says they want to buy a good-wool sheep and gives its price. Partial credit for relevant vocabulary/price-list use, but not the correct response.  
- 97–99 correct.

Part IV (g–h): **24/25**  
- (g) All correspondences are exactly correct.  
- (h) Almost all translations are correct.  
  - 112 should be “Send me a letter”; “Give me a letter/document” loses some credit.  
  - 116 “small birds” instead of “a bird” is a minor issue.  
  - The rest are correct.

TOTAL: **96/100**

---

## Answer

## (a)

30 V, 31 L, 32 O, 33 U, 34 M, 35 T, 36 P, 37 K, 38 R, 39 B, 40 N, 41 C, 42 D, 43 E, 44 W, 45 J, 46 H, 47 X, 48 I, 49 S, 50 G, 51 A, 52 F, 53 Q.

## (b)

54. 3600 chi are equal to 2 li.  
55. From 20 shi, if one subtracts 1 shi 3 sheng, 18 shi 9 dou 7 sheng remain.  
56. If 842 jin are added to 374 jin, the result is 1216 jin.  
57. If 64 fen are multiplied by 15, one obtains 9 liang 6 qian.

## (c)

58. ᠮᠠᠨᠵᡠ ᡥᡝᡵᡤᡝᠨ  
59. ᠮᠣᠩᡤᠣ ᡨᠠᠯᠠ  
60. ᡨᡠᠮᡝᠨ ᡠᠯᠠ  
61. ᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ  
62. ᡨᠠᠩᡤᡡᡨ ᡨᠠᠴᡳᡴᡡ  
63. ᡨᡳᠶᠠᠨ ᠵᡠ ᡤᡠᡵᡠᠨ  
64. ᡥᡠᡥᡠ ᡥᠣᡨᠣᠨ  
65. ᠴᡳᠴᡳᡥᠠᡵ ᡥᠣᡨᠣᠨ  

## (d)

66 A, 67 I, 68 K, 69 F, 70 H, 71 W, 72 M, 73 G, 74 D, 75 P, 76 V, 77 R, 78 U, 79 Q, 80 E, 81 X, 82 O, 83 S, 84 T, 85 C, 86 L, 87 B, 88 N, 89 J.

## (e)

(i) The seventh, eighth and ninth months, when all kinds of things are harvested, are called autumn.  
(ii) The direction where the sun sets is called west.  
(iii) Two fifties are called hundred.  
(iv) Among all living beings created by Heaven, the most intelligent is called human.  
(v) The amount of money/silver at which buying and selling things is settled is called price.  
(vi) Very dark/blackish-blue is called black.

## (f)

90. ᠪᡝ ᡤᡝᠮᡠ ᡝᠯᡥᡝ ᠰᠠᡳᠨ᠉ ᠪᡝ ᠮᠠᠨᠵᡠ ᡤᡳᠰᡠᠨ ᡤᡳᠰᡠᡵᡝᠮᠪᡳ᠉  

91. ᠮᡝᠨᡩᡝ ᠪᡝᠯᡝ ᠶᠠᠯᡳ ᡤᡝᠮᡠ ᠪᡳ᠉  

92. ᠪᡝᠯᡝ ᠣᠴᡳ ᡧᠠᠨᠶᠠᠨ ᠪᡝᠯᡝ᠈ ᠵᠠᡳ ᠶᠠᠯᡳ ᠣᠴᡳ ᠴᠣᡴᠣ ᠶᠠᠯᡳ᠉  

93. ᠴᠣᡴᠣ ᠶᠠᠯᡳ ᠣᠴᡳ ᡝᠮᡠ ᡤᡳᠩᡤᡳᠨ ᡩᡝ ᡝᠮᡠ ᠵᡳᡥᠠ ᠰᡠᠨᠵᠠ ᡶᡠᠨ ᠮᡝᠩᡤᡠᠨ᠉  

94. ᡨᡝᡵᡝ ᡳᠯᡥᠠᠩᡤᠠ ᠰᡳᠵᡳᡤᡳᠶᠠᠨ ᡝᠮᡴᡝ ᡩᡝ ᡩᡠᡳᠨ ᠶᠠᠨ ᠮᡝᠩᡤᡠᠨ᠉  

95. ᡠᡥᡝᡵᡳ ᡩᡠᡳᠨ ᠶᠠᠨ ᠰᡠᠨᠵᠠ ᠵᡳᡥᠠ ᠮᡝᠩᡤᡠᠨ᠉  

96. ᠪᡝ ᡶᡠᠨᡳᠶᡝᡥᡝ ᠰᠠᡳᠨ ᡥᠣᠨᡳᠨ ᠪᡝ ᡠᡩᠠᡴᡳ ᠰᡝᠮᠪᡳ᠉ ᠵᡠᠸᠠᠨ ᠵᡠᠸᡝ ᠶᠠᠨ ᠮᡝᠩᡤᡠᠨ ᡩᡝ ᡠᡩᠠᠮᠪᡳ᠉  

97. ᠪᡝ ᠴᠣᠣᡥᡳᠶᠠᠨ ᠴᡳ ᠵᡳᡥᡝ ᠣᡵᡥᠣᡩᠠ ᠪᡝ ᡠᡩᠠᡴᡳ ᠰᡝᠮᠪᡳ᠉  

98. ᡨᠠᠩᡤᡡ ᠨᠠᡩᠠᠨᠵᡠ ᠪᡝ ᠪᠠᡥᠠᠮᠪᡳ᠉  

99. ᡤᡝᠮᡠᠨ ᡥᡝᠴᡝᠨ ᡳ ᠸᠠᡵᡤᡳ ᡝᡵᡤᡳ ᡩᡝ ᡥᡠᡥᡠ ᡥᠣᡨᠣᠨ ᠪᡳ᠉  

## (g)

100 C, 101 D, 102 K, 103 H, 104 A, 105 B, 106 E, 107 L, 108 F, 109 G, 110 I, 111 J.

## (h)

112. Give me a letter/document!  
113. He/that person is not an adult.  
114. It rained a little yesterday.  
115. I bought new inner clothes.  
116. Today they saw small birds on the mountain.  
117. Mother eats fish; father eats lamb/mutton.  
118. We will go to Qiqihar tomorrow; where will you all go?  
119. I lived in Beijing ten years ago.
# iol_team_2023 — Team Contest — Murrinh-patha

**Agents:** openai/gpt-5.5  
**Judge:** openai/gpt-5.5  
**Format:** answer  

## Score

(a): 0 points.  
The team provided no Murrinh-patha–English matches, instead saying the task could not be determined. This does not correspond to any of the official matching answers.

(b): 0 points.  
Official answer: **60-T-54 = fruit, vegetable, etc. noun class**.  
Team answer: “to chance upon; to come across,” which is incorrect.

TOTAL: 0/100

---

## Answer

(a) Cannot be determined from the supplied material: the actual Murrinh-patha entries/headwords are missing, and the English translations are given in arbitrary order.

(b) 60-T-54 = to chance upon; to come across.
# iol_team_2025 — Team Contest — Camling and Bantawa

**Agents:** openai/gpt-5.5  
**Judge:** openai/gpt-5.5  
**Format:** answer  

## Score

Scoring basis: I treated each answer slot equally and normalized to 100. For Part II(c) items 37–48, I generously interpreted single letters such as `N, S, ...` as intended doubled labels `NN, SS, ...` where applicable.

## Part I: 41/50 raw = 23.3/100

### (a) 31/40
Incorrect: 1, 3, 7, 8, 10, 13, 16, 29, 31.  
All others correct.

### (b) 10/10
All correct.

---

## Part II: 33/48 raw = 18.8/100

### (c) 33/48
Correct through much of the first half, but several mismatches in the middle and final block.

Incorrect: 14, 15, 16, 22, 23, 26, 27, 28, 29, 33, 39, 41, 42, 44, 48.  
The doubled-label shorthand in 37–48 was accepted where it matched the official answer.

---

## Part III: 10.5/78 raw = 6.0/100

### (d) 6/36
Correct: 6, 9, 10, 14, 23, 32.  
Most other matches are wrong.

### (e) 1.5/6
- iii correct.
- i partially correct, but gives an extra impossible object “them”.
- Others incorrect.

### (f) 1/8
No fully correct answers. Limited partial credit for answers with the right root/partial argument structure, especially vi and viii.

### (g) 0/4
No correct Bantawa forms.

### (h) 2/24
Correct:
- ii Camling: `paidacka`
- viii Bantawa: `tɨpatŋaŋnɨŋ`

All other Bantawa/Camling forms are incorrect or not close enough to the official forms.

---

TOTAL: 48/100

---

## Answer

## Part I

### (a)
1. A  
2. D  
3. G  
4. E  
5. C  
6. H  
7. F  
8. B  
9. M  
10. I  
11. L  
12. J  
13. O  
14. K  
15. P  
16. N  
17. V  
18. U  
19. R  
20. Q  
21. T  
22. W  
23. X  
24. S  
25. EE  
26. AA  
27. Z  
28. CC  
29. BB  
30. FF  
31. Y  
32. DD  
33. MM  
34. KK  
35. LL  
36. HH  
37. NN  
38. JJ  
39. II  
40. GG  

### (b)
41. VV  
42. QQ  
43. RR  
44. OO  
45. XX  
46. SS  
47. PP  
48. TT  
49. UU  
50. WW  

---

## Part II

### (c)
1. J  
2. F  
3. D  
4. I  
5. A  
6. H  
7. K  
8. G  
9. B  
10. L  
11. C  
12. E  
13. V  
14. N  
15. Q  
16. W  
17. U  
18. T  
19. X  
20. M  
21. R  
22. O  
23. P  
24. S  
25. II  
26. Z  
27. AA  
28. EE  
29. BB  
30. FF  
31. CC  
32. GG  
33. HH  
34. DD  
35. JJ  
36. Y  
37. N  
38. S  
39. R  
40. P  
41. Q  
42. O  
43. M  
44. L  
45. T  
46. V  
47. U  
48. K  

---

## Part III

### (d)
1. AA  
2. DD  
3. EE  
4. FF  
5. A  
6. B  
7. CC  
8. KK  
9. J  
10. G  
11. I  
12. F  
13. O  
14. GG  
15. N  
16. JJ  
17. G  
18. N  
19. HH  
20. BB  
21. MM  
22. JJ  
23. LL  
24. K  
25. II  
26. A  
27. II  
28. L  
29. K  
30. O  
31. D  
32. NN  
33. M  
34. H  
35. OO  
36. E  

### (e)
i. **idum** — we+ pl gave her/them  
ii. **talosumcumne** — we− pl will tell/sell yousg  
iii. **rinaci** — I/we− du/pl laughed at youdu  
iv. **tadungdi** — I will quarrel  
v. **khangucyu** — yousg looked at/saw themdu/pl  
vi. **tadungace** — youdu will quarrel  

### (f)
i. **tɨcattaŋcɨŋ** — theydu are combing themdu  
ii. **nɨseraŋ** — she/theydu/pl will kill yousg  
iii. **tɨduŋyaŋ** — yousg are quarrelling  
iv. **pɨwacu** — she gave us− du  
v. **taciŋciʔa** — theydu brought her  
vi. **nɨtaraci** — she/theydu/pl will bring/take youpl  
vii. **paraŋa** — I shouted  
viii. **iptuci** — I put themdu to sleep / I will put themdu to sleep  

### (g)
i. youdu are entering — **tɨtʰaŋyaŋcɨŋ**  
ii. I was putting thempl to sleep — **iptuŋcɨŋyaŋa**  
iii. yousg are selling her — **tɨintu**  
iv. theydu are combing themdu — **tɨcattaŋcɨŋ**  

### (h)

|  | Bantawa | Camling |
|---|---|---|
| i. we− pl will bring her | **tattumka** | **tatangika** |
| ii. she gave us− du | **pɨwacu** | **paidacka** |
| iii. we− du will come | **waca** | **taka** |
| iv. theydu will comb youpl | **nɨkʰansaci** | **khinane** |
| v. we− du killed yousg | **setniŋni** | **seine** |
| vi. we− pl quarrelled | **mɨkʰisinka** | **dungumka** |
| vii. we+ du went | **kʰatyaŋ** | **khace** |
| viii. youpl will shout at me | **tɨpatŋaŋnɨŋ** | **tapraine** |
| ix. theydu will laugh at youdu | **ɨʔittaŋcɨŋ** | **rinaci** |
| x. theypl died | **sɨya** | **sika** |
| xi. she helped her | **pʰottu** | **phloku** |
| xii. youpl will kill her | **tɨsesuci** | **takhlakine** |
