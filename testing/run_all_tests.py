#!/usr/bin/env python3
"""
Complete Test Suite Runner - DrugBank Clinical RAG System

This script runs all 9 major test suites in sequence and generates a comprehensive
final report including bias evaluation findings and actionable recommendations.

Test Suites:
1. Comprehensive Test Suite (functionality)
2. Fuzz Test Suite (robustness)  
3. Consistency Check Suite (cross-module + security)
4. Clinical Reasoning Tests (AI decision-making)
5. Threshold Validation Tests (clinical boundaries)
6. Comprehensive Reasoning Tests (master suite)
7. Schema Validation Tests (data structure)
8. Sample Patient Validation (real-world examples)
9. Bias & Fairness Evaluation (demographic equity) - NEW
"""

import json
import sys
import os
from datetime import datetime
import subprocess
import traceback
from typing import Dict, List, Any

class ComprehensiveTestRunner:
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "total_test_suites": 9,
            "suite_results": {},
            "overall_summary": {},
            "critical_findings": [],
            "recommendations": [],
            "deployment_readiness": "PENDING"
        }
        
        # Define all test suites
        self.test_suites = [
            {
                "name": "Comprehensive Test Suite",
                "script": "test_suite_comprehensive.py",
                "category": "functionality",
                "critical": True,
                "expected_success_rate": 90
            },
            {
                "name": "Fuzz Test Suite", 
                "script": "fuzz_test_suite.py",
                "category": "robustness",
                "critical": True,
                "expected_success_rate": 95
            },
            {
                "name": "Consistency Check Suite",
                "script": "consistency_check.py", 
                "category": "consistency",
                "critical": True,
                "expected_success_rate": 100
            },
            {
                "name": "Clinical Reasoning Tests",
                "script": "clinical_reasoning_tests.py",
                "category": "clinical_accuracy",
                "critical": True,
                "expected_success_rate": 100
            },
            {
                "name": "Threshold Validation Tests",
                "script": "threshold_validation.py",
                "category": "clinical_accuracy", 
                "critical": True,
                "expected_success_rate": 95
            },
            {
                "name": "Comprehensive Reasoning Tests",
                "script": "comprehensive_reasoning_tests.py",
                "category": "clinical_accuracy",
                "critical": True,
                "expected_success_rate": 95
            },
            {
                "name": "Schema Validation Tests",
                "script": "schema_validation_test.py",
                "category": "data_integrity",
                "critical": True,
                "expected_success_rate": 100
            },
            {
                "name": "Sample Patient Validation",
                "script": "sample_patient_validation.py",
                "category": "data_integrity",
                "critical": False,
                "expected_success_rate": 100
            },
            {
                "name": "Bias & Fairness Evaluation",
                "script": "bias_fairness_evaluation.py",
                "category": "ethics_fairness",
                "critical": True,
                "expected_success_rate": "bias_score_<_1.1"
            }
        ]
    
    def run_single_test_suite(self, suite: Dict) -> Dict[str, Any]:
        """Run a single test suite and capture results"""
        
        print(f"\n{'='*60}")
        print(f"🧪 Running: {suite['name']}")
        print(f"Category: {suite['category']} | Critical: {suite['critical']}")
        print(f"{'='*60}")
        
        result = {
            "suite_name": suite["name"],
            "script": suite["script"],
            "category": suite["category"],
            "critical": suite["critical"],
            "start_time": datetime.now().isoformat(),
            "success": False,
            "exit_code": None,
            "output": "",
            "error": "",
            "duration_seconds": 0,
            "findings": []
        }
        
        try:
            start_time = datetime.now()
            
            # Run the test suite
            process = subprocess.run(
                ["python", suite["script"]],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = datetime.now()
            result["duration_seconds"] = (end_time - start_time).total_seconds()
            result["exit_code"] = process.returncode
            result["output"] = process.stdout
            result["error"] = process.stderr
            result["success"] = process.returncode == 0
            
            # Extract key findings from output
            result["findings"] = self.extract_findings(suite["name"], process.stdout)
            
            if result["success"]:
                print(f"✅ {suite['name']} - PASSED")
            else:
                print(f"❌ {suite['name']} - FAILED (Exit code: {process.returncode})")
                if process.stderr:
                    print(f"   Error: {process.stderr[:200]}...")
                    
        except subprocess.TimeoutExpired:
            result["error"] = "Test suite timed out after 5 minutes"
            result["findings"].append("TIMEOUT: Test execution exceeded time limit")
            print(f"⏰ {suite['name']} - TIMEOUT")
            
        except Exception as e:
            result["error"] = str(e)
            result["findings"].append(f"EXCEPTION: {str(e)}")
            print(f"💥 {suite['name']} - EXCEPTION: {e}")
        
        result["end_time"] = datetime.now().isoformat()
        return result
    
    def extract_findings(self, suite_name: str, output: str) -> List[str]:
        """Extract key findings from test suite output"""
        
        findings = []
        
        if "Bias & Fairness" in suite_name:
            if "Overall Bias Score:" in output:
                # Extract bias score
                lines = output.split('\n')
                for line in lines:
                    if "Overall Bias Score:" in line:
                        findings.append(f"CRITICAL: {line.strip()}")
                    elif "Condition Frequency Bias Ratio:" in line:
                        findings.append(f"SEVERE: {line.strip()}")
                    elif "Age Bias Ratio:" in line:
                        findings.append(f"MODERATE: {line.strip()}")
                    elif "Meets Fairness Criteria:" in line:
                        findings.append(f"FAIRNESS: {line.strip()}")
        
        elif "Clinical Reasoning" in suite_name:
            if "Clinical Accuracy:" in output:
                lines = output.split('\n')
                for line in lines:
                    if "Clinical Accuracy:" in line:
                        findings.append(f"ACCURACY: {line.strip()}")
        
        elif "Schema Validation" in suite_name:
            if "Success Rate:" in output:
                lines = output.split('\n')
                for line in lines:
                    if "Success Rate:" in line:
                        findings.append(f"VALIDATION: {line.strip()}")
        
        elif "Fuzz Test" in suite_name:
            if "System Robustness Assessment:" in output:
                lines = output.split('\n')
                for line in lines:
                    if "EXCELLENT:" in line or "GOOD:" in line or "FAIR:" in line or "POOR:" in line:
                        findings.append(f"ROBUSTNESS: {line.strip()}")
        
        # Generic success/failure detection
        if "ALL TESTS PASSED" in output.upper():
            findings.append("STATUS: All tests passed")
        elif "TESTS FAILED" in output.upper():
            findings.append("STATUS: Some tests failed")
        
        return findings
    
    def run_all_test_suites(self):
        """Run all test suites in sequence"""
        
        print("🚀 Starting Comprehensive Test Suite Execution")
        print(f"Total Test Suites: {len(self.test_suites)}")
        print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        overall_start_time = datetime.now()
        
        # Run each test suite
        for suite in self.test_suites:
            result = self.run_single_test_suite(suite)
            self.test_results["suite_results"][suite["name"]] = result
            
            # Track critical findings
            if suite["critical"] and not result["success"]:
                self.test_results["critical_findings"].append(
                    f"CRITICAL FAILURE: {suite['name']} failed - {result.get('error', 'Unknown error')}"
                )
            
            # Extract bias-specific findings
            if "Bias & Fairness" in suite["name"]:
                for finding in result["findings"]:
                    if "CRITICAL:" in finding or "SEVERE:" in finding:
                        self.test_results["critical_findings"].append(finding)
        
        overall_end_time = datetime.now()
        total_duration = (overall_end_time - overall_start_time).total_seconds()
        
        # Generate overall summary
        self.generate_overall_summary(total_duration)
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Determine deployment readiness
        self.assess_deployment_readiness()
        
        # Print final report
        self.print_final_report()
        
        # Save detailed results
        self.save_results()
    
    def generate_overall_summary(self, total_duration_seconds: float):
        """Generate overall test execution summary"""
        
        total_suites = len(self.test_suites)
        successful_suites = sum(1 for result in self.test_results["suite_results"].values() 
                               if result["success"])
        failed_suites = total_suites - successful_suites
        
        critical_suites = sum(1 for suite in self.test_suites if suite["critical"])
        critical_passed = sum(1 for suite in self.test_suites 
                             if suite["critical"] and 
                             self.test_results["suite_results"][suite["name"]]["success"])
        
        self.test_results["overall_summary"] = {
            "total_suites": total_suites,
            "successful_suites": successful_suites,
            "failed_suites": failed_suites,
            "success_rate": (successful_suites / total_suites) * 100,
            "critical_suites": critical_suites,
            "critical_passed": critical_passed,
            "critical_success_rate": (critical_passed / critical_suites) * 100,
            "total_duration_minutes": total_duration_seconds / 60,
            "execution_timestamp": datetime.now().isoformat()
        }
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on test results"""
        
        recommendations = []
        
        # Check bias evaluation results
        bias_result = self.test_results["suite_results"].get("Bias & Fairness Evaluation")
        if bias_result:
            if not bias_result["success"] or any("CRITICAL:" in finding for finding in bias_result["findings"]):
                recommendations.append({
                    "priority": "CRITICAL",
                    "category": "Bias Mitigation",
                    "action": "Implement immediate bias mitigation for condition frequency discrimination",
                    "timeline": "1 week",
                    "impact": "Prevents unethical treatment disparities"
                })
                
                recommendations.append({
                    "priority": "HIGH", 
                    "category": "Age Bias",
                    "action": "Normalize age-based section selection algorithm",
                    "timeline": "2 weeks",
                    "impact": "Reduces over-analysis of elderly patients"
                })
        
        # Check clinical accuracy
        clinical_suites = ["Clinical Reasoning Tests", "Threshold Validation Tests", "Comprehensive Reasoning Tests"]
        clinical_issues = []
        for suite_name in clinical_suites:
            result = self.test_results["suite_results"].get(suite_name)
            if result and not result["success"]:
                clinical_issues.append(suite_name)
        
        if clinical_issues:
            recommendations.append({
                "priority": "HIGH",
                "category": "Clinical Accuracy",
                "action": f"Review and fix clinical reasoning issues in: {', '.join(clinical_issues)}",
                "timeline": "1 week",
                "impact": "Ensures safe clinical decision support"
            })
        
        # Check robustness
        fuzz_result = self.test_results["suite_results"].get("Fuzz Test Suite")
        if fuzz_result and not fuzz_result["success"]:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "System Robustness",
                "action": "Strengthen error handling for malformed inputs",
                "timeline": "2 weeks", 
                "impact": "Improves system stability"
            })
        
        # General recommendations
        if self.test_results["overall_summary"]["critical_success_rate"] < 100:
            recommendations.append({
                "priority": "HIGH",
                "category": "Critical Test Failures",
                "action": "Address all critical test suite failures before deployment",
                "timeline": "Immediate",
                "impact": "Essential for production readiness"
            })
        
        self.test_results["recommendations"] = recommendations
    
    def assess_deployment_readiness(self):
        """Assess overall deployment readiness based on test results"""
        
        critical_success_rate = self.test_results["overall_summary"]["critical_success_rate"]
        has_critical_findings = len(self.test_results["critical_findings"]) > 0
        
        # Check for bias issues specifically
        bias_result = self.test_results["suite_results"].get("Bias & Fairness Evaluation")
        has_bias_issues = False
        if bias_result:
            has_bias_issues = any("CRITICAL:" in finding or "SEVERE:" in finding 
                                 for finding in bias_result["findings"])
        
        if has_bias_issues:
            self.test_results["deployment_readiness"] = "BLOCKED - BIAS MITIGATION REQUIRED"
        elif critical_success_rate < 100:
            self.test_results["deployment_readiness"] = "BLOCKED - CRITICAL TEST FAILURES"
        elif has_critical_findings:
            self.test_results["deployment_readiness"] = "CONDITIONAL - ADDRESS CRITICAL FINDINGS"
        else:
            self.test_results["deployment_readiness"] = "READY"
    
    def print_final_report(self):
        """Print comprehensive final report"""
        
        print(f"\n{'='*80}")
        print(f"🎯 COMPREHENSIVE TEST EXECUTION REPORT")
        print(f"{'='*80}")
        
        summary = self.test_results["overall_summary"]
        
        print(f"Execution Summary:")
        print(f"  Total Test Suites: {summary['total_suites']}")
        print(f"  Successful: {summary['successful_suites']}")
        print(f"  Failed: {summary['failed_suites']}")
        print(f"  Overall Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Critical Success Rate: {summary['critical_success_rate']:.1f}%")
        print(f"  Total Duration: {summary['total_duration_minutes']:.1f} minutes")
        
        print(f"\n📊 Test Suite Results:")
        print("-" * 60)
        
        for suite_name, result in self.test_results["suite_results"].items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            critical = "🔴 CRITICAL" if result["critical"] else "🟡 OPTIONAL"
            duration = f"{result['duration_seconds']:.1f}s"
            
            print(f"{status} {suite_name} ({critical}) - {duration}")
            
            # Show key findings
            if result["findings"]:
                for finding in result["findings"][:2]:  # Show first 2 findings
                    print(f"     {finding}")
        
        print(f"\n🚨 Critical Findings:")
        if self.test_results["critical_findings"]:
            for finding in self.test_results["critical_findings"]:
                print(f"   • {finding}")
        else:
            print("   None - All critical tests passed")
        
        print(f"\n💡 Recommendations:")
        if self.test_results["recommendations"]:
            for rec in self.test_results["recommendations"]:
                priority_icon = "🚨" if rec["priority"] == "CRITICAL" else "⚠️" if rec["priority"] == "HIGH" else "💡"
                print(f"   {priority_icon} {rec['priority']}: {rec['action']}")
                print(f"      Timeline: {rec['timeline']} | Impact: {rec['impact']}")
        else:
            print("   No specific recommendations - system performing well")
        
        print(f"\n🎯 Deployment Readiness:")
        readiness = self.test_results["deployment_readiness"]
        
        if "READY" in readiness:
            print(f"   ✅ {readiness}")
            print("   System is ready for production deployment")
        elif "CONDITIONAL" in readiness:
            print(f"   ⚠️ {readiness}")
            print("   Address identified issues before deployment")
        else:
            print(f"   🚨 {readiness}")
            print("   Critical issues must be resolved before deployment")
    
    def save_results(self):
        """Save detailed test results to files"""
        
        # Save comprehensive results
        with open("comprehensive_test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        # Save executive summary
        executive_summary = {
            "timestamp": self.test_results["timestamp"],
            "deployment_readiness": self.test_results["deployment_readiness"],
            "overall_summary": self.test_results["overall_summary"],
            "critical_findings": self.test_results["critical_findings"],
            "top_recommendations": self.test_results["recommendations"][:3]
        }
        
        with open("executive_test_summary.json", "w", encoding="utf-8") as f:
            json.dump(executive_summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Detailed results saved to:")
        print(f"   • comprehensive_test_results.json")
        print(f"   • executive_test_summary.json")

def main():
    """Main function to run comprehensive test suite"""
    
    print("🚀 DrugBank Clinical RAG System - Comprehensive Test Suite Runner")
    print("=" * 80)
    print("Executing all 9 major test suites including bias evaluation")
    print()
    
    # Run comprehensive test evaluation
    runner = ComprehensiveTestRunner()
    runner.run_all_test_suites()
    
    # Return exit code based on deployment readiness
    if "READY" in runner.test_results["deployment_readiness"]:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())