# Demographics
AGES = [60, 65, 72, 78, 83, 88, 92]
SEXES = ["male", "female"]
LANGUAGES = ["Vietnamese", "English", "Bilingual (VI/EN)"]

# Medical Context
# A2 Major Risk Factors: Stroke, Cardiovascular disease, Anticoagulant use, Impaired mobility, Cognitive impairment
CONDITIONS_POOL = ["hypertension", "stroke", "osteoporosis", "diabetes", "cardiovascular disease", "arthritis"]
MEDICATIONS_POOL = ["warfarin", "aspirin", "metformin", "lisinopril", "sedatives"]

MOBILITY_STATUS = ["independent", "assisted", "bedridden"]
COGNITION_STATUS = ["normal", "mild impairment", "severe impairment"]

def get_random_conditions():
    import random
    # Give patients between 0 and 3 conditions
    return random.sample(CONDITIONS_POOL, k=random.randint(0, 3))

def get_random_medications(conditions):
    import random
    meds = []
    # If they have a stroke/cardio history, higher chance of anticoagulants (Warfarin)
    if "stroke" in conditions or "cardiovascular disease" in conditions:
        if random.random() > 0.3:
            meds.append("warfarin")
    
    extra_meds = random.sample([m for m in MEDICATIONS_POOL if m != "warfarin"], k=random.randint(0, 2))
    meds.extend(extra_meds)
    return list(set(meds))