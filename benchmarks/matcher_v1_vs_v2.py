"""
This script is meant to run an automated comparison and evaluation on the Track Matcher V1 and V2.

The dataset is courtesy of MusicBrainz and contributors.
Learn more: https://musicbrainz.org/doc/Development/JSON_Data_Dumps
Thank you to MusicBrainz and the contributors for building this database for free.

This script will download data from the internet. Please make sure you have enough storage.

How to run this?

1. Install the required packages from the repository root's requirements.txt file.
2. From within the benchmarks/ folder, run `python3 matcher_v1_vs_v2.py`.
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple
import asyncio
import random
import re
import multiprocessing as mp
import aiofiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunesynctool.models import Track
from tunesynctool.drivers import ServiceDriver, AsyncWrappedServiceDriver

from tunesynctool.features import TrackMatcher as V1TrackMatcher
from tunesynctool.features import AsyncTrackMatcher as V1AsyncTrackMatcher
from tunesynctool.features.v2 import AsyncTrackMatcher as V2AsyncTrackMatcher
from tunesynctool.features.v2 import track_score, match_track

from utils import (
    get_txt,
    download,
    ensure_path_exists,
    extract_tar_xz,
    rm_dir,
    Report,
    map_dataset_recording_to_domain_model
)

from mutator import generate_candidate_track, get_deterministic_rng

MB_LATEST = "https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/LATEST"

PARENT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PARENT_DIR / "assets"
DOWNLOADS_DIR = ASSETS_DIR / "downloads"

ASSET_RECORDINGS = ("recording", ".tar.xz")
ASSETS = [
    "".join(ASSET_RECORDINGS)
]

# Which published version the cached dump under assets/ came from. The report is
# named after it, so it has to describe the data actually loaded: reading LATEST
# off the network instead would stamp today's version on a dump downloaded weeks
# ago and quietly make two incomparable reports look like the same dataset.
DATASET_VERSION_MARKER = "DATASET_VERSION"

# How many reference tracks to score. The full dump is ~150k tracks which would
# produce millions of pairs; a pinned, index-based sample keeps the benchmark
# fast and still reproducible for anyone re-running it on the same dataset version.
SAMPLE_SIZE = 10000
SAMPLE_SEED = 20260809

# The acceptance floor both scorers are graded against. Re-tuned down from 0.75:
# the cover gate now caps same-song-different-version pairs at 0.5 regardless of
# the floor, so the floor no longer has to defend against covers and is free to
# come down and rescue borderline real matches. The package's _ACCEPT_FLOOR is a
# separate shipping decision; it currently sits at the same 0.70.
ACCEPTANCE_FLOOR = 0.70

# Floors swept to show how recall and precision trade off. Always includes the
# acceptance floor so the headline counts come from the same place.
FLOOR_SWEEP = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85]

# Negative-pair classes tagged on each dataset tuple so the report can break down
# how the scorers handle each kind of non-match, not just the overall confusion.
CLASS_MATCH = 0
CLASS_NEG_RANDOM = 1
CLASS_NEG_SAME_ARTIST = 2
CLASS_NEG_COVER = 3

CLASSES = (CLASS_MATCH, CLASS_NEG_RANDOM, CLASS_NEG_SAME_ARTIST, CLASS_NEG_COVER)

_BRACKET_RE = re.compile(r"[\(\[\{].*?[\)\]\}]")

def _normalize_title(title: Optional[str]) -> str:
    """Title reduced to its core so covers/namesakes that share a name collide.

    Bracketed version and feature markers are dropped first so "Save Your Tears
    (Remix)" and "Save Your Tears" collide, then it is lowercased and
    whitespace-collapsed.
    """
    if not title:
        return ""
    cleaned = _BRACKET_RE.sub(" ", title)
    return " ".join(cleaned.lower().split())

# Populated in main() before the pool is forked, then read copy-on-write by the
# workers. Fork is used on purpose: the benchmarks package uses bare
# `from utils import` which only resolves in the already-imported parent process,
# so spawn workers (which re-import) would fail. Fork inherits the working state.
_DATASET = None

async def get_latest_version_of_dataset() -> str:
    return await get_txt(MB_LATEST)

def build_dataset_version_url(version: str) -> str:
    """The download URL base for one published version of the dump."""

    return f"https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/{version}/"

def read_dataset_version() -> str:
    """The version of the dump actually sitting in assets/.

    Written by download_dataset when the dump is fetched. A dump extracted before
    this file existed has no marker, so its version is reconstructed from the
    TIMESTAMP that MusicBrainz ships inside the archive: not the published
    directory name (that is the export start, TIMESTAMP is the database clock),
    but stable for a given dump, which is what the report needs it to be.

    :return: The version label for the cached dump.
    """

    marker = ASSETS_DIR / DATASET_VERSION_MARKER
    if marker.exists():
        return marker.read_text().strip()

    timestamp = ASSETS_DIR / "".join(ASSET_RECORDINGS) / "TIMESTAMP"
    if timestamp.exists():
        stamp = timestamp.read_text().strip()
        digits = re.sub(r"\D", "", stamp)[:14]

        if len(digits) == 14:
            return f"{digits[:8]}-{digits[8:14]}"

    return "unknown"

def write_dataset_version(version: str) -> None:
    """Records which version was downloaded, so later cached runs label themselves honestly."""

    ensure_path_exists(ASSETS_DIR / DATASET_VERSION_MARKER).write_text(version)

async def download_dataset(version: str) -> None:
    download_url_base = build_dataset_version_url(version)

    save_paths = [
        (file_name, ensure_path_exists(DOWNLOADS_DIR / file_name)) for file_name in ASSETS
    ]

    await asyncio.gather(*[
        download(
            url=download_url_base + file_name,
            path=save_path
        ) for file_name, save_path in save_paths
    ])

async def extract_dataset() -> None:
    await asyncio.gather(*[
       asyncio.to_thread(
           extract_tar_xz,
           ensure_path_exists(DOWNLOADS_DIR / file_name),
           ensure_path_exists(ASSETS_DIR / file_name)
        ) for file_name in ASSETS
    ])

def clean_up_downloads() -> None:
    rm_dir(DOWNLOADS_DIR)

async def load_tracks(path: Path) -> List[Track]:
    """Load a bunch of real tracks."""

    tracks: List[Track] = []

    async with aiofiles.open(str(path), "r") as f:
        async for line in f:
            line = line.rstrip("\n")

            if len(line.strip()) == 0:
                continue

            track = map_dataset_recording_to_domain_model(line)
            tracks.append(track)

    return tracks

def get_extracted_dataset_file_path(file_name_without_extension: str, file_extension: str) -> Path:
    return ASSETS_DIR / (file_name_without_extension + file_extension) / "mbdump" / file_name_without_extension

def sample_tracks(tracks: List[Track], n: int, seed: int) -> List[Track]:
    if len(tracks) <= n:
        return tracks

    rng = random.Random(seed)
    indices = sorted(rng.sample(range(len(tracks)), n))

    return [tracks[i] for i in indices]

def generate_benchmark_dataset(reference_tracks: List[Track], all_tracks: List[Track], iterations: int = 5) -> List[Tuple[Track, Track, float, int]]:
    dataset = []

    sorted_tracks = sorted(reference_tracks, key=lambda t: str(t.service_id))

    artist_lookup = {}
    for track in sorted_tracks:
        if track.primary_artist:
            if track.primary_artist not in artist_lookup:
                artist_lookup[track.primary_artist] = []

            artist_lookup[track.primary_artist].append(track)

    # Same song, different version: a different recording that shares the title
    # with the reference but comes from a different artist (a cover, or two songs
    # that just share a name). The title is identical so only the artist can reject
    # these, which makes them the hardest negatives for the acceptance floor.
    title_lookup = {}
    for track in all_tracks:
        key = _normalize_title(track.title)
        if not key or not track.primary_artist:
            continue
        title_lookup.setdefault(key, []).append(track)

    for reference_track in sorted_tracks:
        # Skip if there's no unique identifier to seed the RNG with
        if not reference_track.service_id:
            continue

        # Same song, different version pool for this reference track. The title
        # does not change across iterations, so this is computed once up front.
        cover_pool = []
        key = _normalize_title(reference_track.title)
        if key:
            for track in title_lookup.get(key, []):
                if track.service_id != reference_track.service_id and track.primary_artist != reference_track.primary_artist:
                    cover_pool.append(track)

        # We generate alternative versions of the base track
        for i in range(iterations):
            rng = get_deterministic_rng(reference_track.service_id, i)

            # This should yield a perfect match
            mutated_candidate = generate_candidate_track(reference_track, rng)
            dataset.append((reference_track, mutated_candidate, 1.0, CLASS_MATCH))

            # Randomly pulling 5 tracks from the entire dataset
            easy_negatives = rng.sample(sorted_tracks, 5)
            for neg in easy_negatives:

                # We don't want to accidentally compare a track to itself
                if neg.service_id != reference_track.service_id:
                    dataset.append((reference_track, neg, 0.0, CLASS_NEG_RANDOM))

            # These are random tracks from the same artist if they even exist
            if reference_track.primary_artist in artist_lookup:
                artist_tracks = artist_lookup[reference_track.primary_artist]

                # Exclude the current base track from the potential hard negatives
                possible_hard_negatives = [
                    t for t in artist_tracks
                    if t.service_id != reference_track.service_id
                ]

                num_to_sample = min(2, len(possible_hard_negatives))
                if num_to_sample > 0:
                    hard_negatives = rng.sample(possible_hard_negatives, num_to_sample)

                    for hard_neg in hard_negatives:
                        dataset.append((reference_track, hard_neg, 0.0, CLASS_NEG_SAME_ARTIST))

            # A different recording of the same song: same title, different artist.
            num_to_sample = min(2, len(cover_pool))
            if num_to_sample > 0:
                cover_negatives = rng.sample(cover_pool, num_to_sample)

                for cover in cover_negatives:
                    dataset.append((reference_track, cover, 0.0, CLASS_NEG_COVER))

    return dataset

# The methods below this comment are AI generated (except main)

def _score_range(start: int, end: int) -> dict:
    chunk = _DATASET[start:end]

    v1_sweep = {t: {"tp": 0, "fp": 0, "tn": 0, "fn": 0} for t in FLOOR_SWEEP}
    v2_sweep = {t: {"tp": 0, "fp": 0, "tn": 0, "fn": 0} for t in FLOOR_SWEEP}
    v1_sum = 0.0
    v2_sum = 0.0
    v2_match_hist = [0] * 11
    v2_nonmatch_hist = [0] * 11
    # Per-class acceptance at the floor: "acc" counts pairs the scorer said yes to,
    # "tot" counts the class. For the match class acc/tot is recall; for the
    # negative classes it is the wrong-match rate (the lower the better).
    v1_class = {c: {"acc": 0, "tot": 0} for c in CLASSES}
    v2_class = {c: {"acc": 0, "tot": 0} for c in CLASSES}
    # Real matches V2 scored below the floor: (global_index, v2_score). The index
    # is into _DATASET so the parent can look the pair up without pickling tracks back.
    fn = []
    # The mirror image: non-matches V2 accepted, carrying their class so the dump
    # can be split by the kind of negative that got through.
    fp = []

    for j, (base, candidate, expected, cls) in enumerate(chunk):
        is_match = expected >= 0.5

        s1 = base.similarity(candidate)
        s2 = track_score(base, candidate)

        v1_sum += s1
        v2_sum += s2
        hist = v2_match_hist if is_match else v2_nonmatch_hist
        hist[min(10, int(round(s2 * 10)))] += 1

        if is_match and s2 < ACCEPTANCE_FLOOR:
            fn.append((start + j, s2))

        if not is_match and s2 >= ACCEPTANCE_FLOOR:
            fp.append((start + j, s2, cls))

        for score, sweep in ((s1, v1_sweep), (s2, v2_sweep)):
            for t in FLOOR_SWEEP:
                c = sweep[t]
                if score >= t:
                    if is_match:
                        c["tp"] += 1
                    else:
                        c["fp"] += 1
                else:
                    if is_match:
                        c["fn"] += 1
                    else:
                        c["tn"] += 1

        v1_class[cls]["tot"] += 1
        v2_class[cls]["tot"] += 1
        if s1 >= ACCEPTANCE_FLOOR:
            v1_class[cls]["acc"] += 1
        if s2 >= ACCEPTANCE_FLOOR:
            v2_class[cls]["acc"] += 1

    return {
        "v1_sweep": v1_sweep,
        "v2_sweep": v2_sweep,
        "v1_sum": v1_sum,
        "v2_sum": v2_sum,
        "v2_match_hist": v2_match_hist,
        "v2_nonmatch_hist": v2_nonmatch_hist,
        "v1_class": v1_class,
        "v2_class": v2_class,
        "fn": fn,
        "fp": fp,
        "count": len(chunk),
    }

def _reduce(partials: List[dict]) -> dict:
    v1_sweep = {t: {"tp": 0, "fp": 0, "tn": 0, "fn": 0} for t in FLOOR_SWEEP}
    v2_sweep = {t: {"tp": 0, "fp": 0, "tn": 0, "fn": 0} for t in FLOOR_SWEEP}
    v1_sum = 0.0
    v2_sum = 0.0
    v2_match_hist = [0] * 11
    v2_nonmatch_hist = [0] * 11
    v1_class = {c: {"acc": 0, "tot": 0} for c in CLASSES}
    v2_class = {c: {"acc": 0, "tot": 0} for c in CLASSES}
    total = 0
    fn = []
    fp = []

    for p in partials:
        for t in FLOOR_SWEEP:
            for key in ("tp", "fp", "tn", "fn"):
                v1_sweep[t][key] += p["v1_sweep"][t][key]
                v2_sweep[t][key] += p["v2_sweep"][t][key]
        v1_sum += p["v1_sum"]
        v2_sum += p["v2_sum"]
        for i in range(11):
            v2_match_hist[i] += p["v2_match_hist"][i]
            v2_nonmatch_hist[i] += p["v2_nonmatch_hist"][i]
        for c in CLASSES:
            v1_class[c]["acc"] += p["v1_class"][c]["acc"]
            v1_class[c]["tot"] += p["v1_class"][c]["tot"]
            v2_class[c]["acc"] += p["v2_class"][c]["acc"]
            v2_class[c]["tot"] += p["v2_class"][c]["tot"]
        total += p["count"]
        fn.extend(p["fn"])
        fp.extend(p["fp"])

    return {
        "v1_sweep": v1_sweep,
        "v2_sweep": v2_sweep,
        "v1_sum": v1_sum,
        "v2_sum": v2_sum,
        "v2_match_hist": v2_match_hist,
        "v2_nonmatch_hist": v2_nonmatch_hist,
        "v1_class": v1_class,
        "v2_class": v2_class,
        "total": total,
        "fn": fn,
        "fp": fp,
    }

def _metrics_at(counts: dict, total: int) -> Tuple[float, float, float, float]:
    tp, fp, tn, fn = counts["tp"], counts["fp"], counts["tn"], counts["fn"]

    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return accuracy, precision, recall, f1

def _headline_row(label: str, v1_value: float, v2_value: float, higher_is_better: bool = True) -> str:
    if not higher_is_better:
        winner = "—"
    elif v2_value > v1_value:
        winner = "V2"
    elif v1_value > v2_value:
        winner = "V1"
    else:
        winner = "tie"

    return f"|{label}|{v1_value:.4f}|{v2_value:.4f}|{winner}|"

def _verdict(results: dict) -> str:
    # A track matcher's job is to find real matches (recall), so the headline
    # percentage is the relative recall change. Precision is reported alongside
    # so a recall gain bought by accepting junk would not look like a clean win.
    total = results["total"]
    v1_counts = results["v1_sweep"][ACCEPTANCE_FLOOR]
    v2_counts = results["v2_sweep"][ACCEPTANCE_FLOOR]

    _, v1_prec, v1_rec, _ = _metrics_at(v1_counts, total)
    _, v2_prec, v2_rec, _ = _metrics_at(v2_counts, total)

    rel_recall = (v2_rec - v1_rec) / v1_rec * 100 if v1_rec else 0.0
    recall_word = "more" if v2_rec >= v1_rec else "fewer"

    rel_fp = (v2_counts["fp"] - v1_counts["fp"]) / v1_counts["fp"] * 100 if v1_counts["fp"] else 0.0
    fp_word = "fewer" if v2_counts["fp"] <= v1_counts["fp"] else "more"

    return (
        f"V2 finds {abs(rel_recall):.1f}% {recall_word} real matches than V1 "
        f"(recall {v2_rec:.1%} vs {v1_rec:.1%}), and makes {abs(rel_fp):.1f}% {fp_word} wrong matches "
        f"(precision {v2_prec:.1%} vs {v1_prec:.1%})."
    )

def run_scoring(benchmark_dataset) -> dict:
    global _DATASET
    _DATASET = benchmark_dataset

    n_workers = mp.cpu_count()
    chunk_size = max(1, len(benchmark_dataset) // (n_workers * 8))
    ranges = [
        (i, min(i + chunk_size, len(benchmark_dataset)))
        for i in range(0, len(benchmark_dataset), chunk_size)
    ]

    with mp.get_context("fork").Pool(n_workers) as pool:
        partials = pool.starmap(_score_range, ranges)

    return _reduce(partials)

def _pair_lines(dataset, idx: int) -> List[str]:
    base, candidate, _, _ = dataset[idx]

    return [
        f"- ref   title={base.title!r}  artist={base.primary_artist!r}  addl={base.additional_artists}  dur={base.duration_seconds}",
        f"- cand  title={candidate.title!r}  artist={candidate.primary_artist!r}  addl={candidate.additional_artists}  dur={candidate.duration_seconds}",
    ]

def _score_band_table(scores: List[float], label: str) -> List[str]:
    """A count per 0.05 score band, so a dump's sample can be read against the whole population."""

    bands = {}
    for s in scores:
        bands[round(s * 20) / 20] = bands.get(round(s * 20) / 20, 0) + 1

    lines = [f"| Score | {label} |", "|---|---|"]
    for band in sorted(bands, reverse=True):
        lines.append(f"|{band:.2f}|{bands[band]}|")

    return lines

