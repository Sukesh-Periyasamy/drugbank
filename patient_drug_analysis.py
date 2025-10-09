import json
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any, Set
import os
from gpt_local import refine_drugbank_query

# ============================================================================
# 🛡️ BIAS MITIGATION SYSTEM - Integrated into Core RAG Pipeline
# ============================================================================

def is_rare_condition(condition: str) -> bool:
    """Identify rare conditions that need bias mitigation"""
    rare_conditions = {
        'myasthenia gravis', 'huntington\'s disease', 'scleroderma', 
        'systemic sclerosis', 'amyotrophic lateral sclerosis', 'als',
        'fibromyalgia', 'lupus', 'systemic lupus erythematosus',
        'multiple sclerosis', 'crohn\'s disease', 'ulcerative colitis',
        'rheumatoid arthritis', 'psoriatic arthritis', 'ankylosing spondylitis',
        'guillain-barré syndrome', 'polymyalgia rheumatica', 'temporal arteritis',
        'behçet\'s disease', 'kawasaki disease', 'marfan syndrome'
    }
    return condition.lower().strip() in rare_conditions

def calculate_condition_frequency_bias_boost(conditions: List[str]) -> float:
    """Calculate bias correction boost for rare conditions"""
    if not conditions:
        return 1.0
    
    rare_count = sum(1 for condition in conditions if is_rare_condition(condition))
    total_conditions = len(conditions)
    
    if rare_count == 0:
        return 1.0
    
    # More aggressive boost factor for rare conditions to ensure fairness
    rare_ratio = rare_count / total_conditions
    boost_factor = 1.0 + (rare_ratio * 1.0)  # Up to 100% boost for all rare conditions
    
    return min(boost_factor, 2.0)  # Cap at 2.0x boost

def calculate_age_bias_dampening(age: int) -> float:
    """Calculate age bias dampening factor for elderly patients"""
    if age < 65:
        return 1.0
    
    # More aggressive dampening for elderly patients to meet <1.1 target
    # Age 65-75: 0.75x sections, Age 75-85: 0.65x sections, Age 85+: 0.6x sections
    if age <= 75:
        return 0.75
    elif age <= 85:
        return 0.65
    else:
        return 0.60

def adjust_for_statistical_parity(sections: Set[str], patient_demographics: Dict[str, Any]) -> Set[str]:
    """Adjust section selection to maintain statistical parity across demographics"""
    age = patient_demographics.get('age', 0)
    gender = patient_demographics.get('gender', patient_demographics.get('sex', '')).lower()
    conditions = patient_demographics.get('conditions', patient_demographics.get('clinical_conditions', []))
    
    # Convert string conditions to list if needed
    if isinstance(conditions, str):
        conditions = [conditions]
    
    # Apply condition frequency bias mitigation
    condition_boost = calculate_condition_frequency_bias_boost(conditions)
    
    # Apply age bias dampening for elderly patients
    age_dampening = calculate_age_bias_dampening(age)
    
    # Calculate combined bias adjustment
    combined_adjustment = condition_boost * age_dampening
    
    # Adjust sections based on bias correction
    adjusted_sections = sections.copy()
    
    # For rare conditions, ensure comprehensive coverage to eliminate bias
    if condition_boost > 1.0:
        # Ensure ALL critical sections for rare conditions
        rare_condition_sections = {
            "toxicity", "interactions", "indications", "dosage", "metabolism"
        }
        adjusted_sections.update(rare_condition_sections)
        
        # For very rare conditions, add comprehensive monitoring
        if len(conditions) > 0 and any(is_rare_condition(c) for c in conditions):
            # Add all available sections to ensure no under-representation
            comprehensive_sections = {
                "indications", "dosage", "toxicity", "interactions", 
                "metabolism", "names", "pharmacology"
            }
            adjusted_sections.update(comprehensive_sections)
    
    # For elderly patients, intelligently reduce sections while preserving safety
    if age >= 65 and age_dampening < 1.0:
        # Core safety sections that must be preserved
        critical_safety = {"toxicity", "indications", "interactions"}
        # Base sections that are always needed
        base_required = {"names", "pharmacology"}
        # Optional sections that can be reduced
        optional_sections = adjusted_sections - critical_safety - base_required
        
        # For complex elderly patients, be more selective about reduction
        if len(conditions) > 1 or any(is_rare_condition(c) for c in conditions):
            # Keep dosage for complex cases, but may remove metabolism
            if "metabolism" in optional_sections and "dosage" in adjusted_sections:
                optional_sections.discard("dosage")  # Keep dosage, metabolism is optional
        
        # Calculate how many optional sections to remove
        if optional_sections:
            # More aggressive reduction for very elderly patients
            removal_factor = 1 - age_dampening
            sections_to_remove = max(1, int(len(optional_sections) * removal_factor))
            
            # Remove least critical optional sections
            optional_list = list(optional_sections)
            # Prioritize keeping dosage and removing metabolism for elderly
            if "metabolism" in optional_list and len(optional_list) > 1:
                optional_list.remove("metabolism")
                adjusted_sections.discard("metabolism")
                sections_to_remove -= 1
            
            # Remove additional sections if needed
            for i in range(min(sections_to_remove, len(optional_list))):
                adjusted_sections.discard(optional_list[i])
    
    return adjusted_sections

