#!/usr/bin/env python3
"""
🏥 DrugBank Clinical Decision Support System - Simplified Single Script
=======================================================================
A standalone script that performs complete patient drug analysis with AI normalization,
semantic search, and bias mitigation using existing ChromaDB embeddings.

Author: Clinical AI Team
Version: 2.0 - Simplified Standalone
"""

import json
import os
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
import torch
import re

# Load environment variables
load_dotenv()

class DrugBankAnalyzer:
    """Simplified DrugBank Clinical Decision Support System"""
    
    def __init__(self):
        """Initialize the analyzer with required components"""
        self.ai_api_key = os.getenv('AI_API_KEY')
        self.chroma_client = None
        self.collection = None
        self.model = None
        
        print("🏥 Initializing DrugBank Clinical Decision Support System...")
        
    def initialize_components(self):
        """Initialize ChromaDB and PubMedBERT model"""
        try:
            print("🔗 Connecting to ChromaDB...")
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
            self.collection = self.chroma_client.get_collection("drugbank")
            print(f"✅ Connected to ChromaDB with {self.collection.count()} records")
            
            print("🧠 Loading PubMedBERT model...")
            self.model = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO")
            print("✅ PubMedBERT model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            raise
    
    def normalize_patient_data(self, patient_file: str = "patient.json") -> Dict[str, Any]:
        """
        Step 1: AI Input Normalizer
        Reads patient.json and normalizes it using AI API or fallback parser
        """
        print("🔍 Normalizing patient input data...")
        
        # Read patient file
        try:
            with open(patient_file, 'r', encoding='utf-8') as f:
                raw_patient_data = json.load(f)
            print(f"📄 Loaded patient data from {patient_file}")
        except FileNotFoundError:
            print(f"❌ Patient file {patient_file} not found")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format in {patient_file}: {e}")
            raise
        
        # Try AI normalization first
        if self.ai_api_key:
            normalized_data = self._ai_normalize_data(raw_patient_data)
            if normalized_data:
                print("✅ AI normalization successful")
                return normalized_data
            else:
                print("⚠️ AI normalization failed, falling back to heuristic parser")
        
        # Fallback to heuristic parser
        normalized_data = self._heuristic_normalize_data(raw_patient_data)
        print("✅ Heuristic normalization completed")
        return normalized_data
    
    def _ai_normalize_data(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use AI API to normalize patient data"""
        try:
            # Simulate AI API call (replace with actual API implementation)
            print("🤖 Calling AI API for data normalization...")
            
            # AI Prompt for normalization
            ai_prompt = f"""
            Please extract and normalize the following patient data into this exact JSON structure:
            {{
              "age": int,
              "gender": str,
              "conditions": [list of strings],
              "medications": [list of strings], 
              "lab_values": {{ key: value }}
            }}
            
            Raw patient data:
            {json.dumps(raw_data, indent=2)}
            
            Return only valid JSON, no explanation.
            """
            
            # TODO: Replace with actual AI API call
            # response = ai_client.complete(prompt=ai_prompt)
            # For now, return None to trigger fallback
            return None
            
        except Exception as e:
            print(f"⚠️ AI API error: {e}")
            return None
    
    def _heuristic_normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback heuristic parser for common patient data formats"""
        normalized = {
            "age": 0,
            "gender": "",
            "conditions": [],
            "medications": [],
            "lab_values": {}
        }
        
        # Extract age
        age_fields = ["age", "Age", "patient_age", "years_old"]
        for field in age_fields:
            if field in raw_data and raw_data[field]:
                try:
                    normalized["age"] = int(str(raw_data[field]).split()[0])
                    break
                except:
                    continue
        
        # Extract gender
        gender_fields = ["gender", "sex", "Gender", "Sex", "patient_gender"]
        for field in gender_fields:
            if field in raw_data and raw_data[field]:
                gender = str(raw_data[field]).lower()
                if gender in ["male", "m", "man"]:
                    normalized["gender"] = "Male"
                elif gender in ["female", "f", "woman"]:
                    normalized["gender"] = "Female"
                else:
                    normalized["gender"] = raw_data[field]
                break
        
        # Extract conditions
        condition_fields = ["conditions", "diagnosis", "medical_conditions", "clinical_conditions", "diagnoses"]
        for field in condition_fields:
            if field in raw_data and raw_data[field]:
                if isinstance(raw_data[field], list):
                    normalized["conditions"] = [str(c) for c in raw_data[field]]
                elif isinstance(raw_data[field], str):
                    normalized["conditions"] = [raw_data[field]]
                break
        
        # Extract medications
        med_fields = ["medications", "drugs", "current_medications", "prescriptions", "meds"]
        for field in med_fields:
            if field in raw_data and raw_data[field]:
                if isinstance(raw_data[field], list):
                    meds = []
                    for med in raw_data[field]:
                        if isinstance(med, dict):
                            # Extract drug name from various possible keys
                            drug_name = med.get("drugName") or med.get("drug_name") or med.get("name") or med.get("medication")
                            if drug_name:
                                meds.append(str(drug_name))
                        elif isinstance(med, str):
                            meds.append(med)
                    normalized["medications"] = meds
                elif isinstance(raw_data[field], str):
                    normalized["medications"] = [raw_data[field]]
                break
        
        # Extract lab values
        lab_fields = ["labs", "lab_results", "laboratory", "lab_values", "bloodwork"]
        for field in lab_fields:
            if field in raw_data and isinstance(raw_data[field], dict):
                normalized["lab_values"] = raw_data[field]
                break
        
        # Also check for direct lab value fields
        direct_lab_fields = ["creatinine", "eGFR", "HbA1c", "glucose", "cholesterol"]
        for lab_field in direct_lab_fields:
            if lab_field in raw_data:
                normalized["lab_values"][lab_field] = raw_data[lab_field]
        
        return normalized
    
    def analyze_patient_drugs(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Drug Analysis
        Perform semantic similarity search for each medication using ChromaDB
        """
        print("💊 Running DrugBank semantic analysis...")
        
        medications = normalized_data.get("medications", [])
        if not medications:
            print("⚠️ No medications found in patient data")
            return {"error": "No medications found"}
        
        print(f"🔍 Analyzing {len(medications)} medications: {', '.join(medications)}")
        
        analysis_results = {
            "patient_summary": {
                "age": normalized_data.get("age", 0),
                "gender": normalized_data.get("gender", ""),
                "conditions": normalized_data.get("conditions", []),
                "lab_values": normalized_data.get("lab_values", {})
            },
            "medication_analysis": [],
            "analysis_metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_medications": len(medications),
                "analysis_type": "semantic_similarity"
            }
        }
        
        for medication in medications:
            print(f"  🔍 Analyzing: {medication}")
            drug_analysis = self._analyze_single_drug(medication, normalized_data)
            analysis_results["medication_analysis"].append(drug_analysis)
        
        print("✅ Drug analysis completed")
        return analysis_results
    
    def _analyze_single_drug(self, drug_name: str, patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single drug using semantic search"""
        try:
            # Create query embedding
            query_text = f"{drug_name} clinical information"
            query_embedding = self.model.encode([query_text]).tolist()
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            drug_info = {
                "drug_name": drug_name,
                "search_results": [],
                "clinical_considerations": self._generate_clinical_considerations(drug_name, patient_context),
                "similarity_scores": []
            }
            
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0], 
                    results["distances"][0]
                )):
                    similarity_score = max(0, (1 - distance) * 100)
                    
                    drug_info["search_results"].append({
                        "content": doc[:500] + "..." if len(doc) > 500 else doc,
                        "section": metadata.get("section", "unknown"),
                        "drug_id": metadata.get("drug_id", "unknown"),
                        "similarity_score": round(similarity_score, 2)
                    })
                    
                    drug_info["similarity_scores"].append(round(similarity_score, 2))
            
            return drug_info
            
        except Exception as e:
            print(f"  ❌ Error analyzing {drug_name}: {e}")
            return {
                "drug_name": drug_name,
                "error": str(e),
                "search_results": [],
                "clinical_considerations": [],
                "similarity_scores": []
            }
    
    def _generate_clinical_considerations(self, drug_name: str, patient_context: Dict[str, Any]) -> List[str]:
        """Generate clinical considerations based on patient context"""
        considerations = []
        
        age = patient_context.get("age", 0)
        conditions = patient_context.get("conditions", [])
        lab_values = patient_context.get("lab_values", {})
        
        # Age-based considerations
        if age >= 65:
            considerations.append(f"Elderly patient (age {age}) - consider dosage adjustments and increased monitoring")
        elif age <= 18:
            considerations.append(f"Pediatric patient (age {age}) - verify pediatric dosing guidelines")
        
        # Condition-based considerations
        for condition in conditions:
            if any(kidney_term in condition.lower() for kidney_term in ["kidney", "renal", "nephro"]):
                considerations.append("Renal condition present - monitor for nephrotoxicity")
            if any(liver_term in condition.lower() for liver_term in ["liver", "hepatic", "hepato"]):
                considerations.append("Hepatic condition present - monitor for hepatotoxicity")
            if "diabetes" in condition.lower():
                considerations.append("Diabetes present - monitor blood glucose interactions")
        
        # Lab-based considerations
        if "creatinine" in lab_values:
            try:
                creat_val = float(str(lab_values["creatinine"]).split()[0])
                if creat_val > 1.5:
                    considerations.append(f"Elevated creatinine ({lab_values['creatinine']}) - consider renal dose adjustment")
            except:
                pass
        
        if "eGFR" in lab_values:
            try:
                egfr_val = float(str(lab_values["eGFR"]).split()[0])
                if egfr_val < 60:
                    considerations.append(f"Reduced eGFR ({lab_values['eGFR']}) - monitor for drug accumulation")
            except:
                pass
        
        return considerations
    
    def apply_bias_mitigation(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: Bias Mitigation
        Import and apply bias correction using bias_system.py
        """
        print("🛡️ Applying bias mitigation...")
        
        try:
            # Import bias system
            from bias_system import apply_bias_mitigation
            
            # Apply bias mitigation
            corrected_results = apply_bias_mitigation(analysis_results)
            print("✅ Bias mitigation applied successfully")
            return corrected_results
            
        except ImportError:
            print("⚠️ bias_system.py not found - skipping bias mitigation")
            analysis_results["bias_mitigation"] = {
                "status": "skipped",
                "reason": "bias_system.py not available"
            }
            return analysis_results
            
        except Exception as e:
            print(f"⚠️ Bias mitigation error: {e}")
            analysis_results["bias_mitigation"] = {
                "status": "failed",
                "error": str(e)
            }
            return analysis_results
    
    def save_results(self, final_results: Dict[str, Any], output_file: str = "patient_drug_data.json"):
        """
        Step 4: Output
        Save results to JSON file
        """
        print(f"💾 Saving results to {output_file}...")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_results, f, indent=2, ensure_ascii=False)
            print(f"✅ Results saved successfully to {output_file}")
            
            # Print summary
            total_meds = final_results.get("analysis_metadata", {}).get("total_medications", 0)
            print(f"📊 Analysis Summary:")
            print(f"   • Patient: {final_results.get('patient_summary', {}).get('age', 'Unknown')} years old")
            print(f"   • Medications analyzed: {total_meds}")
            print(f"   • Analysis timestamp: {final_results.get('analysis_metadata', {}).get('timestamp', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            raise

def main():
    """Main execution function"""
    print("🏥 DrugBank Clinical Decision Support System - Starting Analysis")
    print("=" * 70)
    
    try:
        # Initialize analyzer
        analyzer = DrugBankAnalyzer()
        analyzer.initialize_components()
        
        # Step 1: Normalize patient data
        normalized_data = analyzer.normalize_patient_data()
        
        # Step 2: Analyze patient drugs
        analysis_results = analyzer.analyze_patient_drugs(normalized_data)
        
        # Step 3: Apply bias mitigation
        final_results = analyzer.apply_bias_mitigation(analysis_results)
        
        # Step 4: Save results
        analyzer.save_results(final_results)
        
        print("=" * 70)
        print("🎉 Analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())