def _evenly_spaced(items: list, n: int) -> list:
    """n items spread across a list instead of taken off one end."""

    if len(items) <= n:
        return items

    step = len(items) / n

    return [items[int(i * step)] for i in range(n)]

def dump_fn_sample(results: dict, dataset, path: Path, n: int = 50) -> None:
    fn = list(results["fn"])
    # Closest to the floor first — these are the misses a small scorer
    # improvement could rescue, not the ones obliterated by brutal mutations.
    fn.sort(key=lambda e: e[1], reverse=True)

    half = n // 2
    near = fn[:half]
    # The near-floor half alone is not the miss population: it is the best half of
    # it by construction, and reading only that makes every miss look like a
    # near-miss. The rest are sampled across the whole spread so the dump shows
    # what the misses actually look like, and the band table below says how many
    # sit where.
    rest = _evenly_spaced(fn[half:], n - half)

    lines = [
        "# False negatives — V2 missed real matches",
        "",
        f"{len(fn)} real matches scored below the {ACCEPTANCE_FLOOR} floor.",
        "",
        "## How the misses are spread",
        "",
    ]
    lines.extend(_score_band_table([s for _, s in fn], "Misses"))
    lines.append("")
    lines.append("A pile-up at one score is a cap doing the rejecting rather than the weighted average,")
    lines.append("so it points at a gate to look at instead of a threshold to nudge.")
    lines.append("")

    lines.append(f"## Closest to the floor ({len(near)})")
    lines.append("")
    lines.append("The misses a small scorer improvement could rescue.")
    lines.append("")

    for i, (idx, s2) in enumerate(near, 1):
        lines.append(f"### #{i}  V2={s2:.2f}")
        lines.extend(_pair_lines(dataset, idx))
        lines.append("")

    lines.append(f"## Spread across the rest ({len(rest)})")
    lines.append("")
    lines.append("Sampled evenly down the ranking, so this section is representative where the one above is not.")
    lines.append("")

    for i, (idx, s2) in enumerate(rest, 1):
        lines.append(f"### #{i}  V2={s2:.2f}")
        lines.extend(_pair_lines(dataset, idx))
        lines.append("")

    path.write_text("\n".join(lines))

