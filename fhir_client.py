"""Pull patient data from a FHIR R4 server and format it for the consult agent."""

import json
import base64
import requests

FHIR_BASE = "https://hapi.fhir.org/baseR4"
HEADERS = {"Accept": "application/fhir+json"}


def _get_bundle(resource_type, params):
    """Fetch a FHIR bundle and return the list of resources."""
    resp = requests.get(f"{FHIR_BASE}/{resource_type}", params=params, headers=HEADERS)
    resp.raise_for_status()
    bundle = resp.json()
    return [e["resource"] for e in bundle.get("entry", [])]


def get_patient(patient_id):
    """Fetch patient demographics."""
    resp = requests.get(f"{FHIR_BASE}/Patient/{patient_id}", headers=HEADERS)
    resp.raise_for_status()
    p = resp.json()
    name = p.get("name", [{}])[0]
    full_name = f"{' '.join(name.get('given', []))} {name.get('family', '')}"
    mrn = ""
    for ident in p.get("identifier", []):
        mrn = ident.get("value", "")
        break
    return {
        "name": full_name,
        "mrn": mrn,
        "dob": p.get("birthDate", "Unknown"),
        "gender": p.get("gender", "Unknown"),
    }


def get_encounter(patient_id):
    """Fetch active encounter details."""
    encounters = _get_bundle("Encounter", {"patient": patient_id, "_sort": "-date", "_count": "1"})
    if not encounters:
        return {"location": "Unknown", "reason": "Not specified"}
    enc = encounters[0]
    location = "Unknown"
    for loc in enc.get("location", []):
        location = loc.get("location", {}).get("display", "Unknown")
        break
    reason = ""
    for rc in enc.get("reasonCode", []):
        reason = rc.get("text", "")
        break
    return {"location": location, "reason": reason, "encounter_id": enc["id"]}


def get_conditions(patient_id):
    """Fetch active conditions / problem list."""
    resources = _get_bundle("Condition", {"patient": patient_id, "clinical-status": "active"})
    conditions = []
    for r in resources:
        text = r.get("code", {}).get("text", "")
        codings = r.get("code", {}).get("coding", [])
        code = codings[0].get("code", "") if codings else ""
        if text:
            conditions.append(f"{text} ({code})" if code else text)
    return conditions


def get_allergies(patient_id):
    """Fetch allergy list."""
    resources = _get_bundle("AllergyIntolerance", {"patient": patient_id})
    if not resources:
        return ["No allergies listed"]
    allergies = []
    for r in resources:
        text = r.get("code", {}).get("text", "")
        if text:
            allergies.append(text)
    return allergies or ["No allergies listed"]


def get_vitals(patient_id):
    """Fetch vital signs from most recent encounter."""
    resources = _get_bundle("Observation", {
        "patient": patient_id,
        "category": "vital-signs",
        "_sort": "-date",
        "_count": "20",
    })
    vitals = []
    for r in resources:
        name = r.get("code", {}).get("text", "")
        # Handle compound observations (blood pressure)
        if r.get("component"):
            parts = []
            for comp in r["component"]:
                comp_name = comp.get("code", {}).get("coding", [{}])[0].get("display", "")
                val = comp.get("valueQuantity", {})
                parts.append(f"{comp_name}: {val.get('value', '')} {val.get('unit', '')}")
            vitals.append(f"{name}: {' / '.join(parts)}")
        else:
            val = r.get("valueQuantity", {})
            vitals.append(f"{name}: {val.get('value', '')} {val.get('unit', '')}")
    return vitals


def get_labs(patient_id):
    """Fetch laboratory results."""
    resources = _get_bundle("Observation", {
        "patient": patient_id,
        "category": "laboratory",
        "_sort": "-date",
        "_count": "50",
    })
    labs = []
    for r in resources:
        name = r.get("code", {}).get("text", "")
        val = r.get("valueQuantity", {})
        labs.append(f"{name}: {val.get('value', '')} {val.get('unit', '')}")
    return labs


