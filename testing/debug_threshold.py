#!/usr/bin/env python3
"""
Quick diagnostic for failing threshold tests
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patient_drug_analysis import determine_relevant_sections

def debug_egfr_test():
    """Debug the eGFR 61 vs 59 test"""
    
    base_patient = {
        "name": "Renal Test Patient",
        "age": 55,  # Not elderly
        "sex": "Male",
        "weight_kg": 80,
        "current_medications": [
            {"drug_name": "Metformin", "dose": "1000mg"},
            {"drug_name": "Lisinopril", "dose": "20mg"}
        ],
        "clinical_conditions": ["Type 2 Diabetes", "Hypertension"]
    }
    
    # Patient 1: eGFR 61 (should be normal)
    patient1 = base_patient.copy()
    patient1["patient_id"] = "EGFR_61"
    patient1["lab_results"] = {"eGFR": "61 mL/min/1.73m2"}
    
    # Patient 2: eGFR 59 (should trigger renal impairment)
    patient2 = base_patient.copy()
    patient2["patient_id"] = "EGFR_59"
    patient2["lab_results"] = {"eGFR": "59 mL/min/1.73m2"}
    
    medications = ["Metformin", "Lisinopril"]
    
    print("🔍 DEBUG: eGFR 61 vs 59 Test")
    print(f"Patient 1 Age: {patient1['age']} (elderly threshold: 65)")
    print(f"Patient 1 eGFR: {patient1['lab_results']['eGFR']}")
    
    sections1 = determine_relevant_sections(patient1, medications)
    print(f"Patient 1 sections: {sections1}")
    
    unique1 = set()
    for sections in sections1.values():
        unique1.update(sections)
    print(f"Patient 1 unique sections: {sorted(list(unique1))}")
    
    print(f"\nPatient 2 Age: {patient2['age']} (elderly threshold: 65)")
    print(f"Patient 2 eGFR: {patient2['lab_results']['eGFR']}")
    
    sections2 = determine_relevant_sections(patient2, medications)
    print(f"Patient 2 sections: {sections2}")
    
    unique2 = set()
    for sections in sections2.values():
        unique2.update(sections)
    print(f"Patient 2 unique sections: {sorted(list(unique2))}")
    
    print(f"\nSection differences:")
    print(f"Added: {sorted(list(unique2 - unique1))}")
    print(f"Removed: {sorted(list(unique1 - unique2))}")
    print(f"Net change: {len(unique2) - len(unique1)}")
    
    # This should show that 61->59 eGFR crossing DOES trigger threshold behavior
    # My test logic was wrong about this being "no threshold crossing"

if __name__ == "__main__":
    debug_egfr_test()