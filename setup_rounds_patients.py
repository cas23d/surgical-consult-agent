"""Upload 3 synthetic rounds patients to HAPI FHIR server for demo.

These patients represent a surgery resident's morning patient list:
  1. Harold Whitaker — 68M, ICU, POD#1 Hartmann
  2. Maria Santos — 45F, Floor, POD#0 Lap Chole
  3. Eugene Morales — 72M, ICU, Ischemic Colitis Day 2
"""

import json
import base64
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


def create_patient(name_given, name_family, gender, birth_date, mrn):
    """Create a Patient resource."""
    return post("Patient", {
        "resourceType": "Patient",
        "identifier": [{"system": "urn:oid:1.2.3.4.5", "value": mrn}],
        "name": [{"family": name_family, "given": [name_given]}],
        "gender": gender,
        "birthDate": birth_date,
    })


def create_encounter(patient_id, class_code, class_display, location, reason):
    """Create an Encounter resource."""
    return post("Encounter", {
        "resourceType": "Encounter",
        "status": "in-progress",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": class_code,
            "display": class_display,
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "location": [{"location": {"display": location}}],
        "reasonCode": [{"text": reason}],
    })


def create_conditions(patient_id, conditions):
    """Create Condition resources from a list of (icd10, display) tuples."""
    for code, display in conditions:
        post("Condition", {
            "resourceType": "Condition",
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": code, "display": display}], "text": display},
            "subject": {"reference": f"Patient/{patient_id}"},
        })


def create_allergy_nkda(patient_id):
    """Create NKDA AllergyIntolerance."""
    post("AllergyIntolerance", {
        "resourceType": "AllergyIntolerance",
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
        "code": {"text": "No Known Drug Allergies"},
        "patient": {"reference": f"Patient/{patient_id}"},
    })


def create_allergy_specific(patient_id, allergen_text, reaction_text):
    """Create a specific AllergyIntolerance with reaction."""
    post("AllergyIntolerance", {
        "resourceType": "AllergyIntolerance",
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
        "code": {"text": allergen_text},
        "patient": {"reference": f"Patient/{patient_id}"},
        "reaction": [{"manifestation": [{"text": reaction_text}]}],
    })


def create_vitals(patient_id, encounter_id, bp_sys, bp_dia, hr, temp, rr, o2):
    """Create vital sign Observations."""
    ref = {"reference": f"Patient/{patient_id}"}
    enc_ref = {"reference": f"Encounter/{encounter_id}"}

    vitals = [
        ("8310-5", "Body temperature", temp, "Cel", "\u00b0C"),
        ("8867-4", "Heart rate", hr, "/min", "bpm"),
        ("9279-1", "Respiratory rate", rr, "/min", "breaths/min"),
        ("2708-6", "Oxygen saturation", o2, "%", "%"),
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
            {"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic"}]}, "valueQuantity": {"value": bp_sys, "unit": "mmHg"}},
            {"code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic"}]}, "valueQuantity": {"value": bp_dia, "unit": "mmHg"}},
        ],
    })


def create_labs(patient_id, encounter_id, labs):
    """Create laboratory Observations from a list of (loinc, display, value, unit) tuples."""
    ref = {"reference": f"Patient/{patient_id}"}
    enc_ref = {"reference": f"Encounter/{encounter_id}"}
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


def create_medications(patient_id, encounter_id, home_meds, inpatient_meds):
    """Create MedicationRequest resources."""
    ref = {"reference": f"Patient/{patient_id}"}
    enc_ref = {"reference": f"Encounter/{encounter_id}"}

    for display, rxnorm in home_meds:
        post("MedicationRequest", {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category", "code": "community", "display": "Community"}]}],
            "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": rxnorm, "display": display}], "text": display},
            "subject": ref,
        })

    for display, rxnorm in inpatient_meds:
        post("MedicationRequest", {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category", "code": "inpatient", "display": "Inpatient"}]}],
            "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": rxnorm, "display": display}], "text": display},
            "subject": ref,
            "encounter": enc_ref,
        })


def create_imaging(patient_id, encounter_id, study_name, status, conclusion):
    """Create a DiagnosticReport for imaging."""
    post("DiagnosticReport", {
        "resourceType": "DiagnosticReport",
        "status": status,
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "RAD", "display": "Radiology"}]}],
        "code": {"text": study_name},
        "subject": {"reference": f"Patient/{patient_id}"},
        "encounter": {"reference": f"Encounter/{encounter_id}"},
        "conclusion": conclusion,
    })