def dump_fp_sample(results: dict, dataset, path: Path, n: int = 20) -> None:
    """The mirror of the false-negative dump: the non-matches V2 accepted.

    Split by negative class, because the classes fail for different reasons and
    an overall list is dominated by whichever one is largest. Highest score first
    within each: the most confident wrong matches are the most diagnostic, since
    those are the ones a user would never think to question.
    """

    fp = list(results["fp"])
    fp.sort(key=lambda e: e[1], reverse=True)

    lines = [
        "# False positives — V2 accepted non-matches",
        "",
        f"{len(fp)} non-matches scored at or above the {ACCEPTANCE_FLOOR} floor.",
        "",
        "## Where the wrong matches come from",
        "",
        "| Class | Wrong matches | Share of all wrong matches |",
        "|---|---|---|",
    ]

    class_rows = [
        (CLASS_NEG_RANDOM, "Random track"),
        (CLASS_NEG_SAME_ARTIST, "Same artist, different track"),
        (CLASS_NEG_COVER, "Same song, different version"),
    ]

    for cls, label in class_rows:
        count = sum(1 for _, _, c in fp if c == cls)
        share = count / len(fp) if fp else 0.0
        lines.append(f"|{label}|{count}|{share:.1%}|")

    lines.append("")
    lines.append("The class holding most of the wrong matches is the one worth working on; the per-class")
    lines.append("rates in the main report say how often each class fails, this says how much of the")
    lines.append("damage each one accounts for.")
    lines.append("")

    for cls, label in class_rows:
        entries = [e for e in fp if e[2] == cls][:n]
        lines.append(f"## {label} ({len(entries)} of {sum(1 for _, _, c in fp if c == cls)})")
        lines.append("")

        if not entries:
            lines.append("None.")
            lines.append("")
            continue

        for i, (idx, s2, _) in enumerate(entries, 1):
            lines.append(f"### #{i}  V2={s2:.2f}")
            lines.extend(_pair_lines(dataset, idx))
            lines.append("")

    path.write_text("\n".join(lines))

