# synthetic/

Generators that produce synthetic CALD-senior patient profiles for testing the triage pipeline without any real PHI.

# Synthetic Patient Generator

This folder contains the scripts used to simulate Electronic Health Records (EHR) for the Watch4U prototype, as real patient data cannot be used due to privacy laws.

## How to Run
Navigate to `data/synthetic/` and run:
`python generate_profiles.py -n 100 --out samples/profiles.json`

## Synthetic Bias Acknowledgement (Per A2 Report)
These profiles are generated using randomized heuristic priors defined in `distributions.py`. 
* **Risk:** The generated profiles may not accurately reflect the compounding, real-world coexisting conditions of CALD seniors.
* **Mitigation:** The risk rules applied in `generate_profiles.py` are strictly tied to the CDSS framework proposed in the Mid-Project Update. We intend to validate these mock profiles via a clinical consultation loop with Prof. Paul Middleton to ensure triage outputs map safely to real-world emergency protocols.

## Suggested files

- `generate_profiles.py` — the main generator (CLI: `python generate_profiles.py --n 500 --out profiles.json`)
- `distributions.py` — age / comorbidity / medication priors (document sources!)
- `samples/` — a small committed sample (~10 profiles) so the prototype runs without regenerating

## Schema

Each profile contains:

- `id`, `age`, `sex`, `language` (en / vi / mixed)
- `medical_history[]`, `medications[]`
- `functional_status` (mobility, cognition)
- `fall_history[]`
- `emergency_contacts[]`
- `risk_level`: `"low" | "moderate" | "high"`

## Risk Logic
Risk is calculated per A2 guidelines:
- **High**: >= 2 major factors (Age 65+, Stroke, Anticoagulants, Assisted Mobility, Cognitive Impairment)
- **Moderate**: 1 major factor
- **Low**: 0 major factors

Document **every** prior used by the generator — A2 calls out synthetic bias as a key risk.
