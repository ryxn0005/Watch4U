import pandas as pd
import json
import os
import glob

RAW_DIR = "../raw/vietmed/"
PROCESSED_PATH = "../processed/vietmed/vietmed_cleaned.json"

def generate_manifest(total_records):
    """Creates the manifest.json"""
    manifest = {
        "dataset": "vietmed",
        "version": "1.0",
        "schema": "RAG Medical Entity Context (entity_type, entity_text, context_sentence)",
        "total_records_produced": total_records
    }
    manifest_path = os.path.join(os.path.dirname(PROCESSED_PATH), "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
    print(f"Created manifest file: {manifest_path}")

def clean_vietmed():
    print("Cleaning VietMed-NER dataset...")
    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    
    parquet_files = glob.glob(os.path.join(RAW_DIR, "*.parquet"))
    
    if not parquet_files:
        print(f"Could not find any .parquet files in {RAW_DIR}.")
        return

    cleaned_data = []
    
    for file_path in parquet_files:
        print(f"Processing {os.path.basename(file_path)}...")
        df = pd.read_parquet(file_path)
        
        for _, row in df.iterrows():
            words = row.get('words', [])
            labels = row.get('labels', [])
            full_text = row.get('text', "") 
            
            current_entity = []
            
            # Zip pairs the words and labels together side-by-side
            if len(words) == len(labels):
                for word, label in zip(words, labels):
                    # If we hit a new Disease/Symptom
                    if label == "B-DISEASESYMTOM":
                        # Save the previous entity if we were tracking one
                        if current_entity:
                            cleaned_data.append({
                                "entity_type": "DISEASE_SYMPTOM",
                                "entity_text": " ".join(current_entity).replace("_", " "),
                                "context_sentence": full_text
                            })
                        # Start tracking the new entity
                        current_entity = [word]
                        
                    # If the word is a continuation of the current Disease/Symptom
                    elif label == "I-DISEASESYMTOM" and current_entity:
                        current_entity.append(word)
                        
                    # If it is an outside word ('0') or a different entity (like 'B-ORGAN')
                    else:
                        if current_entity:
                            cleaned_data.append({
                                "entity_type": "DISEASE_SYMPTOM",
                                "entity_text": " ".join(current_entity).replace("_", " "),
                                "context_sentence": full_text
                            })
                            current_entity = []
                            
                # Catch any entity that happens to end on the very last word of the sentence
                if current_entity:
                    cleaned_data.append({
                        "entity_type": "DISEASE_SYMPTOM",
                        "entity_text": " ".join(current_entity).replace("_", " "),
                        "context_sentence": full_text
                    })

    with open(PROCESSED_PATH, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        
    print(f"VietMed-NER cleaned. Extracted {len(cleaned_data)} disease/symptom entities. Saved to {PROCESSED_PATH}")
    generate_manifest(len(cleaned_data))

if __name__ == "__main__":
    clean_vietmed()