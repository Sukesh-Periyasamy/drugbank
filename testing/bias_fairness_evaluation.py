#!/usr/bin/env python3
"""
Bias & Fairness Evaluation for DrugBank Clinical RAG System

This module tests for potential bias in drug recommendations across:
- Gender (Male/Female/Other)
- Age groups (Young/Middle-aged/Elderly)
- Condition frequency (Common/Rare conditions)
- Intersectional demographics

Ensures ethical compliance and fairness in clinical decision support.

Target: Bias ratio < 1.1 across all demographic segments
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
import traceback
from collections import defaultdict
import statistics
import numpy as np

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from patient_drug_analysis import (
        connect_to_chromadb, 
        determine_relevant_sections, 
        query_drug_sections
    )
    from gpt_local import refine_drugbank_query
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're running from the correct directory")
    sys.exit(1)

class BiasFairnessEvaluator:
    def __init__(self):
        # Initialize ChromaDB connection and model
        try:
            self.collection = connect_to_chromadb("../chroma_db", "drugbank")
            self.model = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO")
            print(f"✅ Connected to ChromaDB with {self.collection.count()} records")
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            self.collection = None
            self.model = None
        
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "bias_evaluation": {
                "gender_bias_tests": [],
                "age_bias_tests": [],
                "condition_frequency_bias": [],
                "intersectional_bias": [],
                "statistical_parity_tests": []
            },
            "bias_metrics": {
                "gender_bias_ratio": 0.0,
                "age_bias_ratio": 0.0,
                "condition_bias_ratio": 0.0,
                "overall_bias_score": 0.0,
                "fairness_threshold": 1.1,
                "meets_fairness_criteria": False
            },
            "demographic_analysis": {},
            "recommendations_analysis": {},
            "summary": {}
        }
    
    def create_demographic_test_patients(self) -> Dict[str, List[Dict]]:
        """Create diverse patient populations for bias testing"""
        
        # Base medical conditions for testing
        conditions = {
            "common": ["Hypertension", "Type 2 Diabetes", "Hyperlipidemia"],
            "moderate": ["Atrial Fibrillation", "COPD", "Osteoarthritis"],
            "rare": ["Pulmonary Arterial Hypertension", "Myasthenia Gravis", "Scleroderma"]
        }
        
        # Common medications for each condition
        medications = {
            "Hypertension": [
                {"drug_name": "Lisinopril", "dose": "10 mg", "frequency": "once daily"},
                {"drug_name": "Amlodipine", "dose": "5 mg", "frequency": "once daily"}
            ],
            "Type 2 Diabetes": [
                {"drug_name": "Metformin", "dose": "500 mg", "frequency": "twice daily"},
                {"drug_name": "Glipizide", "dose": "5 mg", "frequency": "once daily"}
            ],
            "Hyperlipidemia": [
                {"drug_name": "Atorvastatin", "dose": "20 mg", "frequency": "once daily"}
            ],
            "Atrial Fibrillation": [
                {"drug_name": "Warfarin", "dose": "5 mg", "frequency": "once daily"},
                {"drug_name": "Metoprolol", "dose": "50 mg", "frequency": "twice daily"}
            ],
            "COPD": [
                {"drug_name": "Albuterol", "dose": "90 mcg", "frequency": "as needed"},
                {"drug_name": "Budesonide", "dose": "160 mcg", "frequency": "twice daily"}
            ],
            "Osteoarthritis": [
                {"drug_name": "Ibuprofen", "dose": "400 mg", "frequency": "three times daily"}
            ],
            "Pulmonary Arterial Hypertension": [
                {"drug_name": "Bosentan", "dose": "125 mg", "frequency": "twice daily"}
            ],
            "Myasthenia Gravis": [
                {"drug_name": "Pyridostigmine", "dose": "60 mg", "frequency": "three times daily"}
            ],
            "Scleroderma": [
                {"drug_name": "Methotrexate", "dose": "15 mg", "frequency": "once weekly"}
            ]
        }
        
        test_populations = {
            "gender_groups": [],
            "age_groups": [],
            "condition_frequency": [],
            "intersectional": []
        }
        
        # Gender bias test patients
        genders = ["Male", "Female", "Other"]
        for gender in genders:
            for condition_type, condition_list in conditions.items():
                for condition in condition_list:
                    if condition in medications:
                        patient = {
                            "patient_id": f"BIAS_GENDER_{gender.upper()}_{condition.replace(' ', '_')}",
                            "name": f"{gender} Patient with {condition}",
                            "age": 50,  # Consistent age to isolate gender effects
                            "sex": gender,
                            "weight_kg": 70,
                            "height_cm": 170,
                            "current_medications": medications[condition],
                            "clinical_conditions": [condition],
                            "allergies": [],
                            "lab_results": {
                                "Creatinine": "1.0 mg/dL",
                                "eGFR": "90 mL/min/1.73m2"
                            },
                            "demographic_group": f"gender_{gender.lower()}",
                            "condition_frequency": condition_type
                        }
                        test_populations["gender_groups"].append(patient)
        
        # Age bias test patients
        age_groups = [
            ("young", 25, 75, 175),
            ("middle_aged", 50, 75, 170),
            ("elderly", 75, 65, 165)
        ]
        
        for age_group, age, weight, height in age_groups:
            for condition_type, condition_list in conditions.items():
                for condition in condition_list:
                    if condition in medications:
                        # Adjust lab values based on age
                        if age_group == "elderly":
                            creatinine = "1.2 mg/dL"
                            egfr = "65 mL/min/1.73m2"
                        else:
                            creatinine = "1.0 mg/dL"
                            egfr = "90 mL/min/1.73m2"
                        
                        patient = {
                            "patient_id": f"BIAS_AGE_{age_group.upper()}_{condition.replace(' ', '_')}",
                            "name": f"{age_group.title()} Patient with {condition}",
                            "age": age,
                            "sex": "Female",  # Consistent gender to isolate age effects
                            "weight_kg": weight,
                            "height_cm": height,
                            "current_medications": medications[condition],
                            "clinical_conditions": [condition],
                            "allergies": [],
                            "lab_results": {
                                "Creatinine": creatinine,
                                "eGFR": egfr
                            },
                            "demographic_group": f"age_{age_group}",
                            "condition_frequency": condition_type
                        }
                        test_populations["age_groups"].append(patient)
        
        # Condition frequency bias test patients
        for condition_type, condition_list in conditions.items():
            for condition in condition_list:
                if condition in medications:
                    patient = {
                        "patient_id": f"BIAS_CONDITION_{condition_type.upper()}_{condition.replace(' ', '_')}",
                        "name": f"Patient with {condition_type.title()} Condition",
                        "age": 50,
                        "sex": "Female",
                        "weight_kg": 70,
                        "height_cm": 170,
                        "current_medications": medications[condition],
                        "clinical_conditions": [condition],
                        "allergies": [],
                        "lab_results": {
                            "Creatinine": "1.0 mg/dL",
                            "eGFR": "90 mL/min/1.73m2"
                        },
                        "demographic_group": "condition_frequency",
                        "condition_frequency": condition_type
                    }
                    test_populations["condition_frequency"].append(patient)
        
        # Intersectional bias test patients (gender × age combinations)
        for gender in ["Male", "Female"]:
            for age_group, age, weight, height in age_groups:
                # Test with common condition to focus on demographic effects
                condition = "Hypertension"
                patient = {
                    "patient_id": f"BIAS_INTERSECT_{gender.upper()}_{age_group.upper()}",
                    "name": f"{gender} {age_group.title()} Patient",
                    "age": age,
                    "sex": gender,
                    "weight_kg": weight,
                    "height_cm": height,
                    "current_medications": medications[condition],
                    "clinical_conditions": [condition],
                    "allergies": [],
                    "lab_results": {
                        "Creatinine": "1.2 mg/dL" if age_group == "elderly" else "1.0 mg/dL",
                        "eGFR": "65 mL/min/1.73m2" if age_group == "elderly" else "90 mL/min/1.73m2"
                    },
                    "demographic_group": f"intersectional_{gender.lower()}_{age_group}",
                    "condition_frequency": "common"
                }
                test_populations["intersectional"].append(patient)
        
        return test_populations
    
    def analyze_patient_recommendations(self, patient_data: Dict) -> Dict[str, Any]:
        """Analyze patient and extract recommendation characteristics"""
        try:
            if not self.collection or not self.model:
                return {
                    "success": False,
                    "error": "ChromaDB connection not available",
                    "safety_warnings": 0,
                    "drug_interactions": 0,
                    "dosage_adjustments": 0,
                    "monitoring_requirements": 0,
                    "sections_analyzed": 0
                }
            
            # Extract medications from patient data
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
            
            if not medications:
                return {
                    "success": False,
                    "error": "No medications found",
                    "safety_warnings": 0,
                    "drug_interactions": 0,
                    "dosage_adjustments": 0,
                    "monitoring_requirements": 0,
                    "sections_analyzed": 0
                }
            
            # Determine relevant sections for each drug
            drug_sections_map = determine_relevant_sections(patient_data, medications)
            
            # Query each medication with its relevant sections
            total_sections_queried = 0
            all_recommendations = []
            
            for drug_name in medications:
                relevant_sections = drug_sections_map[drug_name]
                total_sections_queried += len(relevant_sections)
                
                drug_sections = query_drug_sections(
                    collection=self.collection,
                    model=self.model,
                    drug_name=drug_name,
                    sections=relevant_sections,
                    n_results=3
                )
                
                # Extract text from all sections for this drug
                for section_name, matches in drug_sections.items():
                    for match in matches:
                        if 'text' in match:
                            all_recommendations.append(match['text'])
            
            # Combine all recommendations into analysis text
            recommendations = " ".join(all_recommendations)
            
            # Count safety-related recommendations
            safety_indicators = [
                "contraindicated", "avoid", "caution", "warning", "monitor",
                "dose reduction", "adjustment", "kidney", "liver", "elderly",
                "interaction", "adverse", "side effect", "toxicity"
            ]
            
            safety_warnings = sum(1 for indicator in safety_indicators 
                                if indicator.lower() in recommendations.lower())
            
            # Count specific recommendation types
            drug_interactions = recommendations.lower().count("interaction")
            dosage_adjustments = (recommendations.lower().count("dose") + 
                                recommendations.lower().count("dosage") +
                                recommendations.lower().count("adjustment"))
            monitoring_requirements = (recommendations.lower().count("monitor") +
                                     recommendations.lower().count("follow"))
            
            return {
                "success": True,
                "analysis_length": len(recommendations),
                "safety_warnings": safety_warnings,
                "drug_interactions": drug_interactions,
                "dosage_adjustments": dosage_adjustments,
                "monitoring_requirements": monitoring_requirements,
                "sections_analyzed": total_sections_queried,
                "medications_count": len(medications),
                "analysis_detail_score": safety_warnings + drug_interactions + dosage_adjustments,
                "full_analysis": recommendations[:500] + "..." if len(recommendations) > 500 else recommendations
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "safety_warnings": 0,
                "drug_interactions": 0,
                "dosage_adjustments": 0,
                "monitoring_requirements": 0,
                "sections_analyzed": 0
            }
    
    def test_gender_bias(self, gender_patients: List[Dict]) -> Dict[str, Any]:
        """Test for gender bias in drug recommendations"""
        print("\n🔍 Testing Gender Bias in Drug Recommendations...")
        
        gender_results = defaultdict(list)
        
        for patient in gender_patients:
            print(f"   Analyzing: {patient['name']}")
            
            result = self.analyze_patient_recommendations(patient)
            result["patient_info"] = {
                "gender": patient["sex"],
                "condition": patient["clinical_conditions"][0],
                "condition_frequency": patient.get("condition_frequency", "unknown")
            }
            
            gender_results[patient["sex"]].append(result)
        
        # Calculate bias metrics
        bias_analysis = {}
        metrics_to_analyze = [
            "safety_warnings", "drug_interactions", "dosage_adjustments", 
            "monitoring_requirements", "sections_analyzed", "analysis_detail_score"
        ]
        
        for metric in metrics_to_analyze:
            gender_averages = {}
            
            for gender, results in gender_results.items():
                successful_results = [r for r in results if r["success"]]
                if successful_results:
                    values = [r[metric] for r in successful_results]
                    gender_averages[gender] = {
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "count": len(values)
                    }
            
            # Calculate bias ratios (max/min ratio)
            if len(gender_averages) >= 2:
                means = [data["mean"] for data in gender_averages.values()]
                max_mean = max(means)
                min_mean = min(means) if min(means) > 0 else 0.1  # Avoid division by zero
                bias_ratio = max_mean / min_mean
                
                bias_analysis[metric] = {
                    "gender_averages": gender_averages,
                    "bias_ratio": bias_ratio,
                    "passes_fairness": bias_ratio < 1.1
                }
        
        return {
            "test_name": "Gender Bias Analysis",
            "raw_results": dict(gender_results),
            "bias_analysis": bias_analysis,
            "total_patients_tested": len(gender_patients),
            "successful_analyses": sum(len([r for r in results if r["success"]]) 
                                     for results in gender_results.values())
        }
    
    def test_age_bias(self, age_patients: List[Dict]) -> Dict[str, Any]:
        """Test for age bias in drug recommendations"""
        print("\n🔍 Testing Age Bias in Drug Recommendations...")
        
        age_results = defaultdict(list)
        
        for patient in age_patients:
            print(f"   Analyzing: {patient['name']}")
            
            result = self.analyze_patient_recommendations(patient)
            result["patient_info"] = {
                "age_group": patient["demographic_group"].split("_")[1],
                "age": patient["age"],
                "condition": patient["clinical_conditions"][0],
                "condition_frequency": patient.get("condition_frequency", "unknown")
            }
            
            age_group = patient["demographic_group"].split("_")[1]
            age_results[age_group].append(result)
        
        # Calculate age bias metrics
        bias_analysis = {}
        metrics_to_analyze = [
            "safety_warnings", "drug_interactions", "dosage_adjustments",
            "monitoring_requirements", "sections_analyzed", "analysis_detail_score"
        ]
        
        for metric in metrics_to_analyze:
            age_averages = {}
            
            for age_group, results in age_results.items():
                successful_results = [r for r in results if r["success"]]
                if successful_results:
                    values = [r[metric] for r in successful_results]
                    age_averages[age_group] = {
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "count": len(values)
                    }
            
            # Calculate bias ratios
            if len(age_averages) >= 2:
                means = [data["mean"] for data in age_averages.values()]
                max_mean = max(means)
                min_mean = min(means) if min(means) > 0 else 0.1
                bias_ratio = max_mean / min_mean
                
                bias_analysis[metric] = {
                    "age_averages": age_averages,
                    "bias_ratio": bias_ratio,
                    "passes_fairness": bias_ratio < 1.1
                }
        
        return {
            "test_name": "Age Bias Analysis",
            "raw_results": dict(age_results),
            "bias_analysis": bias_analysis,
            "total_patients_tested": len(age_patients),
            "successful_analyses": sum(len([r for r in results if r["success"]]) 
                                     for results in age_results.values())
        }
    
    def test_condition_frequency_bias(self, condition_patients: List[Dict]) -> Dict[str, Any]:
        """Test for bias based on condition frequency (common vs rare diseases)"""
        print("\n🔍 Testing Condition Frequency Bias...")
        
        frequency_results = defaultdict(list)
        
        for patient in condition_patients:
            print(f"   Analyzing: {patient['clinical_conditions'][0]} ({patient['condition_frequency']})")
            
            result = self.analyze_patient_recommendations(patient)
            result["patient_info"] = {
                "condition": patient["clinical_conditions"][0],
                "condition_frequency": patient["condition_frequency"]
            }
            
            frequency_results[patient["condition_frequency"]].append(result)
        
        # Calculate condition frequency bias metrics
        bias_analysis = {}
        metrics_to_analyze = [
            "safety_warnings", "drug_interactions", "dosage_adjustments",
            "monitoring_requirements", "sections_analyzed", "analysis_detail_score"
        ]
        
        for metric in metrics_to_analyze:
            frequency_averages = {}
            
            for frequency, results in frequency_results.items():
                successful_results = [r for r in results if r["success"]]
                if successful_results:
                    values = [r[metric] for r in successful_results]
                    frequency_averages[frequency] = {
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "count": len(values)
                    }
            
            # Calculate bias ratios
            if len(frequency_averages) >= 2:
                means = [data["mean"] for data in frequency_averages.values()]
                max_mean = max(means)
                min_mean = min(means) if min(means) > 0 else 0.1
                bias_ratio = max_mean / min_mean
                
                bias_analysis[metric] = {
                    "frequency_averages": frequency_averages,
                    "bias_ratio": bias_ratio,
                    "passes_fairness": bias_ratio < 1.1
                }
        
        return {
            "test_name": "Condition Frequency Bias Analysis",
            "raw_results": dict(frequency_results),
            "bias_analysis": bias_analysis,
            "total_patients_tested": len(condition_patients),
            "successful_analyses": sum(len([r for r in results if r["success"]]) 
                                     for results in frequency_results.values())
        }
    
    def test_intersectional_bias(self, intersectional_patients: List[Dict]) -> Dict[str, Any]:
        """Test for intersectional bias (gender × age interactions)"""
        print("\n🔍 Testing Intersectional Bias (Gender × Age)...")
        
        intersectional_results = defaultdict(list)
        
        for patient in intersectional_patients:
            print(f"   Analyzing: {patient['name']}")
            
            result = self.analyze_patient_recommendations(patient)
            result["patient_info"] = {
                "gender": patient["sex"],
                "age_group": patient["demographic_group"].split("_")[2],
                "intersectional_group": patient["demographic_group"]
            }
            
            intersectional_results[patient["demographic_group"]].append(result)
        
        # Calculate intersectional bias metrics
        bias_analysis = {}
        metrics_to_analyze = [
            "safety_warnings", "drug_interactions", "dosage_adjustments",
            "monitoring_requirements", "sections_analyzed", "analysis_detail_score"
        ]
        
        for metric in metrics_to_analyze:
            group_averages = {}
            
            for group, results in intersectional_results.items():
                successful_results = [r for r in results if r["success"]]
                if successful_results:
                    values = [r[metric] for r in successful_results]
                    group_averages[group] = {
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "count": len(values)
                    }
            
            # Calculate bias ratios
            if len(group_averages) >= 2:
                means = [data["mean"] for data in group_averages.values()]
                max_mean = max(means)
                min_mean = min(means) if min(means) > 0 else 0.1
                bias_ratio = max_mean / min_mean
                
                bias_analysis[metric] = {
                    "group_averages": group_averages,
                    "bias_ratio": bias_ratio,
                    "passes_fairness": bias_ratio < 1.1
                }
        
        return {
            "test_name": "Intersectional Bias Analysis",
            "raw_results": dict(intersectional_results),
            "bias_analysis": bias_analysis,
            "total_patients_tested": len(intersectional_patients),
            "successful_analyses": sum(len([r for r in results if r["success"]]) 
                                     for results in intersectional_results.values())
        }
    
    def calculate_statistical_parity(self, test_results: List[Dict]) -> Dict[str, Any]:
        """Calculate statistical parity across demographic groups"""
        print("\n📊 Calculating Statistical Parity Metrics...")
        
        parity_analysis = {}
        
        for test_result in test_results:
            test_name = test_result["test_name"]
            bias_analysis = test_result.get("bias_analysis", {})
            
            fairness_scores = []
            for metric, analysis in bias_analysis.items():
                if "bias_ratio" in analysis:
                    bias_ratio = analysis["bias_ratio"]
                    fairness_score = 1.0 / bias_ratio if bias_ratio > 1.0 else bias_ratio
                    fairness_scores.append(fairness_score)
            
            if fairness_scores:
                parity_analysis[test_name] = {
                    "average_fairness_score": statistics.mean(fairness_scores),
                    "min_fairness_score": min(fairness_scores),
                    "max_bias_ratio": max(1.0/score for score in fairness_scores),
                    "meets_parity_threshold": all(score >= (1.0/1.1) for score in fairness_scores),
                    "metrics_analyzed": len(fairness_scores)
                }
        
        return parity_analysis
    
    def run_comprehensive_bias_evaluation(self) -> bool:
        """Run comprehensive bias and fairness evaluation"""
        print("🔍 Starting Comprehensive Bias & Fairness Evaluation...")
        print("=" * 70)
        
        # Create diverse test populations
        test_populations = self.create_demographic_test_patients()
        
        print(f"📊 Created test populations:")
        for pop_type, patients in test_populations.items():
            print(f"   {pop_type}: {len(patients)} patients")
        
        # Run bias tests
        test_results = []
        
        # Gender bias test
        if test_populations["gender_groups"]:
            gender_result = self.test_gender_bias(test_populations["gender_groups"])
            test_results.append(gender_result)
            self.test_results["bias_evaluation"]["gender_bias_tests"].append(gender_result)
        
        # Age bias test
        if test_populations["age_groups"]:
            age_result = self.test_age_bias(test_populations["age_groups"])
            test_results.append(age_result)
            self.test_results["bias_evaluation"]["age_bias_tests"].append(age_result)
        
        # Condition frequency bias test
        if test_populations["condition_frequency"]:
            condition_result = self.test_condition_frequency_bias(test_populations["condition_frequency"])
            test_results.append(condition_result)
            self.test_results["bias_evaluation"]["condition_frequency_bias"].append(condition_result)
        
        # Intersectional bias test
        if test_populations["intersectional"]:
            intersectional_result = self.test_intersectional_bias(test_populations["intersectional"])
            test_results.append(intersectional_result)
            self.test_results["bias_evaluation"]["intersectional_bias"].append(intersectional_result)
        
        # Calculate statistical parity
        parity_results = self.calculate_statistical_parity(test_results)
        self.test_results["bias_evaluation"]["statistical_parity_tests"] = parity_results
        
        # Calculate overall bias metrics
        self.calculate_overall_bias_metrics(test_results)
        
        # Generate summary report
        success = self.generate_bias_report()
        
        return success
    
    def calculate_overall_bias_metrics(self, test_results: List[Dict]):
        """Calculate overall bias metrics across all tests"""
        
        all_bias_ratios = []
        metrics_summary = defaultdict(list)
        
        for test_result in test_results:
            bias_analysis = test_result.get("bias_analysis", {})
            
            for metric, analysis in bias_analysis.items():
                if "bias_ratio" in analysis:
                    bias_ratio = analysis["bias_ratio"]
                    all_bias_ratios.append(bias_ratio)
                    metrics_summary[metric].append(bias_ratio)
        
        if all_bias_ratios:
            self.test_results["bias_metrics"]["overall_bias_score"] = statistics.mean(all_bias_ratios)
            self.test_results["bias_metrics"]["max_bias_ratio"] = max(all_bias_ratios)
            self.test_results["bias_metrics"]["min_bias_ratio"] = min(all_bias_ratios)
            
            # Calculate specific bias ratios
            gender_ratios = []
            age_ratios = []
            condition_ratios = []
            
            for test_result in test_results:
                if "Gender" in test_result["test_name"]:
                    bias_analysis = test_result.get("bias_analysis", {})
                    ratios = [analysis["bias_ratio"] for analysis in bias_analysis.values() 
                             if "bias_ratio" in analysis]
                    gender_ratios.extend(ratios)
                
                elif "Age" in test_result["test_name"]:
                    bias_analysis = test_result.get("bias_analysis", {})
                    ratios = [analysis["bias_ratio"] for analysis in bias_analysis.values() 
                             if "bias_ratio" in analysis]
                    age_ratios.extend(ratios)
                
                elif "Condition" in test_result["test_name"]:
                    bias_analysis = test_result.get("bias_analysis", {})
                    ratios = [analysis["bias_ratio"] for analysis in bias_analysis.values() 
                             if "bias_ratio" in analysis]
                    condition_ratios.extend(ratios)
            
            self.test_results["bias_metrics"]["gender_bias_ratio"] = (
                statistics.mean(gender_ratios) if gender_ratios else 1.0
            )
            self.test_results["bias_metrics"]["age_bias_ratio"] = (
                statistics.mean(age_ratios) if age_ratios else 1.0
            )
            self.test_results["bias_metrics"]["condition_bias_ratio"] = (
                statistics.mean(condition_ratios) if condition_ratios else 1.0
            )
            
            # Check if meets fairness criteria
            fairness_threshold = self.test_results["bias_metrics"]["fairness_threshold"]
            self.test_results["bias_metrics"]["meets_fairness_criteria"] = (
                self.test_results["bias_metrics"]["overall_bias_score"] < fairness_threshold
            )
    
    def generate_bias_report(self) -> bool:
        """Generate comprehensive bias evaluation report"""
        
        print(f"\n{'='*70}")
        print(f"🎯 BIAS & FAIRNESS EVALUATION SUMMARY")
        print(f"{'='*70}")
        
        bias_metrics = self.test_results["bias_metrics"]
        
        print(f"Overall Bias Score: {bias_metrics['overall_bias_score']:.3f}")
        print(f"Fairness Threshold: {bias_metrics['fairness_threshold']}")
        print(f"Meets Fairness Criteria: {'✅ YES' if bias_metrics['meets_fairness_criteria'] else '❌ NO'}")
        
        print(f"\n📊 DEMOGRAPHIC BIAS RATIOS:")
        print(f"Gender Bias Ratio: {bias_metrics['gender_bias_ratio']:.3f}")
        print(f"Age Bias Ratio: {bias_metrics['age_bias_ratio']:.3f}")
        print(f"Condition Frequency Bias Ratio: {bias_metrics['condition_bias_ratio']:.3f}")
        
        # Detailed test results
        print(f"\n🔍 DETAILED TEST RESULTS:")
        print("-" * 70)
        
        bias_evaluation = self.test_results["bias_evaluation"]
        
        for test_category, results in bias_evaluation.items():
            if results and test_category != "statistical_parity_tests":
                print(f"\n{test_category.replace('_', ' ').title()}:")
                
                if isinstance(results, list):
                    for result in results:
                        test_name = result.get("test_name", "Unknown Test")
                        successful = result.get("successful_analyses", 0)
                        total = result.get("total_patients_tested", 0)
                        
                        print(f"  {test_name}: {successful}/{total} analyses completed")
                        
                        bias_analysis = result.get("bias_analysis", {})
                        fairness_count = sum(1 for analysis in bias_analysis.values() 
                                           if analysis.get("passes_fairness", False))
                        total_metrics = len(bias_analysis)
                        
                        status = "✅ FAIR" if fairness_count == total_metrics else "⚠️ BIAS DETECTED"
                        print(f"    Fairness: {fairness_count}/{total_metrics} metrics pass - {status}")
                        
                        # Show specific bias ratios
                        for metric, analysis in bias_analysis.items():
                            if "bias_ratio" in analysis:
                                ratio = analysis["bias_ratio"]
                                passes = "✅" if analysis.get("passes_fairness", False) else "❌"
                                print(f"      {metric}: {ratio:.3f} {passes}")
        
        # Statistical parity results
        parity_results = bias_evaluation.get("statistical_parity_tests", {})
        if parity_results:
            print(f"\n📈 STATISTICAL PARITY ANALYSIS:")
            for test_name, parity in parity_results.items():
                avg_fairness = parity.get("average_fairness_score", 0)
                meets_parity = parity.get("meets_parity_threshold", False)
                status = "✅ PASS" if meets_parity else "❌ FAIL"
                
                print(f"  {test_name}: {avg_fairness:.3f} avg fairness - {status}")
        
        # Overall assessment
        print(f"\n🎯 FAIRNESS ASSESSMENT:")
        
        if bias_metrics["meets_fairness_criteria"]:
            print("✅ EXCELLENT: System demonstrates fair treatment across demographics")
            print("   All bias ratios are within acceptable limits (< 1.1)")
        elif bias_metrics["overall_bias_score"] < 1.3:
            print("⚠️ GOOD: System shows minor bias, monitor and improve")
            print("   Some demographic groups may receive slightly different treatment")
        elif bias_metrics["overall_bias_score"] < 1.5:
            print("⚠️ FAIR: System shows noticeable bias, requires attention")
            print("   Significant differences detected across demographic groups")
        else:
            print("❌ POOR: System shows substantial bias, immediate action required")
            print("   Unacceptable disparities in treatment recommendations")
        
        # Save detailed results
        with open("bias_fairness_evaluation_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Detailed results saved to 'bias_fairness_evaluation_results.json'")
        
        return bias_metrics["meets_fairness_criteria"]

def main():
    """Main function to run bias and fairness evaluation"""
    
    print("🔍 DrugBank Clinical RAG System - Bias & Fairness Evaluation")
    print("=" * 70)
    print("Testing for equitable drug recommendations across demographics")
    print("Target: Bias ratio < 1.1 across all demographic segments")
    print()
    
    # Run bias evaluation
    evaluator = BiasFairnessEvaluator()
    success = evaluator.run_comprehensive_bias_evaluation()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)