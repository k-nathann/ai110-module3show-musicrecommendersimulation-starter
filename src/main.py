"""
Command line runner for the Music Recommender Simulation.

Run it from the project root with:

    python3 -m src.main

It stress-tests the recommender against several distinct user profiles,
including adversarial / edge-case profiles with conflicting preferences,
and prints the top 5 songs for each. Output is rendered as a clean, pure
standard-library ASCII table (Challenge 4). The run also demonstrates an
alternative scoring strategy (Challenge 2) and the diversity option
(Challenge 3) so every stretch feature is visible.
"""

from typing import Dict, List, Optional, Tuple

from src.recommender import (
    ScoringStrategy,
    EnergyFocusedStrategy,
    load_songs,
    recommend_songs,
)


# Each entry is (label, prefs). Keys MUST match what score_song() reads:
# favorite_genre / favorite_mood / target_energy. The last profile also sets
# the OPTIONAL Challenge 1 keys (target_popularity / preferred_decade /
# target_instrumentalness) to show they refine the ranking.
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
    (
        # CHALLENGE 1: exercises the optional advanced features. Wants a modern,
        # popular, highly-instrumental chill lofi track.
        "Advanced Features: Modern Instrumental Chill",
        {
            "favorite_genre": "lofi",
            "favorite_mood": "chill",
            "target_energy": 0.40,
            "target_popularity": 65,
            "preferred_decade": 2020,
            "target_instrumentalness": 0.90,
        },
    ),
]


def _wrap(text: str, width: int) -> List[str]:
    """Greedy word-wrap into lines no wider than `width` (pure stdlib)."""
    if not text:
        return [""]
    words = text.split(" ")
    lines: List[str] = []
    current = ""
    for word in words:
        # A single word longer than width: hard-split it.
        while len(word) > width:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:width])
            word = word[width:]
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_table(
    recommendations: List[Tuple[Dict, float, str]],
    reasons_width: int = 46,
) -> str:
    """
    Render recommendations as an aligned, pure-stdlib ASCII table.

    Columns: Rank | Title | Artist | Genre/Mood | Score | Reasons
    The Reasons column is word-wrapped to `reasons_width`; a row spans as many
    physical lines as its wrapped reasons require.
    """
    headers = ["Rank", "Title", "Artist", "Genre/Mood", "Score", "Reasons"]

    # Build the logical cells for each row (Reasons kept as a wrapped list).
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        rows.append(
            [
                str(rank),
                song["title"],
                song["artist"],
                f"{song['genre']}/{song['mood']}",
                f"{score:.2f}",
                _wrap(explanation, reasons_width),
            ]
        )

    # Compute column widths. Columns 0-4 are single-line; column 5 (Reasons)
    # width is the max wrapped-line length, capped at reasons_width.
    widths = [len(h) for h in headers]
    for row in rows:
        for c in range(5):
            widths[c] = max(widths[c], len(row[c]))
        reason_len = max((len(line) for line in row[5]), default=0)
        widths[5] = max(widths[5], reason_len)
    widths[5] = min(widths[5], reasons_width)
    widths[5] = max(widths[5], len(headers[5]))

    def sep() -> str:
        return "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def fmt_line(cells: List[str]) -> str:
        return (
            "| "
            + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))
            + " |"
        )

    out: List[str] = [sep(), fmt_line(headers), sep()]
    for row in rows:
        reason_lines = row[5] or [""]
        # First physical line carries all the single-line cells.
        first = [row[0], row[1], row[2], row[3], row[4], reason_lines[0]]
        out.append(fmt_line(first))
        # Continuation lines only carry wrapped reasons.
        for extra in reason_lines[1:]:
            out.append(fmt_line(["", "", "", "", "", extra]))
        out.append(sep())
    return "\n".join(out)


def print_profile(
    label: str,
    prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: Optional[ScoringStrategy] = None,
    diversify: bool = False,
) -> None:
    recommendations = recommend_songs(
        prefs, songs, k=k, strategy=strategy, diversify=diversify
    )

    mode_bits = [f"strategy={strategy.name}" if strategy else "strategy=Balanced"]
    if diversify:
        mode_bits.append("diversify=on")
    header = (
        f"Top {k} for profile: {label}  "
        f"[{prefs['favorite_genre']} / {prefs['favorite_mood']} "
        f"(target energy {prefs['target_energy']:.2f})]  "
        f"({', '.join(mode_bits)})"
    )
    bar = "=" * len(header)
    print(f"\n{bar}\n{header}\n{bar}\n")
    print(render_table(recommendations))
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Baseline profiles with the default balanced strategy, rendered as tables.
    for label, prefs in PROFILES:
        print_profile(label, prefs, songs, k=5)

    # CHALLENGE 2 demo: same "High-Energy Pop" taste, but Energy-Focused
    # strategy makes energy the dominant term and reshuffles the ranking.
    print_profile(
        "Strategy Demo: High-Energy Pop via Energy-Focused",
        {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.90},
        songs,
        k=5,
        strategy=EnergyFocusedStrategy(),
    )

    # CHALLENGE 3 demo: "High-Energy Pop" with diversity on so repeated
    # artists/genres get penalized and the list spreads across the catalog.
    print_profile(
        "Diversity Demo: High-Energy Pop with diversify=on",
        {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.90},
        songs,
        k=5,
        diversify=True,
    )


if __name__ == "__main__":
    main()
