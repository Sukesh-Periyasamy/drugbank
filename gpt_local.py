import json
import os
from datetime import datetime

def refine_drugbank_query(patient_data):
    """Extract relevant patient details for DrugBank queries using local rule-based approach"""
    query_parts = []
    
    # Extract medications (flexible field names)
    medications = []
    med_data = patient_data.get("medications", patient_data.get("current_medications", []))
    if med_data:
        for med in med_data:
            if isinstance(med, dict):
                # Try both drugName and drug_name
                drug_name = med.get("drugName", med.get("drug_name", ""))
                if drug_name:
                    medications.append(drug_name)
            elif isinstance(med, str):
                medications.append(med)
    
    if medications:
        query_parts.append(f"Medications: {', '.join(medications)}")
    
    # Extract conditions (flexible field names)
    conditions = patient_data.get("conditions", patient_data.get("clinical_conditions", []))
    if conditions:
        if isinstance(conditions, list):
            query_parts.append(f"Conditions: {', '.join(conditions)}")
        elif isinstance(conditions, str):
            query_parts.append(f"Conditions: {conditions}")
    
    # Extract allergies
    if "allergic_to" in patient_data or "allergies" in patient_data:
        allergies = patient_data.get("allergic_to", patient_data.get("allergies", ""))
        if isinstance(allergies, list):
            query_parts.append(f"Allergies: {', '.join(allergies)}")
        elif isinstance(allergies, str) and allergies.strip():
            query_parts.append(f"Allergies: {allergies}")
    
    # Extract relevant labs (flexible field names)
    labs = patient_data.get("labs", patient_data.get("lab_results", {}))
    if labs:
        relevant_labs = []
        for lab, value in labs.items():
            if lab.lower() in ['creatinine', 'serum_creatinine', 'egfr', 'lft', 'hba1c', 'liver', 'hb', 'calcium', 'vitamin_d']:
                relevant_labs.append(f"{lab}: {value}")
        if relevant_labs:
            query_parts.append(f"Labs: {', '.join(relevant_labs)}")
    
    # Extract demographics if relevant
    demo_parts = []
    if "sex" in patient_data:
        demo_parts.append(f"Sex: {patient_data['sex']}")
    if "weight_kg" in patient_data:
        demo_parts.append(f"Weight: {patient_data['weight_kg']}kg")
    
    # Calculate age if DOB is available, or use direct age
    if "age" in patient_data:
        demo_parts.append(f"Age: {patient_data['age']}")
    elif "dob" in patient_data:
        try:
            dob = datetime.strptime(patient_data["dob"], "%Y-%m-%d")
            age = datetime.now().year - dob.year
            demo_parts.append(f"Age: {age}")
        except:
            pass
    
    if demo_parts:
        query_parts.append(f"Demographics: {', '.join(demo_parts)}")
    
    return " | ".join(query_parts)

if __name__ == "__main__":
    # Load patient JSON
    with open("patient.json", "r") as f:
        patient_data = json.load(f)
    
    refined_query = refine_drugbank_query(patient_data)
    print("Refined Query for DrugBank DB:")
    print(refined_query)