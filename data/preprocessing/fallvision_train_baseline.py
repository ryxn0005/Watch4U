"""Train a dependency-free baseline fall classifier on FallVision features."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a simple logistic regression baseline from FallVision JSONL features."
    )
    parser.add_argument(
        "--features-dir",
        type=Path,
        default=Path("data/processed/FallVision/features"),
        help="Folder containing train.jsonl, val.jsonl, test.jsonl, and feature_schema.json.",
    )
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}. Run fallvision_features.py first.")
    records = []
    with path.open() as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def matrix(records: list[dict[str, object]]) -> tuple[list[list[float]], list[int]]:
    return (
        [[float(value) for value in record["features"]] for record in records],
        [int(record["label_id"]) for record in records],
    )


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def fit_standardizer(features: list[list[float]]) -> tuple[list[float], list[float]]:
    count = len(features)
    width = len(features[0])
    means = [sum(row[index] for row in features) / count for index in range(width)]
    scales = []
    for index in range(width):
        variance = sum((row[index] - means[index]) ** 2 for row in features) / count
        scale = math.sqrt(variance)
        scales.append(scale if scale > 1e-12 else 1.0)
    return means, scales


def transform(features: list[list[float]], means: list[float], scales: list[float]) -> list[list[float]]:
    return [
        [(value - means[index]) / scales[index] for index, value in enumerate(row)]
        for row in features
    ]


def predict_proba(features: list[list[float]], weights: list[float], bias: float) -> list[float]:
    probabilities = []
    for row in features:
        score = bias + sum(weight * value for weight, value in zip(weights, row))
        probabilities.append(sigmoid(score))
    return probabilities


def binary_cross_entropy(probabilities: list[float], labels: list[int]) -> float:
    epsilon = 1e-12
    losses = []
    for probability, label in zip(probabilities, labels):
        p = min(max(probability, epsilon), 1 - epsilon)
        losses.append(-(label * math.log(p) + (1 - label) * math.log(1 - p)))
    return sum(losses) / len(losses)


def train_logistic_regression(
    features: list[list[float]],
    labels: list[int],
    epochs: int,
    learning_rate: float,
    l2: float,
    seed: int,
) -> tuple[list[float], float, list[dict[str, float]]]:
    randomizer = random.Random(seed)
    width = len(features[0])
    weights = [0.0] * width
    bias = 0.0
    history = []
    indices = list(range(len(features)))

    for epoch in range(1, epochs + 1):
        randomizer.shuffle(indices)
        for row_index in indices:
            row = features[row_index]
            label = labels[row_index]
            probability = sigmoid(bias + sum(weight * value for weight, value in zip(weights, row)))
            error = probability - label
            for feature_index, value in enumerate(row):
                weights[feature_index] -= learning_rate * (error * value + l2 * weights[feature_index])
            bias -= learning_rate * error

        if epoch == 1 or epoch % 25 == 0 or epoch == epochs:
            probabilities = predict_proba(features, weights, bias)
            loss = binary_cross_entropy(probabilities, labels)
            history.append({"epoch": epoch, "train_loss": round(loss, 6)})

    return weights, bias, history


def metrics_at_threshold(
    probabilities: list[float],
    labels: list[int],
    threshold: float,
) -> dict[str, float | int]:
    tp = fp = tn = fn = 0
    for probability, label in zip(probabilities, labels):
        predicted = int(probability >= threshold)
        if predicted == 1 and label == 1:
            tp += 1
        elif predicted == 1 and label == 0:
            fp += 1
        elif predicted == 0 and label == 0:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(labels) if labels else 0.0
    return {
        "threshold": round(threshold, 4),
        "accuracy": round(accuracy, 4),
        "fall_precision": round(precision, 4),
        "fall_recall": round(recall, 4),
        "fall_f1": round(f1, 4),
        "no_fall_specificity": round(specificity, 4),
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
    }


def choose_threshold(probabilities: list[float], labels: list[int]) -> float:
    candidates = [index / 100 for index in range(5, 96)]
    best_threshold = 0.5
    best_score = (-1.0, -1.0)
    for threshold in candidates:
        result = metrics_at_threshold(probabilities, labels, threshold)
        score = (float(result["fall_f1"]), float(result["fall_recall"]))
        if score > best_score:
            best_score = score
            best_threshold = threshold
    return best_threshold


def scene_metrics(
    records: list[dict[str, object]],
    probabilities: list[float],
    threshold: float,
) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, tuple[list[float], list[int]]] = {}
    for record, probability in zip(records, probabilities):
        scene = str(record["scene"])
        if scene not in grouped:
            grouped[scene] = ([], [])
        grouped[scene][0].append(probability)
        grouped[scene][1].append(int(record["label_id"]))
    return {
        scene: metrics_at_threshold(scene_probabilities, scene_labels, threshold)
        for scene, (scene_probabilities, scene_labels) in sorted(grouped.items())
    }


def top_weights(
    weights: list[float],
    feature_names: list[str],
    limit: int = 12,
) -> list[dict[str, float | str]]:
    ranked = sorted(
        zip(feature_names, weights),
        key=lambda item: abs(item[1]),
        reverse=True,
    )
    return [
        {"feature": name, "weight": round(weight, 6)}
        for name, weight in ranked[:limit]
    ]


def main() -> None:
    args = parse_args()
    features_dir = args.features_dir
    train_records = read_jsonl(features_dir / "train.jsonl")
    val_records = read_jsonl(features_dir / "val.jsonl")
    test_records = read_jsonl(features_dir / "test.jsonl")

    with (features_dir / "feature_schema.json").open() as handle:
        feature_schema = json.load(handle)

    train_x, train_y = matrix(train_records)
    val_x, val_y = matrix(val_records)
    test_x, test_y = matrix(test_records)
    means, scales = fit_standardizer(train_x)
    train_x = transform(train_x, means, scales)
    val_x = transform(val_x, means, scales)
    test_x = transform(test_x, means, scales)

    weights, bias, history = train_logistic_regression(
        features=train_x,
        labels=train_y,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
        seed=args.seed,
    )

    val_probabilities = predict_proba(val_x, weights, bias)
    threshold = choose_threshold(val_probabilities, val_y)
    test_probabilities = predict_proba(test_x, weights, bias)

    results = {
        "model": "stdlib_logistic_regression",
        "positive_label": "Fall",
        "training": {
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "l2": args.l2,
            "seed": args.seed,
            "history": history,
        },
        "validation": metrics_at_threshold(val_probabilities, val_y, threshold),
        "test": metrics_at_threshold(test_probabilities, test_y, threshold),
        "test_by_scene": scene_metrics(test_records, test_probabilities, threshold),
        "top_weighted_features": top_weights(weights, feature_schema["feature_names"]),
    }

    model = {
        "model": "stdlib_logistic_regression",
        "feature_names": feature_schema["feature_names"],
        "means": means,
        "scales": scales,
        "weights": weights,
        "bias": bias,
        "threshold": threshold,
        "label_to_id": feature_schema["label_to_id"],
    }

    output_dir = features_dir / "baseline_model"
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "metrics.json").open("w") as handle:
        json.dump(results, handle, indent=2)
        handle.write("\n")
    with (output_dir / "model.json").open("w") as handle:
        json.dump(model, handle, indent=2)
        handle.write("\n")

    print(f"Wrote {output_dir / 'metrics.json'}")
    print(f"Wrote {output_dir / 'model.json'}")
    print("Validation:", results["validation"])
    print("Test:", results["test"])


if __name__ == "__main__":
    main()
