# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFinder 1.0**

A lightweight, explainable music recommender that scores every song in a small
catalog against a listener's stated taste and returns the best matches with a
plain-language reason for each pick.

---

## 2. Intended Use  

VibeFinder is built for **classroom exploration**, not production use. It takes
a single listener's stated preferences — a favorite genre, a favorite mood, and
a target energy level — and returns the top few songs from an 18-track catalog,
each with a short explanation of *why* it was chosen.

Assumptions it makes about the user:

- The user can name one favorite genre, one favorite mood, and one energy level.
- Those three preferences are internally consistent (see Limitations — this
  assumption breaks down for conflicting tastes).
- The user wants transparency (every recommendation is explained) more than
  scale or novelty.

It is a teaching artifact for understanding how a scoring "judge" turns
preferences into ranked results, not a real streaming recommender.

---

## 3. How the Model Works  

Think of it like a judge handing out points to every song in a small record bin.

Each song can earn up to **4 points**:

- **2 points** if the song's genre is exactly your favorite genre.
- **1 point** if the song's mood is exactly your favorite mood.
- **up to 1 point** for energy, based on how close the song's energy is to the
  energy level you asked for. A perfect energy match earns the full point; the
  further away it is, the less it earns (but it never loses points).

Every song gets a total score, the songs are sorted highest-first, and the top 5
are shown. Alongside each song, the judge lists the reasons it earned its points
("genre match", "mood match", "energy fit"), so a listener can see the logic.

Compared to the starter logic, the working recipe keeps genre as the single
strongest signal (worth as much as mood and energy combined) because genre is
usually the clearest expression of taste, while energy is treated as a "close is
good enough" dial rather than an all-or-nothing match.

---

## 4. Data  

The catalog is `data/songs.csv`, containing **18 songs**. Each song lists an id,
title, artist, genre, mood, energy, tempo, valence, danceability, and
acousticness.

**Genre distribution (this matters — see Limitations):**

| Count | Genres |
|-------|--------|
| 3 | lofi |
| 2 | pop |
| 1 each | rock, ambient, jazz, synthwave, indie pop, hip hop, classical, edm, reggae, metal, country, funk, blues |

So only **lofi (3) and pop (2)** have more than one song; the other **13 genres
have exactly one song each**.

Moods are similarly spread thin: happy and chill appear a couple of times, but
most moods (intense, sad, euphoric, aggressive, nostalgic, playful, etc.) are
attached to just one song.

Nothing was added or removed from the starter dataset. Large parts of real
musical taste are missing: there is no way to express *disliking* something, no
sub-genres, no artist affinity, and no notion that some moods (e.g. "sad") are
almost always paired with certain energy levels.

---

## 5. Strengths  

- **Consistent, mainstream profiles work great.** When a user's genre, mood, and
  energy naturally go together, VibeFinder nails it. The "Chill Lofi" profile
  (lofi / chill / energy 0.35) returns *Library Rain* with a perfect **4.00 /
  4.0** — genre, mood, and energy all line up exactly.
- **Every pick is explainable.** The per-song reason list makes it obvious why a
  song ranked where it did, which is ideal for teaching.
- **Energy behaves sensibly as a dial.** Because energy gives partial credit for
  closeness, two profiles that both want high energy (Pop vs Rock) correctly
  surface an overlapping set of high-energy songs, then use genre to
  personalize the #1 slot.
- **Well-populated genres give real depth.** For lofi and pop — the only genres
  with multiple songs — the top of the list is filled with genuinely relevant
  matches rather than filler.

---

## 6. Limitations and Bias 

The clearest weakness is **genre over-domination combined with a sparse
catalog**. Genre is worth 2 of the 4 available points — half the maximum — yet
**13 of the 15 genres in the catalog have only a single song** (only lofi with 3
and pop with 2 have more). This means that for a user whose favorite genre is a
"singleton" genre, VibeFinder can surface *at most one* genuinely
genre-matched song; every remaining slot in their top 5 is filled by songs from
unrelated genres that merely happen to sit near the requested energy level. This
is visible in the "Deep Intense Rock" profile: *Storm Runner* is the only rock
song, so it wins #1 with 3.99, but slots #2–#5 are pop, edm, pop, and metal
tracks chosen almost purely on energy fit (scores collapse from 3.99 to ~0.92).
The result is a **filter-bubble-shaped list with a hard floor**: one strong match
on top, then a generic energy-ranked tail, and users of niche genres are
systematically worse served than lofi/pop users purely because of dataset
imbalance. A second bias is that the model **cannot reconcile conflicting
preferences** and lets genre override emotional intent: the adversarial "sad but
high-energy" profile pushes the catalog's only actually-sad song (*Rainy Bar
Blues*) down to #3, behind two upbeat pop songs that match genre and energy but
are the emotional opposite of what was asked for. Finally, the model considers
only genre, mood, and energy — it ignores valence, tempo, danceability, and
acousticness that are already in the data, so it has no way to tell a listener
that a "high-energy" song is also sad-sounding (low valence).

