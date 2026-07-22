import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

# Example "taste profile": target values used to score/compare songs.
# Consumed by the dict-based path (score_song / recommend_songs).
# NOTE: target_tempo is NORMALIZED to 0-1, matching how tempo_bpm should be
# scaled during scoring: (bpm - 60) / (152 - 60).
taste_profile: Dict = {
    "favorite_genre":  "lofi",
    "favorite_mood":   "chill",
    "target_energy":   0.40,
    "target_acoustic": 0.86,
    "target_valence":  0.60,
    # Raised from 0.20 -> 0.58: real lofi tracks in the dataset sit ~0.58-0.62,
    # so a low target would penalize the very songs this profile should match.
    "target_dance":    0.58,
    "target_tempo":    0.23,  # normalized (~78 bpm)
}

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    @staticmethod
    def _to_prefs(user: UserProfile) -> Dict:
        """Adapt a UserProfile dataclass to the dict score_song() expects."""
        return {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
        }

    @staticmethod
    def _to_song_dict(song: Song) -> Dict:
        """Adapt a Song dataclass to the dict score_song() expects."""
        return {"genre": song.genre, "mood": song.mood, "energy": song.energy}

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs, highest score first, using score_song()."""
        prefs = self._to_prefs(user)
        ranked = sorted(
            self.songs,
            key=lambda song: score_song(prefs, self._to_song_dict(song))[0],
            reverse=True,
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language explanation of why this song was scored."""
        score, reasons = score_song(self._to_prefs(user), self._to_song_dict(song))
        if not reasons:
            return f"'{song.title}' scored {score:.2f} (no matching preferences)."
        return f"'{song.title}' scored {score:.2f} because: " + "; ".join(reasons)