def create_note(patient_id, note_type_code, note_type_display, note_type_text, note_content):
    """Create a DocumentReference for a clinical note."""
    post("DocumentReference", {
        "resourceType": "DocumentReference",
        "status": "current",
        "type": {"coding": [{"system": "http://loinc.org", "code": note_type_code, "display": note_type_display}], "text": note_type_text},
        "subject": {"reference": f"Patient/{patient_id}"},
        "content": [{"attachment": {"contentType": "text/plain", "data": base64.b64encode(note_content.encode()).decode()}}],
    })


def setup_harold():
    """Patient 1: Harold Whitaker — 68M, ICU, POD#1 Hartmann."""
    print("=== Harold Whitaker (68M, ICU, POD#1 Hartmann) ===\n")

    patient_id = create_patient("Harold", "Whitaker", "male", "1957-08-03", "004593821")

    encounter_id = create_encounter(
        patient_id, "IMP", "Inpatient",
        "ICU Bed 4",
        "s/p Hartmann procedure for perforated diverticulitis POD#1",
    )

    create_conditions(patient_id, [
        ("I10", "Hypertension"),
        ("I25.10", "Coronary artery disease"),
        ("K57.30", "Diverticulosis of large intestine"),
        ("E78.5", "Hyperlipidemia"),
    ])

    create_allergy_nkda(patient_id)

    create_vitals(patient_id, encounter_id, 102, 64, 98, 37.8, 18, 97)

    create_labs(patient_id, encounter_id, [
        ("6690-2", "WBC", 14.2, "10*3/uL"),
        ("718-7", "Hemoglobin", 11.8, "g/dL"),
        ("777-3", "Platelets", 298, "10*3/uL"),
        ("2951-2", "Sodium", 136, "mEq/L"),
        ("2823-3", "Potassium", 4.0, "mEq/L"),
        ("2075-0", "Chloride", 102, "mEq/L"),
        ("2028-9", "CO2", 22, "mEq/L"),
        ("3094-0", "BUN", 22, "mg/dL"),
        ("2160-0", "Creatinine", 1.4, "mg/dL"),
        ("2345-7", "Glucose", 128, "mg/dL"),
        ("2524-7", "Lactate", 2.1, "mmol/L"),
    ])

    create_medications(patient_id, encounter_id,
        home_meds=[
            ("Aspirin 81mg daily", "1191"),
            ("Metoprolol 50mg BID", "6918"),
            ("Atorvastatin 40mg nightly", "83367"),
            ("Lisinopril 10mg daily", "29046"),
        ],
        inpatient_meds=[
            ("Norepinephrine 0.05 mcg/kg/min", "7512"),
            ("Piperacillin-Tazobactam IV", "139462"),
            ("Morphine PCA", "7052"),
            ("Lactated Ringers 125mL/hr", "847626"),
            ("Heparin 5000u SQ q8h", "5224"),
        ],
    )

    create_imaging(patient_id, encounter_id,
        "CT Abdomen/Pelvis with IV Contrast", "final",
        "Post-operative changes from sigmoid colectomy with end colostomy. "
        "Expected post-surgical inflammatory changes. No abscess or leak identified. "
        "Small amount of free fluid in pelvis, expected.",
    )

    # Nursing note
    create_note(patient_id, "34746-8", "Nursing note", "Nursing Note",
        "NURSING NOTE (03:30)\n"
        "Overnight: Patient resting comfortably. Pressors weaning \u2014 norepinephrine "
        "decreased from 0.08 to 0.05 mcg/kg/min. MAPs maintained >65. UOP 40-50cc/hr "
        "via foley. Received 1 unit PRBC at 0100 for Hgb 10.2, post-transfusion Hgb "
        "11.8. PCA usage: 4 demands in last 4 hours, adequate pain control, patient "
        "rates pain 4/10. Stoma: pink, viable, no output yet. Abdomen soft, mildly "
        "distended. No flatus reported. NPO. IV fluids running.",
    )

    # Yesterday's surgery team note
    create_note(patient_id, "11506-3", "Progress note", "Surgery Progress Note",
        "SURGERY PROGRESS NOTE \u2014 POD#0 (Yesterday)\n"
        "S: Patient intubated/sedated in ICU post emergent Hartmann procedure.\n"
        "O: Hemodynamically unstable on norepinephrine 0.12 mcg/kg/min. "
        "Lactate 4.8 \u2192 3.2 post-resuscitation. UOP 25-30cc/hr. Stoma pink and viable.\n"
        "A: 68M s/p emergent Hartmann for perforated sigmoid diverticulitis Hinchey III. "
        "Septic shock, improving with resuscitation.\n"
        "P: Continue aggressive IVF, wean pressors as tolerated, serial lactate q6h, "
        "pip-tazo, pain management, NPO, stoma nurse consult in AM, repeat CBC/BMP/lactate "
        "in AM. Will assess for extubation tomorrow if hemodynamics improve.",
    )

    return {"name": "Harold Whitaker", "patient_id": patient_id, "mrn": "004593821"}


