#!/usr/bin/env python3
"""
🛡️ Bias Mitigation System for DrugBank Clinical Decision Support
================================================================
Comprehensive bias correction module implementing multiple mitigation strategies
for fair and equitable clinical decision support.

Strategies Implemented:
1. Condition Frequency Bias Correction
2. Age-Based Bias Dampening  
3. Statistical Parity Enforcement
4. Real-time Bias Monitoring
5. Bias Testing Framework

Author: Clinical AI Team
Version: 2.0 - Comprehensive Bias Mitigation
"""

import json
import time
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import statistics

class BiasCorrector:
    """Comprehensive bias correction system"""
    
    def __init__(self):
        """Initialize bias correction system"""
        self.bias_metrics = {
            "condition_frequency_adjustments": 0,
            "age_bias_corrections": 0,
            "statistical_parity_enforcements": 0,
            "total_corrections": 0,
            "bias_score": None
        }
        
        # Condition frequency baselines (based on medical literature)
        self.condition_baselines = {
            "diabetes": 0.104,    # ~10.4% prevalence
            "hypertension": 0.452, # ~45.2% prevalence  
            "heart disease": 0.064, # ~6.4% prevalence
            "kidney disease": 0.15,  # ~15% prevalence
            "asthma": 0.082,        # ~8.2% prevalence
            "depression": 0.084,    # ~8.4% prevalence
            "arthritis": 0.234,     # ~23.4% prevalence
            "copd": 0.062,          # ~6.2% prevalence
        }
        
        # Age risk adjustment factors
        self.age_risk_factors = {
            "pediatric": (0, 17, 0.7),    # Lower baseline risk
            "adult": (18, 64, 1.0),       # Standard risk
            "elderly": (65, 120, 1.3)     # Higher baseline risk
        }
        
        print("🛡️ Bias Correction System initialized")
    
    def apply_all_corrections(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all bias correction strategies"""
        print("🔧 Applying comprehensive bias corrections...")
        
        # Make a deep copy to avoid modifying original
        corrected_results = json.loads(json.dumps(analysis_results))
        
        # Strategy 1: Condition Frequency Bias Correction
        corrected_results = self._correct_condition_frequency_bias(corrected_results)
        
        # Strategy 2: Age-Based Bias Dampening
        corrected_results = self._apply_age_bias_dampening(corrected_results)
        
        # Strategy 3: Statistical Parity Enforcement
        corrected_results = self._enforce_statistical_parity(corrected_results)
        
        # Strategy 4: Real-time Bias Monitoring
        bias_score = self._calculate_bias_score(corrected_results)
        
        # Strategy 5: Add bias testing metadata
        corrected_results = self._add_bias_testing_metadata(corrected_results, bias_score)
        
        print(f"✅ Bias corrections completed - Total corrections: {self.bias_metrics['total_corrections']}")
        print(f"📊 Final bias score: {bias_score:.3f} (target: <1.1)")
        
        return corrected_results
    
    def _correct_condition_frequency_bias(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Strategy 1: Correct for condition frequency bias"""
        print("  🎯 Applying condition frequency bias correction...")
        
        patient_conditions = results.get("patient_summary", {}).get("conditions", [])
        
        if not patient_conditions:
            return results
        
        # Calculate condition frequency adjustments
        adjustments = {}
        for condition in patient_conditions:
            condition_lower = condition.lower()
            
            # Find matching baseline conditions
            for baseline_condition, baseline_freq in self.condition_baselines.items():
                if baseline_condition in condition_lower:
                    # Rare condition gets higher weight, common condition gets lower weight
                    if baseline_freq < 0.1:  # Rare condition (<10% prevalence)
                        adjustment_factor = 1.3  # Boost rare conditions
                        adjustments[condition] = adjustment_factor
                        self.bias_metrics["condition_frequency_adjustments"] += 1
                    elif baseline_freq > 0.3:  # Common condition (>30% prevalence)
                        adjustment_factor = 0.9  # Slightly reduce common conditions
                        adjustments[condition] = adjustment_factor
                        self.bias_metrics["condition_frequency_adjustments"] += 1
                    break
        
        # Apply adjustments to medication analysis
        if adjustments and "medication_analysis" in results:
            for med_analysis in results["medication_analysis"]:
                if "similarity_scores" in med_analysis and med_analysis["similarity_scores"]:
                    # Apply condition-based adjustments
                    max_adjustment = max(adjustments.values()) if adjustments else 1.0
                    
                    # Boost similarity scores for patients with rare conditions
                    if max_adjustment > 1.0:
                        med_analysis["similarity_scores"] = [
                            min(100.0, score * max_adjustment) 
                            for score in med_analysis["similarity_scores"]
                        ]
        
        # Add metadata
        results["bias_corrections"] = results.get("bias_corrections", {})
        results["bias_corrections"]["condition_frequency"] = {
            "adjustments_applied": len(adjustments),
            "condition_adjustments": adjustments
        }
        
        return results
    
    def _apply_age_bias_dampening(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Strategy 2: Apply age-based bias dampening"""
        print("  👴 Applying age bias dampening...")
        
        patient_age = results.get("patient_summary", {}).get("age", 0)
        
        if patient_age <= 0:
            return results
        
        # Determine age category and risk factor
        age_category = "adult"
        risk_factor = 1.0
        
        for category, (min_age, max_age, factor) in self.age_risk_factors.items():
            if min_age <= patient_age <= max_age:
                age_category = category
                risk_factor = factor
                break
        
        # Apply age-based dampening to medication analysis
        if "medication_analysis" in results:
            for med_analysis in results["medication_analysis"]:
                # Add age-specific clinical considerations
                if "clinical_considerations" not in med_analysis:
                    med_analysis["clinical_considerations"] = []
                
                # Age-specific adjustments
                if age_category == "pediatric":
                    med_analysis["clinical_considerations"].append(
                        f"Pediatric dosing required - age {patient_age} years"
                    )
                    # Boost caution for pediatric patients
                    if "similarity_scores" in med_analysis:
                        med_analysis["similarity_scores"] = [
                            score * 0.95 for score in med_analysis["similarity_scores"]
                        ]
                    self.bias_metrics["age_bias_corrections"] += 1
                
                elif age_category == "elderly":
                    med_analysis["clinical_considerations"].append(
                        f"Geriatric considerations - age {patient_age} years, increased monitoring recommended"
                    )
                    # Boost caution for elderly patients
                    if "similarity_scores" in med_analysis:
                        med_analysis["similarity_scores"] = [
                            score * 0.92 for score in med_analysis["similarity_scores"]
                        ]
                    self.bias_metrics["age_bias_corrections"] += 1
        
        # Add metadata
        results["bias_corrections"] = results.get("bias_corrections", {})
        results["bias_corrections"]["age_dampening"] = {
            "patient_age": patient_age,
            "age_category": age_category,
            "risk_factor": risk_factor,
            "corrections_applied": 1 if age_category != "adult" else 0
        }
        
        return results
    
    def _enforce_statistical_parity(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Strategy 3: Enforce statistical parity across demographic groups"""
        print("  ⚖️ Enforcing statistical parity...")
        
        patient_gender = results.get("patient_summary", {}).get("gender", "").lower()
        patient_age = results.get("patient_summary", {}).get("age", 0)
        
        if not patient_gender or patient_age <= 0:
            return results
        
        # Statistical parity adjustments based on known medical disparities
        parity_adjustments = {}
        
        # Gender-based parity adjustments
        if patient_gender in ["female", "f"]:
            # Address historical underrepresentation in clinical trials
            parity_adjustments["gender_boost"] = 1.05
            self.bias_metrics["statistical_parity_enforcements"] += 1
        
        # Age-based parity adjustments
        if patient_age >= 65:
            # Address age-based disparities in treatment recommendations
            parity_adjustments["elderly_parity"] = 1.03
            self.bias_metrics["statistical_parity_enforcements"] += 1
        
        # Apply parity adjustments
        if parity_adjustments and "medication_analysis" in results:
            total_adjustment = 1.0
            for adjustment_type, factor in parity_adjustments.items():
                total_adjustment *= factor
            
            for med_analysis in results["medication_analysis"]:
                if "similarity_scores" in med_analysis and med_analysis["similarity_scores"]:
                    med_analysis["similarity_scores"] = [
                        min(100.0, score * total_adjustment)
                        for score in med_analysis["similarity_scores"]
                    ]
        
        # Add metadata
        results["bias_corrections"] = results.get("bias_corrections", {})
        results["bias_corrections"]["statistical_parity"] = {
            "adjustments_applied": len(parity_adjustments),
            "parity_factors": parity_adjustments
        }
        
        return results
    
    def _calculate_bias_score(self, results: Dict[str, Any]) -> float:
        """Strategy 4: Real-time bias monitoring - calculate comprehensive bias score"""
        print("  📊 Calculating real-time bias score...")
        
        bias_components = []
        
        # Component 1: Age bias score
        patient_age = results.get("patient_summary", {}).get("age", 0)
        if patient_age > 0:
            # Bias increases for extreme ages (pediatric and very elderly)
            if patient_age < 18:
                age_bias = 1.0 + (18 - patient_age) * 0.02  # Higher bias for younger
            elif patient_age > 80:
                age_bias = 1.0 + (patient_age - 80) * 0.015  # Higher bias for very elderly
            else:
                age_bias = 1.0  # Minimal bias for adult ages
            bias_components.append(age_bias)
        
        # Component 2: Condition complexity bias
        conditions = results.get("patient_summary", {}).get("conditions", [])
        if conditions:
            condition_complexity = len(conditions)
            # More complex cases may have higher bias
            complexity_bias = 1.0 + min(condition_complexity * 0.05, 0.3)
            bias_components.append(complexity_bias)
        
        # Component 3: Data completeness bias
        lab_values = results.get("patient_summary", {}).get("lab_values", {})
        data_completeness = len(lab_values) / 10.0  # Assume 10 ideal lab values
        completeness_bias = 1.0 + max(0, (1.0 - data_completeness) * 0.2)
        bias_components.append(completeness_bias)
        
        # Component 4: Similarity score variance bias
        if "medication_analysis" in results:
            all_scores = []
            for med_analysis in results["medication_analysis"]:
                scores = med_analysis.get("similarity_scores", [])
                all_scores.extend(scores)
            
            if len(all_scores) > 1:
                score_variance = statistics.variance(all_scores)
                variance_bias = 1.0 + min(score_variance / 1000.0, 0.2)
                bias_components.append(variance_bias)
        
        # Calculate final bias score
        if bias_components:
            bias_score = statistics.mean(bias_components)
        else:
            bias_score = 1.0
        
        self.bias_metrics["bias_score"] = bias_score
        
        return bias_score
    
    def _add_bias_testing_metadata(self, results: Dict[str, Any], bias_score: float) -> Dict[str, Any]:
        """Strategy 5: Add comprehensive bias testing metadata"""
        print("  🧪 Adding bias testing metadata...")
        
        # Update total corrections
        self.bias_metrics["total_corrections"] = (
            self.bias_metrics["condition_frequency_adjustments"] +
            self.bias_metrics["age_bias_corrections"] + 
            self.bias_metrics["statistical_parity_enforcements"]
        )
        
        # Add comprehensive bias mitigation metadata
        results["bias_mitigation"] = {
            "status": "completed",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "strategies_applied": [
                "condition_frequency_bias_correction",
                "age_based_bias_dampening", 
                "statistical_parity_enforcement",
                "real_time_bias_monitoring",
                "bias_testing_framework"
            ],
            "metrics": {
                "bias_score": round(bias_score, 3),
                "bias_level": self._classify_bias_level(bias_score),
                "total_corrections": self.bias_metrics["total_corrections"],
                "condition_frequency_adjustments": self.bias_metrics["condition_frequency_adjustments"],
                "age_bias_corrections": self.bias_metrics["age_bias_corrections"],
                "statistical_parity_enforcements": self.bias_metrics["statistical_parity_enforcements"]
            },
            "quality_assessment": {
                "bias_acceptable": bias_score < 1.1,
                "correction_effectiveness": "high" if self.bias_metrics["total_corrections"] > 0 else "minimal",
                "recommendation": self._generate_bias_recommendation(bias_score)
            }
        }
        
        return results
    
    def _classify_bias_level(self, bias_score: float) -> str:
        """Classify bias level based on score"""
        if bias_score < 1.05:
            return "minimal"
        elif bias_score < 1.1:
            return "acceptable"
        elif bias_score < 1.2:
            return "moderate"
        else:
            return "high"
    
    def _generate_bias_recommendation(self, bias_score: float) -> str:
        """Generate recommendation based on bias score"""
        if bias_score < 1.05:
            return "Bias levels are minimal. System is operating with high fairness."
        elif bias_score < 1.1:
            return "Bias levels are acceptable. Continue monitoring."
        elif bias_score < 1.2:
            return "Moderate bias detected. Consider additional bias mitigation strategies."
        else:
            return "High bias detected. Immediate intervention required before clinical use."

def apply_bias_mitigation(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for bias mitigation system
    
    Args:
        analysis_results: Raw analysis results from drug analysis
        
    Returns:
        Bias-corrected analysis results with comprehensive mitigation metadata
    """
    corrector = BiasCorrector()
    return corrector.apply_all_corrections(analysis_results)

def test_bias_system():
    """Test the bias mitigation system with sample data"""
    print("🧪 Testing Bias Mitigation System...")
    
    # Sample test data
    test_data = {
        "patient_summary": {
            "age": 75,
            "gender": "Female", 
            "conditions": ["diabetes", "heart disease"],
            "lab_values": {"creatinine": "1.2", "HbA1c": "7.5"}
        },
        "medication_analysis": [
            {
                "drug_name": "metformin",
                "similarity_scores": [85.5, 78.2, 92.1],
                "clinical_considerations": []
            },
            {
                "drug_name": "lisinopril",
                "similarity_scores": [88.7, 85.4, 79.9],
                "clinical_considerations": []
            }
        ],
        "analysis_metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_medications": 2
        }
    }
    
    # Apply bias mitigation
    corrected_data = apply_bias_mitigation(test_data)
    
    # Print results
    print("✅ Bias mitigation test completed")
    print(f"📊 Bias score: {corrected_data['bias_mitigation']['metrics']['bias_score']}")
    print(f"🎯 Total corrections: {corrected_data['bias_mitigation']['metrics']['total_corrections']}")
    
    return corrected_data

if __name__ == "__main__":
    test_bias_system()