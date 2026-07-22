# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Explain your design in plain language.

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
- What information does your `UserProfile` store
- How does your `Recommender` compute a score for each song
- How do you choose which songs to recommend

You can include a simple diagram or bullet list if helpful.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Running `python -m src.main` with the default profile (`favorite_genre=pop`,
`favorite_mood=happy`, `target_energy=0.80`) produces the following output.
Each song shows its final score (out of a maximum of 4.0) and the specific
reasons that earned those points:

```
===================================================
Top 5 for profile: pop / happy (target energy 0.80)
===================================================

1. Sunrise City — Neon Echo
   Genre/Mood: pop / happy
   Score: 3.98 / 4.0
   Reasons:
     • genre match: pop (+2.0)
     • mood match: happy (+1.0)
     • energy fit: 0.98 (target 0.80 vs 0.82) (+0.98)

2. Gym Hero — Max Pulse
   Genre/Mood: pop / intense
   Score: 2.87 / 4.0
   Reasons:
     • genre match: pop (+2.0)
     • energy fit: 0.87 (target 0.80 vs 0.93) (+0.87)

3. Rooftop Lights — Indigo Parade
   Genre/Mood: indie pop / happy
   Score: 1.96 / 4.0
   Reasons:
     • mood match: happy (+1.0)
     • energy fit: 0.96 (target 0.80 vs 0.76) (+0.96)

4. Groove Machine — The Funk Collective
   Genre/Mood: funk / playful
   Score: 1.00 / 4.0
   Reasons:
     • energy fit: 1.00 (target 0.80 vs 0.80) (+1.00)

5. Concrete Kingdom — Rhyme Atlas
   Genre/Mood: hip hop / energetic
   Score: 0.99 / 4.0
   Reasons:
     • energy fit: 0.99 (target 0.80 vs 0.81) (+0.99)
```

**Why these results make sense:** *Sunrise City* is the only song that matches
all three criteria (pop **and** happy **and** ~0.8 energy), so it tops the list.
*Gym Hero* is pop but "intense," so it keeps the +2.0 genre points but loses the
mood bonus. *Rooftop Lights* is "indie pop" (not an exact `pop` match) but is
happy, so it earns the mood points instead. The last two match neither genre nor
mood and rank purely on how close their energy is to the target.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



