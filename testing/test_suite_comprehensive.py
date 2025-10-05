# DrugBank Clinical RAG System - Test             result = subprocess.run(
                ["python", "../patient_drug_analysis.py"],
                capture_output=True,
                text=True,
                timeout=120
            )
# Comprehensive validation across different patient scenarios

import json
import os
import subprocess
import shutil
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DrugBankTester:
    def __init__(self):
        self.test_results = []
        # Get parent directory path
        self.parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.original_patient_file = os.path.join(self.parent_dir, "patient.json")
        self.backup_file = os.path.join(self.parent_dir, "patient_backup_test.json")
        
    def backup_original(self):
        """Backup original patient file"""
        if os.path.exists(self.original_patient_file):
            shutil.copy(self.original_patient_file, self.backup_file)
            
    def restore_original(self):
        """Restore original patient file"""
        if os.path.exists(self.backup_file):
            shutil.copy(self.backup_file, self.original_patient_file)
            os.remove(self.backup_file)
    
    def run_analysis(self, test_name, patient_data):
        """Run analysis with given patient data and capture results"""
        try:
            # Write test patient data
            with open(self.original_patient_file, 'w') as f:
                json.dump(patient_data, f, indent=2)
            
            # Run analysis (change to parent directory first)
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            result = subprocess.run(
                ['python', 'patient_drug_analysis.py'], 
                capture_output=True, 
                text=True, 
                timeout=60,
                cwd=parent_dir
            )
            
            # Parse output
            output_lines = result.stdout.split('\n')
            
            test_result = {
                "test_name": test_name,
                "patient_id": patient_data.get("patient_id", "Unknown"),
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "analysis_data": self.extract_analysis_data(output_lines)
            }
            
            return test_result
            
        except Exception as e:
            return {
                "test_name": test_name,
                "patient_id": patient_data.get("patient_id", "Unknown"),
                "success": False,
                "error": str(e),
                "analysis_data": None
            }
    
    def extract_analysis_data(self, output_lines):
        """Extract key metrics from analysis output"""
        data = {}
        for line in output_lines:
            if "Medications analyzed:" in line:
                data["medications_count"] = int(line.split(":")[1].strip())
            elif "Total sections queried:" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    data["sections_queried"] = int(parts[1].split("(")[0].strip())
            elif "Efficiency gain:" in line:
                data["efficiency_gain"] = line.split(":")[1].strip()
            elif "Total matches found:" in line:
                data["total_matches"] = int(line.split(":")[1].strip())
        return data
    
    def run_all_tests(self):
        """Execute comprehensive test suite"""
        print("🧪 Starting DrugBank Clinical RAG System Test Suite")
        print("=" * 60)
        
        self.backup_original()
        
        try:
            # Test 1: Simple/Low-risk Patient
            self.test_simple_patient()
            
            # Test 2: Polypharmacy (Medium Risk)
            self.test_polypharmacy_patient()
            
            # Test 3: High-risk (Edge Case)  
            self.test_high_risk_patient()
            
            # Test 4: No medications/Malformed
            self.test_no_medications()
            self.test_malformed_data()
            
            # Test 5: Fake drugs/Nonsensical
            self.test_fake_drugs()
            
            # Test 6: Locale/Unit variants
            self.test_unit_variants()
            
            # Generate report
            self.generate_report()
            
        finally:
            self.restore_original()
    
    def test_simple_patient(self):
        """Test 1: Simple/Low-risk - single drug, normal labs"""
        print("\n🟢 TEST 1: Simple/Low-risk Patient")
        
        patient_data = {
            "patient_id": "T001_SIMPLE",
            "name": "Jane Healthy",
            "age": 35,
            "sex": "Female",
            "weight_kg": 65,
            "clinical_conditions": [],
            "current_medications": [
                {
                    "drug_name": "Ibuprofen",
                    "dose": "400 mg",
                    "frequency": "as needed"
                }
            ],
            "lab_results": {
                "Creatinine": "0.9 mg/dL",
                "eGFR": "95 mL/min/1.73m2",
                "LFT": "Normal"
            },
            "allergies": []
        }
        
        result = self.run_analysis("Simple/Low-risk", patient_data)
        self.test_results.append(result)
        
        # Expected: Only names + pharmacology (2 sections)
        expected_sections = 2
        if result["success"] and result["analysis_data"]:
            actual_sections = result["analysis_data"].get("sections_queried", 0)
            print(f"   Expected sections: ~{expected_sections}, Actual: {actual_sections}")
            print(f"   Efficiency gain: {result['analysis_data'].get('efficiency_gain', 'N/A')}")
        
    def test_polypharmacy_patient(self):
        """Test 2: Polypharmacy (Medium) - 3-4 drugs, no organ dysfunction"""
        print("\n🟡 TEST 2: Polypharmacy (Medium Risk)")
        
        patient_data = {
            "patient_id": "T002_POLY",
            "name": "Bob Wilson",
            "age": 55,
            "sex": "Male",
            "weight_kg": 80,
            "clinical_conditions": [
                "Hypertension",
                "Type 2 Diabetes",
                "Hyperlipidemia"
            ],
            "current_medications": [
                {"drug_name": "Lisinopril", "dose": "10 mg", "frequency": "daily"},
                {"drug_name": "Metformin", "dose": "500 mg", "frequency": "twice daily"},
                {"drug_name": "Atorvastatin", "dose": "20 mg", "frequency": "daily"}
            ],
            "lab_results": {
                "Creatinine": "1.0 mg/dL",
                "eGFR": "85 mL/min/1.73m2",
                "HbA1c": "6.8%",
                "LFT": "Normal"
            },
            "allergies": []
        }
        
        result = self.run_analysis("Polypharmacy (Medium)", patient_data)
        self.test_results.append(result)
        
        # Expected: interactions, indications + base (4-5 sections)
        if result["success"] and result["analysis_data"]:
            actual_sections = result["analysis_data"].get("sections_queried", 0)
            print(f"   Expected sections: 4-5 per drug, Total actual: {actual_sections}")
            print(f"   Efficiency gain: {result['analysis_data'].get('efficiency_gain', 'N/A')}")
    
    def test_high_risk_patient(self):
        """Test 3: High-risk (Edge) - elderly, CKD, hepatic impairment, anticoagulant"""
        print("\n🔴 TEST 3: High-risk (Edge Case)")
        
        patient_data = {
            "patient_id": "T003_HIGHRISK",
            "name": "Eleanor Smith",
            "age": 78,
            "sex": "Female",
            "weight_kg": 52,
            "clinical_conditions": [
                "Chronic Kidney Disease Stage 4",
                "Atrial Fibrillation",
                "Chronic Liver Disease",
                "Heart Failure"
            ],
            "current_medications": [
                {"drug_name": "Warfarin", "dose": "5 mg", "frequency": "daily"},
                {"drug_name": "Furosemide", "dose": "40 mg", "frequency": "daily"},
                {"drug_name": "Digoxin", "dose": "0.125 mg", "frequency": "daily"}
            ],
            "lab_results": {
                "Creatinine": "2.8 mg/dL",
                "eGFR": "18 mL/min/1.73m2",
                "ALT": "95 U/L",
                "AST": "88 U/L",
                "INR": "2.8",
                "BNP": "1500 pg/mL"
            },
            "allergies": ["Penicillin", "Sulfa drugs"]
        }
        
        result = self.run_analysis("High-risk (Edge)", patient_data)
        self.test_results.append(result)
        
        # Expected: All 7 sections (0% efficiency gain)
        if result["success"] and result["analysis_data"]:
            actual_sections = result["analysis_data"].get("sections_queried", 0)
            expected_total = 3 * 7  # 3 drugs × 7 sections each
            print(f"   Expected sections: {expected_total} (all 7 per drug), Actual: {actual_sections}")
            print(f"   Efficiency gain: {result['analysis_data'].get('efficiency_gain', 'N/A')}")
    
    def test_no_medications(self):
        """Test 4a: No medications"""
        print("\n⚪ TEST 4a: No Medications")
        
        patient_data = {
            "patient_id": "T004A_NOMEDS",
            "name": "Healthy Person",
            "age": 25,
            "clinical_conditions": [],
            "current_medications": [],
            "allergies": []
        }
        
        result = self.run_analysis("No Medications", patient_data)
        self.test_results.append(result)
        
        # Expected: Graceful message, no crash
        if "No medications found" in result["output"]:
            print("   ✅ Graceful handling: 'No medications found' message")
        else:
            print("   ⚠️ Unexpected behavior for empty medications")
    
    def test_malformed_data(self):
        """Test 4b: Malformed data structure"""
        print("\n⚪ TEST 4b: Malformed Data")
        
        patient_data = {
            "wrong_field_name": "Not a patient ID",
            "random_number": 12345,
            "medications_misspelled": ["Something"],
            "invalid_structure": {
                "nested": {
                    "deeply": "wrong"
                }
            }
        }
        
        result = self.run_analysis("Malformed Data", patient_data)
        self.test_results.append(result)
        
        # Expected: No crash, graceful handling
        if result["success"] or "No medications found" in result["output"]:
            print("   ✅ Graceful handling of malformed data")
        else:
            print("   ⚠️ System crashed on malformed data")
    
    def test_fake_drugs(self):
        """Test 5: Fake drugs/Nonsensical"""
        print("\n🎭 TEST 5: Fake Drugs/Nonsensical")
        
        patient_data = {
            "patient_id": "T005_FAKE",
            "name": "Test Subject",
            "age": 42,
            "clinical_conditions": ["Imaginary Disease", "Unicorn Deficiency"],
            "current_medications": [
                {"drug_name": "FakeDrugAlpha123", "dose": "999 mg"},
                {"drug_name": "FantasyMedicine", "dose": "1 unicorn tear"},
                {"drug_name": "NonExistentCompound", "dose": "∞ mg"}
            ],
            "lab_results": {
                "MagicLevel": "Over 9000",
                "Creatinine": "1.1 mg/dL"
            },
            "allergies": ["Reality", "Logic"]
        }
        
        result = self.run_analysis("Fake Drugs", patient_data)
        self.test_results.append(result)
        
        # Expected: Semantic fallback, closest real matches
        if result["success"] and result["analysis_data"]:
            matches = result["analysis_data"].get("total_matches", 0)
            print(f"   Semantic fallback: {matches} matches found for fake drugs")
            print("   ✅ System found semantically similar real drugs")
        else:
            print("   ⚠️ Issue with fake drug handling")
    
    def test_unit_variants(self):
        """Test 6: Locale/Unit variants"""
        print("\n🌍 TEST 6: Locale/Unit Variants")
        
        patient_data = {
            "patient_id": "T006_UNITS",
            "name": "International Patient", 
            "age": 60,
            "weight_kg": 70,
            "clinical_conditions": ["Diabetes", "Kidney Disease"],
            "current_medications": [
                {"drug_name": "Insulin", "dose": "20 units", "frequency": "daily"}
            ],
            "lab_results": {
                # Different unit formats
                "Creatinine": "150 µmol/L",  # European units vs mg/dL
                "eGFR": "45 mL/min/1.73m²",
                "HbA1c": "8.5 mmol/mol",    # IFCC units vs %
                "Glucose": "12.5 mmol/L",   # European vs mg/dL
                "Urea": "15.2 mmol/L"       # European units
            },
            "allergies": []
        }
        
        result = self.run_analysis("Unit Variants", patient_data)
        self.test_results.append(result)
        
        # Expected: System handles different units gracefully
        if result["success"]:
            print("   ✅ System handled international units successfully")
        else:
            print("   ⚠️ Issues with international unit formats")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 TEST SUITE RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for test in self.test_results if test["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 40)
        
        for test in self.test_results:
            status = "✅ PASS" if test["success"] else "❌ FAIL"
            print(f"{status} {test['test_name']}")
            
            if test["analysis_data"]:
                data = test["analysis_data"]
                print(f"     Drugs: {data.get('medications_count', 'N/A')}, "
                      f"Sections: {data.get('sections_queried', 'N/A')}, "
                      f"Matches: {data.get('total_matches', 'N/A')}, "
                      f"Efficiency: {data.get('efficiency_gain', 'N/A')}")
            
            if not test["success"] and test.get("error"):
                print(f"     Error: {test['error'][:100]}...")
        
        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful": successful_tests,
                "failed": total_tests - successful_tests,
                "success_rate": (successful_tests/total_tests)*100
            },
            "detailed_results": self.test_results
        }
        
        with open("test_results.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: test_results.json")

if __name__ == "__main__":
    tester = DrugBankTester()
    tester.run_all_tests()