def get_medications(patient_id):
    """Fetch active medications, separated into home and inpatient."""
    resources = _get_bundle("MedicationRequest", {"patient": patient_id, "status": "active"})
    home_meds = []
    inpatient_meds = []
    for r in resources:
        med_text = r.get("medicationCodeableConcept", {}).get("text", "Unknown medication")
        category = ""
        for cat in r.get("category", []):
            for coding in cat.get("coding", []):
                category = coding.get("code", "")
        if category == "community":
            home_meds.append(med_text)
        else:
            inpatient_meds.append(med_text)
    return {"home": home_meds, "inpatient": inpatient_meds}


def get_imaging(patient_id):
    """Fetch diagnostic/imaging reports."""
    resources = _get_bundle("DiagnosticReport", {"patient": patient_id, "_sort": "-date", "_count": "5"})
    reports = []
    for r in resources:
        name = r.get("code", {}).get("text", "")
        conclusion = r.get("conclusion", "No conclusion provided")
        status = r.get("status", "")
        reports.append({"study": name, "status": status, "findings": conclusion})
    return reports


def get_notes(patient_id):
    """Fetch clinical notes (DocumentReference)."""
    resources = _get_bundle("DocumentReference", {"patient": patient_id, "_sort": "-date", "_count": "5"})
    notes = []
    for r in resources:
        doc_type = r.get("type", {}).get("text", "Clinical Note")
        content_list = r.get("content", [])
        text = ""
        for c in content_list:
            attachment = c.get("attachment", {})
            if attachment.get("data"):
                text = base64.b64decode(attachment["data"]).decode("utf-8", errors="replace")
        notes.append({"type": doc_type, "text": text})
    return notes


def pull_full_chart(patient_id):
    """Pull all available data for a patient and return as structured dict."""
    patient = get_patient(patient_id)
    encounter = get_encounter(patient_id)
    conditions = get_conditions(patient_id)
    allergies = get_allergies(patient_id)
    vitals = get_vitals(patient_id)
    labs = get_labs(patient_id)
    meds = get_medications(patient_id)
    imaging = get_imaging(patient_id)
    notes = get_notes(patient_id)

    return {
        "patient": patient,
        "encounter": encounter,
        "conditions": conditions,
        "allergies": allergies,
        "vitals": vitals,
        "labs": labs,
        "medications": meds,
        "imaging": imaging,
        "notes": notes,
    }


def format_chart_for_ai(chart_data):
    """Format the pulled chart data into a readable string for the AI."""
    lines = []

    p = chart_data["patient"]
    lines.append("═══ PATIENT ═══")
    lines.append(f"Name: {p['name']}")
    lines.append(f"MRN: {p['mrn']}")
    lines.append(f"DOB: {p['dob']}  |  Sex: {p['gender']}")

    enc = chart_data["encounter"]
    lines.append(f"Location: {enc['location']}")
    lines.append(f"Reason for Visit: {enc['reason']}")

    lines.append(f"\nAllergies: {', '.join(chart_data['allergies'])}")

    lines.append("\n═══ PROBLEM LIST ═══")
    for c in chart_data["conditions"]:
        lines.append(f"  • {c}")

    lines.append("\n═══ VITALS ═══")
    for v in chart_data["vitals"]:
        lines.append(f"  • {v}")

    lines.append("\n═══ LABS ═══")
    for lab in chart_data["labs"]:
        lines.append(f"  • {lab}")

    lines.append("\n═══ HOME MEDICATIONS ═══")
    for m in chart_data["medications"]["home"]:
        lines.append(f"  • {m}")

    lines.append("\n═══ CURRENT ORDERS ═══")
    for m in chart_data["medications"]["inpatient"]:
        lines.append(f"  • {m}")

    lines.append("\n═══ IMAGING ═══")
    for img in chart_data["imaging"]:
        lines.append(f"  [{img['status'].upper()}] {img['study']}")
        lines.append(f"  {img['findings']}")

    lines.append("\n═══ CLINICAL NOTES ═══")
    for note in chart_data["notes"]:
        lines.append(f"--- {note['type']} ---")
        lines.append(note["text"])

    return "\n".join(lines)
