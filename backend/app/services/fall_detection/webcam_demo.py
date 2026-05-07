"""Webcam demo for the FallVision baseline fall detector.

Run from the project root after training the baseline model:

    python -m backend.app.services.fall_detection.webcam_demo

Press q to quit.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.request
from collections import deque
from pathlib import Path
from statistics import mean, median


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "FallVision"
    / "features"
    / "baseline_model"
    / "model.json"
)
POSE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
DEFAULT_POSE_MODEL_PATH = PROJECT_ROOT / "data" / "models" / "pose_landmarker_lite.task"

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

MEDIAPIPE_INDEX = {
    "Nose": 0,
    "Left Eye": 2,
    "Right Eye": 5,
    "Left Ear": 7,
    "Right Ear": 8,
    "Left Shoulder": 11,
    "Right Shoulder": 12,
    "Left Elbow": 13,
    "Right Elbow": 14,
    "Left Wrist": 15,
    "Right Wrist": 16,
    "Left Hip": 23,
    "Right Hip": 24,
    "Left Knee": 25,
    "Right Knee": 26,
    "Left Ankle": 27,
    "Right Ankle": 28,
}

SKELETON_EDGES = [
    ("Left Shoulder", "Right Shoulder"),
    ("Left Shoulder", "Left Elbow"),
    ("Left Elbow", "Left Wrist"),
    ("Right Shoulder", "Right Elbow"),
    ("Right Elbow", "Right Wrist"),
    ("Left Shoulder", "Left Hip"),
    ("Right Shoulder", "Right Hip"),
    ("Left Hip", "Right Hip"),
    ("Left Hip", "Left Knee"),
    ("Left Knee", "Left Ankle"),
    ("Right Hip", "Right Knee"),
    ("Right Knee", "Right Ankle"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the baseline fall detector on a webcam.")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--window-frames", type=int, default=96)
    parser.add_argument("--min-frames", type=int, default=24)
    parser.add_argument(
        "--pose-model-path",
        type=Path,
        default=DEFAULT_POSE_MODEL_PATH,
        help="MediaPipe Tasks pose landmarker .task model path.",
    )
    parser.add_argument(
        "--download-pose-model",
        action="store_true",
        help="Download the MediaPipe lite pose landmarker model if it is missing.",
    )
    parser.add_argument("--mirror", action="store_true", help="Mirror the webcam image.")
    return parser.parse_args()


def require_webcam_dependencies():
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Webcam demo requires opencv-python.\n"
            "Install them in your environment, for example:\n"
            "  python -m pip install opencv-python\n"
            "or rebuild the backend container after installing requirements."
        ) from exc

    try:
        import mediapipe as mp  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Webcam demo requires mediapipe.\n"
            "Install it in your environment, for example:\n"
            "  python -m pip install mediapipe"
        ) from exc

    try:
        return cv2, {"api": "solutions", "pose": mp.solutions.pose}
    except AttributeError:
        pass

    try:
        from mediapipe.tasks import python as mp_python  # type: ignore
        from mediapipe.tasks.python import vision  # type: ignore

        return cv2, {
            "api": "tasks",
            "mp": mp,
            "base_options": mp_python.BaseOptions,
            "vision": vision,
        }
    except ImportError as exc:
        raise SystemExit(
            "This mediapipe install exposes neither the old solutions.pose API nor "
            "the newer tasks.vision PoseLandmarker API.\n"
            "Try installing one of the versions available for your Python:\n"
            "  python -m pip install --upgrade --force-reinstall mediapipe==0.10.35"
        ) from exc


def ensure_pose_model(path: Path, should_download: bool) -> Path:
    if path.exists():
        return path
    if not should_download:
        raise SystemExit(
            f"MediaPipe Tasks needs a pose model file and it was not found:\n"
            f"  {path}\n\n"
            "Download it with:\n"
            f"  python -m backend.app.services.fall_detection.webcam_demo --download-pose-model --mirror\n\n"
            "Or manually:\n"
            f"  mkdir -p {path.parent}\n"
            f"  wget -O {path} {POSE_MODEL_URL}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading pose model to {path}")
    urllib.request.urlretrieve(POSE_MODEL_URL, path)
    return path


class PoseEstimator:
    def detect(self, rgb_frame, width: int, height: int):
        raise NotImplementedError

    def close(self) -> None:
        pass


class SolutionsPoseEstimator(PoseEstimator):
    def __init__(self, mp_pose):
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def detect(self, rgb_frame, width: int, height: int):
        result = self.pose.process(rgb_frame)
        if not result.pose_landmarks:
            return None
        return mediapipe_to_keypoints(result.pose_landmarks.landmark, width, height)

    def close(self) -> None:
        self.pose.close()


class TasksPoseEstimator(PoseEstimator):
    def __init__(self, deps: dict[str, object], model_path: Path):
        self.mp = deps["mp"]
        vision = deps["vision"]
        base_options = deps["base_options"]
        options = vision.PoseLandmarkerOptions(
            base_options=base_options(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)
        self.timestamp_ms = 0

    def detect(self, rgb_frame, width: int, height: int):
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb_frame)
        self.timestamp_ms += 33
        result = self.landmarker.detect_for_video(image, self.timestamp_ms)
        if not result.pose_landmarks:
            return None
        return mediapipe_to_keypoints(result.pose_landmarks[0], width, height)

    def close(self) -> None:
        self.landmarker.close()


def create_pose_estimator(deps: dict[str, object], args: argparse.Namespace) -> PoseEstimator:
    if deps["api"] == "solutions":
        return SolutionsPoseEstimator(deps["pose"])

    model_path = ensure_pose_model(args.pose_model_path, args.download_pose_model)
    return TasksPoseEstimator(deps, model_path)


def load_model(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(
            f"Missing model file: {path}\n"
            "Run: python data/preprocessing/fallvision_train_baseline.py"
        )
    with path.open() as handle:
        return json.load(handle)


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
    return median(torso_lengths) if torso_lengths else 1.0


def per_frame_series(frames: list[dict[str, dict[str, float]]]) -> dict[str, list[float]]:
    scale = clip_scale(frames)
    first_hips = midpoint(frames[0], "Left Hip", "Right Hip")
    series = {name: [] for name in FEATURE_SERIES}

    for frame in frames:
        shoulders = midpoint(frame, "Left Shoulder", "Right Shoulder")
        hips = midpoint(frame, "Left Hip", "Right Hip")
        ankle_y = (frame["Left Ankle"]["y"] + frame["Right Ankle"]["y"]) / 2
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


def describe(values: list[float]) -> list[float]:
    diffs = [values[index] - values[index - 1] for index in range(1, len(values))]
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


def build_feature_vector(frames: list[dict[str, dict[str, float]]]) -> list[float]:
    series = per_frame_series(frames)
    features = [len(frames) / 100.0]
    for name in FEATURE_SERIES:
        features.extend(describe(series[name]))
    return features


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def predict_fall_probability(features: list[float], model: dict[str, object]) -> float:
    means = [float(value) for value in model["means"]]
    scales = [float(value) for value in model["scales"]]
    weights = [float(value) for value in model["weights"]]
    bias = float(model["bias"])
    standardized = [
        (value - means[index]) / scales[index]
        for index, value in enumerate(features)
    ]
    score = bias + sum(weight * value for weight, value in zip(weights, standardized))
    return sigmoid(score)


def mediapipe_to_keypoints(
    landmarks,
    width: int,
    height: int,
) -> dict[str, dict[str, float]]:
    keypoints = {}
    for keypoint, index in MEDIAPIPE_INDEX.items():
        landmark = landmarks[index]
        keypoints[keypoint] = {
            "x": landmark.x * width,
            "y": landmark.y * height,
            "confidence": getattr(landmark, "visibility", 1.0),
        }
    return keypoints


def draw_skeleton(cv2, frame, keypoints: dict[str, dict[str, float]]) -> None:
    for start, end in SKELETON_EDGES:
        start_point = keypoints[start]
        end_point = keypoints[end]
        cv2.line(
            frame,
            (int(start_point["x"]), int(start_point["y"])),
            (int(end_point["x"]), int(end_point["y"])),
            (0, 220, 255),
            2,
        )
    for point in keypoints.values():
        cv2.circle(frame, (int(point["x"]), int(point["y"])), 3, (0, 255, 0), -1)


def overlay_status(
    cv2,
    frame,
    probability: float | None,
    threshold: float,
    buffered_frames: int,
    min_frames: int,
) -> None:
    if probability is None:
        label = f"Collecting pose frames {buffered_frames}/{min_frames}"
        color = (255, 255, 255)
    else:
        is_fall = probability >= threshold
        label = f"{'FALL' if is_fall else 'NO FALL'}  probability={probability:.2f}  threshold={threshold:.2f}"
        color = (0, 0, 255) if is_fall else (0, 180, 0)

    cv2.rectangle(frame, (12, 12), (760, 58), (0, 0, 0), -1)
    cv2.putText(frame, label, (24, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(
        frame,
        "Press q to quit",
        (24, frame.shape[0] - 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
    )


def main() -> None:
    args = parse_args()
    cv2, pose_deps = require_webcam_dependencies()
    model = load_model(args.model_path)
    threshold = float(model["threshold"])
    pose_buffer: deque[dict[str, dict[str, float]]] = deque(maxlen=args.window_frames)

    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        raise SystemExit(f"Could not open webcam index {args.camera}")

    pose = create_pose_estimator(pose_deps, args)

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                raise SystemExit("Could not read a frame from the webcam")

            if args.mirror:
                frame = cv2.flip(frame, 1)

            height, width = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            keypoints = pose.detect(rgb, width, height)
            probability = None

            if keypoints:
                pose_buffer.append(keypoints)
                draw_skeleton(cv2, frame, keypoints)

                if len(pose_buffer) >= args.min_frames:
                    features = build_feature_vector(list(pose_buffer))
                    probability = predict_fall_probability(features, model)

            overlay_status(cv2, frame, probability, threshold, len(pose_buffer), args.min_frames)
            cv2.imshow("Watch4U Fall Detection Webcam Demo", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        pose.close()
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
