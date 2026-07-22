"""
Command line runner for the Music Recommender Simulation.

Run it from the project root with:

    python -m src.main
"""

from src.recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Default example profile. Keys must match what score_song() reads:
    # favorite_genre / favorite_mood / target_energy.
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
    }

    k = 5
    recommendations = recommend_songs(user_prefs, songs, k=k)

    header = (
        f"Top {k} for profile: "
        f"{user_prefs['favorite_genre']} / {user_prefs['favorite_mood']} "
        f"(target energy {user_prefs['target_energy']:.2f})"
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


if __name__ == "__main__":
    main()