# Columns that must be parsed as numbers so we can do math with them later.
# Challenge 1 adds popularity + release_decade (ints) and instrumentalness +
# liveness (floats). `language` stays a plain string.
INT_FIELDS = ("id", "tempo_bpm", "popularity", "release_decade")
FLOAT_FIELDS = ("energy", "valence", "danceability", "acousticness",
                "instrumentalness", "liveness")

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dictionaries.

    Numeric columns are converted from strings to numbers so downstream
    scoring can do arithmetic on them:
      - id, tempo_bpm      -> int
      - energy, valence,
        danceability,
        acousticness       -> float
    All other columns (title, artist, genre, mood) stay as strings.

    Required by src/main.py
    """
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):  # line 1 is the header
            try:
                for field in INT_FIELDS:
                    row[field] = int(row[field])
                for field in FLOAT_FIELDS:
                    row[field] = float(row[field])
            except (KeyError, ValueError, TypeError) as e:
                raise ValueError(
                    f"{csv_path}: bad numeric data on line {line_no}: {e}"
                ) from e
            songs.append(row)
    return songs

# --- Scoring recipe (Phase 2) -------------------------------------------------
# Categoricals are all-or-nothing; the numeric feature earns partial credit by
# how CLOSE it is to the target (closer = more points), never negative.
GENRE_POINTS = 2.0   # genre is the strongest signal -> weighted highest
MOOD_POINTS = 1.0    # mood is a weaker, genre-spanning signal
ENERGY_POINTS = 1.0  # a perfect energy match is worth as much as a mood match
# Max possible score = 2.0 + 1.0 + 1.0 = 4.0

# --- Challenge 1: optional advanced-feature weights ---------------------------
# These only ever fire when the matching key is present in user_prefs, so
# existing profiles/tests (which never set them) are completely unaffected. They
# are small on purpose: they refine ties, they never overrule genre/mood/energy.
POPULARITY_POINTS = 0.5        # keyed by "target_popularity" (0-100)
DECADE_POINTS = 0.5            # keyed by "preferred_decade"  (e.g. 2010)
INSTRUMENTALNESS_POINTS = 0.5  # keyed by "target_instrumentalness" (0-1)

# The balanced weight set == the original 2.0/1.0/1.0 recipe. The Strategy
# classes below reuse the exact same scorer with a different weight set, so the
# formula lives in exactly one place (_weighted_score).
DEFAULT_WEIGHTS: Dict[str, float] = {
    "genre": GENRE_POINTS,
    "mood": MOOD_POINTS,
    "energy": ENERGY_POINTS,
    "popularity": POPULARITY_POINTS,
    "decade": DECADE_POINTS,
    "instrumentalness": INSTRUMENTALNESS_POINTS,
}


def _weighted_score(
    user_prefs: Dict, song: Dict, weights: Dict[str, float]
) -> Tuple[float, List[str]]:
    """
    Single, parameterized scorer shared by score_song() and every strategy.

    Core terms (always considered):
      + weights['genre']  if song genre == favorite_genre
      + weights['mood']   if song mood  == favorite_mood
      + weights['energy'] * (1 - |target_energy - song energy|)   [clamped 0..1]

    Optional advanced terms (Challenge 1 — only when the pref key is present):
      + weights['popularity']       * closeness(target_popularity/100, popularity/100)
      + weights['decade']           if release_decade == preferred_decade
      + weights['instrumentalness'] * closeness(target_instrumentalness, instrumentalness)
    """
    score = 0.0
    reasons: List[str] = []

    # --- Genre: exact match, all-or-nothing ---
    genre_w = weights.get("genre", 0.0)
    if genre_w and song.get("genre") == user_prefs.get("favorite_genre"):
        score += genre_w
        reasons.append(f"genre match: {song['genre']} (+{genre_w:.1f})")

    # --- Mood: exact match, all-or-nothing ---
    mood_w = weights.get("mood", 0.0)
    if mood_w and song.get("mood") == user_prefs.get("favorite_mood"):
        score += mood_w
        reasons.append(f"mood match: {song['mood']} (+{mood_w:.1f})")

    # --- Energy: closeness (closer to target = more points) ---
    # closeness = 1 - |target - value|, clamped to [0, 1] so it never subtracts.
    energy_w = weights.get("energy", 0.0)
    target_energy = user_prefs.get("target_energy")
    if energy_w and target_energy is not None and "energy" in song:
        closeness = max(0.0, 1.0 - abs(target_energy - song["energy"]))
        energy_award = energy_w * closeness
        score += energy_award
        reasons.append(
            f"energy fit: {closeness:.2f} "
            f"(target {target_energy:.2f} vs {song['energy']:.2f}) "
            f"(+{energy_award:.2f})"
        )

    # --- Optional: popularity closeness (target_popularity is 0-100) ---
    pop_w = weights.get("popularity", 0.0)
    target_pop = user_prefs.get("target_popularity")
    if pop_w and target_pop is not None and "popularity" in song:
        closeness = max(0.0, 1.0 - abs(target_pop - song["popularity"]) / 100.0)
        pop_award = pop_w * closeness
        score += pop_award
        reasons.append(
            f"popularity fit: {closeness:.2f} "
            f"(target {target_pop} vs {song['popularity']}) (+{pop_award:.2f})"
        )

    # --- Optional: decade exact match ---
    decade_w = weights.get("decade", 0.0)
    preferred_decade = user_prefs.get("preferred_decade")
    if decade_w and preferred_decade is not None and "release_decade" in song:
        if song["release_decade"] == preferred_decade:
            score += decade_w
            reasons.append(f"decade match: {song['release_decade']}s (+{decade_w:.1f})")

    # --- Optional: instrumentalness closeness (0-1) ---
    instr_w = weights.get("instrumentalness", 0.0)
    target_instr = user_prefs.get("target_instrumentalness")
    if instr_w and target_instr is not None and "instrumentalness" in song:
        closeness = max(0.0, 1.0 - abs(target_instr - song["instrumentalness"]))
        instr_award = instr_w * closeness
        score += instr_award
        reasons.append(
            f"instrumentalness fit: {closeness:.2f} "
            f"(target {target_instr:.2f} vs {song['instrumentalness']:.2f}) "
            f"(+{instr_award:.2f})"
        )

    return round(score, 3), reasons


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences using the DEFAULT balanced
    weights (genre 2.0 / mood 1.0 / energy 1.0).

    This is the backward-compatible entry point used by the OOP Recommender and
    by the tests. It delegates to the shared _weighted_score() with
    DEFAULT_WEIGHTS.

    Returns (score, reasons) where `reasons` is a human-readable list such as
    ["genre match: lofi (+2.0)", "energy fit: 0.95 (+0.95)"] so the user can
    see WHY a song was recommended.

    Required by recommend_songs() and src/main.py
    """
    return _weighted_score(user_prefs, song, DEFAULT_WEIGHTS)


# --- Challenge 2: Strategy pattern -------------------------------------------
# Each strategy is just a named bundle of weights fed into the ONE shared
# scorer. Swapping strategies changes which signal dominates without touching
# the formula. The balanced strategy reproduces score_song() exactly.
class ScoringStrategy:
    """Base Strategy: a named weight set plus a score() method."""

    name: str = "Base"
    weights: Dict[str, float] = DEFAULT_WEIGHTS

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
        return _weighted_score(user_prefs, song, self.weights)

    def __repr__(self) -> str:  # nice for debugging / logs
        return f"<ScoringStrategy {self.name!r}>"