---

## 7. Evaluation  

### Profiles tested

I stress-tested VibeFinder against **five distinct profiles**, including two
deliberately adversarial / edge-case profiles, and printed the top 5 for each.
The three "normal" profiles cover well-populated and niche genres; the two edge
cases probe conflicting preferences and a combination that does not exist in the
data.

What I looked for: whether internally-consistent profiles produce sensible,
on-theme lists; how the ranking degrades for niche genres; and how the model
behaves when no song can satisfy all three preferences at once.

### Terminal output (baseline recipe: genre 2.0 / mood 1.0 / energy 1.0)

**Profile 1 — High-Energy Pop (pop / happy / 0.90)**

```
1. Sunrise City — Neon Echo
   Genre/Mood: pop / happy
   Score: 3.92 / 4.0
     • genre match: pop (+2.0)
     • mood match: happy (+1.0)
     • energy fit: 0.92 (target 0.90 vs 0.82) (+0.92)
2. Gym Hero — Max Pulse            (pop / intense)      Score: 2.97 / 4.0
3. Rooftop Lights — Indigo Parade  (indie pop / happy)  Score: 1.86 / 4.0
4. Storm Runner — Voltline         (rock / intense)     Score: 0.99 / 4.0
5. Pulse Reactor — Voltage Kids    (edm / euphoric)     Score: 0.94 / 4.0
```

**Profile 2 — Chill Lofi (lofi / chill / 0.35)**

```
1. Library Rain — Paper Lanterns
   Genre/Mood: lofi / chill
   Score: 4.00 / 4.0
     • genre match: lofi (+2.0)
     • mood match: chill (+1.0)
     • energy fit: 1.00 (target 0.35 vs 0.35) (+1.00)
2. Midnight Coding — LoRoom        (lofi / chill)    Score: 3.93 / 4.0
3. Focus Flow — LoRoom             (lofi / focused)  Score: 2.95 / 4.0
4. Spacewalk Thoughts — Orbit Bloom(ambient / chill) Score: 1.93 / 4.0
5. Coffee Shop Stories — Slow Stereo(jazz / relaxed) Score: 0.98 / 4.0
```

**Profile 3 — Deep Intense Rock (rock / intense / 0.90)**

```
1. Storm Runner — Voltline
   Genre/Mood: rock / intense
   Score: 3.99 / 4.0
     • genre match: rock (+2.0)
     • mood match: intense (+1.0)
     • energy fit: 0.99 (target 0.90 vs 0.91) (+0.99)
2. Gym Hero — Max Pulse            (pop / intense)     Score: 1.97 / 4.0
3. Pulse Reactor — Voltage Kids    (edm / euphoric)    Score: 0.94 / 4.0
4. Sunrise City — Neon Echo        (pop / happy)       Score: 0.92 / 4.0
5. Ironclad — Blackforge           (metal / aggressive)Score: 0.92 / 4.0
```

**Profile 4 — ADVERSARIAL: Sad but High-Energy (pop / sad / 0.90)** — a
contradiction, because the only sad song in the catalog is low-energy.

```
1. Gym Hero — Max Pulse
   Genre/Mood: pop / intense
   Score: 2.97 / 4.0
     • genre match: pop (+2.0)
     • energy fit: 0.97 (target 0.90 vs 0.93) (+0.97)
2. Sunrise City — Neon Echo        (pop / happy)    Score: 2.92 / 4.0
3. Rainy Bar Blues — Delta Mae     (blues / sad)    Score: 1.49 / 4.0
     • mood match: sad (+1.0)
     • energy fit: 0.49 (target 0.90 vs 0.39) (+0.49)
4. Storm Runner — Voltline         (rock / intense) Score: 0.99 / 4.0
5. Pulse Reactor — Voltage Kids    (edm / euphoric) Score: 0.94 / 4.0
```

**Profile 5 — EDGE CASE: Classical Euphoric (classical / euphoric / 0.50)** — a
genre+mood combo that does not co-occur in the data.

```
1. Winter Elegy — Aria Soltane
   Genre/Mood: classical / melancholic
   Score: 2.80 / 4.0
     • genre match: classical (+2.0)
     • energy fit: 0.80 (target 0.50 vs 0.30) (+0.80)
2. Pulse Reactor — Voltage Kids    (edm / euphoric)     Score: 1.54 / 4.0
     • mood match: euphoric (+1.0)
3. Dusty Backroads — Hank Willow   (country / nostalgic)Score: 0.99 / 4.0
4. Island Time — Golden Tide       (reggae / uplifting) Score: 0.95 / 4.0
5. Midnight Coding — LoRoom        (lofi / chill)       Score: 0.92 / 4.0
```

### Profile-pair comparisons (plain language)

