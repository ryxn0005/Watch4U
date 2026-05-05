import os
import cv2
import glob
import yaml
from sklearn.model_selection import train_test_split

RAW_DIR = "../raw/omnifall"
PROCESSED_DIR = "../processed/omnifall"

def setup_yolo_directories():
    """Creates the folder structure required by YOLO."""
    for split in ['train', 'val']:
        for category in ['Fall', 'No_Fall']:
            os.makedirs(os.path.join(PROCESSED_DIR, split, category), exist_ok=True)

def align_label(original_label):
    """Translates OmniFall's complex labels into YOLO binary folders."""
    original_label = original_label.lower()
    fall_keywords = ['fall', 'fallen', 'fallsitting', 'fallbackwards', 'fallleft']
    
    if any(keyword in original_label for keyword in fall_keywords):
        return "Fall"
    return "No_Fall"

def process_video_for_yolo(video_path, split, aligned_category, video_id):
    """Extracts frames and resizes them to YOLO's standard 640x640."""
    cap = cv2.VideoCapture(video_path)
    frame_count = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        # Extract 1 frame per second to prevent dataset bloat
        if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % 30 == 0:
            resized_frame = cv2.resize(frame, (640, 640))
            frame_filename = f"{video_id}_f{frame_count}.jpg"
            frame_path = os.path.join(PROCESSED_DIR, split, aligned_category, frame_filename)
            
            cv2.imwrite(frame_path, resized_frame)
            frame_count += 1

    cap.release()
    return frame_count

def generate_yolo_yaml():
    """Creates the dataset.yaml file for OmniFall."""
    yaml_content = {
        "path": os.path.abspath(PROCESSED_DIR),
        "train": "train",
        "val": "val",
        "names": {
            0: "Fall",
            1: "No_Fall"
        }
    }
    yaml_path = os.path.join(PROCESSED_DIR, "dataset.yaml")
    with open(yaml_path, "w") as f:
        yaml.dump(yaml_content, f, sort_keys=False)

def run_pipeline():
    print("Starting YOLO-Optimized OmniFall Pipeline...")
    setup_yolo_directories()
    
    # Assuming OmniFall videos have the label in the filename or folder name
    all_videos = glob.glob(f"{RAW_DIR}/**/*.mp4", recursive=True)
    
    if not all_videos:
        print(f" No videos found in {RAW_DIR}.")
        return

    train_vids, val_vids = train_test_split(all_videos, test_size=0.2, random_state=42)
    
    total_frames = 0
    for split, vids in [("train", train_vids), ("val", val_vids)]:
        for vid_path in vids:
            # Extract the original complex label from the filename/folder
            # (e.g., 'fallbackwards_01.mp4' -> 'fallbackwards')
            raw_label = os.path.basename(vid_path).split('_')[0] 
            
            # Align it to Fall / No_Fall
            aligned_category = align_label(raw_label)
            video_id = os.path.basename(vid_path).replace('.mp4', '')
            
            frames = process_video_for_yolo(vid_path, split, aligned_category, video_id)
            total_frames += frames
            
    generate_yolo_yaml()
    print(f" Pipeline complete. OmniFall frames formatted for YOLO: {total_frames}")

def generate_manifest(total_frames):
    """Creates the manifest.json"""
    manifest = {
        "dataset": os.path.basename(PROCESSED_DIR),
        "version": "1.0",
        "schema": "YOLO Image Classification (Fall / No_Fall)",
        "total_frames_produced": total_frames,
        "image_dimensions": "640x640"
    }
    manifest_path = os.path.join(PROCESSED_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        import json
        json.dump(manifest, f, indent=4)
    print(f"Created manifest file: {manifest_path}")

if __name__ == "__main__":
    run_pipeline()