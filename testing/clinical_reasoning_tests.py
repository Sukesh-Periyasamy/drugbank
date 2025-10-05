#!/usr/bin/env python3
"""
AI Reasoning Consistency Tests for DrugBank Clinical RAG System

This module tests clinical decision-making consistency across threshold boundaries:
- Age thresholds (64 vs 65 for elderly classification)
- Renal function thresholds (eGFR boundaries)
- Lab value thresholds (HbA1c, creatinine, etc.)
- Multi-parameter interactions

Validates that small input changes produce appropriate clinical reasoning changes.
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
import copy

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gpt_local import refine_drugbank_query
from patient_drug_analysis import determine_relevant_sections

class ClinicalReasoningTester:
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "threshold_tests": [],
            "consistency_issues": [],
            "summary": {
                "total_threshold_tests": 0,
                "consistent_behaviors": 0,
                "inconsistent_behaviors": 0,
                "clinical_accuracy": 0.0
            }
        }
        
        # Define clinical thresholds for testing
        self.clinical_thresholds = {
            "age_elderly": 65,
            "egfr_impaired": 60,
            "egfr_severe": 30,
            "creatinine_elevated": 1.5,
            "hba1c_poor_control": 7.0,
            "hba1c_very_poor": 9.0
        }
    
    def create_threshold_test_pairs(self) -> List[Tuple[str, Dict, Dict, str]]:
        """Create pairs of patient data that test clinical thresholds"""
        
        base_patient = {
            "patient_id": "THRESHOLD_BASE",
            "name": "Threshold Test Patient",
            "sex": "Male",
            "weight_kg": 75,
            "current_medications": [
                {"drug_name": "Metformin", "dose": "500mg"},
                {"drug_name": "Lisinopril", "dose": "10mg"}
            ],
            "clinical_conditions": ["Type 2 Diabetes", "Hypertension"],
            "allergies": ["Penicillin"]
        }
        
        test_pairs = []
        
        # Test 1: Age threshold (elderly classification)
        patient1 = copy.deepcopy(base_patient)
        patient1["patient_id"] = "AGE_64"
        patient1["age"] = 64
        patient1["lab_results"] = {"eGFR": "65 mL/min/1.73m2", "Creatinine": "1.2 mg/dL"}
        
        patient2 = copy.deepcopy(base_patient)
        patient2["patient_id"] = "AGE_65"
        patient2["age"] = 65
        patient2["lab_results"] = {"eGFR": "65 mL/min/1.73m2", "Creatinine": "1.2 mg/dL"}
        
        test_pairs.append((
            "Age Threshold (64 vs 65)",
            patient1, patient2,
            "Age 65+ should trigger metabolism/dosage sections due to elderly status"
        ))
        
        # Test 2: eGFR threshold (renal impairment)
        patient3 = copy.deepcopy(base_patient)
        patient3["patient_id"] = "EGFR_61"
        patient3["age"] = 55
        patient3["lab_results"] = {"eGFR": "61 mL/min/1.73m2", "Creatinine": "1.4 mg/dL"}
        
        patient4 = copy.deepcopy(base_patient)
        patient4["patient_id"] = "EGFR_59"
        patient4["age"] = 55
        patient4["lab_results"] = {"eGFR": "59 mL/min/1.73m2", "Creatinine": "1.6 mg/dL"}
        
        test_pairs.append((
            "eGFR Threshold (61 vs 59)",
            patient3, patient4,
            "eGFR <60 should trigger toxicity and metabolism sections"
        ))
        
        # Test 3: Creatinine threshold
        patient5 = copy.deepcopy(base_patient)
        patient5["patient_id"] = "CREAT_1.4"
        patient5["age"] = 55
        patient5["lab_results"] = {"Creatinine": "1.4 mg/dL", "eGFR": "65 mL/min/1.73m2"}
        
        patient6 = copy.deepcopy(base_patient)
        patient6["patient_id"] = "CREAT_1.6"
        patient6["age"] = 55
        patient6["lab_results"] = {"Creatinine": "1.6 mg/dL", "eGFR": "62 mL/min/1.73m2"}
        
        test_pairs.append((
            "Creatinine Threshold (1.4 vs 1.6)",
            patient5, patient6,
            "Creatinine >1.5 should trigger toxicity concerns"
        ))
        
        # Test 4: HbA1c threshold (diabetes control)
        patient7 = copy.deepcopy(base_patient)
        patient7["patient_id"] = "HBA1C_6.9"
        patient7["age"] = 55
        patient7["lab_results"] = {"HbA1c": "6.9%", "Creatinine": "1.0 mg/dL"}
        
        patient8 = copy.deepcopy(base_patient)
        patient8["patient_id"] = "HBA1C_7.1"
        patient8["age"] = 55
        patient8["lab_results"] = {"HbA1c": "7.1%", "Creatinine": "1.0 mg/dL"}
        
        test_pairs.append((
            "HbA1c Threshold (6.9% vs 7.1%)",
            patient7, patient8,
            "HbA1c >7.0% should trigger toxicity/metabolism sections for poor control"
        ))
        
        # Test 5: Combined thresholds (age + renal)
        patient9 = copy.deepcopy(base_patient)
        patient9["patient_id"] = "COMBINED_LOW"
        patient9["age"] = 64
        patient9["lab_results"] = {"eGFR": "61 mL/min/1.73m2", "Creatinine": "1.4 mg/dL"}
        
        patient10 = copy.deepcopy(base_patient)
        patient10["patient_id"] = "COMBINED_HIGH"
        patient10["age"] = 65
        patient10["lab_results"] = {"eGFR": "59 mL/min/1.73m2", "Creatinine": "1.6 mg/dL"}
        
        test_pairs.append((
            "Combined Age+Renal (64+eGFR61 vs 65+eGFR59)",
            patient9, patient10,
            "Combined elderly + renal impairment should trigger comprehensive analysis"
        ))
        
        # Test 6: Weight extremes
        patient11 = copy.deepcopy(base_patient)
        patient11["patient_id"] = "WEIGHT_51"
        patient11["age"] = 45
        patient11["weight_kg"] = 51
        patient11["lab_results"] = {"Creatinine": "1.0 mg/dL"}
        
        patient12 = copy.deepcopy(base_patient)
        patient12["patient_id"] = "WEIGHT_49"
        patient12["age"] = 45
        patient12["weight_kg"] = 49
        patient12["lab_results"] = {"Creatinine": "1.0 mg/dL"}
        
        test_pairs.append((
            "Weight Threshold (51kg vs 49kg)",
            patient11, patient12,
            "Weight <50kg should trigger dosage/metabolism considerations"
        ))
        
        return test_pairs
    
    def analyze_clinical_reasoning(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze clinical reasoning for a patient"""
        
        # Get query refinement reasoning
        refined_query = refine_drugbank_query(patient_data)
        
        # Extract medications
        medications = []
        med_data = patient_data.get("current_medications", patient_data.get("medications", []))
        for med in med_data:
            if isinstance(med, dict):
                drug_name = med.get("drug_name", med.get("drugName", ""))
                if drug_name:
                    medications.append(drug_name)
        
        # Get section determination reasoning
        if medications:
            section_map = determine_relevant_sections(patient_data, medications)
            total_sections = sum(len(sections) for sections in section_map.values())
            unique_sections = set()
            for sections in section_map.values():
                unique_sections.update(sections)
        else:
            section_map = {}
            total_sections = 0
            unique_sections = set()
        
        # Analyze reasoning triggers
        reasoning = {
            "refined_query": refined_query,
            "medications_count": len(medications),
            "total_sections": total_sections,
            "unique_sections": sorted(list(unique_sections)),
            "section_breakdown": {drug: sections for drug, sections in section_map.items()},
            "reasoning_triggers": self.extract_reasoning_triggers(patient_data, unique_sections)
        }
        
        return reasoning
    
    def extract_reasoning_triggers(self, patient_data: Dict[str, Any], sections: set) -> Dict[str, bool]:
        """Extract what clinical factors triggered specific reasoning"""
        
        triggers = {
            "age_elderly": False,
            "renal_impairment": False,
            "elevated_creatinine": False,
            "poor_diabetes_control": False,
            "multiple_medications": False,
            "conditions_present": False,
            "allergies_present": False,
            "low_weight": False
        }
        
        # Age trigger
        age = patient_data.get("age", 0)
        if age >= 65:
            triggers["age_elderly"] = True
        
        # Lab triggers
        labs = patient_data.get("lab_results", patient_data.get("labs", {}))
        if labs:
            # eGFR
            egfr = labs.get("eGFR", labs.get("egfr", ""))
            if egfr:
                try:
                    egfr_val = float(str(egfr).split()[0])
                    if egfr_val < 60:
                        triggers["renal_impairment"] = True
                except:
                    pass
            
            # Creatinine
            creatinine = labs.get("Creatinine", labs.get("creatinine", ""))
            if creatinine:
                try:
                    creat_val = float(str(creatinine).split()[0])
                    if creat_val > 1.5:
                        triggers["elevated_creatinine"] = True
                except:
                    pass
            
            # HbA1c
            hba1c = labs.get("HbA1c", labs.get("hba1c", ""))
            if hba1c:
                try:
                    hba1c_val = float(str(hba1c).replace("%", ""))
                    if hba1c_val > 7.0:
                        triggers["poor_diabetes_control"] = True
                except:
                    pass
        
        # Weight trigger
        weight = patient_data.get("weight_kg", 0)
        if weight > 0 and (weight < 50 or weight > 120):
            triggers["low_weight"] = True
        
        # Other triggers
        medications = patient_data.get("current_medications", patient_data.get("medications", []))
        if len(medications) > 1:
            triggers["multiple_medications"] = True
        
        conditions = patient_data.get("clinical_conditions", patient_data.get("conditions", []))
        if conditions:
            triggers["conditions_present"] = True
        
        allergies = patient_data.get("allergies", patient_data.get("allergic_to", []))
        if allergies:
            triggers["allergies_present"] = True
        
        return triggers
    
    def test_threshold_consistency(self, test_name: str, patient1: Dict, patient2: Dict, expected_behavior: str) -> Dict[str, Any]:
        """Test clinical reasoning consistency across a threshold"""
        
        print(f"\n🧪 Testing: {test_name}")
        
        # Analyze both patients
        reasoning1 = self.analyze_clinical_reasoning(patient1)
        reasoning2 = self.analyze_clinical_reasoning(patient2)
        
        # Compare reasoning
        result = {
            "test_name": test_name,
            "patient1_id": patient1["patient_id"],
            "patient2_id": patient2["patient_id"],
            "expected_behavior": expected_behavior,
            "patient1_reasoning": reasoning1,
            "patient2_reasoning": reasoning2,
            "consistency_check": {},
            "clinical_appropriateness": True,
            "issues": []
        }
        
        # Check for expected differences
        sections1 = set(reasoning1["unique_sections"])
        sections2 = set(reasoning2["unique_sections"])
        
        triggers1 = reasoning1["reasoning_triggers"]
        triggers2 = reasoning2["reasoning_triggers"]
        
        # Analyze threshold-specific expectations
        if "Age" in test_name:
            if triggers2["age_elderly"] and not triggers1["age_elderly"]:
                if "metabolism" in sections2 and "metabolism" not in sections1:
                    print("✅ Correct: Age 65 triggered metabolism section")
                else:
                    result["issues"].append("Age 65 should trigger metabolism section")
            else:
                result["issues"].append("Age threshold not properly detected")
        
        elif "eGFR" in test_name:
            if triggers2["renal_impairment"] and not triggers1["renal_impairment"]:
                if "toxicity" in sections2:
                    print("✅ Correct: Low eGFR triggered toxicity concerns")
                else:
                    result["issues"].append("Low eGFR should trigger toxicity section")
            else:
                result["issues"].append("eGFR threshold not properly detected")
        
        elif "Creatinine" in test_name:
            if triggers2["elevated_creatinine"] and not triggers1["elevated_creatinine"]:
                if "toxicity" in sections2:
                    print("✅ Correct: Elevated creatinine triggered toxicity")
                else:
                    result["issues"].append("Elevated creatinine should trigger toxicity")
            else:
                result["issues"].append("Creatinine threshold not properly detected")
        
        elif "HbA1c" in test_name:
            if triggers2["poor_diabetes_control"] and not triggers1["poor_diabetes_control"]:
                if "toxicity" in sections2:
                    print("✅ Correct: Poor HbA1c control triggered toxicity")
                else:
                    result["issues"].append("Poor diabetes control should trigger toxicity")
            else:
                result["issues"].append("HbA1c threshold not properly detected")
        
        elif "Weight" in test_name:
            if triggers2["low_weight"] and not triggers1["low_weight"]:
                if "dosage" in sections2:
                    print("✅ Correct: Low weight triggered dosage considerations")
                else:
                    result["issues"].append("Low weight should trigger dosage adjustments")
            else:
                result["issues"].append("Weight threshold not properly detected")
        
        elif "Combined" in test_name:
            # Should trigger multiple sections
            expected_sections = {"metabolism", "dosage", "toxicity"}
            if expected_sections.issubset(sections2):
                print("✅ Correct: Combined risk factors triggered comprehensive analysis")
            else:
                missing = expected_sections - sections2
                result["issues"].append(f"Combined risk should trigger: {missing}")
        
        # Record consistency metrics
        result["consistency_check"] = {
            "sections_added": list(sections2 - sections1),
            "sections_removed": list(sections1 - sections2),
            "trigger_changes": {k: v2 != triggers1[k] for k, v2 in triggers2.items()},
            "total_sections_change": reasoning2["total_sections"] - reasoning1["total_sections"]
        }
        
        if result["issues"]:
            result["clinical_appropriateness"] = False
            print(f"❌ Issues found: {result['issues']}")
        else:
            print("✅ Clinical reasoning appropriate")
        
        return result
    
    def run_threshold_tests(self):
        """Run all clinical reasoning threshold tests"""
        
        print("🧠 Starting AI Reasoning Consistency Tests...")
        print("Testing clinical decision-making across threshold boundaries\n")
        
        test_pairs = self.create_threshold_test_pairs()
        
        for test_name, patient1, patient2, expected_behavior in test_pairs:
            result = self.test_threshold_consistency(test_name, patient1, patient2, expected_behavior)
            self.test_results["threshold_tests"].append(result)
            
            if result["clinical_appropriateness"]:
                self.test_results["summary"]["consistent_behaviors"] += 1
            else:
                self.test_results["summary"]["inconsistent_behaviors"] += 1
                self.test_results["consistency_issues"].extend(result["issues"])
        
        # Calculate summary
        total_tests = len(test_pairs)
        self.test_results["summary"]["total_threshold_tests"] = total_tests
        if total_tests > 0:
            self.test_results["summary"]["clinical_accuracy"] = (
                self.test_results["summary"]["consistent_behaviors"] / total_tests
            ) * 100
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"🧠 AI REASONING CONSISTENCY SUMMARY")
        print(f"{'='*70}")
        print(f"Total Threshold Tests: {total_tests}")
        print(f"Clinically Appropriate: {self.test_results['summary']['consistent_behaviors']}")
        print(f"Issues Found: {self.test_results['summary']['inconsistent_behaviors']}")
        print(f"Clinical Accuracy: {self.test_results['summary']['clinical_accuracy']:.1f}%")
        
        if self.test_results["consistency_issues"]:
            print(f"\n⚠️  CLINICAL REASONING ISSUES:")
            for issue in self.test_results["consistency_issues"]:
                print(f"   - {issue}")
        else:
            print(f"\n✅ ALL CLINICAL REASONING IS APPROPRIATE!")
        
        # Save results
        with open("clinical_reasoning_test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Detailed results saved to 'clinical_reasoning_test_results.json'")
        
        return self.test_results["summary"]["inconsistent_behaviors"] == 0

def main():
    """Main function to run clinical reasoning tests"""
    tester = ClinicalReasoningTester()
    success = tester.run_threshold_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()