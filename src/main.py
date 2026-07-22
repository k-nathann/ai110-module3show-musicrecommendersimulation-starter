"""
Command line runner for the Music Recommender Simulation.

Run it from the project root with:

    python3 -m src.main

It stress-tests the recommender against several distinct user profiles,
including adversarial / edge-case profiles with conflicting preferences,
and prints the top 5 songs for each with a clear per-profile header.
"""

from typing import Dict, List, Tuple

from src.recommender import load_songs, recommend_songs


# Each entry is (label, prefs). Keys MUST match what score_song() reads:
# favorite_genre / favorite_mood / target_energy.
PROFILES: List[Tuple[str, Dict]] = [
    (
        "High-Energy Pop",
        {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.90},
    ),
    (
        "Chill Lofi",
        {"favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.35},
    ),
    (
        "Deep Intense Rock",
        {"favorite_genre": "rock", "favorite_mood": "intense", "target_energy": 0.90},
    ),
    (
        # ADVERSARIAL: "sad" mood but high target energy is a contradiction —
        # sad songs in the catalog are low-energy, so mood and energy pull apart.
        "Adversarial: Sad but High-Energy",
        {"favorite_genre": "pop", "favorite_mood": "sad", "target_energy": 0.90},
    ),
    (
        # EDGE CASE: genre + mood combo that does not exist together in the
        # dataset (classical songs are melancholic; euphoric is an edm song).
        "Edge Case: Classical Euphoric",
        {"favorite_genre": "classical", "favorite_mood": "euphoric", "target_energy": 0.50},
    ),
]


def print_profile(label: str, prefs: Dict, songs: List[Dict], k: int = 5) -> None:
    recommendations = recommend_songs(prefs, songs, k=k)

    header = (
        f"Top {k} for profile: {label}  "
        f"[{prefs['favorite_genre']} / {prefs['favorite_mood']} "
        f"(target energy {prefs['target_energy']:.2f})]"
    )
    bar = "=" * len(header)
    print(f"\n{bar}\n{header}\n{bar}\n")

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} — {song['artist']}")
        print(f"   Genre/Mood: {song['genre']} / {song['mood']}")
        print(f"   Score: {score:.2f} / 4.0")
        print("   Reasons:")
        # explanation is the reasons list joined with "; " — split it back out
        # so each reason prints on its own bulleted line.
        for reason in explanation.split("; "):
            print(f"     • {reason}")
        print()


def main() -> None:
    songs = load_songs("data/songs.csv")

    for label, prefs in PROFILES:
        print_profile(label, prefs, songs, k=5)


if __name__ == "__main__":
    main()