def build_report(report: Report, results: dict) -> None:
    total = results["total"]
    floor = ACCEPTANCE_FLOOR
    v1_counts = results["v1_sweep"][floor]
    v2_counts = results["v2_sweep"][floor]

    v1_acc, v1_prec, v1_rec, v1_f1 = _metrics_at(v1_counts, total)
    v2_acc, v2_prec, v2_rec, v2_f1 = _metrics_at(v2_counts, total)
    v1_mean = results["v1_sum"] / total if total else 0.0
    v2_mean = results["v2_sum"] / total if total else 0.0

    # The dataset is the same for both scorers, so the number of real matches is fixed
    # regardless of who got them right. A scorer that rejected everything would still
    # "correctly" reject every non-match, which sets a floor on accuracy.
    real_matches = v1_counts["tp"] + v1_counts["fn"]
    negatives = total - real_matches
    reject_all_accuracy = negatives / total if total else 0.0

    report.add("## What this measures")
    report.add("")
    report.add("Each pair asks the scorer: \"is this candidate the same song as the reference?\"")
    report.add(f"The scorer says YES if its similarity is at least {floor}, otherwise NO.")
    report.add("We already know the truth (the candidate is either a mutated copy of the reference = a real match,")
    report.add("or a different track = not a match: a random track, a different song by the same artist, or a")
    report.add("different recording that shares the title — a cover or a namesake), so the benchmark just counts")
    report.add("how often the scorer's answer agrees with the truth.")
    report.add("")

    report.add("## Verdict")
    report.add("")
    report.add(_verdict(results))
    report.add("")

    report.add("## Headline scores")
    report.add("")
    report.add("| Metric | V1 | V2 | Winner |")
    report.add("|---|---|---|---|")
    report.add(_headline_row("Accuracy", v1_acc, v2_acc))
    report.add(_headline_row("Precision", v1_prec, v2_prec))
    report.add(_headline_row("Recall", v1_rec, v2_rec))
    report.add(_headline_row("F1", v1_f1, v2_f1))
    report.add(_headline_row("Mean score", v1_mean, v2_mean, higher_is_better=False))
    report.add("")

    report.add("## What the metrics mean")
    report.add("")
    report.add(f"- **Accuracy** — fraction of all decisions that were right. Misleading here: {reject_all_accuracy:.0%} of")
    report.add(f"  pairs are different tracks (easy rejections), so a matcher that rejected *everything* would still")
    report.add(f"  score {reject_all_accuracy:.0%}. Don't judge a matcher by this alone.")
    report.add("- **Precision** — of all the matches the scorer accepted, how many were actually the right song.")
    report.add("  High precision means few wrong matches (the user rarely gets the wrong song).")
    report.add("- **Recall** — of all the real matches, how many the scorer actually found. This is the one that")
    report.add("  matters for a matcher: how much of a user's library gets matched. V2's whole point is this number.")
    report.add("- **F1** — precision and recall rolled into one number. Handy for a quick comparison, but read it")
    report.add("  next to precision and recall so you know which one moved.")
    report.add("- **Mean score** — average similarity across all pairs. Not a verdict, just shows the scorer is")
    report.add("  well-scaled (real matches high, different tracks low).")
    report.add("")

    report.add("## The counts")
    report.add("")
    report.add("| Outcome | Meaning | V1 | V2 |")
    report.add("|---|---|---|---|")
    report.add(f"| Real match found | correctly matched the right song | {v1_counts['tp']} | {v2_counts['tp']} |")
    report.add(f"| Wrong match | matched the wrong song | {v1_counts['fp']} | {v2_counts['fp']} |")
    report.add(f"| Real match missed | failed to match a real song | {v1_counts['fn']} | {v2_counts['fn']} |")
    report.add(f"| Correctly rejected | correctly said \"different track\" | {v1_counts['tn']} | {v2_counts['tn']} |")
    report.add("")

    report.add("## Floor sweep")
    report.add("")
    report.add("How recall and precision move as the acceptance floor changes. The row matching the current floor")
    report.add(f"({floor}) is the one used everywhere else in this report.")
    report.add("")
    report.add("| Floor | V1 Recall | V2 Recall | V1 Precision | V2 Precision |")
    report.add("|---|---|---|---|---|")
    for t in FLOOR_SWEEP:
        _, v1_p, v1_r, _ = _metrics_at(results["v1_sweep"][t], total)
        _, v2_p, v2_r, _ = _metrics_at(results["v2_sweep"][t], total)
        report.add(f"|{t:.2f}|{v1_r:.4f}|{v2_r:.4f}|{v1_p:.4f}|{v2_p:.4f}|")
    report.add("")
    report.add("If recall climbs fast as the floor drops while precision barely moves, the floor is the lever — just")
    report.add("lower it. If precision collapses the moment recall rises, the scorer can't separate the cases and the")
    report.add("floor won't help; the algorithm needs to improve.")
    report.add("")

    report.add("## V2 score distribution (split by truth)")
    report.add("")
    report.add("How V2 scores spread, split by whether the pair is actually a real match. Real matches should clump")
    report.add("high, non-matches low.")
    report.add("")
    report.add("| Score | Real matches | Non-matches |")
    report.add("|---|---|---|")
    for i in range(11):
        report.add(f"|{i / 10:.1f}|{results['v2_match_hist'][i]}|{results['v2_nonmatch_hist'][i]}|")
    report.add("")
    report.add(f"Real matches below the {floor} floor are V2's misses (FN). Non-matches above it are V2's false")
    report.add("positives (FP). The cleaner the gap between the two columns, the better V2 separates matches from")
    report.add("non-matches at that score.")
    report.add("")

    report.add("## Same song, different version (hard negatives)")
    report.add("")
    report.add("A different recording that shares the title with the reference but comes from a different")
    report.add("artist — a cover, or two songs that just share a name. The title is identical, so the only thing")
    report.add("that can reject these is the artist. This is the case the floor has to survive: a matcher that")
    report.add("scored on title alone would falsely match every one of them.")
    report.add("")
    report.add(f"The rate is the share of each class the scorer accepted at the {floor} floor. For the match row")
    report.add("that is recall (higher is better); for the negative rows it is the wrong-match rate (lower is")
    report.add("better). The cover row is the one that tells you whether the floor is safe against real-world")
    report.add("different recordings.")
    report.add("")
    report.add("| Class | Pairs | V1 | V2 |")
    report.add("|---|---|---|---|")
    class_rows = [
        (CLASS_MATCH, "Real match (mutated copy)"),
        (CLASS_NEG_RANDOM, "Random track"),
        (CLASS_NEG_SAME_ARTIST, "Same artist, different track"),
        (CLASS_NEG_COVER, "Same song, different version"),
    ]
    for c, label in class_rows:
        tot = results["v1_class"][c]["tot"]
        v1 = results["v1_class"][c]["acc"] / tot if tot else 0.0
        v2 = results["v2_class"][c]["acc"] / tot if tot else 0.0
        report.add(f"|{label}|{tot}|{v1:.1%}|{v2:.1%}|")
    report.add("")

    # A per-class rate says how often a class fails, not how much of the damage it
    # accounts for. A rare class failing often can still be a rounding error next
    # to a common class failing sometimes, and it is the second number that says
    # where the work is.
    fp_by_class = {c: 0 for c in CLASSES}
    for _, _, cls in results["fp"]:
        fp_by_class[cls] += 1

    worst = max((c for c in CLASSES if c != CLASS_MATCH), key=lambda c: fp_by_class[c])
    worst_label = {
        CLASS_NEG_RANDOM: "random tracks",
        CLASS_NEG_SAME_ARTIST: "different tracks by the same artist",
        CLASS_NEG_COVER: "different recordings that share the title",
    }[worst]
    worst_share = fp_by_class[worst] / v2_counts["fp"] if v2_counts["fp"] else 0.0

    report.add(f"Of V2's {v2_counts['fp']} wrong matches, {worst_share:.0%} are {worst_label}.")
    report.add("The `-fp.md` file beside this report lists the accepted non-matches themselves, split by class.")
    report.add("")

    cover_tot = results["v2_class"][CLASS_NEG_COVER]["tot"]
    cover_fp_v2 = results["v2_class"][CLASS_NEG_COVER]["acc"] / cover_tot if cover_tot else 0.0
    cover_fp_v1 = results["v1_class"][CLASS_NEG_COVER]["acc"] / cover_tot if cover_tot else 0.0
    report.add(f"V2 wrongly matched {cover_fp_v2:.1%} of same-song-different-version pairs (V1: {cover_fp_v1:.1%}).")
    if cover_fp_v2 < 0.05:
        report.add("That is low: the floor holds against title-identical different recordings, so lowering it is")
        report.add("unlikely to flood in real-world covers.")
    elif cover_fp_v2 < 0.20:
        report.add("That is moderate: a lower floor would start letting covers through. Keep the floor where it is.")
    else:
        report.add("That is high: the floor already lets too many covers through. The artist handling, not the")
        report.add("floor, is what has to improve before recall can go up.")
    report.add("")

