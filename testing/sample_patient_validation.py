#!/usr/bin/env python3
"""
Sample Patient Data for Schema Validation Testing

This file contains various patient data examples to test against the patient schema:
- Valid patient records in different formats
- Invalid records with common data entry errors
- Edge cases and boundary conditions
"""

import json
import sys
import os

# Sample valid patient data
VALID_PATIENTS = [
    {
        "patient_id": "PAT_001",
        "name": "Robert Johnson",
        "age": 55,
        "sex": "Male",
        "weight_kg": 80.5,
        "height_cm": 180,
        "current_medications": [
            {
                "drug_name": "Lisinopril",
                "dose": "10 mg",
                "frequency": "once daily",
                "route": "oral"
            },
            {
                "drug_name": "Simvastatin",
                "dose": "20 mg",
                "frequency": "bedtime"
            }
        ],
        "clinical_conditions": ["Hypertension", "Hyperlipidemia"],
        "allergies": ["Shellfish"],
        "lab_results": {
            "Creatinine": "1.1 mg/dL",
            "eGFR": "75 mL/min/1.73m2",
            "Total_Cholesterol": "180 mg/dL"
        }
    },
    {
        "patient_id": "PAT_002",
        "name": "Maria Garcia",
        "age": 34,
        "sex": "Female",
        "weight_kg": 65.2,
        "current_medications": [
            {
                "drug_name": "Metformin",
                "dose": "500 mg",
                "frequency": "twice daily"
            }
        ],
        "clinical_conditions": ["Type 2 Diabetes"],
        "allergies": [],
        "lab_results": {
            "HbA1c": "7.2%",
            "Glucose": "140 mg/dL"
        }
    }
]

# Sample invalid patient data (common errors)
INVALID_PATIENTS = [
    {
        # Missing required field 'age'
        "patient_id": "PAT_ERR_001",
        "name": "Missing Age Patient",
        "sex": "Male",
        "current_medications": []
    },
    {
        # Wrong data types
        "patient_id": "PAT_ERR_002",
        "name": "Wrong Types Patient",
        "age": "thirty-five",  # Should be integer
        "sex": "Male",
        "weight_kg": "65 kg",  # Should be number
        "current_medications": "Aspirin"  # Should be array
    },
    {
        # Invalid constraint values
        "patient_id": "",  # Empty string
        "name": "Invalid Constraints Patient",
        "age": 150,  # Too old
        "sex": "InvalidSex",  # Not in enum
        "weight_kg": -10,  # Negative weight
        "current_medications": [
            {
                "drug_name": "",  # Empty drug name
                "dose": "A" * 200  # Too long
            }
        ]
    }
]

def validate_sample_data():
    """Validate sample patient data using the schema validation test"""
    
    # Import the schema validator
    from schema_validation_test import SchemaValidator
    
    print("🧪 Testing Sample Patient Data Against Schema")
    print("=" * 60)
    
    validator = SchemaValidator("patient_schema.json")
    
    print("\n📋 Testing Valid Patient Samples:")
    print("-" * 40)
    
    valid_results = []
    for i, patient in enumerate(VALID_PATIENTS):
        result = validator.validate_patient_data(
            f"Valid Sample Patient {i+1}",
            patient,
            expect_valid=True
        )
        valid_results.append(result)
    
    print("\n📋 Testing Invalid Patient Samples:")
    print("-" * 40)
    
    invalid_results = []
    for i, patient in enumerate(INVALID_PATIENTS):
        result = validator.validate_patient_data(
            f"Invalid Sample Patient {i+1}",
            patient,
            expect_valid=False
        )
        invalid_results.append(result)
    
    # Summary
    total_valid = sum(1 for r in valid_results if r["test_passed"])
    total_invalid = sum(1 for r in invalid_results if r["test_passed"])
    total_tests = len(valid_results) + len(invalid_results)
    total_passed = total_valid + total_invalid
    
    print(f"\n{'='*60}")
    print(f"📋 SAMPLE DATA VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Valid Samples Tested: {len(valid_results)}")
    print(f"Valid Samples Passed: {total_valid}")
    print(f"Invalid Samples Tested: {len(invalid_results)}")
    print(f"Invalid Samples Correctly Rejected: {total_invalid}")
    print(f"Overall Success Rate: {(total_passed/total_tests)*100:.1f}%")
    
    if total_passed == total_tests:
        print("✅ All sample data validations successful!")
    else:
        print("⚠️ Some validations failed - review results above")
    
    return total_passed == total_tests

def create_sample_patient_files():
    """Create individual JSON files for each sample patient"""
    
    # Create directory for sample files
    samples_dir = "sample_patients"
    if not os.path.exists(samples_dir):
        os.makedirs(samples_dir)
    
    # Save valid patients
    for i, patient in enumerate(VALID_PATIENTS):
        filename = os.path.join(samples_dir, f"valid_patient_{i+1}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(patient, f, indent=2, ensure_ascii=False)
        print(f"✅ Created: {filename}")
    
    # Save invalid patients
    for i, patient in enumerate(INVALID_PATIENTS):
        filename = os.path.join(samples_dir, f"invalid_patient_{i+1}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(patient, f, indent=2, ensure_ascii=False)
        print(f"✅ Created: {filename}")
    
    print(f"\n📁 Sample patient files created in '{samples_dir}' directory")

def main():
    """Main function"""
    print("🏥 Patient Data Schema Validation - Sample Data Testing")
    print("=" * 60)
    
    # Create sample files
    create_sample_patient_files()
    
    # Run validation tests
    print(f"\n{'-'*60}")
    success = validate_sample_data()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)