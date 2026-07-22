# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked the agent to implement four stretch challenges on top of my working music
recommender, without breaking the existing pytest suite or the CLI, and without
adding any new pip dependencies:
1. Add five advanced song features to the dataset and let the scorer optionally reward them.
2. Add multiple scoring modes using a proper design pattern.
3. Add a diversity penalty so one artist/genre can't dominate the results.
4. Render the recommendations as a clean ASCII summary table.

**Prompts used:**

- "Add 5 new columns to data/songs.csv (popularity, release_decade, instrumentalness,
  liveness, language) for all 18 rows, update load_songs() field parsing, and extend
  score_song() to optionally reward the new features only when the matching key is
  present in user_prefs so my existing tests still pass."
- "Refactor scoring into one weighted function and build a Strategy pattern with
  Genre-First, Mood-First, and Energy-Focused strategies that each supply different
  weights. Keep score_song() working with the default 2.0/1.0/1.0 weights."
- "Add a diversity option to recommend_songs() that greedily penalizes candidates
  sharing an artist or genre with an already-picked song, and note it in the reasons."
- "Add a pure-stdlib ASCII table to main.py with Rank/Title/Artist/Genre-Mood/Score/Reasons
  columns (aligned, word-wrapped reasons) and wire main.py to also show an alternate
  strategy and the diversity option."

**What did the agent generate or change?**

- `data/songs.csv` — added the 5 new columns to all 18 rows with values consistent
  with each song (e.g. classical/ambient/lofi get high instrumentalness).
- `src/recommender.py` — extended `INT_FIELDS`/`FLOAT_FIELDS`; added a shared
  `_weighted_score()` helper; refactored `score_song()` to delegate to it; added the
  `ScoringStrategy` base class plus `Balanced/GenreFirst/MoodFirst/EnergyFocused`
  strategies and a `STRATEGIES` registry; added `_diversified_pick()` and new
  `strategy`/`diversify` parameters on `recommend_songs()`.
- `src/main.py` — added `render_table()` and `_wrap()` helpers, a Challenge 1 profile
  that sets the optional keys, and demo runs for the Energy-Focused strategy and the
  diversity option.

**What did you verify or fix manually?**

- Ran `python3 -m pytest` — 2 passed, confirming the OOP `Recommender` path was
  unaffected because it only feeds genre/mood/energy into the scorer.
- Ran `python3 -m src.main` and eyeballed the tables: confirmed columns align even
  when the Reasons column wraps across multiple physical lines.
- Confirmed the diversity penalty actually reorders results: "Gym Hero" dropped from
  2.97 to 1.49 for sharing the pop genre with the already-picked "Sunrise City",
  falling below "Rooftop Lights".
- Confirmed the optional features only fire when their key is present, so the original
  five baseline profiles score exactly as before.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The Strategy pattern. Each "scoring mode" (Genre-First, Mood-First, Energy-Focused,
and the default Balanced) is an interchangeable strategy that the recommender can
swap in at call time.

**How did AI help you brainstorm or implement it?**

I wanted three scoring modes but didn't want to copy-paste the scoring formula three
times. The agent suggested Strategy over Factory/Template Method because the modes
differ only in their *weights*, not in their algorithm. The key refactor it proposed
was to extract one parameterized scorer, `_weighted_score(user_prefs, song, weights)`,
so every strategy is just a named bundle of weights pointing at the same formula —
this keeps the recipe in exactly one place and makes adding a new mode a two-line change.

**How does the pattern appear in your final code?**

In `src/recommender.py`: `ScoringStrategy` is the base class exposing
`score(self, user_prefs, song) -> (float, list[str])`, and `BalancedStrategy`,
`GenreFirstStrategy`, `MoodFirstStrategy`, and `EnergyFocusedStrategy` are the concrete
strategies, each overriding only the `weights` dict. `recommend_songs()` takes an
optional `strategy` argument and calls `strategy.score(...)`, defaulting to the
module-level `score_song()` (balanced weights) when none is given, so the tests and the
OOP `Recommender` keep their original behavior.
