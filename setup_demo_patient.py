"""Upload synthetic patient Harold Whitaker to HAPI FHIR server for demo."""

import json
import requests

FHIR_BASE = "https://hapi.fhir.org/baseR4"
HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}


def post(resource_type, data):
    """Post a FHIR resource and return its server-assigned ID."""
    resp = requests.post(f"{FHIR_BASE}/{resource_type}", json=data, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()
    rid = result["id"]
    print(f"  Created {resource_type}/{rid}")
    return rid


def main():
    print("Uploading Harold Whitaker to HAPI FHIR...\n")

    # --- Patient ---
    patient_id = post("Patient", {
        "resourceType": "Patient",
        "identifier": [{"system": "urn:oid:1.2.3.4.5", "value": "004593821"}],
        "name": [{"family": "Whitaker", "given": ["Harold"]}],
        "gender": "male",
        "birthDate": "1957-08-03",
    })

    # --- Encounter (ED visit) ---
    encounter_id = post("Encounter", {
        "resourceType": "Encounter",
        "status": "in-progress",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "EMER", "display": "Emergency"},
        "subject": {"reference": f"Patient/{patient_id}"},
        "location": [{"location": {"display": "ED Room 12"}}],
        "reasonCode": [{"text": "Abdominal pain, CT shows free air"}],
    })

    ref = {"reference": f"Patient/{patient_id}"}
    enc_ref = {"reference": f"Encounter/{encounter_id}"}

    # --- Allergies (NKDA) ---
    post("AllergyIntolerance", {
        "resourceType": "AllergyIntolerance",
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
        "code": {"text": "No Known Drug Allergies"},
        "patient": ref,
    })

    # --- Conditions ---
    conditions = [
        ("I10", "Hypertension"),
        ("I25.10", "Coronary artery disease"),
        ("K57.30", "Diverticulosis of large intestine"),
        ("E78.5", "Hyperlipidemia"),
    ]
    for code, display in conditions:
        post("Condition", {
            "resourceType": "Condition",
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": code, "display": display}], "text": display},
            "subject": ref,
        })

    # --- Vitals ---
    vitals = [
        ("8310-5", "Body temperature", 38.3, "Cel", "°C"),
        ("8867-4", "Heart rate", 112, "/min", "bpm"),
        ("9279-1", "Respiratory rate", 22, "/min", "breaths/min"),
        ("2708-6", "Oxygen saturation", 96, "%", "%"),
    ]
    for loinc, display, value, unit, unit_display in vitals:
        post("Observation", {
            "resourceType": "Observation",
            "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": loinc, "display": display}], "text": display},
            "subject": ref,
            "encounter": enc_ref,
            "valueQuantity": {"value": value, "unit": unit_display, "system": "http://unitsofmeasure.org", "code": unit},
        })

    # Blood pressure (compound)
    post("Observation", {
        "resourceType": "Observation",
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
        "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure"}], "text": "Blood pressure"},
        "subject": ref,
        "encounter": enc_ref,
        "component": [
            {"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic"}]}, "valueQuantity": {"value": 94, "unit": "mmHg"}},
            {"code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic"}]}, "valueQuantity": {"value": 58, "unit": "mmHg"}},
        ],
    })

    # --- Labs ---
    labs = [
        ("6690-2", "WBC", 18.9, "10*3/uL"),
        ("718-7", "Hemoglobin", 13.4, "g/dL"),
        ("777-3", "Platelets", 312, "10*3/uL"),
        ("2951-2", "Sodium", 134, "mEq/L"),
        ("2823-3", "Potassium", 4.2, "mEq/L"),
        ("2075-0", "Chloride", 101, "mEq/L"),
        ("2028-9", "CO2", 19, "mEq/L"),
        ("3094-0", "BUN", 28, "mg/dL"),
        ("2160-0", "Creatinine", 1.6, "mg/dL"),
        ("2345-7", "Glucose", 142, "mg/dL"),
        ("2524-7", "Lactate", 4.8, "mmol/L"),
    ]
    for loinc, display, value, unit in labs:
        post("Observation", {
            "resourceType": "Observation",
            "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": loinc, "display": display}], "text": display},
            "subject": ref,
            "encounter": enc_ref,
            "valueQuantity": {"value": value, "unit": unit, "system": "http://unitsofmeasure.org"},
        })

    # --- Home Medications ---
    home_meds = [
        ("Aspirin 81 mg daily", "1191"),
        ("Metoprolol 50 mg BID", "6918"),
        ("Atorvastatin 40 mg nightly", "83367"),
        ("Lisinopril 10 mg daily", "29046"),
    ]
    for display, rxnorm in home_meds:
        post("MedicationRequest", {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category", "code": "community", "display": "Community"}]}],
            "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": rxnorm, "display": display}], "text": display},
            "subject": ref,
        })

    # --- ED Medications ---
    ed_meds = [
        ("Piperacillin-Tazobactam IV", "139462"),
        ("Lactated Ringer's 2L IV", "847626"),
    ]
    for display, rxnorm in ed_meds:
        post("MedicationRequest", {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category", "code": "inpatient", "display": "Inpatient"}]}],
            "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": rxnorm, "display": display}], "text": display},
            "subject": ref,
            "encounter": enc_ref,
        })

    # --- CT Report ---
    post("DiagnosticReport", {
        "resourceType": "DiagnosticReport",
        "status": "preliminary",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "RAD", "display": "Radiology"}]}],
        "code": {"text": "CT Abdomen/Pelvis with IV Contrast"},
        "subject": ref,
        "encounter": enc_ref,
        "conclusion": (
            "Moderate pneumoperitoneum. Free fluid in pelvis. "
            "Sigmoid colon with wall thickening and surrounding inflammatory changes. "
            "2.5 cm pericolic abscess. "
            "Findings concerning for perforated sigmoid diverticulitis."
        ),
    })

    # --- ED Provider Note (as DocumentReference) ---
    import base64
    note_text = """ED PROVIDER NOTE (14:05)
HPI: 68M with history of HTN, CAD (s/p PCI 2018), and diverticulosis presents with acute onset abdominal pain beginning this morning. Pain started periumbilical, now diffuse. Constant, worsening. Associated nausea. No bowel movement since yesterday. No hematemesis or melena. Denies prior abdominal surgeries.

ROS (Pertinent): +Abdominal pain, +Nausea, -Vomiting, -Chest pain, -SOB

Exam:
General: Ill appearing, diaphoretic
CV: Tachycardic, regular
Lungs: Clear
Abdomen: Distended, diffuse tenderness, guarding, rebound present
Extremities: Cool

ED Interventions: 2L LR given, blood cultures drawn, started on Piperacillin-Tazobactam, Type & Screen sent."""

    post("DocumentReference", {
        "resourceType": "DocumentReference",
        "status": "current",
        "type": {"coding": [{"system": "http://loinc.org", "code": "34878-9", "display": "Emergency medicine Note"}], "text": "ED Provider Note"},
        "subject": ref,
        "content": [{"attachment": {"contentType": "text/plain", "data": base64.b64encode(note_text.encode()).decode()}}],
    })

    print(f"\nDone! Patient ID: {patient_id}")
    print(f"MRN: 004593821")
    print(f"\nSave this patient ID — the agent will use it to pull data.")

    # Save patient ID for the agent
    with open("demo_patient.json", "w") as f:
        json.dump({"patient_id": patient_id, "mrn": "004593821", "fhir_base": FHIR_BASE}, f, indent=2)
    print(f"Saved to demo_patient.json")


if __name__ == "__main__":
    main()
