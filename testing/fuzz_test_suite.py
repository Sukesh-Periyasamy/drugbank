#!/usr/bin/env python3
"""
Error Injection and Fuzz Testing Suite for DrugBank Clinical RAG System
Tests system robustness with corrupted, malformed, and edge case data
"""

import json
import os
import subprocess
import random
import string
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FuzzTester:
    def __init__(self):
        self.test_results = []
        self.backup_patient_file = "patient_backup_fuzz.json"
        
    def backup_original_patient(self):
        """Backup original patient.json"""
        if os.path.exists("patient.json"):
            with open("patient.json", 'r') as f:
                original = json.load(f)
            with open(self.backup_patient_file, 'w') as f:
                json.dump(original, f, indent=2)
                
    def restore_original_patient(self):
        """Restore original patient.json"""
        if os.path.exists(self.backup_patient_file):
            with open(self.backup_patient_file, 'r') as f:
                original = json.load(f)
            with open("patient.json", 'w') as f:
                json.dump(original, f, indent=2)
            os.remove(self.backup_patient_file)
            
    def generate_random_string(self, length=10):
        """Generate random string with special characters"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*()[]{}|\\:;\"'<>,.?/~`"
        return ''.join(random.choice(chars) for _ in range(length))
    
    def corrupt_json_structure(self, data: Dict) -> Dict:
        """Randomly corrupt JSON structure"""
        corrupted = data.copy()
        
        # Random field renaming
        if random.random() < 0.5:
            old_keys = list(corrupted.keys())
            for key in old_keys[:random.randint(1, len(old_keys))]:
                new_key = self.generate_random_string(random.randint(3, 15))
                corrupted[new_key] = corrupted.pop(key)
        
        # Add random noise fields
        for _ in range(random.randint(0, 5)):
            noise_key = self.generate_random_string(random.randint(5, 20))
            noise_value = random.choice([
                self.generate_random_string(random.randint(1, 50)),
                random.randint(-1000, 1000),
                random.random() * 1000,
                None,
                [],
                {},
                True,
                False
            ])
            corrupted[noise_key] = noise_value
            
        return corrupted
    
    def create_test_cases(self):
        """Create various error injection test cases"""
        
        test_cases = [
            # Test 1: Field name corruption
            {
                "name": "Field Renaming Attack",
                "patient_id": "FUZZ001_RENAME",
                "data": {
                    "patient_id": "FUZZ001_RENAME",
                    "rx_medications": [  # Renamed field
                        {"drug_name": "Aspirin", "dose": "100mg"}
                    ],
                    "medical_conditions": ["Hypertension"],  # Renamed field
                    "laboratory_results": {"creatinine": "1.5 mg/dL"}  # Renamed field
                }
            },
            
            # Test 2: Special characters injection
            {
                "name": "Special Characters Injection",
                "patient_id": "FUZZ002_CHARS",
                "data": {
                    "patient_id": "FUZZ002_CHARS",
                    "name": "Test<script>alert('xss')</script>Patient",
                    "current_medications": [
                        {
                            "drug_name": "Drug\"';DROP TABLE medications;--",
                            "dose": "∞ mg/∀∃∈∉∇∆∑∏√∫",
                            "frequency": "ﾟДﾟ)☆彡彡彡☽☺☻♠♣♥♦"
                        }
                    ],
                    "clinical_conditions": ["Disease™®©℗℠℡№"],
                    "allergies": ["🐍🚫💊⚡🔥💀☠️"]
                }
            },
            
            # Test 3: Extreme data values
            {
                "name": "Extreme Values",
                "patient_id": "FUZZ003_EXTREME",
                "data": {
                    "patient_id": "FUZZ003_EXTREME",
                    "age": 999999,
                    "weight_kg": -50.7,
                    "height_cm": 0.001,
                    "current_medications": [
                        {
                            "drug_name": "A" * 1000,  # Extremely long drug name
                            "dose": "-999999999999999999999999999999",
                            "frequency": "Every nanosecond for eternity"
                        }
                    ],
                    "lab_results": {
                        "creatinine": "∞",
                        "glucose": "-0",
                        "hemoglobin": "NaN",
                        "invalid_lab": "undefined"
                    }
                }
            },
            
            # Test 4: Data type confusion
            {
                "name": "Data Type Confusion",
                "patient_id": "FUZZ004_TYPES",
                "data": {
                    "patient_id": ["FUZZ004", "TYPES"],  # Array instead of string
                    "age": "twenty-five",  # String instead of number
                    "current_medications": "Single drug as string",  # String instead of array
                    "clinical_conditions": {  # Object instead of array
                        "primary": "Diabetes",
                        "secondary": "Hypertension"
                    },
                    "lab_results": [  # Array instead of object
                        "creatinine: 1.2",
                        "glucose: 120"
                    ]
                }
            },
            
            # Test 5: Nested corruption
            {
                "name": "Deep Nesting Corruption",
                "patient_id": "FUZZ005_NESTED",
                "data": {
                    "patient_id": "FUZZ005_NESTED",
                    "current_medications": [
                        {
                            "medication_info": {
                                "drug_details": {
                                    "substance": {
                                        "name": "Deeply nested drug",
                                        "corrupted_field": None
                                    }
                                }
                            },
                            "dosing": {
                                "amount": {
                                    "value": 50,
                                    "units": {
                                        "primary": "mg",
                                        "corrupt": {"nested": {"further": True}}
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            
            # Test 6: Empty and null values
            {
                "name": "Null/Empty Values",
                "patient_id": "FUZZ006_NULL",
                "data": {
                    "patient_id": "",
                    "name": None,
                    "current_medications": [],
                    "clinical_conditions": [None, "", "   "],
                    "lab_results": {},
                    "allergies": [None],
                    "notes": ""
                }
            },
            
            # Test 7: Unicode and encoding attacks
            {
                "name": "Unicode/Encoding Attack",
                "patient_id": "FUZZ007_UNICODE",
                "data": {
                    "patient_id": "FUZZ007_UNICODE",
                    "name": "Test患者ネーム病院🏥",
                    "current_medications": [
                        {
                            "drug_name": "薬物名称Медицина药物🧬💊",
                            "dose": "５０ｍｇ",  # Full-width characters
                            "frequency": "يوميًا مرتين"  # Arabic text
                        }
                    ],
                    "clinical_conditions": ["مرض السكري", "高血压", "Гипертония"],
                    "notes": "\\u0000\\u0001\\u0002\\u001f\\x00\\x01\\x02"  # Control characters
                }
            },
            
            # Test 8: Massive data payload
            {
                "name": "Large Payload Attack",
                "patient_id": "FUZZ008_LARGE",
                "data": {
                    "patient_id": "FUZZ008_LARGE",
                    "current_medications": [
                        {
                            "drug_name": f"Drug{i}",
                            "dose": f"{i}mg",
                            "notes": "A" * 1000  # Large text field
                        } for i in range(100)  # 100 medications
                    ],
                    "massive_field": "X" * 50000,  # 50KB field
                    "clinical_conditions": [f"Condition{i}" for i in range(500)]
                }
            }
        ]
        
        return test_cases
    
    def run_analysis(self, test_name: str, patient_data: Dict) -> Dict:
        """Run analysis with given patient data and capture results"""
        try:
            # Write test patient data
            with open("patient.json", 'w', encoding='utf-8') as f:
                json.dump(patient_data, f, indent=2, ensure_ascii=False)
            
            # Run analysis
            result = subprocess.run(
                ["python", "patient_drug_analysis.py"],
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                encoding='utf-8',
                errors='replace'
            )
            
            return {
                "test_name": test_name,
                "patient_id": patient_data.get("patient_id", "Unknown"),
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode,
                "timeout": False
            }
            
        except subprocess.TimeoutExpired:
            return {
                "test_name": test_name,
                "patient_id": patient_data.get("patient_id", "Unknown"),
                "success": False,
                "output": "",
                "error": "Process timeout (>60s)",
                "returncode": -1,
                "timeout": True
            }
        except Exception as e:
            return {
                "test_name": test_name,
                "patient_id": patient_data.get("patient_id", "Unknown"),
                "success": False,
                "output": "",
                "error": f"Test execution error: {str(e)}",
                "returncode": -2,
                "timeout": False
            }
    
    def run_fuzz_tests(self):
        """Run comprehensive fuzz testing suite"""
        print("🧪 Starting Error Injection & Fuzz Testing Suite...")
        print("=" * 60)
        
        self.backup_original_patient()
        test_cases = self.create_test_cases()
        
        # Add random corruption tests
        base_patient = {
            "patient_id": "BASE_CORRUPT",
            "current_medications": [
                {"drug_name": "TestDrug", "dose": "10mg"}
            ],
            "clinical_conditions": ["TestCondition"]
        }
        
        for i in range(5):  # 5 random corruption tests
            corrupted = self.corrupt_json_structure(base_patient.copy())
            corrupted["patient_id"] = f"FUZZ_RAND_{i+1}"
            test_cases.append({
                "name": f"Random Corruption {i+1}",
                "patient_id": f"FUZZ_RAND_{i+1}",
                "data": corrupted
            })
        
        # Run all tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"🔬 Test {i}/{len(test_cases)}: {test_case['name']}")
            
            result = self.run_analysis(test_case["name"], test_case["data"])
            self.test_results.append(result)
            
            # Print immediate result
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            if result["timeout"]:
                status += " (TIMEOUT)"
            print(f"   Status: {status}")
            
            if not result["success"] and result["error"]:
                print(f"   Error: {result['error'][:100]}...")
            
            print()
        
        self.restore_original_patient()
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save detailed test results to JSON file"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "successful": sum(1 for r in self.test_results if r["success"]),
            "failed": sum(1 for r in self.test_results if not r["success"]),
            "timeouts": sum(1 for r in self.test_results if r.get("timeout", False)),
            "success_rate": (sum(1 for r in self.test_results if r["success"]) / len(self.test_results)) * 100
        }
        
        results = {
            "summary": summary,
            "detailed_results": self.test_results
        }
        
        with open("fuzz_test_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        timeouts = sum(1 for r in self.test_results if r.get("timeout", False))
        
        print("=" * 60)
        print("🧪 FUZZ TESTING SUMMARY")
        print("=" * 60)
        print(f"Total Tests:    {total}")
        print(f"✅ Passed:      {passed}")
        print(f"❌ Failed:      {failed}")
        print(f"⏰ Timeouts:    {timeouts}")
        print(f"Success Rate:   {(passed/total)*100:.1f}%")
        print("=" * 60)
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test_name']}: {result['error'][:100]}")
        
        print(f"\n📊 Detailed results saved to: fuzz_test_results.json")
        print("\n🎯 System Robustness Assessment:")
        
        if passed == total:
            print("🟢 EXCELLENT: System handles all error conditions gracefully")
        elif (passed/total) >= 0.8:
            print("🟡 GOOD: System is robust with minor issues")
        elif (passed/total) >= 0.6:
            print("🟠 FAIR: System needs improvement in error handling")
        else:
            print("🔴 POOR: System has significant robustness issues")

if __name__ == "__main__":
    fuzzer = FuzzTester()
    fuzzer.run_fuzz_tests()