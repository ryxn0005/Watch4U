import os
import cv2
import glob
import yaml
from sklearn.model_selection import train_test_split

# Setup paths
RAW_DIR = "../raw/fallvision"
PROCESSED_DIR = "../processed/fallvision"

def setup_yolo_directories():
    """Creates the folder structure required by YOLO."""
    # YOLO requires 'train' and 'val' (validation) folders
    for split in ['train', 'val']:
        for category in ['Fall', 'No_Fall']:
            os.makedirs(os.path.join(PROCESSED_DIR, split, category), exist_ok=True)

def process_video_for_yolo(video_path, split, category, video_id):
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
            frame_path = os.path.join(PROCESSED_DIR, split, category, frame_filename)
            
            cv2.imwrite(frame_path, resized_frame)
            frame_count += 1

    cap.release()
    return frame_count

def generate_yolo_yaml():
    """YOLO requires a dataset.yaml file to know where the data is."""
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
    print(f"Created YOLO config file: {yaml_path}")

def run_pipeline():
    print("Starting YOLO-Optimized FallVision Pipeline...")
    setup_yolo_directories()
    
    all_videos = glob.glob(f"{RAW_DIR}/**/*.mp4", recursive=True)
    
    if not all_videos:
        print(f" No videos found in {RAW_DIR}.")
        return

    # Train/Val split
    train_vids, val_vids = train_test_split(all_videos, test_size=0.2, random_state=42)
    
    total_frames = 0
    for split, vids in [("train", train_vids), ("val", val_vids)]:
        for vid_path in vids:
            # 1. Look at the FULL path (not just the file name) to determine the category
            full_path_lower = vid_path.lower()
            if "nf_" in full_path_lower or "no fall" in full_path_lower:
                category = "No_Fall"
            else:
                category = "Fall"
                
            # 2. Create a unique video ID by combining the folder name AND the file name
            # Example: 'nf_raw_b_2_B_N_01' instead of just 'B_N_01'
            parent_folder = os.path.basename(os.path.dirname(vid_path))
            file_name = os.path.basename(vid_path).replace('.mp4', '')
            video_id = f"{parent_folder}_{file_name}"
            
            frames = process_video_for_yolo(vid_path, split, category, video_id)
            total_frames += frames
            
    generate_yolo_yaml()
    print(f"Pipeline complete. Total frames extracted for YOLO: {total_frames}")

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