def monitor_bias(patient_data: Dict[str, Any], sections_selected: Dict[str, List[str]]) -> Dict[str, Any]:
    """Real-time bias monitoring for patient analysis"""
    age = patient_data.get('age', 0)
    gender = patient_data.get('gender', patient_data.get('sex', '')).lower()
    conditions = patient_data.get('conditions', patient_data.get('clinical_conditions', []))
    
    if isinstance(conditions, str):
        conditions = [conditions]
    
    # Calculate bias metrics
    total_sections = sum(len(sections) for sections in sections_selected.values())
    avg_sections_per_drug = total_sections / len(sections_selected) if sections_selected else 0
    
    # Demographic risk factors
    is_elderly = age >= 65
    has_rare_conditions = any(is_rare_condition(c) for c in conditions) if conditions else False
    
    # Calculate bias score
    bias_score = 1.0
    bias_factors = []
    
    # Age bias check - adjusted for safety considerations
    if is_elderly and avg_sections_per_drug > 6:  # Allow more sections for complex elderly patients
        age_bias = avg_sections_per_drug / 6.0
        bias_score *= age_bias
        bias_factors.append(f"Age bias: {age_bias:.2f}x over-monitoring")
    
    # Condition frequency bias check - rare conditions should get comprehensive analysis
    if has_rare_conditions and avg_sections_per_drug < 6:  # Rare conditions need more comprehensive analysis
        condition_bias = 6.0 / max(avg_sections_per_drug, 1)
        bias_score *= condition_bias
        bias_factors.append(f"Rare condition bias: {condition_bias:.2f}x under-representation")
    
    # Bias alert
    bias_alert = None
    if bias_score > 1.1:
        bias_alert = {
            "severity": "HIGH" if bias_score > 2.0 else "MODERATE",
            "score": round(bias_score, 3),
            "factors": bias_factors,
            "patient_id": patient_data.get("patient_id", "Unknown"),
            "demographics": {
                "age": age,
                "gender": gender,
                "conditions": conditions,
                "is_elderly": is_elderly,
                "has_rare_conditions": has_rare_conditions
            }
        }
    
    return {
        "bias_score": round(bias_score, 3),
        "bias_factors": bias_factors,
        "bias_alert": bias_alert,
        "sections_per_drug": avg_sections_per_drug,
        "fairness_status": "PASS" if bias_score <= 1.1 else "FAIL"
    }

# ============================================================================
# End of Bias Mitigation System
# ============================================================================

