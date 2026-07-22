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
INT_FIELDS = ("id", "tempo_bpm")
FLOAT_FIELDS = ("energy", "valence", "danceability", "acousticness")

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

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.

    Recipe:
      +2.0  if song genre == favorite_genre
      +1.0  if song mood  == favorite_mood
      +ENERGY_POINTS * (1 - |target_energy - song energy|)   [energy closeness]

    Returns (score, reasons) where `reasons` is a human-readable list such as
    ["genre match: lofi (+2.0)", "energy fit: 0.95 (+0.95)"] so the user can
    see WHY a song was recommended.

    Required by recommend_songs() and src/main.py
    """
    score = 0.0
    reasons: List[str] = []

    # --- Genre: exact match, all-or-nothing ---
    if song.get("genre") == user_prefs.get("favorite_genre"):
        score += GENRE_POINTS
        reasons.append(f"genre match: {song['genre']} (+{GENRE_POINTS:.1f})")

    # --- Mood: exact match, all-or-nothing ---
    if song.get("mood") == user_prefs.get("favorite_mood"):
        score += MOOD_POINTS
        reasons.append(f"mood match: {song['mood']} (+{MOOD_POINTS:.1f})")

    # --- Energy: closeness (closer to target = more points) ---
    # closeness = 1 - |target - value|, clamped to [0, 1] so it never subtracts.
    target_energy = user_prefs.get("target_energy")
    if target_energy is not None and "energy" in song:
        closeness = 1.0 - abs(target_energy - song["energy"])
        closeness = max(0.0, closeness)
        energy_award = ENERGY_POINTS * closeness
        score += energy_award
        reasons.append(
            f"energy fit: {closeness:.2f} "
            f"(target {target_energy:.2f} vs {song['energy']:.2f}) "
            f"(+{energy_award:.2f})"
        )

    return round(score, 3), reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Ranks the whole catalog and returns the top-k recommendations.

    Uses score_song() as the "judge" for every song, then sorts by score
    (highest first) and keeps the best k.

    Returns a list of (song_dict, score, explanation) tuples, where
    `explanation` is the reasons list joined into one readable string.

    Required by src/main.py
    """
    # Judge every song once. score_song returns (score, reasons); we join the
    # reasons into a single explanation string for the output contract.
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, "; ".join(reasons)))

    # Sort a NEW list by score, highest first. sorted() leaves the original
    # `songs`/`scored` lists untouched; the key lambda pulls the score (index 1).
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    return ranked[:k]
