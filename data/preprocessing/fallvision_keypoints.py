"""Audit and clean the local FallVision keypoint CSV dataset.

This script is intentionally separate from fallvision.py, which assumes raw
videos. The local FallVision folder used here already contains pose keypoints.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


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

KEYPOINT_SET = set(KEYPOINT_ORDER)
FIELDNAMES = ["Frame", "Keypoint", "X", "Y", "Confidence"]
VARIANT_RE = re.compile(r"_(resized|anonymized)_keypoints\.csv$")


@dataclass
class CsvAudit:
    source_path: Path
    label: str
    scene: str
    clip_id: str
    variant: str
    output_path: Path | None = None
    row_count: int = 0
    frame_count: int = 0
    cleaned_frame_count: int = 0
    cleaned_row_count: int = 0
    skipped_frame_count: int = 0
    min_rows_per_frame: int = 0
    max_rows_per_frame: int = 0
    max_people_per_frame_estimate: int = 0
    mean_confidence: float | None = None
    min_confidence: float | None = None
    max_confidence: float | None = None
    has_empty_data: bool = False
    has_multiple_people: bool = False
    has_partial_person_rows: bool = False
    is_duplicate_variant: bool = False
    is_kept: bool = False
    skip_reason: str = ""
    warnings: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit FallVision keypoint CSVs and write cleaned sequences."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/FallVision"),
        help="Input FallVision keypoint folder.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed/FallVision"),
        help="Output folder for manifest, summary, and cleaned CSVs.",
    )
    parser.add_argument(
        "--min-frames",
        type=int,
        default=16,
        help="Minimum cleaned frames required to keep a clip.",
    )
    parser.add_argument(
        "--low-confidence-threshold",
        type=float,
        default=0.35,
        help="Mean confidence below this value is flagged in the manifest.",
    )
    return parser.parse_args()


def detect_variant(path: Path) -> str:
    if "_anonymized_keypoints.csv" in path.name:
        return "anonymized"
    if "_resized_keypoints.csv" in path.name:
        return "resized"
    return "original"


def base_clip_name(path: Path) -> str:
    return VARIANT_RE.sub("_keypoints.csv", path.name)


def iter_source_files(raw_dir: Path) -> Iterable[Path]:
    yield from sorted(raw_dir.rglob("*.csv"))


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    warnings: list[str] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDNAMES:
            warnings.append(f"unexpected_header={reader.fieldnames}")
        rows = [row for row in reader]
    return rows, warnings


def numeric_frame_key(frame: str) -> tuple[int, str]:
    try:
        return int(float(frame)), frame
    except ValueError:
        return math.inf, frame


def confidence(row: dict[str, str]) -> float:
    try:
        return float(row["Confidence"])
    except (KeyError, TypeError, ValueError):
        return 0.0


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def candidate_chunks(rows: list[dict[str, str]]) -> tuple[list[list[dict[str, str]]], bool]:
    chunks: list[list[dict[str, str]]] = []
    has_partial = False
    for start in range(0, len(rows), len(KEYPOINT_ORDER)):
        chunk = rows[start : start + len(KEYPOINT_ORDER)]
        if len(chunk) != len(KEYPOINT_ORDER):
            has_partial = True
            continue
        chunks.append(chunk)
    return chunks, has_partial


def choose_primary_person(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]] | None, bool]:
    chunks, has_partial = candidate_chunks(rows)
    complete_chunks = []

    for chunk in chunks:
        keypoints = [row.get("Keypoint", "") for row in chunk]
        if set(keypoints) == KEYPOINT_SET:
            complete_chunks.append(chunk)

    if not complete_chunks:
        return None, has_partial

    return max(complete_chunks, key=lambda chunk: mean([confidence(row) for row in chunk]) or 0), has_partial


def reorder_keypoints(frame: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_keypoint = {row["Keypoint"]: row for row in rows}
    ordered_rows = []
    for keypoint in KEYPOINT_ORDER:
        row = by_keypoint[keypoint]
        ordered_rows.append(
            {
                "Frame": frame,
                "Keypoint": keypoint,
                "X": row["X"],
                "Y": row["Y"],
                "Confidence": row["Confidence"],
            }
        )
    return ordered_rows


def audit_and_clean_file(
    path: Path,
    raw_dir: Path,
    processed_dir: Path,
    duplicate_keys: set[tuple[str, str, str]],
    min_frames: int,
    low_confidence_threshold: float,
) -> CsvAudit:
    relative_parts = path.relative_to(raw_dir).parts
    label = relative_parts[0]
    scene = relative_parts[1]
    clip_id = base_clip_name(path).replace("_keypoints.csv", "")
    variant = detect_variant(path)
    audit = CsvAudit(
        source_path=path,
        label=label,
        scene=scene,
        clip_id=clip_id,
        variant=variant,
    )

    rows, warnings = read_rows(path)
    audit.warnings.extend(warnings)
    audit.row_count = len(rows)
    audit.has_empty_data = len(rows) == 0

    if audit.has_empty_data:
        audit.skip_reason = "empty_csv"
        return audit

    frames: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    confidences: list[float] = []
    for row in rows:
        frames.setdefault(row["Frame"], []).append(row)
        confidences.append(confidence(row))

    rows_per_frame = [len(frame_rows) for frame_rows in frames.values()]
    audit.frame_count = len(frames)
    audit.min_rows_per_frame = min(rows_per_frame)
    audit.max_rows_per_frame = max(rows_per_frame)
    audit.max_people_per_frame_estimate = math.ceil(audit.max_rows_per_frame / len(KEYPOINT_ORDER))
    audit.has_multiple_people = audit.max_rows_per_frame > len(KEYPOINT_ORDER)
    audit.mean_confidence = mean(confidences)
    audit.min_confidence = min(confidences)
    audit.max_confidence = max(confidences)

    duplicate_key = (label, scene, base_clip_name(path))
    audit.is_duplicate_variant = duplicate_key in duplicate_keys and variant != "original"
    if audit.is_duplicate_variant:
        audit.skip_reason = "duplicate_variant"
        return audit

    cleaned_rows: list[dict[str, str]] = []
    for frame, frame_rows in sorted(frames.items(), key=lambda item: numeric_frame_key(item[0])):
        selected_rows, has_partial = choose_primary_person(frame_rows)
        audit.has_partial_person_rows = audit.has_partial_person_rows or has_partial
        if selected_rows is None:
            audit.skipped_frame_count += 1
            continue
        cleaned_rows.extend(reorder_keypoints(frame, selected_rows))

    audit.cleaned_row_count = len(cleaned_rows)
    audit.cleaned_frame_count = audit.cleaned_row_count // len(KEYPOINT_ORDER)

    if audit.cleaned_frame_count < min_frames:
        audit.skip_reason = f"too_few_cleaned_frames<{min_frames}"
        return audit

    if audit.mean_confidence is not None and audit.mean_confidence < low_confidence_threshold:
        audit.warnings.append("low_mean_confidence")

    output_path = processed_dir / "cleaned_sequences" / label.replace(" ", "_") / scene / path.name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    audit.output_path = output_path
    audit.is_kept = True
    return audit


def find_duplicate_variant_keys(files: list[Path], raw_dir: Path) -> set[tuple[str, str, str]]:
    groups: dict[tuple[str, str, str], set[str]] = {}
    for path in files:
        relative_parts = path.relative_to(raw_dir).parts
        key = (relative_parts[0], relative_parts[1], base_clip_name(path))
        groups.setdefault(key, set()).add(detect_variant(path))
    return {key for key, variants in groups.items() if len(variants) > 1}


def audit_to_row(audit: CsvAudit, raw_dir: Path, processed_dir: Path) -> dict[str, str | int | float | bool]:
    return {
        "source_path": str(audit.source_path.relative_to(raw_dir)),
        "output_path": (
            str(audit.output_path.relative_to(processed_dir)) if audit.output_path else ""
        ),
        "label": audit.label,
        "scene": audit.scene,
        "clip_id": audit.clip_id,
        "variant": audit.variant,
        "row_count": audit.row_count,
        "frame_count": audit.frame_count,
        "cleaned_row_count": audit.cleaned_row_count,
        "cleaned_frame_count": audit.cleaned_frame_count,
        "skipped_frame_count": audit.skipped_frame_count,
        "min_rows_per_frame": audit.min_rows_per_frame,
        "max_rows_per_frame": audit.max_rows_per_frame,
        "max_people_per_frame_estimate": audit.max_people_per_frame_estimate,
        "mean_confidence": "" if audit.mean_confidence is None else round(audit.mean_confidence, 6),
        "min_confidence": "" if audit.min_confidence is None else round(audit.min_confidence, 6),
        "max_confidence": "" if audit.max_confidence is None else round(audit.max_confidence, 6),
        "has_empty_data": audit.has_empty_data,
        "has_multiple_people": audit.has_multiple_people,
        "has_partial_person_rows": audit.has_partial_person_rows,
        "is_duplicate_variant": audit.is_duplicate_variant,
        "is_kept": audit.is_kept,
        "skip_reason": audit.skip_reason,
        "warnings": "|".join(audit.warnings),
    }


def write_manifest(audits: list[CsvAudit], raw_dir: Path, processed_dir: Path) -> None:
    manifest_path = processed_dir / "manifest.csv"
    rows = [audit_to_row(audit, raw_dir, processed_dir) for audit in audits]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(audits: list[CsvAudit], processed_dir: Path) -> dict[str, object]:
    summary: dict[str, object] = {
        "total_files": len(audits),
        "kept_files": sum(audit.is_kept for audit in audits),
        "skipped_files": sum(not audit.is_kept for audit in audits),
        "empty_files": sum(audit.has_empty_data for audit in audits),
        "duplicate_variant_files": sum(audit.is_duplicate_variant for audit in audits),
        "multi_person_files": sum(audit.has_multiple_people for audit in audits),
        "partial_person_row_files": sum(audit.has_partial_person_rows for audit in audits),
        "low_confidence_warning_files": sum(
            "low_mean_confidence" in audit.warnings for audit in audits
        ),
        "buckets": {},
        "skip_reasons": {},
        "schema": {
            "cleaned_sequence": FIELDNAMES,
            "keypoint_order": KEYPOINT_ORDER,
            "primary_person_rule": "choose the complete 17-keypoint skeleton with highest mean confidence per frame",
        },
    }

    buckets: dict[str, dict[str, int]] = {}
    skip_reasons: dict[str, int] = {}
    for audit in audits:
        bucket = f"{audit.label}/{audit.scene}"
        buckets.setdefault(bucket, {"total": 0, "kept": 0})
        buckets[bucket]["total"] += 1
        buckets[bucket]["kept"] += int(audit.is_kept)
        if audit.skip_reason:
            skip_reasons[audit.skip_reason] = skip_reasons.get(audit.skip_reason, 0) + 1

    summary["buckets"] = dict(sorted(buckets.items()))
    summary["skip_reasons"] = dict(sorted(skip_reasons.items()))

    summary_path = processed_dir / "summary.json"
    with summary_path.open("w") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    return summary


def main() -> None:
    args = parse_args()
    raw_dir = args.raw_dir
    processed_dir = args.processed_dir

    if not raw_dir.exists():
        raise SystemExit(f"Raw directory does not exist: {raw_dir}")

    files = list(iter_source_files(raw_dir))
    if not files:
        raise SystemExit(f"No CSV files found under: {raw_dir}")

    duplicate_keys = find_duplicate_variant_keys(files, raw_dir)
    audits = [
        audit_and_clean_file(
            path=path,
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            duplicate_keys=duplicate_keys,
            min_frames=args.min_frames,
            low_confidence_threshold=args.low_confidence_threshold,
        )
        for path in files
    ]

    write_manifest(audits, raw_dir, processed_dir)
    summary = summarize(audits, processed_dir)

    print(f"Audited {summary['total_files']} files")
    print(f"Kept {summary['kept_files']} cleaned sequences")
    print(f"Skipped {summary['skipped_files']} files")
    print(f"Wrote {processed_dir / 'manifest.csv'}")
    print(f"Wrote {processed_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
