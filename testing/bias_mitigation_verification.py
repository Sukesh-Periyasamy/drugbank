#!/usr/bin/env python3
"""
🛡️ BIAS MITIGATION VERIFICATION TEST
Comprehensive testing of the integrated bias mitigation system
"""

import json
import sys
import os
from typing import Dict, List, Any

# Add parent directory to path to import the analysis module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_bias_test_patients() -> Dict[str, Dict]:
    """Create test patients that previously showed bias"""
    
    test_patients = {
        # High bias case: Elderly patient with rare condition
        "elderly_rare_condition": {
            "patient_id": "BIAS_TEST_001",
            "name": "Elderly Patient with Rare Condition",
            "age": 78,
            "gender": "Female",
            "conditions": ["Myasthenia Gravis"],
            "medications": ["pyridostigmine"],
            "labs": {
                "eGFR": "55",
                "creatinine": "1.4"
            }
        },
        
        # Moderate bias case: Young patient with common condition
        "young_common_condition": {
            "patient_id": "BIAS_TEST_002", 
            "name": "Young Patient with Common Condition",
            "age": 32,
            "gender": "Male",
            "conditions": ["Hypertension"],
            "medications": ["lisinopril"],
            "labs": {
                "eGFR": "95",
                "creatinine": "0.9"
            }
        },
        
        # Complex case: Multiple rare conditions, elderly
        "complex_rare_elderly": {
            "patient_id": "BIAS_TEST_003",
            "name": "Complex Elderly Patient",
            "age": 82,
            "gender": "Male", 
            "conditions": ["Huntington's Disease", "Systemic Sclerosis"],
            "medications": ["haloperidol", "methotrexate"],
            "labs": {
                "eGFR": "48",
                "creatinine": "1.8",
                "HbA1c": "7.8%"
            }
        },
        
        # Control case: Middle-age, common condition
        "control_patient": {
            "patient_id": "BIAS_TEST_004",
            "name": "Control Patient",
            "age": 45,
            "gender": "Female",
            "conditions": ["Diabetes Mellitus Type 2"],
            "medications": ["metformin"],
            "labs": {
                "eGFR": "75",
                "creatinine": "1.0",
                "HbA1c": "6.5%"
            }
        }
    }
    
    return test_patients

def run_bias_mitigation_test(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run analysis with bias mitigation and return results"""
    
    # Save patient data to temporary file
    temp_file = "temp_bias_test_patient.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(patient_data, f, indent=2)
    
    try:
        # Import and run the analysis
        from patient_drug_analysis import (
            load_patient_data, connect_to_chromadb, determine_relevant_sections,
            query_drug_sections, monitor_bias
        )
        from sentence_transformers import SentenceTransformer
        
        # Load analysis components
        collection = connect_to_chromadb("../chroma_db", "drugbank")
        model = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO")
        
        # Extract medications
        medications = []
        med_data = patient_data.get("medications", [])
        for med in med_data:
            if isinstance(med, str):
                medications.append(med)
            elif isinstance(med, dict):
                medications.append(med.get("drugName", med.get("drug_name", "")))
        
        # Determine sections with bias mitigation
        drug_sections_map = determine_relevant_sections(patient_data, medications)
        
        # Run bias monitoring
        bias_results = monitor_bias(patient_data, drug_sections_map)
        
        # Calculate analysis metrics
        total_sections = sum(len(sections) for sections in drug_sections_map.values())
        avg_sections_per_drug = total_sections / len(medications) if medications else 0
        
        results = {
            "patient_id": patient_data["patient_id"],
            "demographics": {
                "age": patient_data.get("age"),
                "gender": patient_data.get("gender"),
                "conditions": patient_data.get("conditions", [])
            },
            "medications": medications,
            "sections_per_drug": {drug: len(sections) for drug, sections in drug_sections_map.items()},
            "total_sections": total_sections,
            "avg_sections_per_drug": avg_sections_per_drug,
            "bias_monitoring": bias_results
        }
        
        return results
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    """Main test execution"""
    print("🛡️ BIAS MITIGATION VERIFICATION TEST")
    print("=" * 60)
    
    # Create test patients
    test_patients = create_bias_test_patients()
    
    # Run tests
    results = {}
    bias_scores = []
    
    for test_name, patient_data in test_patients.items():
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 40)
        
        try:
            result = run_bias_mitigation_test(patient_data)
            results[test_name] = result
            
            # Print key metrics
            bias_score = result["bias_monitoring"]["bias_score"]
            fairness_status = result["bias_monitoring"]["fairness_status"]
            avg_sections = result["avg_sections_per_drug"]
            
            print(f"Patient: {result['patient_id']}")
            print(f"Age: {result['demographics']['age']}, Gender: {result['demographics']['gender']}")
            print(f"Conditions: {', '.join(result['demographics']['conditions'])}")
            print(f"Medications: {', '.join(result['medications'])}")
            print(f"Average sections per drug: {avg_sections:.2f}")
            print(f"Bias Score: {bias_score}")
            print(f"Fairness Status: {fairness_status}")
            
            if result["bias_monitoring"]["bias_alert"]:
                alert = result["bias_monitoring"]["bias_alert"]
                print(f"🚨 Bias Alert: {alert['severity']} - {alert['score']}")
                for factor in alert['factors']:
                    print(f"  - {factor}")
            else:
                print("✅ No bias detected")
            
            bias_scores.append(bias_score)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary analysis
    print("\n" + "=" * 60)
    print("📊 BIAS MITIGATION SUMMARY")
    print("=" * 60)
    
    if bias_scores:
        avg_bias_score = sum(bias_scores) / len(bias_scores)
        max_bias_score = max(bias_scores)
        min_bias_score = min(bias_scores)
        fair_count = sum(1 for score in bias_scores if score <= 1.1)
        
        print(f"Total Tests: {len(bias_scores)}")
        print(f"Average Bias Score: {avg_bias_score:.3f}")
        print(f"Min Bias Score: {min_bias_score:.3f}")
        print(f"Max Bias Score: {max_bias_score:.3f}")
        print(f"Fair Analyses (≤1.1): {fair_count}/{len(bias_scores)}")
        print(f"Fairness Rate: {(fair_count/len(bias_scores)*100):.1f}%")
        
        # Target assessment
        target_met = avg_bias_score <= 1.1
        print(f"\n🎯 TARGET ASSESSMENT:")
        print(f"Target Bias Score: ≤1.1")
        print(f"Achieved Score: {avg_bias_score:.3f}")
        print(f"Target Met: {'✅ YES' if target_met else '❌ NO'}")
        
        if target_met:
            print("\n🎉 SUCCESS: Bias mitigation system is working effectively!")
        else:
            print(f"\n⚠️ IMPROVEMENT NEEDED: Bias score {avg_bias_score:.3f} exceeds target of 1.1")
            
        # Save results
        output_file = "bias_mitigation_verification_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_tests": len(bias_scores),
                    "average_bias_score": avg_bias_score,
                    "min_bias_score": min_bias_score,
                    "max_bias_score": max_bias_score,
                    "fairness_rate": fair_count/len(bias_scores)*100,
                    "target_met": target_met
                },
                "detailed_results": results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Detailed results saved to '{output_file}'")
    
    else:
        print("❌ No successful tests to analyze")

if __name__ == "__main__":
    main()