def setup_maria():
    """Patient 2: Maria Santos — 45F, Floor, POD#0 Lap Chole."""
    print("\n=== Maria Santos (45F, Floor, POD#0 Lap Chole) ===\n")

    patient_id = create_patient("Maria", "Santos", "female", "1980-11-22", "005182736")

    encounter_id = create_encounter(
        patient_id, "IMP", "Inpatient",
        "Floor 4 Bed 12",
        "s/p laparoscopic cholecystectomy",
    )

    create_conditions(patient_id, [
        ("K80.20", "Cholelithiasis"),
        ("K21.0", "GERD"),
        ("E66.01", "Obesity BMI 34"),
    ])

    create_allergy_specific(patient_id, "Penicillin", "Rash")

    create_vitals(patient_id, encounter_id, 128, 78, 74, 36.9, 14, 99)

    create_labs(patient_id, encounter_id, [
        ("6690-2", "WBC", 8.2, "10*3/uL"),
        ("718-7", "Hemoglobin", 13.1, "g/dL"),
        ("777-3", "Platelets", 245, "10*3/uL"),
        ("2951-2", "Sodium", 140, "mEq/L"),
        ("2823-3", "Potassium", 4.1, "mEq/L"),
        ("2075-0", "Chloride", 103, "mEq/L"),
        ("2028-9", "CO2", 24, "mEq/L"),
        ("3094-0", "BUN", 14, "mg/dL"),
        ("2160-0", "Creatinine", 0.8, "mg/dL"),
        ("2345-7", "Glucose", 98, "mg/dL"),
    ])

    create_medications(patient_id, encounter_id,
        home_meds=[
            ("Omeprazole 20mg daily", "7646"),
        ],
        inpatient_meds=[
            ("Acetaminophen 1g q6h", "161"),
            ("Ibuprofen 400mg q6h", "5640"),
            ("Ondansetron 4mg IV PRN", "26225"),
        ],
    )

    # No imaging for Maria

    # Nursing note
    create_note(patient_id, "34746-8", "Nursing note", "Nursing Note",
        "NURSING NOTE (04:00)\n"
        "Overnight: Uncomplicated. Patient tolerating clear liquids without nausea "
        "or vomiting. Ambulated x2 in hallway with nursing assistance, steady gait. "
        "Pain well controlled 3/10 on PO Tylenol and ibuprofen. Voiding without "
        "difficulty. Port sites clean/dry/intact, no drainage. Resting comfortably. "
        "Requesting breakfast.",
    )

    return {"name": "Maria Santos", "patient_id": patient_id, "mrn": "005182736"}


