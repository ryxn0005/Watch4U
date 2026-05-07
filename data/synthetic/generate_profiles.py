import json
import random
import argparse
import uuid
from distributions import *

def calculate_risk(profile):
    """
    Applies the A2 Rule-Based Triage Logic.
    Major risk factors: Age >= 65, Stroke/cardio, Anticoagulant, Impaired mobility, Cognitive impairment.
    """
    major_factors = 0
    
    if profile["age"] >= 65: 
        major_factors += 1
    if "stroke" in profile["conditions"] or "cardiovascular disease" in profile["conditions"]: 
        major_factors += 1
    if "warfarin" in profile["medications"]: 
        major_factors += 1
    if profile["functional_status"]["mobility"] in ["assisted", "bedridden"]: 
        major_factors += 1
    if profile["functional_status"]["cognition"] != "normal": 
        major_factors += 1

    # Classify based on A2 rules
    if major_factors >= 2:
        return "high"
    elif major_factors == 1:
        return "moderate"
    else:
        return "low"

def generate_profile():
    conditions = get_random_conditions()
    medications = get_random_medications(conditions)
    
    profile = {
        "id": f"P{str(uuid.uuid4().hex[:5]).upper()}",
        "name": f"Synthetic Patient {random.randint(100, 999)}",
        "age": random.choice(AGES),
        "sex": random.choice(SEXES),
        "language": random.choice(LANGUAGES),
        "conditions": conditions,
        "medications": medications,
        "functional_status": {
            "mobility": random.choice(MOBILITY_STATUS),
            "cognition": random.choice(COGNITION_STATUS)
        },
        "previous_falls": random.randint(0, 3),
        "emergency_contacts": [
            {"name": "Primary Carer", "relationship": "family", "phone": "0400000000"}
        ]
    }
    
    # Calculate and assign risk level
    profile["risk_level"] = calculate_risk(profile)
    return profile

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic CALD senior patient profiles.")
    parser.add_argument("-n", "--number", type=int, default=10, help="Number of profiles to generate")
    parser.add_argument("--out", type=str, default="samples/profiles.json", help="Output file path")
    args = parser.parse_args()

    profiles = [generate_profile() for _ in range(args.number)]
    
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully generated {args.number} synthetic profiles at {args.out}")