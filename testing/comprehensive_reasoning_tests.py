#!/usr/bin/env python3
"""
Comprehensive AI Reasoning Consistency Test Suite

This is the main entry point for testing clinical decision-making consistency
across threshold boundaries. It combines threshold validation, reasoning consistency,
and behavioral validation to ensure the clinical RAG system makes appropriate
decisions when patient parameters change slightly.

Test Categories:
1. Clinical Threshold Validation - Tests specific medical thresholds
2. AI Reasoning Consistency - Tests decision-making patterns  
3. Cross-Parameter Interactions - Tests combined parameter effects
4. Edge Case Validation - Tests boundary conditions
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from clinical_reasoning_tests import ClinicalReasoningTester
from threshold_validation import ThresholdValidator

class ComprehensiveReasoningTestSuite:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_suite_version": "1.0",
            "comprehensive_results": {
                "clinical_reasoning": {},
                "threshold_validation": {},
                "overall_summary": {}
            }
        }
    
    def run_all_reasoning_tests(self):
        """Run all clinical reasoning and threshold tests"""
        
        print("🧠 COMPREHENSIVE AI REASONING CONSISTENCY TEST SUITE")
        print("=" * 80)
        print("Testing clinical decision-making across threshold boundaries")
        print("Validating AI reasoning consistency for clinical parameters\n")
        
        # Run clinical reasoning tests
        print("🔬 Phase 1: Clinical Reasoning Consistency Tests")
        print("-" * 50)
        reasoning_tester = ClinicalReasoningTester()
        reasoning_success = reasoning_tester.run_threshold_tests()
        self.results["comprehensive_results"]["clinical_reasoning"] = reasoning_tester.test_results
        
        print("\n" + "🎯" + " " * 49)
        print("🎯 Phase 2: Clinical Threshold Validation Tests")
        print("-" * 50)
        threshold_validator = ThresholdValidator()
        threshold_success = threshold_validator.run_all_validations()
        self.results["comprehensive_results"]["threshold_validation"] = threshold_validator.results
        
        # Calculate overall summary
        total_tests = (
            self.results["comprehensive_results"]["clinical_reasoning"]["summary"]["total_threshold_tests"] +
            self.results["comprehensive_results"]["threshold_validation"]["validation_summary"]["tests_passed"] +
            self.results["comprehensive_results"]["threshold_validation"]["validation_summary"]["tests_failed"]
        )
        
        total_passed = (
            self.results["comprehensive_results"]["clinical_reasoning"]["summary"]["consistent_behaviors"] +
            self.results["comprehensive_results"]["threshold_validation"]["validation_summary"]["tests_passed"]
        )
        
        total_failed = (
            self.results["comprehensive_results"]["clinical_reasoning"]["summary"]["inconsistent_behaviors"] +
            self.results["comprehensive_results"]["threshold_validation"]["validation_summary"]["tests_failed"]
        )
        
        overall_accuracy = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        self.results["comprehensive_results"]["overall_summary"] = {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_accuracy": overall_accuracy,
            "clinical_reasoning_accuracy": self.results["comprehensive_results"]["clinical_reasoning"]["summary"]["clinical_accuracy"],
            "threshold_validation_accuracy": self.results["comprehensive_results"]["threshold_validation"]["validation_summary"]["threshold_accuracy"],
            "all_tests_passed": reasoning_success and threshold_success
        }
        
        # Print comprehensive summary
        self.print_comprehensive_summary()
        
        # Save results
        with open("comprehensive_reasoning_test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Comprehensive results saved to 'comprehensive_reasoning_test_results.json'")
        
        return self.results["comprehensive_results"]["overall_summary"]["all_tests_passed"]
    
    def print_comprehensive_summary(self):
        """Print a comprehensive summary of all test results"""
        
        summary = self.results["comprehensive_results"]["overall_summary"]
        
        print("\n" + "=" * 80)
        print("🧠 COMPREHENSIVE AI REASONING TEST SUMMARY")
        print("=" * 80)
        
        print(f"Total Tests Executed: {summary['total_tests']}")
        print(f"Total Passed: {summary['total_passed']}")
        print(f"Total Failed: {summary['total_failed']}")
        print(f"Overall Accuracy: {summary['overall_accuracy']:.1f}%")
        
        print(f"\n📊 DETAILED BREAKDOWN:")
        print(f"  Clinical Reasoning Tests: {summary['clinical_reasoning_accuracy']:.1f}% accuracy")
        print(f"  Threshold Validation Tests: {summary['threshold_validation_accuracy']:.1f}% accuracy")
        
        if summary["all_tests_passed"]:
            print(f"\n✅ ALL CLINICAL REASONING TESTS PASSED!")
            print(f"   The AI system demonstrates consistent clinical decision-making")
            print(f"   across threshold boundaries and parameter variations.")
        else:
            print(f"\n❌ Some tests failed - review individual test results for details")
            
            # Show specific issues
            reasoning_issues = self.results["comprehensive_results"]["clinical_reasoning"]["consistency_issues"]
            if reasoning_issues:
                print(f"\n⚠️  Clinical Reasoning Issues:")
                for issue in reasoning_issues:
                    print(f"   - {issue}")
            
            # Show threshold validation failures
            threshold_validations = self.results["comprehensive_results"]["threshold_validation"]["threshold_validations"]
            failed_validations = [v for v in threshold_validations if not v["passed"]]
            if failed_validations:
                print(f"\n⚠️  Threshold Validation Issues:")
                for validation in failed_validations:
                    print(f"   - {validation['test_name']}: {validation['validation']['issues']}")
        
        print(f"\n🎯 CLINICAL THRESHOLD BEHAVIOR ANALYSIS:")
        print(f"   Age Threshold (65): {'✅ Working correctly' if self.check_age_threshold() else '❌ Issues detected'}")
        print(f"   eGFR Threshold (60): {'✅ Working correctly' if self.check_egfr_threshold() else '❌ Issues detected'}")
        print(f"   Combined Risk Factors: {'✅ Working correctly' if self.check_combined_thresholds() else '❌ Issues detected'}")
        
        # Clinical recommendations
        print(f"\n🏥 CLINICAL DECISION-MAKING ASSESSMENT:")
        if summary["overall_accuracy"] >= 95:
            print(f"   ✅ EXCELLENT: System ready for clinical support applications")
        elif summary["overall_accuracy"] >= 85:
            print(f"   ⚠️  GOOD: System suitable with monitoring")
        elif summary["overall_accuracy"] >= 70:
            print(f"   ⚠️  FAIR: System needs improvement before clinical use")
        else:
            print(f"   ❌ POOR: System requires significant refinement")
    
    def check_age_threshold(self) -> bool:
        """Check if age threshold (65) is working correctly"""
        reasoning_tests = self.results["comprehensive_results"]["clinical_reasoning"]["threshold_tests"]
        age_tests = [t for t in reasoning_tests if "Age" in t["test_name"]]
        return all(t["clinical_appropriateness"] for t in age_tests)
    
    def check_egfr_threshold(self) -> bool:
        """Check if eGFR threshold (60) is working correctly"""
        reasoning_tests = self.results["comprehensive_results"]["clinical_reasoning"]["threshold_tests"]
        egfr_tests = [t for t in reasoning_tests if "eGFR" in t["test_name"]]
        return all(t["clinical_appropriateness"] for t in egfr_tests)
    
    def check_combined_thresholds(self) -> bool:
        """Check if combined threshold interactions are working"""
        reasoning_tests = self.results["comprehensive_results"]["clinical_reasoning"]["threshold_tests"]
        combined_tests = [t for t in reasoning_tests if "Combined" in t["test_name"]]
        return all(t["clinical_appropriateness"] for t in combined_tests)

def main():
    """Main function to run comprehensive reasoning tests"""
    
    # Run comprehensive test suite
    test_suite = ComprehensiveReasoningTestSuite()
    success = test_suite.run_all_reasoning_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()