def setup_eugene():
    """Patient 3: Eugene Morales — 72M, ICU, Ischemic Colitis Day 2."""
    print("\n=== Eugene Morales (72M, ICU, Ischemic Colitis Day 2) ===\n")

    patient_id = create_patient("Eugene", "Morales", "male", "1953-09-17", "007281944")

    encounter_id = create_encounter(
        patient_id, "IMP", "Inpatient",
        "ICU Bed 7",
        "Ischemic colitis with sepsis, non-operative management",
    )

    create_conditions(patient_id, [
        ("I10", "Hypertension"),
        ("I48.91", "Atrial fibrillation"),
        ("I25.10", "Coronary artery disease"),
        ("N18.3", "Chronic kidney disease stage 3"),
        ("E78.5", "Hyperlipidemia"),
        ("G45.9", "TIA 2017"),
        ("Z95.818", "s/p AAA repair"),
    ])

    create_allergy_nkda(patient_id)

    # Earlier vitals
    create_vitals(patient_id, encounter_id, 94, 58, 118, 38.3, 24, 95)
    # Most recent vitals
    create_vitals(patient_id, encounter_id, 98, 62, 108, 37.6, 20, 95)

    create_labs(patient_id, encounter_id, [
        ("6690-2", "WBC", 15.8, "10*3/uL"),
        ("718-7", "Hemoglobin", 9.8, "g/dL"),
        ("777-3", "Platelets", 198, "10*3/uL"),
        ("2951-2", "Sodium", 133, "mEq/L"),
        ("2823-3", "Potassium", 5.1, "mEq/L"),
        ("2028-9", "CO2", 17, "mEq/L"),
        ("3094-0", "BUN", 38, "mg/dL"),
        ("2160-0", "Creatinine", 2.2, "mg/dL"),
        ("2345-7", "Glucose", 152, "mg/dL"),
        ("2524-7", "Lactate", 2.8, "mmol/L"),
        ("34714-6", "INR", 1.3, ""),
        ("6598-7", "Troponin", 0.04, "ng/mL"),
        ("2744-1", "pH", 7.33, ""),
        ("2019-8", "pCO2", 30, "mmHg"),
        ("1963-8", "HCO3", 15, "mEq/L"),
    ])

    create_medications(patient_id, encounter_id,
        home_meds=[
            ("Apixaban 5mg BID", "1364430"),
            ("Metoprolol 50mg BID", "6918"),
            ("Lisinopril 20mg daily", "29046"),
            ("Atorvastatin 40mg nightly", "83367"),
            ("Aspirin 81mg daily", "1191"),
        ],
        inpatient_meds=[
            ("Ceftriaxone IV", "309090"),
            ("Metronidazole IV", "6922"),
            ("Lactated Ringers 100mL/hr", "847626"),
            ("Pantoprazole 40mg IV daily", "40790"),
        ],
    )

    create_imaging(patient_id, encounter_id,
        "CT Abdomen/Pelvis without Contrast", "preliminary",
        "Diffuse thickening descending and sigmoid colon. Pericolonic stranding. "
        "Mild pneumatosis cannot be excluded. No free air. Limited evaluation of "
        "vasculature without contrast. Impression: Colitis, questionable ischemic "
        "changes in sigmoid, correlate clinically.",
    )

    # Nursing note
    create_note(patient_id, "34746-8", "Nursing note", "Nursing Note",
        "NURSING NOTE (03:45)\n"
        "Overnight: Received 2 units PRBC (0000 and 0230). Post-transfusion Hgb "
        "pending. Still having bloody stools but less frequent \u2014 2 episodes since "
        "midnight vs 5 in prior 8 hours. Mental status improved significantly, now "
        "oriented x3 (was only oriented to self on admission). BP remains borderline "
        "96-102 systolic without pressors. HR afib 104-112. Serial abdominal exams "
        "per surgery: LLQ tenderness with mild guarding, no rebound, no rigidity. "
        "Apixaban and aspirin held. Metoprolol held for hypotension. Strict I&O: "
        "1850mL in / 920mL out (including stool).",
    )

    # Yesterday's surgery consult note
    create_note(patient_id, "11488-4", "Consultation note", "Surgery Consult Note",
        "SURGERY CONSULT NOTE \u2014 Day 1 (Yesterday)\n"
        "Consulted for: Colitis on CT, hypotensive\n"
        "S: 72M with afib on apixaban, CAD, CKD3, hx AAA repair presents with "
        "acute abdominal pain, bloody diarrhea, confusion.\n"
        "O: Ill-appearing, confused. Abdomen diffusely tender, LLQ worst, mild "
        "guarding, no rebound. Rectal: gross blood. Femoral pulses palpable, feet "
        "warm. CT: colitis descending/sigmoid, questionable pneumatosis, no free air. "
        "Lactate 4.6, WBC 18.4, Cr 2.4.\n"
        "A: Ischemic colitis likely related to prior AAA repair (IMA ligation) "
        "complicated by sepsis. Hemodynamically unstable but no peritonitis \u2014 favor "
        "non-operative management with serial exams.\n"
        "P: Aggressive fluid resuscitation, broad-spectrum abx, hold anticoagulation, "
        "serial abdominal exams q4h, serial lactate q6h, CBC q6h, NPO, GI consult "
        "for scope when stable. OR if develops peritonitis, hemodynamic collapse, or "
        "rising lactate despite resuscitation. Type and screen. Discussed with "
        "attending Dr. Morrison \u2014 agrees with non-operative approach for now.",
    )

    return {"name": "Eugene Morales", "patient_id": patient_id, "mrn": "007281944"}


def main():
    print("Uploading 3 rounds patients to HAPI FHIR...\n")

    patients = []
    patients.append(setup_harold())
    patients.append(setup_maria())
    patients.append(setup_eugene())

    print(f"\n{'='*60}")
    print("  All patients uploaded successfully!")
    print(f"{'='*60}\n")

    for p in patients:
        print(f"  {p['name']} — Patient ID: {p['patient_id']} (MRN: {p['mrn']})")

    # Save patient IDs for the rounds agent
    with open("rounds_patients.json", "w") as f:
        json.dump(patients, f, indent=2)
    print(f"\nSaved to rounds_patients.json")


if __name__ == "__main__":
    main()
