#!/usr/bin/env python3
"""
Threshold Behavior Diagnostic Tool

Analyzes how the clinical RAG system responds to threshold changes
to understand the decision-making logic.
"""

import json
import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gpt_local import refine_drugbank_query
from patient_drug_analysis import determine_relevant_sections

def analyze_patient_decision_making(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the decision-making process for a patient"""
    
    print(f"\n🔍 Analyzing: {patient_data.get('patient_id', 'Unknown')}")
    print(f"Age: {patient_data.get('age', 'N/A')}")
    print(f"Weight: {patient_data.get('weight_kg', 'N/A')} kg")
    
    labs = patient_data.get('lab_results', {})
    if labs:
        print(f"Labs: {labs}")
    
    # Get query refinement
    refined_query = refine_drugbank_query(patient_data)
    print(f"Refined Query: {refined_query[:100]}...")
    
    # Get medications
    medications = []
    med_data = patient_data.get("current_medications", [])
    for med in med_data:
        if isinstance(med, dict):
            drug_name = med.get("drug_name", "")
            if drug_name:
                medications.append(drug_name)
    
    print(f"Medications: {medications}")
    
    # Get sections
    if medications:
        section_map = determine_relevant_sections(patient_data, medications)
        print(f"Section Map: {section_map}")
        
        unique_sections = set()
        for sections in section_map.values():
            unique_sections.update(sections)
        print(f"Unique Sections: {sorted(list(unique_sections))}")
        
        return {
            "refined_query": refined_query,
            "medications": medications,
            "section_map": section_map,
            "unique_sections": sorted(list(unique_sections)),
            "total_sections": sum(len(sections) for sections in section_map.values())
        }
    else:
        print("No medications found")
        return {"error": "No medications"}

def test_age_threshold_detailed():
    """Detailed test of age threshold behavior"""
    
    print("="*60)
    print("🎂 DETAILED AGE THRESHOLD ANALYSIS")
    print("="*60)
    
    base_patient = {
        "name": "Age Test Patient",
        "sex": "Female",
        "weight_kg": 70,
        "current_medications": [
            {"drug_name": "Amlodipine", "dose": "5mg"},
            {"drug_name": "Simvastatin", "dose": "20mg"}
        ],
        "clinical_conditions": ["Hypertension", "Hyperlipidemia"],
        "lab_results": {"eGFR": "70 mL/min/1.73m2", "Creatinine": "1.1 mg/dL"}
    }
    
    # Test different ages
    ages = [60, 63, 64, 65, 66, 70]
    results = []
    
    for age in ages:
        patient = base_patient.copy()
        patient["patient_id"] = f"AGE_{age}"
        patient["age"] = age
        
        result = analyze_patient_decision_making(patient)
        result["age"] = age
        results.append(result)
    
    # Compare results
    print("\n📊 AGE THRESHOLD COMPARISON:")
    print("Age | Sections | Unique Sections")
    print("-" * 40)
    
    for result in results:
        if "unique_sections" in result:
            sections_str = ", ".join(result["unique_sections"])
            print(f"{result['age']:3d} | {len(result['unique_sections']):8d} | {sections_str}")
    
    return results

def test_egfr_threshold_detailed():
    """Detailed test of eGFR threshold behavior"""
    
    print("\n" + "="*60)
    print("🫘 DETAILED eGFR THRESHOLD ANALYSIS")
    print("="*60)
    
    base_patient = {
        "name": "Renal Test Patient",
        "age": 55,
        "sex": "Male",
        "weight_kg": 80,
        "current_medications": [
            {"drug_name": "Metformin", "dose": "1000mg"},
            {"drug_name": "Lisinopril", "dose": "20mg"}
        ],
        "clinical_conditions": ["Type 2 Diabetes", "Hypertension"]
    }
    
    # Test different eGFR values
    egfr_values = [70, 65, 61, 60, 59, 55, 35, 30, 29, 25]
    results = []
    
    for egfr in egfr_values:
        patient = base_patient.copy()
        patient["patient_id"] = f"EGFR_{egfr}"
        patient["lab_results"] = {"eGFR": f"{egfr} mL/min/1.73m2"}
        
        result = analyze_patient_decision_making(patient)
        result["egfr"] = egfr
        results.append(result)
    
    # Compare results
    print("\n📊 eGFR THRESHOLD COMPARISON:")
    print("eGFR | Sections | Unique Sections")
    print("-" * 50)
    
    for result in results:
        if "unique_sections" in result:
            sections_str = ", ".join(result["unique_sections"])
            print(f"{result['egfr']:4d} | {len(result['unique_sections']):8d} | {sections_str}")
    
    return results

def test_medication_impact():
    """Test how different medications affect section selection"""
    
    print("\n" + "="*60)
    print("💊 MEDICATION IMPACT ANALYSIS")
    print("="*60)
    
    base_patient = {
        "name": "Medication Test Patient",
        "age": 65,  # Elderly
        "sex": "Male",
        "weight_kg": 75,
        "clinical_conditions": ["Type 2 Diabetes", "Hypertension"],
        "lab_results": {"eGFR": "59 mL/min/1.73m2", "Creatinine": "1.6 mg/dL"}  # Impaired
    }
    
    medication_sets = [
        [{"drug_name": "Metformin", "dose": "500mg"}],
        [{"drug_name": "Amlodipine", "dose": "5mg"}],
        [{"drug_name": "Simvastatin", "dose": "20mg"}],
        [{"drug_name": "Metformin", "dose": "500mg"}, {"drug_name": "Amlodipine", "dose": "5mg"}],
        [{"drug_name": "Warfarin", "dose": "5mg"}],  # High-risk medication
    ]
    
    results = []
    
    for i, medications in enumerate(medication_sets):
        patient = base_patient.copy()
        patient["patient_id"] = f"MED_SET_{i+1}"
        patient["current_medications"] = medications
        
        med_names = [med["drug_name"] for med in medications]
        print(f"\nTesting medications: {med_names}")
        
        result = analyze_patient_decision_making(patient)
        result["medication_set"] = med_names
        results.append(result)
    
    return results

def main():
    """Run diagnostic tests"""
    
    print("🔬 CLINICAL THRESHOLD DIAGNOSTIC TOOL")
    print("Analyzing decision-making logic in clinical RAG system\n")
    
    # Run diagnostic tests
    age_results = test_age_threshold_detailed()
    egfr_results = test_egfr_threshold_detailed()
    med_results = test_medication_impact()
    
    # Save results
    diagnostic_results = {
        "age_threshold_analysis": age_results,
        "egfr_threshold_analysis": egfr_results,
        "medication_impact_analysis": med_results
    }
    
    with open("threshold_diagnostic_results.json", "w", encoding="utf-8") as f:
        json.dump(diagnostic_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 Diagnostic results saved to 'threshold_diagnostic_results.json'")

if __name__ == "__main__":
    main()