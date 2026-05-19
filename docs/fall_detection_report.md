# Fall Detection Training Report

## Training Strategy

The fall detection model uses a pose-based temporal strategy rather than raw image or video classification.
he fall detection model uses a pose-based temporal strategy rather than raw image or video classification.

The dataset used was:

```text
data/raw/FallVision
```

This dataset contains keypoint CSV files that were already extracted from video. Each row contains:

```text
Frame, Keypoint, X, Y, Confidence
```

The model uses two labels:

```text
Fall = 1
No Fall = 0
```

The dataset also preserves three scene contexts:

```text
Bed
Chair
Stand
```

Before training, the dataset was cleaned:

```text
Total raw CSV files: 1608
Kept after cleaning: 1569
Skipped: 39
```

Skipped files included:

```text
Empty CSVs: 3
Duplicate variant: 1
Too few cleaned frames: 35
```

A major issue was that many clips contained multiple detected people:

```text
Multi-person files: 1002
```

To handle this, each frame was reduced to one primary skeleton by selecting the complete 17-keypoint skeleton with the highest average confidence.

The cleaned skeleton format used 17 keypoints:

```text
Nose
Left Eye / Right Eye
Left Ear / Right Ear
Left Shoulder / Right Shoulder
Left Elbow / Right Elbow
Left Wrist / Right Wrist
Left Hip / Right Hip
Left Knee / Right Knee
Left Ankle / Right Ankle
```

## Feature Strategy

Each cleaned clip was converted into temporal motion features. The model does not classify single frames; it uses movement patterns across time.

The features include:

```text
head vertical movement
hip vertical movement
ankle vertical movement
body height
body width
height-to-width ratio
torso angle
pose confidence
velocity summaries
```

Each clip produced:

```text
73 features
```

The split was stratified by:

```text
label + scene
```

Final split:

```text
Train: 1098 clips
Validation: 236 clips
Test: 235 clips
Total: 1569 clips
```

Training distribution:

```text
Train:
Fall:    489
No Fall: 609

Validation:
Fall:    105
No Fall: 131

Test:
Fall:    104
No Fall: 131
```

## Model Used

The baseline model was:

```text
Logistic Regression
```

Training settings:

```text
Epochs: 400
Learning rate: 0.05
L2 regularisation: 0.001
Random seed: 42
Decision threshold: 0.54
```

The threshold was selected using the validation set.

## Validation Results

```text
Accuracy:        0.8941
Fall precision:  0.9082
Fall recall:     0.8476
Fall F1-score:   0.8768
Specificity:     0.9313
```

Validation confusion matrix:

```text
True Fall detected:      89
Missed Falls:            16
Correct No Fall:        122
False Fall alarms:        9
```

## Test Results

```text
Accuracy:        0.8809
Fall precision:  0.8585
Fall recall:     0.8750
Fall F1-score:   0.8667
Specificity:     0.8855
```

Test confusion matrix:

```text
True Fall detected:      91
Missed Falls:            13
Correct No Fall:        116
False Fall alarms:       15
```

## Results By Scene

```text
Bed:
Accuracy:        0.7816
Fall precision:  0.6829
Fall recall:     0.8235
Fall F1-score:   0.7467

Chair:
Accuracy:        0.9296
Fall precision:  0.9677
Fall recall:     0.8824
Fall F1-score:   0.9231

Stand:
Accuracy:        0.9481
Fall precision:  0.9706
Fall recall:     0.9167
Fall F1-score:   0.9429
```

## Interpretation

The model performs well overall, with a test fall recall of 87.5%. This means it detected most fall cases. This is important because in fall detection, missing a real fall is more serious than producing a false alarm.

The strongest performance was on:

```text
Stand
Chair
```

The weakest performance was on:

```text
Bed
```

This makes sense because bed scenes are more ambiguous. A person lying normally on a bed can look similar to a fall or post-fall lying posture. The bed category had more false positives and lower precision.

## Most Important Features

The most influential features were related to:

```text
hip movement variation
body height change
height-to-width ratio
head movement
ankle movement
pose confidence
```

The strongest feature was:

```text
hip_y_std
```

This means the model relied heavily on variation in hip movement, which is reasonable because falls usually involve a rapid change in body position.

## Conclusion

The baseline fall detection system successfully demonstrates that pose-based temporal features can classify Fall vs No Fall using the FallVision keypoint dataset.

The model achieved:

```text
Test accuracy: 88.09%
Fall recall:   87.50%
Fall F1-score: 86.67%
```

The results are promising for a lightweight baseline. However, the weaker performance on bed scenes shows that future work should focus on improving context-aware detection, especially distinguishing normal lying from fall events near beds.
