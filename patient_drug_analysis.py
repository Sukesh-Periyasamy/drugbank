import json
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any, Set
import os
from gpt_local import refine_drugbank_query

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
    """Dynamically determine relevant sections for each drug based on patient data"""
    
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
    
    # Convert sets to lists
    for drug in drug_sections:
        drug_sections[drug] = list(drug_sections[drug])
    
    return drug_sections

def query_drug_sections(collection: chromadb.Collection, model: SentenceTransformer, 
                       drug_name: str, sections: List[str], n_results: int = 3) -> Dict[str, List[Dict]]:
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
                    result = {
                        "drug_id": metadata.get("drug_id", "Unknown"),
                        "section": section,
                        "text": doc,
                        "similarity_score": calculate_similarity_score(distance)
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
        
        # Query each medication with its relevant sections only
        drug_data = []
        total_queries = 0
        
        for drug_name in medications:
            relevant_sections = drug_sections_map[drug_name]
            print(f"Querying {len(relevant_sections)} sections for {drug_name}: {relevant_sections}")
            total_queries += len(relevant_sections)
            
            drug_sections = query_drug_sections(
                collection=collection,
                model=model,
                drug_name=drug_name,
                sections=relevant_sections,
                n_results=3
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
                    "interaction_based": "interactions added due to multiple medications"
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