# Fall Detection

Pose-based fall detection for Watch4U.

This component uses the local `data/raw/FallVision` keypoint dataset, not the full raw-video FallVision dataset. The pipeline cleans keypoint CSVs, builds baseline motion features, trains a small classifier, and can run a webcam demo.

## What This Code Does

The current pipeline is:

```text
FallVision keypoint CSVs
  -> cleaned single-person skeleton sequences
  -> train/validation/test feature files
  -> baseline fall classifier
  -> webcam demo using live pose landmarks
```

The model is intentionally simple for now. It is a baseline logistic regression classifier trained on engineered temporal pose features. It is useful for proving the workflow and identifying weak cases before moving to an LSTM, TCN, Transformer, or other sequence model.

## Expected Dataset Layout

Put the FallVision keypoint CSVs here:

```text
data/raw/FallVision/
  Fall/
    Bed/
    Chair/
    Stand/
  No Fall/
    Bed/
    Chair/
    Stand/
```

Each CSV should use this schema:

```text
Frame,Keypoint,X,Y,Confidence
```

The label is read from the folder name:

```text
Fall     -> label 1
No Fall  -> label 0
```

The scene is also preserved:

```text
Bed / Chair / Stand
```

## Setup

From the project root:

```bash
python -m pip install -r backend/requirements.txt
```

For the preprocessing and baseline training scripts, no extra ML package is required. The webcam demo needs:

```text
opencv-python
mediapipe
```

These are listed in `backend/requirements.txt`.

## Step 1: Clean The Keypoint Dataset

Run:

```bash
python data/preprocessing/fallvision_keypoints.py
```

This writes:

```text
data/processed/FallVision/
  manifest.csv
  summary.json
  cleaned_sequences/
```

The cleaner:

- audits every raw CSV
- skips empty CSVs
- skips duplicate variants
- skips clips with too few usable frames
- handles multi-person frames by keeping the complete 17-keypoint skeleton with the highest average confidence
- writes one cleaned 17-keypoint skeleton per frame

Useful options:

```bash
python data/preprocessing/fallvision_keypoints.py --min-frames 24
python data/preprocessing/fallvision_keypoints.py --low-confidence-threshold 0.4
```

## Step 2: Build Model Features

Run:

```bash
python data/preprocessing/fallvision_features.py
```

This writes:

```text
data/processed/FallVision/features/
  train.jsonl
  val.jsonl
  test.jsonl
  split_manifest.csv
  feature_schema.json
  summary.json
```

The feature builder creates a stratified train/validation/test split by:

```text
label + scene
```

Each record contains:

```text
label
label_id
scene
clip_id
frame_count
features
```

The baseline features include:

- head, hip, and ankle vertical motion
- body height and width
- height-to-width ratio
- torso angle
- pose confidence
- velocity summaries

## Step 3: Train The Baseline Classifier

Run:

```bash
python data/preprocessing/fallvision_train_baseline.py
```

This writes:

```text
data/processed/FallVision/features/baseline_model/
  metrics.json
  model.json
```

The script:

- trains a dependency-free logistic regression model
- standardizes features using the training split
- chooses the decision threshold on the validation split
- reports test metrics overall and by scene

Current baseline results from the local dataset:

```text
Test accuracy:       0.8809
Test fall precision: 0.8585
Test fall recall:    0.8750
Test fall F1:        0.8667
```

Scene-level test F1:

```text
Bed:    0.7467
Chair:  0.9231
Stand:  0.9429
```

The weaker Bed result is expected because normal lying and fall-like postures are harder to separate near beds.

## Step 4: Test With A Webcam

First make sure the baseline model exists:

```bash
python data/preprocessing/fallvision_train_baseline.py
```

Then run:

```bash
python -m backend.app.services.fall_detection.webcam_demo --download-pose-model --mirror
```

The first run downloads the MediaPipe pose model to:

```text
data/models/pose_landmarker_lite.task
```

After the first run, use:

```bash
python -m backend.app.services.fall_detection.webcam_demo --mirror
```

If the webcam does not open, try a different camera index:

```bash
python -m backend.app.services.fall_detection.webcam_demo --camera 1 --mirror
```

Press `q` to quit the webcam window.

## Important Notes

This webcam demo is a prototype. It uses MediaPipe landmarks at runtime, while the model was trained on FallVision keypoints. The keypoint layout is mapped into the same 17-joint format, but the landmark source is not identical. Expect noisy behavior until the model is improved with more live-camera-like data.

The current model is also clip-level. In the webcam demo, predictions are made over a rolling pose window. This is good enough for testing, but a production fall detector should add:

- temporal smoothing
- event start/end detection
- long-lie detection
- false-positive suppression
- privacy-safe event logging

## Troubleshooting

If MediaPipe cannot install:

```bash
python -m pip install --upgrade --force-reinstall mediapipe==0.10.35
```

If OpenCV cannot access the camera:

```bash
python -m backend.app.services.fall_detection.webcam_demo --camera 1 --mirror
```

If the pose model is missing:

```bash
python -m backend.app.services.fall_detection.webcam_demo --download-pose-model --mirror
```

If `model.json` is missing:

```bash
python data/preprocessing/fallvision_keypoints.py
python data/preprocessing/fallvision_features.py
python data/preprocessing/fallvision_train_baseline.py
```

## Files

```text
data/preprocessing/fallvision_keypoints.py
  Cleans and audits raw FallVision keypoint CSVs.

data/preprocessing/fallvision_features.py
  Converts cleaned sequences into train/val/test feature JSONL files.

data/preprocessing/fallvision_train_baseline.py
  Trains and evaluates the baseline classifier.

backend/app/services/fall_detection/webcam_demo.py
  Runs the trained baseline model on webcam pose landmarks.
```

Generated data under `data/processed/` and downloaded models under `data/models/` should stay out of git.
