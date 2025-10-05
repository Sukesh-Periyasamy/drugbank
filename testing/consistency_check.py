#!/usr/bin/env python3
"""
Cross-Module Consistency Tests for DrugBank Clinical RAG System

This module tests consistency across all system components:
- Patient data parsing
- Query refinement 
- Drug analysis
- Result summarization

Ensures all modules interpret the same patient data identically.
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
import traceback

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main system components
from gpt_local import refine_drugbank_query
from patient_drug_analysis import (
    load_patient_data, 
    determine_relevant_sections,
    connect_to_chromadb,
    query_drug_sections
)

class ConsistencyTester:
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "consistency_issues": [],
            "detailed_results": []
        }
        
    def extract_medications_parser(self, patient_data: Dict[str, Any]) -> List[str]:
        """Extract medications using the same logic as patient_drug_analysis.py"""
        medications = []
        med_data = patient_data.get("medications", patient_data.get("current_medications", []))
        if med_data:
            for med in med_data:
                if isinstance(med, dict):
                    drug_name = med.get("drugName", med.get("drug_name", ""))
                    if drug_name:
                        medications.append(drug_name)
                elif isinstance(med, str):
                    medications.append(med)
        return medications
    
    def extract_conditions_parser(self, patient_data: Dict[str, Any]) -> List[str]:
        """Extract conditions using the same logic as patient_drug_analysis.py"""
        conditions = patient_data.get("conditions", patient_data.get("clinical_conditions", []))
        if isinstance(conditions, list):
            return conditions
        elif isinstance(conditions, str) and conditions.strip():
            return [conditions]  # Treat single string as one condition
        return []
    
    def extract_allergies_parser(self, patient_data: Dict[str, Any]) -> List[str]:
        """Extract allergies using the same logic as patient_drug_analysis.py"""
        allergies = patient_data.get("allergic_to", patient_data.get("allergies", []))
        if isinstance(allergies, list):
            return allergies
        elif isinstance(allergies, str) and allergies.strip():
            return [allergies]
        return []
    
    def extract_labs_parser(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract labs using the same logic as patient_drug_analysis.py"""
        return patient_data.get("labs", patient_data.get("lab_results", {}))
    
    def test_patient_data_consistency(self, test_name: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test cross-module consistency for a single patient"""
        print(f"\n=== Testing {test_name} ===")
        
        result = {
            "test_name": test_name,
            "patient_id": patient_data.get("patient_id", "Unknown"),
            "success": True,
            "issues": [],
            "metrics": {}
        }
        
        try:
            # Step 1: Parse patient data
            medications = self.extract_medications_parser(patient_data)
            conditions = self.extract_conditions_parser(patient_data)
            allergies = self.extract_allergies_parser(patient_data)
            labs = self.extract_labs_parser(patient_data)
            
            print(f"Parser found: {len(medications)} medications, {len(conditions)} conditions, {len(allergies)} allergies")
            
            # Step 2: Query refinement
            refined_query = refine_drugbank_query(patient_data)
            
            # Extract info from refined query
            query_meds = []
            query_conditions = []
            query_allergies = []
            
            if "Medications:" in refined_query:
                med_part = refined_query.split("Medications:")[1].split("|")[0].strip()
                if med_part:
                    query_meds = [med.strip() for med in med_part.split(",")]
            
            if "Conditions:" in refined_query:
                cond_part = refined_query.split("Conditions:")[1].split("|")[0].strip()
                if cond_part:
                    query_conditions = [cond.strip() for cond in cond_part.split(",")]
            
            if "Allergies:" in refined_query:
                allergy_part = refined_query.split("Allergies:")[1].split("|")[0].strip()
                if allergy_part:
                    query_allergies = [allergy.strip() for allergy in allergy_part.split(",")]
            
            print(f"Query refinement found: {len(query_meds)} medications, {len(query_conditions)} conditions, {len(query_allergies)} allergies")
            
            # Step 3: Section determination
            if medications:
                section_map = determine_relevant_sections(patient_data, medications)
                analyzer_meds = list(section_map.keys())
                print(f"Section analyzer found: {len(analyzer_meds)} medications")
            else:
                analyzer_meds = []
                section_map = {}
                print("Section analyzer found: 0 medications")
            
            # Step 4: Consistency checks
            issues = []
            
            # Check medication consistency
            if len(medications) != len(query_meds) and query_meds != ['']:
                issues.append(f"Medication count mismatch: Parser={len(medications)}, Query={len(query_meds)}")
            
            if len(medications) != len(analyzer_meds):
                issues.append(f"Medication count mismatch: Parser={len(medications)}, Analyzer={len(analyzer_meds)}")
            
            # Check medication names consistency
            if medications and query_meds and query_meds != ['']:
                parser_set = set(medications)
                query_set = set(query_meds)
                if parser_set != query_set:
                    issues.append(f"Medication names mismatch: Parser={parser_set}, Query={query_set}")
            
            if medications and analyzer_meds:
                parser_set = set(medications)
                analyzer_set = set(analyzer_meds)
                if parser_set != analyzer_set:
                    issues.append(f"Medication names mismatch: Parser={parser_set}, Analyzer={analyzer_set}")
            
            # Check condition consistency
            if len(conditions) != len(query_conditions) and query_conditions != ['']:
                issues.append(f"Condition count mismatch: Parser={len(conditions)}, Query={len(query_conditions)}")
            
            # Check allergy consistency
            if len(allergies) != len(query_allergies) and query_allergies != ['']:
                issues.append(f"Allergy count mismatch: Parser={len(allergies)}, Query={len(query_allergies)}")
            
            # Record metrics
            result["metrics"] = {
                "parser_medications": len(medications),
                "query_medications": len(query_meds) if query_meds != [''] else 0,
                "analyzer_medications": len(analyzer_meds),
                "parser_conditions": len(conditions),
                "query_conditions": len(query_conditions) if query_conditions != [''] else 0,
                "parser_allergies": len(allergies),
                "query_allergies": len(query_allergies) if query_allergies != [''] else 0,
                "total_sections_selected": sum(len(sections) for sections in section_map.values()) if section_map else 0
            }
            
            if issues:
                result["success"] = False
                result["issues"] = issues
                self.test_results["tests_failed"] += 1
                print(f"❌ CONSISTENCY ISSUES FOUND:")
                for issue in issues:
                    print(f"   - {issue}")
            else:
                self.test_results["tests_passed"] += 1
                print(f"✅ All modules consistent")
            
        except Exception as e:
            result["success"] = False
            result["issues"] = [f"Exception during testing: {str(e)}"]
            self.test_results["tests_failed"] += 1
            print(f"❌ ERROR: {e}")
            traceback.print_exc()
        
        return result
    
    def run_comprehensive_tests(self):
        """Run consistency tests across multiple patient scenarios"""
        print("🔍 Starting Cross-Module Consistency Tests...")
        
        # Test Case 1: Simple patient
        test1_data = {
            "patient_id": "CONS_001",
            "name": "Simple Patient",
            "age": 30,
            "current_medications": [
                {"drug_name": "Aspirin", "dose": "81mg", "frequency": "daily"}
            ],
            "clinical_conditions": ["Headache"],
            "allergies": ["Penicillin"]
        }
        
        # Test Case 2: Complex patient
        test2_data = {
            "patient_id": "CONS_002", 
            "name": "Complex Patient",
            "age": 75,
            "weight_kg": 60,
            "medications": [
                {"drugName": "Warfarin", "dose": "5mg"},
                {"drugName": "Metformin", "dose": "500mg"},
                {"drugName": "Lisinopril", "dose": "10mg"}
            ],
            "conditions": ["Diabetes", "Hypertension", "Atrial Fibrillation"],
            "allergic_to": ["Sulfa drugs", "Penicillin"],
            "labs": {
                "creatinine": "1.8 mg/dL",
                "egfr": "45 mL/min/1.73m2",
                "hba1c": "8.2%"
            }
        }
        
        # Test Case 3: Edge case - Mixed field names
        test3_data = {
            "patient_id": "CONS_003",
            "age": 45,
            "current_medications": [
                {"drug_name": "Atorvastatin"}
            ],
            "conditions": ["Hyperlipidemia"],
            "lab_results": {
                "Cholesterol": "280 mg/dL"
            },
            "allergies": []
        }
        
        # Test Case 4: Empty/minimal data
        test4_data = {
            "patient_id": "CONS_004",
            "medications": []
        }
        
        # Test Case 5: Inconsistent structure
        test5_data = {
            "patient_id": "CONS_005",
            "current_medications": [
                "Ibuprofen",  # String instead of dict
                {"drug_name": "Acetaminophen"}  # Dict format
            ],
            "clinical_conditions": "Single condition as string",
            "allergic_to": "Single allergy as string"
        }
        
        test_cases = [
            ("Simple Patient", test1_data),
            ("Complex Patient", test2_data), 
            ("Mixed Field Names", test3_data),
            ("Empty Data", test4_data),
            ("Inconsistent Structure", test5_data)
        ]
        
        # Run all tests
        for test_name, test_data in test_cases:
            result = self.test_patient_data_consistency(test_name, test_data)
            self.test_results["detailed_results"].append(result)
            if not result["success"]:
                self.test_results["consistency_issues"].extend(result["issues"])
        
        # Summary
        total_tests = len(test_cases)
        self.test_results["total_tests"] = total_tests
        self.test_results["success_rate"] = (self.test_results["tests_passed"] / total_tests) * 100
        
        print(f"\n{'='*60}")
        print(f"🏁 CONSISTENCY TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.test_results['tests_passed']}")
        print(f"Failed: {self.test_results['tests_failed']}")
        print(f"Success Rate: {self.test_results['success_rate']:.1f}%")
        
        if self.test_results["consistency_issues"]:
            print(f"\n⚠️  CONSISTENCY ISSUES DETECTED:")
            for issue in self.test_results["consistency_issues"]:
                print(f"   - {issue}")
        else:
            print(f"\n✅ ALL MODULES ARE CONSISTENT!")
        
        # Save results
        with open("consistency_test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Detailed results saved to 'consistency_test_results.json'")
        
        return self.test_results["tests_failed"] == 0

def main():
    """Main function to run consistency tests"""
    tester = ConsistencyTester()
    success = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()