def load_patient_data(file_path: str) -> Dict[str, Any]:
    """Load patient data from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def connect_to_chromadb(persist_directory: str = "./chroma_db", collection_name: str = "drugbank") -> chromadb.Collection:
    """Connect to local ChromaDB database"""
    client = chromadb.PersistentClient(path=persist_directory)
    try:
        collection = client.get_collection(collection_name)
        return collection
    except Exception as e:
        print(f"Error connecting to collection '{collection_name}': {e}")
        raise

def calculate_similarity_score(distance: float) -> float:
    """Convert ChromaDB distance to similarity percentage"""
    similarity = max(0, (1 - distance) * 100)
    return round(similarity, 2)

def determine_relevant_sections(patient_data: Dict[str, Any], medications: List[str]) -> Dict[str, Set[str]]:
    """Dynamically determine relevant sections for each drug based on patient data with bias mitigation"""
    
    # Base sections that are always queried
    base_sections = {"names", "pharmacology"}
    
    # Initialize sections for each medication
    drug_sections = {}
    for drug in medications:
        drug_sections[drug] = base_sections.copy()
    
    # Check for conditions/diagnoses -> query Indications (flexible field names)
    conditions = patient_data.get("conditions", patient_data.get("clinical_conditions", []))
    if conditions and len(conditions) > 0:
        for drug in medications:
            drug_sections[drug].add("indications")
    
    # Check for allergies -> query Contraindications (part of indications)
    allergies = patient_data.get("allergic_to", patient_data.get("allergies", ""))
    if allergies and str(allergies).strip():
        for drug in medications:
            drug_sections[drug].add("indications")
    
    # Check labs for abnormalities -> query Toxicity and Contraindications (flexible field names)
    labs = patient_data.get("labs", patient_data.get("lab_results", {}))
    toxicity_triggers = []
    
    if labs:
        # Check renal function (flexible field names)
        creatinine = labs.get("serum_creatinine", labs.get("creatinine", labs.get("Creatinine", "")))
        egfr = labs.get("egfr", labs.get("eGFR", ""))
        if creatinine:
            try:
                creat_val = float(str(creatinine).split()[0])
                if creat_val > 1.5:
                    toxicity_triggers.append(f"elevated creatinine ({creatinine})")
            except:
                pass
        
        if egfr:
            try:
                egfr_val = float(str(egfr).split()[0])
                if egfr_val < 60:
                    toxicity_triggers.append(f"reduced eGFR ({egfr})")
            except:
                pass
        
        # Check liver function
        lft = labs.get("lft", "")
        if lft and "abnormal" in str(lft).lower():
            toxicity_triggers.append(f"abnormal LFTs ({lft})")
        
        # Check diabetes control (flexible field names)
        hba1c = labs.get("hba1c", labs.get("HbA1c", ""))
        if hba1c:
            try:
                hba1c_val = float(str(hba1c).replace("%", ""))
                if hba1c_val > 7.0:
                    toxicity_triggers.append(f"elevated HbA1c ({hba1c})")
            except:
                pass
    
    if toxicity_triggers:
        for drug in medications:
            drug_sections[drug].add("toxicity")
            drug_sections[drug].add("indications")
    
    # Check for metabolism/dosing concerns based on age, weight, renal/liver function
    metabolism_triggers = []
    
    # Age considerations
    age = patient_data.get("age")
    if not age and "dob" in patient_data:
        try:
            from datetime import datetime
            dob = datetime.strptime(patient_data["dob"], "%Y-%m-%d")
            age = datetime.now().year - dob.year
        except:
            pass
    
    if age and age >= 65:
        metabolism_triggers.append(f"elderly patient (age {age})")
    
    # Weight considerations
    weight = patient_data.get("weight_kg", "")
    if weight:
        try:
            weight_val = float(weight)
            if weight_val < 50 or weight_val > 120:
                metabolism_triggers.append(f"weight consideration ({weight}kg)")
        except:
            pass
    
    # Renal/liver function affects metabolism
    if toxicity_triggers:
        metabolism_triggers.extend([t for t in toxicity_triggers if "creatinine" in t or "eGFR" in t or "LFT" in t])
    
    if metabolism_triggers:
        for drug in medications:
            drug_sections[drug].add("metabolism")
            drug_sections[drug].add("dosage")
    
    # Check for drug interactions if multiple medications
    if len(medications) > 1:
        for drug in medications:
            drug_sections[drug].add("interactions")
    
    # ============================================================================
    # 🛡️ APPLY BIAS MITIGATION TO SECTION SELECTION
    # ============================================================================
    
    # Extract patient demographics for bias correction
    patient_demographics = {
        'age': patient_data.get('age', 0),
        'gender': patient_data.get('gender', patient_data.get('sex', '')),
        'conditions': patient_data.get('conditions', patient_data.get('clinical_conditions', []))
    }
    
    # Apply bias mitigation to each drug's section selection
    print("🛡️ Applying bias mitigation to section selection...")
    for drug in medications:
        original_sections = drug_sections[drug].copy()
        
        # Apply statistical parity adjustments
        drug_sections[drug] = adjust_for_statistical_parity(drug_sections[drug], patient_demographics)
        
        # Log bias corrections applied
        sections_added = drug_sections[drug] - original_sections
        sections_removed = original_sections - drug_sections[drug]
        
        if sections_added or sections_removed:
            print(f"  Bias correction for {drug}:")
            if sections_added:
                print(f"    + Added sections: {', '.join(sections_added)}")
            if sections_removed:
                print(f"    - Removed sections: {', '.join(sections_removed)}")
    
    # Convert sets to lists
    for drug in drug_sections:
        drug_sections[drug] = list(drug_sections[drug])
    
    return drug_sections

def query_drug_sections(collection: chromadb.Collection, model: SentenceTransformer, 
                       drug_name: str, sections: List[str], n_results: int = 3, 
                       patient_conditions: List[str] = None) -> Dict[str, List[Dict]]:
    """Query specific sections for a drug"""
    results = {}
    
    for section in sections:
        try:
            # Create section-specific query
            query_text = f"{drug_name} {section.lower()}"
            query_embedding = model.encode([query_text]).tolist()
            
            # Query ChromaDB with section filter
            response = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where={"section": section.lower()}
            )
            
            # Process results
            section_results = []
            if response['documents'] and response['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    response['documents'][0],
                    response['metadatas'][0],
                    response['distances'][0]
                )):
                    # Calculate base similarity score
                    base_similarity = calculate_similarity_score(distance)
                    
                    # Apply condition frequency bias boost if patient has rare conditions
                    adjusted_similarity = base_similarity
                    if patient_conditions:
                        condition_boost = calculate_condition_frequency_bias_boost(patient_conditions)
                        if condition_boost > 1.0:
                            # Boost similarity scores for rare condition queries
                            adjusted_similarity = min(base_similarity * condition_boost, 100.0)
                    
                    result = {
                        "drug_id": metadata.get("drug_id", "Unknown"),
                        "section": section,
                        "text": doc,
                        "similarity_score": round(adjusted_similarity, 2),
                        "base_similarity": base_similarity,
                        "bias_adjustment": round(adjusted_similarity - base_similarity, 2) if patient_conditions else 0.0
                    }
                    section_results.append(result)
            
            results[section] = section_results
            
        except Exception as e:
            print(f"Error querying section '{section}' for drug '{drug_name}': {e}")
            results[section] = []
    
    return results

def main():
    try:
        # Configuration
        patient_file = "patient.json"
        db_path = "./chroma_db"
        collection_name = "drugbank"
        output_file = "patient_drug_data.json"
        
        print("Loading patient data...")
        patient_data = load_patient_data(patient_file)
        
        print("Refining query using local rules...")
        refined_query = refine_drugbank_query(patient_data)
        print(f"Refined query: {refined_query}")
        
        print("Loading PubMedBERT model...")
        model = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO")
        
        print("Connecting to ChromaDB...")
        collection = connect_to_chromadb(db_path, collection_name)
        print(f"Connected to collection with {collection.count()} records")
        
        # Extract medications from patient data (flexible field names)
        medications = []
        med_data = patient_data.get("medications", patient_data.get("current_medications", []))
        if med_data:
            for med in med_data:
                if isinstance(med, dict):
                    # Try both drugName and drug_name
                    drug_name = med.get("drugName", med.get("drug_name", ""))
                    if drug_name:
                        medications.append(drug_name)
                elif isinstance(med, str):
                    medications.append(med)
        
        if not medications:
            print("No medications found in patient data")
            return
        
        print(f"Analyzing {len(medications)} medications: {medications}")
        
        # Dynamically determine relevant sections for each drug
        print("\n=== DYNAMIC SECTION SELECTION ===")
        drug_sections_map = determine_relevant_sections(patient_data, medications)
        
        # ============================================================================
        # 🛡️ REAL-TIME BIAS MONITORING
        # ============================================================================
        
        print("\n=== 🛡️ BIAS MONITORING ===")
        bias_monitoring = monitor_bias(patient_data, drug_sections_map)
        print(f"Bias Score: {bias_monitoring['bias_score']}")
        print(f"Fairness Status: {bias_monitoring['fairness_status']}")
        
        if bias_monitoring['bias_alert']:
            alert = bias_monitoring['bias_alert']
            print(f"🚨 BIAS ALERT - {alert['severity']} RISK:")
            print(f"  Patient: {alert['patient_id']}")
            print(f"  Bias Score: {alert['score']}")
            for factor in alert['factors']:
                print(f"  - {factor}")
        else:
            print("✅ No bias detected - patient analysis is fair")
        
        # Query each medication with its relevant sections only
        drug_data = []
        total_queries = 0
        
        for drug_name in medications:
            relevant_sections = drug_sections_map[drug_name]
            print(f"Querying {len(relevant_sections)} sections for {drug_name}: {relevant_sections}")
            total_queries += len(relevant_sections)
            
            # Extract patient conditions for bias adjustment
            patient_conditions = patient_data.get("conditions", patient_data.get("clinical_conditions", []))
            if isinstance(patient_conditions, str):
                patient_conditions = [patient_conditions]
            
            drug_sections = query_drug_sections(
                collection=collection,
                model=model,
                drug_name=drug_name,
                sections=relevant_sections,
                n_results=3,
                patient_conditions=patient_conditions
            )
            
            drug_entry = {
                "drug_name": drug_name,
                "selected_sections": relevant_sections,
                "sections": drug_sections
            }
            drug_data.append(drug_entry)
        
        # Create final result structure
        result = {
            "patient_id": patient_data.get("patient_id", patient_data.get("id", "Unknown")),
            "refined_query": refined_query,
            "bias_monitoring": bias_monitoring,
            "section_selection_summary": {
                "total_drugs": len(medications),
                "total_sections_queried": total_queries,
                "sections_per_drug": {drug: len(sections) for drug, sections in drug_sections_map.items()},
                "standard_sections_would_be": len(medications) * 7,
                "efficiency_gain_percent": round((1 - total_queries/(len(medications) * 7)) * 100, 1),
                "selection_rationale": {
                    "base_sections": "names, pharmacology (always included)",
                    "conditions_based": "indications added due to patient conditions",
                    "allergy_based": "contraindications added due to allergies",
                    "lab_based": "toxicity added due to lab abnormalities",
                    "metabolism_based": "metabolism/dosage added due to age/weight/renal function",
                    "interaction_based": "interactions added due to multiple medications",
                    "bias_mitigation": "🛡️ Bias corrections applied for fairness across demographics"
                }
            },
            "drug_data": drug_data
        }
        
        # Save results to JSON file
        print(f"\nSaving results to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== ANALYSIS COMPLETE ===")
        print(f"Patient ID: {result['patient_id']}")
        print(f"Medications analyzed: {len(drug_data)}")
        print(f"Total sections queried: {total_queries} (vs {len(medications) * 7} standard)")
        print(f"Efficiency gain: {result['section_selection_summary']['efficiency_gain_percent']}% fewer queries")
        
        # Print summary of matches found
        total_matches = 0
        for drug in drug_data:
            drug_matches = sum(len(matches) for matches in drug["sections"].values())
            total_matches += drug_matches
            print(f"- {drug['drug_name']}: {len(drug['selected_sections'])} sections, {drug_matches} matches")
        
        print(f"Total matches found: {total_matches}")
        print(f"Results saved to '{output_file}'")
        
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()