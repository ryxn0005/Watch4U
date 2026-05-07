# data/preprocessing/vimq.py
import json
import os
import glob

RAW_DIR = "../raw/vimq/"
PROCESSED_PATH = "../processed/vimq/vimq_cleaned.json"

def generate_manifest(total_records):
    """Creates the manifest.json"""
    manifest = {
        "dataset": "vimq",
        "version": "1.0",
        "schema": "RAG Intent and Entity Mapping (text, intent, entities)",
        "total_records_produced": total_records
    }
    manifest_path = os.path.join(os.path.dirname(PROCESSED_PATH), "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
    print(f"Created manifest file: {manifest_path}")

def clean_vimq():
    print("Cleaning ViMQ dataset...")
    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    
    raw_files = glob.glob(os.path.join(RAW_DIR, "*.json"))
    
    if not raw_files:
        print(f"Could not find any .json files in {RAW_DIR}.")
        return

    cleaned_data = []
    
    for file_path in raw_files:
        with open(file_path, 'r', encoding='utf-8') as f: 
            raw_data = json.load(f)
            
            for item in raw_data:
                sentence = item.get("sentence", "")
                
                # ViMQ sentences are usually pre-tokenized with spaces (e.g., "đau_đầu")
                words = sentence.split()
                extracted_entities = []
                
                # Parse the seq_label to grab the exact entity strings
                seq_labels = item.get("seq_label", [])
                for label in seq_labels:
                    if len(label) == 3:
                        start_idx, end_idx, entity_type = label
                        try:
                            # Extract words using indices (inclusive) and clean up underscores
                            entity_text = " ".join(words[start_idx:end_idx+1]).replace("_", " ")
                            extracted_entities.append({
                                "type": entity_type,
                                "text": entity_text
                            })
                        except IndexError:
                            continue
                            
                cleaned_data.append({
                    "intent": item.get("sent_label", "Unknown"), 
                    # Clean the underscores out of the main text so PhoBERT reads it naturally
                    "text": sentence.replace("_", " "),
                    "entities": extracted_entities
                })
                
    with open(PROCESSED_PATH, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        
    print(f"ViMQ cleaned. Merged {len(raw_files)} files. Saved to {PROCESSED_PATH}")
    generate_manifest(len(cleaned_data))

if __name__ == "__main__":
    clean_vimq()