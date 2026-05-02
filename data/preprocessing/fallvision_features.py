"""Create baseline model features from cleaned FallVision keypoint sequences."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean, median


KEYPOINT_ORDER = [
    "Nose",
    "Left Eye",
    "Right Eye",
    "Left Ear",
    "Right Ear",
    "Left Shoulder",
    "Right Shoulder",
    "Left Elbow",
    "Right Elbow",
    "Left Wrist",
    "Right Wrist",
    "Left Hip",
    "Right Hip",
    "Left Knee",
    "Right Knee",
    "Left Ankle",
    "Right Ankle",
]

LABEL_TO_ID = {"No Fall": 0, "Fall": 1}
FEATURE_SERIES = [
    "head_y",
    "hip_y",
    "ankle_y",
    "body_height",
    "body_width",
    "height_width_ratio",
    "torso_angle_degrees",
    "mean_confidence",
]
STAT_NAMES = [
    "mean",
    "std",
    "min",
    "max",
    "first",
    "last",
    "delta",
    "max_abs_velocity",
    "mean_abs_velocity",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build train/val/test JSONL feature files from cleaned FallVision CSVs."
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed/FallVision"),
        help="Processed FallVision folder containing manifest.csv and cleaned_sequences/.",
    )
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def read_kept_manifest(processed_dir: Path) -> list[dict[str, str]]:
    manifest_path = processed_dir / "manifest.csv"
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest: {manifest_path}. Run fallvision_keypoints.py first.")

    with manifest_path.open(newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["is_kept"] == "True"]

    if not rows:
        raise SystemExit(f"No kept rows found in {manifest_path}")

    return rows


def to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_sequence(path: Path) -> list[dict[str, dict[str, float]]]:
    frames: dict[str, dict[str, dict[str, float]]] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            frames.setdefault(row["Frame"], {})[row["Keypoint"]] = {
                "x": to_float(row["X"]),
                "y": to_float(row["Y"]),
                "confidence": to_float(row["Confidence"]),
            }

    ordered_frames = []
    for frame in sorted(frames, key=lambda value: int(float(value))):
        keypoints = frames[frame]
        if all(name in keypoints for name in KEYPOINT_ORDER):
            ordered_frames.append(keypoints)
    return ordered_frames


def midpoint(frame: dict[str, dict[str, float]], left: str, right: str) -> tuple[float, float]:
    return (
        (frame[left]["x"] + frame[right]["x"]) / 2,
        (frame[left]["y"] + frame[right]["y"]) / 2,
    )


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def clip_scale(frames: list[dict[str, dict[str, float]]]) -> float:
    torso_lengths = []
    for frame in frames:
        shoulders = midpoint(frame, "Left Shoulder", "Right Shoulder")
        hips = midpoint(frame, "Left Hip", "Right Hip")
        length = distance(shoulders, hips)
        if length > 1:
            torso_lengths.append(length)
    if torso_lengths:
        return median(torso_lengths)
    return 1.0


def per_frame_series(frames: list[dict[str, dict[str, float]]]) -> dict[str, list[float]]:
    scale = clip_scale(frames)
    first_hips = midpoint(frames[0], "Left Hip", "Right Hip")
    series = {name: [] for name in FEATURE_SERIES}

    for frame in frames:
        shoulders = midpoint(frame, "Left Shoulder", "Right Shoulder")
        hips = midpoint(frame, "Left Hip", "Right Hip")
        left_ankle = frame["Left Ankle"]
        right_ankle = frame["Right Ankle"]
        ankle_y = (left_ankle["y"] + right_ankle["y"]) / 2
        ys = [frame[name]["y"] for name in KEYPOINT_ORDER]
        xs = [frame[name]["x"] for name in KEYPOINT_ORDER]
        body_height = (max(ys) - min(ys)) / scale
        body_width = (max(xs) - min(xs)) / scale
        torso_angle = math.degrees(math.atan2(hips[1] - shoulders[1], hips[0] - shoulders[0]))
        confidences = [frame[name]["confidence"] for name in KEYPOINT_ORDER]

        series["head_y"].append((frame["Nose"]["y"] - first_hips[1]) / scale)
        series["hip_y"].append((hips[1] - first_hips[1]) / scale)
        series["ankle_y"].append((ankle_y - first_hips[1]) / scale)
        series["body_height"].append(body_height)
        series["body_width"].append(body_width)
        series["height_width_ratio"].append(body_height / max(body_width, 1e-6))
        series["torso_angle_degrees"].append(torso_angle)
        series["mean_confidence"].append(mean(confidences))

    return series


def std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / len(values))


def velocities(values: list[float]) -> list[float]:
    return [values[index] - values[index - 1] for index in range(1, len(values))]


def describe(values: list[float]) -> list[float]:
    diffs = velocities(values)
    abs_diffs = [abs(value) for value in diffs]
    return [
        mean(values),
        std(values),
        min(values),
        max(values),
        values[0],
        values[-1],
        values[-1] - values[0],
        max(abs_diffs) if abs_diffs else 0.0,
        mean(abs_diffs) if abs_diffs else 0.0,
    ]


def build_feature_vector(sequence_path: Path) -> tuple[list[float], int]:
    frames = load_sequence(sequence_path)
    if not frames:
        raise ValueError(f"No complete frames in {sequence_path}")

    series = per_frame_series(frames)
    features = [len(frames) / 100.0]
    for name in FEATURE_SERIES:
        features.extend(describe(series[name]))
    return [round(value, 8) for value in features], len(frames)


def split_rows(
    rows: list[dict[str, str]],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[dict[str, str]]]:
    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        raise SystemExit("train/val/test ratios must sum to 1.0")

    randomizer = random.Random(seed)
    buckets: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        buckets[(row["label"], row["scene"])].append(row)

    splits = {"train": [], "val": [], "test": []}
    for bucket_rows in buckets.values():
        bucket_rows = bucket_rows[:]
        randomizer.shuffle(bucket_rows)
        count = len(bucket_rows)
        train_end = round(count * train_ratio)
        val_end = train_end + round(count * val_ratio)
        splits["train"].extend(bucket_rows[:train_end])
        splits["val"].extend(bucket_rows[train_end:val_end])
        splits["test"].extend(bucket_rows[val_end:])

    for split_rows_ in splits.values():
        randomizer.shuffle(split_rows_)
    return splits


def feature_names() -> list[str]:
    names = ["frame_count_div_100"]
    for series_name in FEATURE_SERIES:
        names.extend(f"{series_name}_{stat_name}" for stat_name in STAT_NAMES)
    return names


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w") as handle:
        for record in records:
            json.dump(record, handle, separators=(",", ":"))
            handle.write("\n")


def write_split_manifest(path: Path, records: list[dict[str, object]]) -> None:
    fieldnames = [
        "split",
        "source_path",
        "cleaned_path",
        "label",
        "label_id",
        "scene",
        "clip_id",
        "frame_count",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: record[key] for key in fieldnames} for record in records)


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    summary: dict[str, object] = {"total_records": len(records), "splits": {}}
    for record in records:
        split = str(record["split"])
        label = str(record["label"])
        scene = str(record["scene"])
        split_summary = summary["splits"].setdefault(split, {"total": 0, "labels": {}, "scenes": {}})
        split_summary["total"] += 1
        split_summary["labels"][label] = split_summary["labels"].get(label, 0) + 1
        split_summary["scenes"][scene] = split_summary["scenes"].get(scene, 0) + 1
    return summary


def main() -> None:
    args = parse_args()
    processed_dir = args.processed_dir
    features_dir = processed_dir / "features"
    features_dir.mkdir(parents=True, exist_ok=True)

    rows = read_kept_manifest(processed_dir)
    splits = split_rows(rows, args.train_ratio, args.val_ratio, args.test_ratio, args.seed)
    all_records: list[dict[str, object]] = []

    for split, split_rows_ in splits.items():
        records = []
        for row in split_rows_:
            cleaned_path = processed_dir / row["output_path"]
            vector, frame_count = build_feature_vector(cleaned_path)
            record = {
                "split": split,
                "source_path": row["source_path"],
                "cleaned_path": row["output_path"],
                "label": row["label"],
                "label_id": LABEL_TO_ID[row["label"]],
                "scene": row["scene"],
                "clip_id": row["clip_id"],
                "frame_count": frame_count,
                "features": vector,
            }
            records.append(record)
            all_records.append(record)
        write_jsonl(features_dir / f"{split}.jsonl", records)

    write_split_manifest(features_dir / "split_manifest.csv", all_records)
    schema = {
        "feature_count": len(feature_names()),
        "feature_names": feature_names(),
        "label_to_id": LABEL_TO_ID,
        "split_ratios": {
            "train": args.train_ratio,
            "val": args.val_ratio,
            "test": args.test_ratio,
        },
        "seed": args.seed,
        "normalization": "y motion and body dimensions are normalized by each clip median torso length; y motion is relative to first-frame hip center",
    }
    with (features_dir / "feature_schema.json").open("w") as handle:
        json.dump(schema, handle, indent=2)
        handle.write("\n")
    with (features_dir / "summary.json").open("w") as handle:
        json.dump(summarize(all_records), handle, indent=2)
        handle.write("\n")

    print(f"Wrote features to {features_dir}")
    print(f"Feature count: {schema['feature_count']}")
    print(f"Records: {len(all_records)}")


if __name__ == "__main__":
    main()