class BalancedStrategy(ScoringStrategy):
    """The default 2.0 / 1.0 / 1.0 recipe."""

    name = "Balanced"
    weights = DEFAULT_WEIGHTS


class GenreFirstStrategy(ScoringStrategy):
    """Genre dominates; mood and energy are minor tie-breakers."""

    name = "Genre-First"
    weights = {
        "genre": 3.0, "mood": 0.5, "energy": 0.5,
        "popularity": 0.5, "decade": 0.5, "instrumentalness": 0.5,
    }


class MoodFirstStrategy(ScoringStrategy):
    """Mood dominates; good for 'I want a vibe regardless of genre'."""

    name = "Mood-First"
    weights = {
        "genre": 0.5, "mood": 3.0, "energy": 0.5,
        "popularity": 0.5, "decade": 0.5, "instrumentalness": 0.5,
    }


class EnergyFocusedStrategy(ScoringStrategy):
    """Energy is the biggest term; ideal for workout / focus playlists."""

    name = "Energy-Focused"
    weights = {
        "genre": 0.5, "mood": 0.5, "energy": 3.0,
        "popularity": 0.5, "decade": 0.5, "instrumentalness": 0.5,
    }


# Convenience registry so callers can pick a strategy by name.
STRATEGIES: Dict[str, ScoringStrategy] = {
    s.name: s
    for s in (
        BalancedStrategy(),
        GenreFirstStrategy(),
        MoodFirstStrategy(),
        EnergyFocusedStrategy(),
    )
}


# --- Challenge 3: diversity penalty ------------------------------------------
# Multiply a candidate's score by this factor for EACH already-selected song
# that shares its artist or genre. Repeated overlaps compound (0.5, 0.25, ...).
DIVERSITY_FACTOR = 0.5


def _diversified_pick(
    scored: List[Tuple[Dict, float, List[str]]], k: int
) -> List[Tuple[Dict, float, List[str]]]:
    """
    Greedy diversity re-ranking: repeatedly pick the highest *adjusted* score,
    where a candidate is penalized by DIVERSITY_FACTOR for every already-picked
    song sharing its artist or genre. Returns (song, adjusted_score, reasons).
    """
    remaining = [(song, score, list(reasons)) for song, score, reasons in scored]
    picked: List[Tuple[Dict, float, List[str]]] = []

    while remaining and len(picked) < k:
        best_idx = None
        best_adj = -1.0
        best_payload: Optional[Tuple[Dict, float, List[str]]] = None

        for idx, (song, base, reasons) in enumerate(remaining):
            shared = sum(
                1
                for psong, _, _ in picked
                if psong["artist"] == song["artist"] or psong["genre"] == song["genre"]
            )
            factor = DIVERSITY_FACTOR ** shared
            adj = base * factor
            adj_reasons = list(reasons)
            if shared:
                adj_reasons.append(
                    f"diversity penalty: shares artist/genre with {shared} "
                    f"already-picked (score x{factor:.2f} -> {adj:.2f})"
                )
            if adj > best_adj:
                best_adj = adj
                best_idx = idx
                best_payload = (song, round(adj, 3), adj_reasons)

        picked.append(best_payload)
        remaining.pop(best_idx)

    return picked


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: Optional[ScoringStrategy] = None,
    diversify: bool = False,
) -> List[Tuple[Dict, float, str]]:
    """
    Ranks the whole catalog and returns the top-k recommendations.

    By default it uses score_song() (the balanced 2.0/1.0/1.0 recipe) and a
    plain highest-first sort — identical behavior to the original.

    Optional layers:
      strategy:  a ScoringStrategy (Challenge 2). If None, uses score_song().
      diversify: when True, applies the greedy diversity penalty (Challenge 3)
                 so the same artist/genre doesn't dominate the list.

    Returns a list of (song_dict, score, explanation) tuples, where
    `explanation` is the reasons list joined into one readable string.

    Required by src/main.py
    """
    judge = strategy.score if strategy is not None else score_song

    # Judge every song once. The judge returns (score, reasons).
    scored: List[Tuple[Dict, float, List[str]]] = []
    for song in songs:
        score, reasons = judge(user_prefs, song)
        scored.append((song, score, reasons))

    if diversify:
        ranked = _diversified_pick(scored, k)
    else:
        # Sort a NEW list by score, highest first; leaves inputs untouched.
        ranked = sorted(scored, key=lambda item: item[1], reverse=True)[:k]

    return [(song, score, "; ".join(reasons)) for song, score, reasons in ranked]