- **High-Energy Pop vs Chill Lofi:** Both get their favorite genre at the top,
  but Chill Lofi earns a *perfect* 4.00 while High-Energy Pop tops out at 3.92.
  Why: there happens to be a lofi song sitting at exactly the requested energy
  (0.35), so all three preferences line up perfectly, whereas no pop song sits
  exactly at energy 0.90. A perfect score requires the catalog to contain a song
  that matches on all three dials at once.
- **Deep Intense Rock vs High-Energy Pop:** These two lists overlap a lot — Storm
  Runner, Gym Hero, Pulse Reactor, and Sunrise City all show up in both. Why:
  both listeners asked for very high energy (~0.9), and energy is a shared dial
  that pulls the same loud songs toward the top for everyone; the favorite genre
  is what breaks the tie and decides who lands at #1 (rock's Storm Runner vs
  pop's Sunrise City).
- **Chill Lofi vs Adversarial Sad-but-High-Energy:** Chill Lofi asks for things
  that naturally go together (chilled-out mood *and* low energy), so it gets a
  flawless match. The adversarial profile asks for a sad mood *and* high energy,
  which almost never happens in real music — so no song can satisfy both, and the
  #1 result is an intense pop workout track that matches neither the mood nor the
  feeling the listener wanted. This shows the model has no concept that some
  moods and energy levels are contradictory.
- **Adversarial vs Classical Euphoric:** Both are "impossible" profiles, but they
  fail in different ways. The adversarial pop profile still finds genre-matched
  pop songs to put on top (pop has 2 songs), so it at least stays in the right
  genre. The classical profile has only *one* classical song, so #1 is that lone
  track (with the wrong mood) and everything below it is unrelated filler picked
  on energy alone. The failure mode depends on how many songs the requested genre
  actually has.

### Weight experiment: what I changed and whether it helped

I ran a controlled experiment: I **doubled the energy weight (1.0 → 2.0) and
halved the genre weight (2.0 → 1.0)**, keeping mood at 1.0. The maximum score
stays **4.0** (1.0 genre + 1.0 mood + 2.0 energy = 4.0), so the scale is still
valid and comparable.

Observations vs the baseline:

- For the three *consistent* profiles (Pop, Lofi, Rock) the **top-5 ordering did
  not change at all** — only the absolute scores compressed, because
  energy-only songs jumped from ~0.9 to ~1.9 points while genre-matched songs
  gained less. Genre-matched songs became *relatively* less dominant.
- The one real ranking flip was in the **adversarial "sad but high-energy"**
  profile: *Storm Runner* (pure energy fit) and *Rainy Bar Blues* (the actual
  sad song) **swapped places** (#4 ↔ #3). Boosting energy pushed the genuinely
  sad match *down*, making the emotionally-wrong result even stronger.

**Verdict: the change made results *different*, not *more accurate*.** Because
most genres have only one song, genre is doing important "keep it on theme" work;
weakening it mostly flattened the scores and, in the adversarial case, actively
demoted the one song that matched the user's mood. I therefore **reverted to the
original recipe (genre 2.0 / mood 1.0 / energy 1.0)**, which is the finalized
committed logic.

### What surprised me

The perfect 4.00 for Chill Lofi was satisfying, but the surprise was how quickly
scores collapse below the #1 or #2 spot for niche-genre users — the tail of the
list is essentially "nearest energy" rather than "similar music," which is a
direct artifact of the dataset having one song per genre.

---

## 8. Future Work  

- **Use the features already in the data.** Valence, tempo, danceability, and
  acousticness are loaded but unused; scoring on them would stop "high-energy"
  from surfacing emotionally-wrong songs.
- **Detect contradictory preferences.** Warn the user (or down-weight) when a
  requested mood and energy rarely co-occur, as in the sad/high-energy case.
- **Balance the catalog or diversify the top-k.** Add more songs per genre, or
  add a diversity rule so niche-genre users don't get an all-energy filler tail.
- **Soften genre matching.** Allow near-genre credit (e.g. pop ≈ indie pop) so a
  single-song genre isn't a dead end.
- **Model dislikes and artist affinity** to capture more of real taste.

---

## 9. Personal Reflection  

Building and stress-testing VibeFinder made it concrete that a recommender is
only as good as the interaction between its *weights* and its *data*. The scoring
recipe looked reasonable in isolation, but the moment I counted genres I could
see that giving genre half the points, in a catalog where most genres have one
song, guarantees a filter-bubble tail for anyone outside lofi or pop. The
adversarial profiles were the most educational part: watching the system
confidently recommend an upbeat pop song to a "sad" listener showed how a model
with no notion of contradiction will always return *something* that looks
mathematically optimal while being obviously wrong to a human. It changed how I
read the "Because you listened to…" rows in real apps — I now assume there is a
simple weighted judge underneath, and that its blind spots come as much from the
catalog it draws on as from the formula itself.
