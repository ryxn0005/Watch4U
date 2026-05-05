import pandas as pd
import json
import os
import glob

RAW_DIR = "../raw/vimedical/"
PROCESSED_PATH = "../processed/vimedical/vimedical_chunks.json"

def generate_manifest(total_records):
    """Creates the manifest.json"""
    manifest = {
        "dataset": "vimedical",
        "version": "1.0",
        "schema": "RAG Knowledge Base Chunks (id, disease, chunk)",
        "total_records_produced": total_records
    }
    manifest_path = os.path.join(os.path.dirname(PROCESSED_PATH), "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
    print(f"Created manifest file: {manifest_path}")

def chunk_vimedical():
    print("Chunking ViMedical Disease dataset...")
    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    
    csv_files = glob.glob(os.path.join(RAW_DIR, "*.csv"))
    
    if not csv_files:
        print(f"Could not find any .csv files in {RAW_DIR}.")
        return

    file_path = csv_files[0]
    print(f"Processing {os.path.basename(file_path)}...")
    
    # FIX 1: Explicitly force UTF-8 encoding so the Vietnamese characters don't break
    df = pd.read_csv(file_path, encoding='utf-8')
    
    records = df.to_dict('records')
    chunked_data = []
    
    for index, item in enumerate(records):
        disease_name = str(item.get("Disease", "Unknown"))
        
        # FIX 2: Look specifically for the "Question" column
        question_text = str(item.get("Question", ""))
        
        if question_text and question_text != "nan":
            # Split by periods to create RAG chunks
            sentences = question_text.split(". ")
            for s_idx, sentence in enumerate(sentences):
                if len(sentence.strip()) > 10: # Ignore tiny fragments
                    # Ensure the chunk ends with a period for clean reading
                    clean_sentence = sentence.strip()
                    if not clean_sentence.endswith("."):
                        clean_sentence += "."
                        
                    chunked_data.append({
                        "id": f"d{index}_c{s_idx}",
                        "disease": disease_name.strip(),
                        "chunk": clean_sentence
                    })
                    
    with open(PROCESSED_PATH, 'w', encoding='utf-8') as f:
        json.dump(chunked_data, f, ensure_ascii=False, indent=4)
        
    print(f"ViMedical Disease chunked. Processed {len(records)} entries. Saved to {PROCESSED_PATH}")
    generate_manifest(len(chunked_data))
    
if __name__ == "__main__":
    chunk_vimedical()