#!/usr/bin/env python3
"""
Schema Validation Tests for DrugBank Clinical RAG System

This module validates that JSON patient data conforms to the expected schema:
- Detects missing required fields
- Validates data types and formats
- Checks field constraints (min/max values, string lengths, patterns)
- Identifies unexpected or extra fields
- Ensures nested object structures are correct

Provides comprehensive validation for production data integrity.
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
import traceback

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("❌ jsonschema library not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema"])
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SchemaValidator:
    def __init__(self, schema_file="patient_schema.json"):
        self.schema_file = schema_file
        self.schema = self.load_schema()
        self.validator = Draft7Validator(self.schema)
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "schema_file": schema_file,
            "validation_tests": [],
            "tests_passed": 0,
            "tests_failed": 0,
            "summary": {}
        }
    
    def load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema from file"""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), self.schema_file)
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            print(f"✅ Loaded schema from {self.schema_file}")
            return schema
        except FileNotFoundError:
            print(f"❌ Schema file not found: {self.schema_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in schema file: {e}")
            sys.exit(1)
    
    def validate_patient_data(self, test_name: str, patient_data: Dict[str, Any], 
                            expect_valid: bool = True) -> Dict[str, Any]:
        """Validate patient data against schema"""
        print(f"\n📋 Testing: {test_name}")
        
        result = {
            "test_name": test_name,
            "patient_id": patient_data.get("patient_id", "Unknown"),
            "expect_valid": expect_valid,
            "is_valid": False,
            "validation_errors": [],
            "schema_violations": [],
            "field_analysis": {}
        }
        
        try:
            # Validate against schema
            validate(instance=patient_data, schema=self.schema)
            result["is_valid"] = True
            print("✅ Schema validation passed")
            
        except ValidationError as e:
            result["is_valid"] = False
            result["validation_errors"].append({
                "message": e.message,
                "path": list(e.absolute_path),
                "failed_value": str(e.instance)[:200] if hasattr(e, 'instance') else None,
                "schema_path": list(e.schema_path) if hasattr(e, 'schema_path') else []
            })
            print(f"❌ Schema validation failed: {e.message}")
            
            # Get all validation errors, not just the first one
            errors = list(self.validator.iter_errors(patient_data))
            for error in errors[1:]:  # Skip first one as it's already added
                result["validation_errors"].append({
                    "message": error.message,
                    "path": list(error.absolute_path),
                    "failed_value": str(error.instance)[:200] if hasattr(error, 'instance') else None,
                    "schema_path": list(error.schema_path) if hasattr(error, 'schema_path') else []
                })
        
        except Exception as e:
            result["validation_errors"].append({
                "message": f"Unexpected validation error: {str(e)}",
                "path": [],
                "failed_value": None,
                "schema_path": []
            })
            print(f"❌ Unexpected error: {e}")
        
        # Analyze fields
        result["field_analysis"] = self.analyze_fields(patient_data)
        
        # Check if result matches expectation
        success = (result["is_valid"] == expect_valid)
        
        if success:
            self.test_results["tests_passed"] += 1
            if expect_valid:
                print("✅ Valid data correctly validated")
            else:
                print("✅ Invalid data correctly rejected")
        else:
            self.test_results["tests_failed"] += 1
            if expect_valid:
                print("❌ Valid data incorrectly rejected")
            else:
                print("❌ Invalid data incorrectly accepted")
        
        result["test_passed"] = success
        return result
    
    def analyze_fields(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze field structure and content"""
        analysis = {
            "required_fields_present": [],
            "required_fields_missing": [],
            "optional_fields_present": [],
            "unexpected_fields": [],
            "data_type_issues": [],
            "constraint_violations": []
        }
        
        required_fields = self.schema.get("required", [])
        schema_properties = self.schema.get("properties", {})
        
        # Check required fields
        for field in required_fields:
            if field in patient_data:
                analysis["required_fields_present"].append(field)
            else:
                analysis["required_fields_missing"].append(field)
        
        # Check all fields in patient data
        for field, value in patient_data.items():
            if field in schema_properties:
                if field not in required_fields:
                    analysis["optional_fields_present"].append(field)
                
                # Check data type
                expected_type = schema_properties[field].get("type")
                if expected_type:
                    actual_type = type(value).__name__
                    if not self.check_type_compatibility(value, expected_type):
                        analysis["data_type_issues"].append({
                            "field": field,
                            "expected_type": expected_type,
                            "actual_type": actual_type,
                            "value": str(value)[:100]
                        })
            else:
                # Check if additional properties are allowed
                if not self.schema.get("additionalProperties", True):
                    analysis["unexpected_fields"].append(field)
        
        return analysis
    
    def check_type_compatibility(self, value: Any, expected_type: str) -> bool:
        """Check if value is compatible with expected JSON schema type"""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "null":
            return value is None
        return False
    
    def run_comprehensive_schema_tests(self):
        """Run comprehensive schema validation tests"""
        print("📋 Starting Schema Validation Tests...")
        print(f"Using schema: {self.schema_file}")
        print("=" * 60)
        
        # Test 1: Valid complete patient data
        valid_patient = {
            "patient_id": "SCHEMA_001",
            "name": "John Smith",
            "age": 45,
            "sex": "Male",
            "weight_kg": 75.5,
            "height_cm": 175,
            "current_medications": [
                {
                    "drug_name": "Lisinopril",
                    "dose": "10 mg",
                    "frequency": "once daily",
                    "route": "oral"
                },
                {
                    "drug_name": "Metformin",
                    "dose": "500 mg",
                    "frequency": "twice daily"
                }
            ],
            "clinical_conditions": ["Hypertension", "Type 2 Diabetes"],
            "allergies": ["Penicillin"],
            "lab_results": {
                "Creatinine": "1.0 mg/dL",
                "eGFR": "85 mL/min/1.73m2",
                "HbA1c": "6.8%"
            }
        }
        
        result = self.validate_patient_data("Valid Complete Patient", valid_patient, expect_valid=True)
        self.test_results["validation_tests"].append(result)
        
        # Test 2: Minimal valid patient (only required fields)
        minimal_patient = {
            "patient_id": "SCHEMA_002", 
            "name": "Jane Doe",
            "age": 30,
            "sex": "Female",
            "current_medications": []
        }
        
        result = self.validate_patient_data("Minimal Valid Patient", minimal_patient, expect_valid=True)
        self.test_results["validation_tests"].append(result)
        
        # Test 3: Missing required field
        missing_required = {
            "patient_id": "SCHEMA_003",
            "name": "Missing Age Patient",
            # "age": missing intentionally
            "sex": "Male",
            "current_medications": [{"drug_name": "Aspirin"}]
        }
        
        result = self.validate_patient_data("Missing Required Field", missing_required, expect_valid=False)
        self.test_results["validation_tests"].append(result)
        
        # Test 4: Wrong data types
        wrong_types = {
            "patient_id": "SCHEMA_004",
            "name": "Wrong Types Patient",
            "age": "forty-five",  # Should be integer
            "sex": "Male",
            "weight_kg": "seventy-five",  # Should be number
            "current_medications": "Aspirin, Lisinopril"  # Should be array
        }
        
        result = self.validate_patient_data("Wrong Data Types", wrong_types, expect_valid=False)
        self.test_results["validation_tests"].append(result)
        
        # Test 5: Constraint violations
        constraint_violations = {
            "patient_id": "",  # Empty string (minLength violation)
            "name": "A" * 200,  # Too long (maxLength violation)
            "age": 200,  # Too old (maximum violation)
            "sex": "InvalidSex",  # Not in enum
            "weight_kg": -5,  # Negative weight (minimum violation)
            "current_medications": [
                {
                    "drug_name": "",  # Empty drug name
                    "dose": "A" * 150  # Too long dose
                }
            ]
        }
        
        result = self.validate_patient_data("Constraint Violations", constraint_violations, expect_valid=False)
        self.test_results["validation_tests"].append(result)
        
        # Test 6: Invalid lab result formats
        invalid_labs = {
            "patient_id": "SCHEMA_006",
            "name": "Invalid Labs Patient",
            "age": 50,
            "sex": "Female",
            "current_medications": [{"drug_name": "Metformin"}],
            "lab_results": {
                "Creatinine": "invalid format",  # Should match pattern
                "eGFR": "85",  # Missing units
                "HbA1c": "6.8 invalid"  # Invalid units
            }
        }
        
        result = self.validate_patient_data("Invalid Lab Formats", invalid_labs, expect_valid=False)
        self.test_results["validation_tests"].append(result)
        
        # Test 7: Alternative field names (medications vs current_medications)
        alternative_fields = {
            "patient_id": "SCHEMA_007",
            "name": "Alternative Fields Patient",
            "age": 35,
            "sex": "Male",
            "medications": ["Aspirin", "Lisinopril"],  # Alternative to current_medications
            "conditions": ["Hypertension"],  # Alternative to clinical_conditions
            "allergic_to": ["Sulfa"],  # Alternative to allergies
            "labs": {  # Alternative to lab_results
                "Creatinine": "1.2 mg/dL"
            }
        }
        
        result = self.validate_patient_data("Alternative Field Names", alternative_fields, expect_valid=False)  # This should fail because current_medications is required
        self.test_results["validation_tests"].append(result)
        
        # Test 8: Extra unexpected fields (when additionalProperties is true)
        extra_fields = {
            "patient_id": "SCHEMA_008",
            "name": "Extra Fields Patient",
            "age": 40,
            "sex": "Female",
            "current_medications": [{"drug_name": "Aspirin"}],
            "unexpected_field": "This should be allowed",
            "another_extra": {"nested": "object"},
            "social_security": "123-45-6789"  # Extra field
        }
        
        result = self.validate_patient_data("Extra Fields Allowed", extra_fields, expect_valid=True)
        self.test_results["validation_tests"].append(result)
        
        # Test 9: Complex nested medication structure
        complex_medications = {
            "patient_id": "SCHEMA_009",
            "name": "Complex Medications Patient",
            "age": 60,
            "sex": "Male",
            "current_medications": [
                {
                    "drug_name": "Warfarin",
                    "dose": "5 mg",
                    "frequency": "once daily",
                    "route": "oral",
                    "start_date": "2023-01-15"
                },
                {
                    "drug_name": "Insulin",
                    "dose": "20 units",
                    "frequency": "twice daily",
                    "route": "SC"
                }
            ],
            "vital_signs": {
                "blood_pressure_systolic": 140,
                "blood_pressure_diastolic": 90,
                "heart_rate": 75,
                "temperature": 36.5
            }
        }
        
        result = self.validate_patient_data("Complex Nested Structure", complex_medications, expect_valid=True)
        self.test_results["validation_tests"].append(result)
        
        # Test 10: Edge case values
        edge_cases = {
            "patient_id": "SCHEMA_010",
            "name": "Edge Case Patient",
            "age": 0,  # Minimum age
            "sex": "Other",
            "weight_kg": 0.1,  # Minimum weight
            "height_cm": 1,  # Minimum height
            "current_medications": [],  # Empty array (allowed)
            "clinical_conditions": [],
            "allergies": []
        }
        
        result = self.validate_patient_data("Edge Case Values", edge_cases, expect_valid=True)
        self.test_results["validation_tests"].append(result)
        
        return self.test_results["validation_tests"]
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        total_tests = len(self.test_results["validation_tests"])
        passed_tests = self.test_results["tests_passed"]
        failed_tests = self.test_results["tests_failed"]
        
        print(f"\n{'='*60}")
        print(f"📋 SCHEMA VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Schema File: {self.schema_file}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show detailed results
        print(f"\n📊 DETAILED TEST RESULTS:")
        print("-" * 60)
        
        for test in self.test_results["validation_tests"]:
            status = "✅ PASS" if test["test_passed"] else "❌ FAIL"
            validity = "Valid" if test["expect_valid"] else "Invalid"
            actual = "Valid" if test["is_valid"] else "Invalid"
            
            print(f"{status} {test['test_name']}")
            print(f"     Expected: {validity}, Actual: {actual}")
            
            # Show field analysis
            analysis = test["field_analysis"]
            if analysis["required_fields_missing"]:
                print(f"     Missing Required: {analysis['required_fields_missing']}")
            if analysis["data_type_issues"]:
                print(f"     Type Issues: {len(analysis['data_type_issues'])}")
            if analysis["unexpected_fields"]:
                print(f"     Unexpected Fields: {analysis['unexpected_fields']}")
            
            # Show validation errors for failed cases
            if test["validation_errors"] and not test["test_passed"]:
                print(f"     Validation Errors:")
                for error in test["validation_errors"][:2]:  # Show first 2 errors
                    path_str = ".".join(map(str, error["path"])) if error["path"] else "root"
                    print(f"       - {path_str}: {error['message']}")
                if len(test["validation_errors"]) > 2:
                    print(f"       ... and {len(test['validation_errors']) - 2} more errors")
        
        # Summary statistics
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "tests_passed": passed_tests,
            "tests_failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "schema_compliance": "Excellent" if failed_tests == 0 else "Needs Review"
        }
        
        # Schema analysis
        print(f"\n🔍 SCHEMA ANALYSIS:")
        required_fields = self.schema.get("required", [])
        properties = self.schema.get("properties", {})
        print(f"Required Fields: {len(required_fields)} - {required_fields}")
        print(f"Total Properties: {len(properties)}")
        print(f"Additional Properties: {'Allowed' if self.schema.get('additionalProperties', True) else 'Forbidden'}")
        
        if failed_tests == 0:
            print(f"\n✅ ALL SCHEMA VALIDATIONS PASSED!")
            print(f"   Patient data structure is well-defined and enforced")
        else:
            print(f"\n⚠️  SCHEMA VALIDATION ISSUES DETECTED")
            print(f"   Review failed tests and consider schema refinements")
        
        # Save results
        with open("schema_validation_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Detailed results saved to 'schema_validation_results.json'")
        
        return failed_tests == 0

def main():
    """Main function to run schema validation tests"""
    
    # Check if schema file exists
    schema_file = "patient_schema.json"
    if not os.path.exists(schema_file):
        print(f"❌ Schema file not found: {schema_file}")
        print("Please ensure the schema file is in the same directory as this script.")
        return False
    
    # Run schema validation tests
    validator = SchemaValidator(schema_file)
    validator.run_comprehensive_schema_tests()
    success = validator.generate_summary_report()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)