async def main() -> None:
    report = Report()

    tracks_file_path = get_extracted_dataset_file_path(ASSET_RECORDINGS[0], ASSET_RECORDINGS[1])

    if not tracks_file_path.exists():
        dataset_version = await get_latest_version_of_dataset()
        await download_dataset(dataset_version)
        await extract_dataset()
        clean_up_downloads()
        write_dataset_version(dataset_version)
    else:
        print("Cached dataset found, skipping download and extraction.")
        dataset_version = read_dataset_version()

    report.set_title("Benchmark: TrackMatcher V1 vs TrackMatcher V2")
    report.add_meta("Dataset version", dataset_version)
    report.add_meta("Sample size", SAMPLE_SIZE)
    report.add_meta("Iterations", 5)
    report.add_meta("Acceptance floor", ACCEPTANCE_FLOOR)
    report.add_meta("Workers", mp.cpu_count())

    tracks = await load_tracks(tracks_file_path)

    report.add_meta("Track count", len(tracks))

    sampled = sample_tracks(tracks, SAMPLE_SIZE, SAMPLE_SEED)
    benchmark_dataset = generate_benchmark_dataset(sampled, tracks)

    report.add_meta("Total pairs", len(benchmark_dataset))

    results = run_scoring(benchmark_dataset)

    build_report(report, results)
    dump_fn_sample(results, benchmark_dataset, PARENT_DIR / f"report-{dataset_version}-fn.md")
    dump_fp_sample(results, benchmark_dataset, PARENT_DIR / f"report-{dataset_version}-fp.md")

    report.save(PARENT_DIR / f"report-{dataset_version}.md")

    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())