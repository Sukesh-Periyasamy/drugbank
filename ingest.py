"""
Script to load JSON data and store into ChromaDB vector database
with semantic/section-based chunking for medical data
"""
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import os
import numpy as np

def load_json_data(file_path):
    """Load JSON data from file"""
    print(f"Loading JSON data from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def extract_text_from_dict(data):
    """Extract text from nested dictionary structures"""
    if isinstance(data, str):
        return data
    elif isinstance(data, dict):
        if '#text' in data:
            return data['#text']
        elif 'value' in data:
            return data['value']
        else:
            # Extract text from all string values
            texts = []
            for v in data.values():
                if isinstance(v, str):
                    texts.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            texts.append(item)
                        elif isinstance(item, dict) and '#text' in item:
                            texts.append(item['#text'])
            return " | ".join(texts[:5])  # Limit to avoid too long text
    elif isinstance(data, list):
        texts = []
        for item in data:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict) and '#text' in item:
                texts.append(item['#text'])
            elif isinstance(item, dict):
                text = extract_text_from_dict(item)
                if text:
                    texts.append(text)
        return " | ".join(texts[:5])
    return ""

def chunk_drug_entry(drug_entry):
    """
    Section-based chunking for DrugBank entries.
    Creates semantic chunks that preserve medical context.
    """
    chunks = []
    
    # Handle non-dictionary entries
    if not isinstance(drug_entry, dict):
        return []
    
    # Get drug identifier (DrugBank uses 'drugbank-id' as a list)
    drug_id_raw = drug_entry.get("drugbank-id", [])
    if isinstance(drug_id_raw, list) and len(drug_id_raw) > 0:
        # Primary ID is usually the first one with @primary=true
        for id_item in drug_id_raw:
            if isinstance(id_item, dict) and id_item.get('@primary') == 'true':
                drug_id = id_item.get('#text', 'Unknown')
                break
            elif isinstance(id_item, str):
                drug_id = id_item
                break
        else:
            drug_id = drug_id_raw[0] if drug_id_raw else "Unknown Drug"
    else:
        drug_id = "Unknown Drug"
    
    drug_name = drug_entry.get("name", drug_id)
    
    # Define semantic sections for medical data
    sections = {}
    
    # Drug names and identifiers section
    synonyms_data = drug_entry.get("synonyms", {})
    synonyms = []
    if isinstance(synonyms_data, dict) and 'synonym' in synonyms_data:
        syn_list = synonyms_data['synonym']
        if isinstance(syn_list, list):
            synonyms = [s.get('#text', s) if isinstance(s, dict) else s for s in syn_list[:5]]
        elif isinstance(syn_list, dict):
            synonyms = [syn_list.get('#text', str(syn_list))]
    
    names_text = f"Drug: {drug_name}"
    if synonyms:
        names_text += f", Synonyms: {', '.join(synonyms)}"
    if drug_id != drug_name:
        names_text += f", ID: {drug_id}"
    sections["names"] = names_text
    
    # Indications and contraindications
    indication = drug_entry.get("indication", "")
    contraindications = drug_entry.get("contraindications", "")
    if indication or contraindications:
        indications_text = ""
        if indication:
            indications_text += f"Indications: {indication}"
        if contraindications:
            if indications_text:
                indications_text += " | "
            indications_text += f"Contraindications: {contraindications}"
        sections["indications"] = indications_text
    
    # Pharmacology and mechanism
    pharmacology = drug_entry.get("pharmacodynamics", "")
    mechanism = drug_entry.get("mechanism-of-action", "")
    if pharmacology or mechanism:
        pharm_text = ""
        if mechanism:
            pharm_text += f"Mechanism of Action: {mechanism}"
        if pharmacology:
            if pharm_text:
                pharm_text += " | "
            pharm_text += f"Pharmacodynamics: {pharmacology}"
        sections["pharmacology"] = pharm_text
    
    # Toxicity
    toxicity = drug_entry.get("toxicity", "")
    if toxicity:
        sections["toxicity"] = f"Toxicity: {toxicity}"
    
    # Metabolism and pharmacokinetics
    metabolism = drug_entry.get("metabolism", "")
    absorption = drug_entry.get("absorption", "")
    half_life = drug_entry.get("half-life", "")
    clearance = drug_entry.get("clearance", "")
    protein_binding = drug_entry.get("protein-binding", "")
    
    met_parts = []
    if absorption:
        met_parts.append(f"Absorption: {absorption}")
    if metabolism:
        met_parts.append(f"Metabolism: {metabolism}")
    if half_life:
        met_parts.append(f"Half-life: {half_life}")
    if clearance:
        met_parts.append(f"Clearance: {clearance}")
    if protein_binding:
        met_parts.append(f"Protein Binding: {protein_binding}")
    
    if met_parts:
        sections["metabolism"] = " | ".join(met_parts)
    
    # Drug interactions
    interactions_data = drug_entry.get("drug-interactions", {})
    if interactions_data:
        interaction_texts = []
        if isinstance(interactions_data, dict) and 'drug-interaction' in interactions_data:
            interactions = interactions_data['drug-interaction']
            if isinstance(interactions, list):
                for interaction in interactions[:10]:  # Limit to first 10
                    if isinstance(interaction, dict):
                        drug = interaction.get("name", "")
                        desc = interaction.get("description", "")
                        if drug:
                            interaction_texts.append(f"{drug}: {desc}" if desc else drug)
            elif isinstance(interactions, dict):
                drug = interactions.get("name", "")
                desc = interactions.get("description", "")
                if drug:
                    interaction_texts.append(f"{drug}: {desc}" if desc else drug)
        
        if interaction_texts:
            sections["interactions"] = f"Drug Interactions: {' | '.join(interaction_texts)}"
    
    # Dosage information
    dosages_data = drug_entry.get("dosages", {})
    if dosages_data:
        dosage_text = extract_text_from_dict(dosages_data)
        if dosage_text:
            sections["dosage"] = f"Dosage: {dosage_text}"
    
    # Create chunks from sections
    for section_name, text in sections.items():
        if text and len(text.strip()) > 20:  # Skip empty or very short sections
            chunks.append({
                "drug_id": drug_id,
                "drug_name": drug_name,
                "section": section_name,
                "text": text.strip()
            })
    
    return chunks

def create_vector_database(data, collection_name="drugbank", persist_directory="./chroma_db"):
    """Create ChromaDB vector database from JSON data"""
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=persist_directory)
    
    # Create or get collection
    try:
        collection = client.get_collection(collection_name)
        print(f"Collection '{collection_name}' already exists. Deleting and recreating...")
        client.delete_collection(collection_name)
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Initialize PubMedBERT model for biomedical domain
    print("Loading PubMedBERT model for biomedical embeddings...")
    model = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO")
    
    # Process data in batches
    batch_size = 100
    documents = []
    metadatas = []
    ids = []
    
    # Handle different JSON structures
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # DrugBank specific structure
        if 'drugbank' in data and 'drug' in data['drugbank']:
            items = data['drugbank']['drug']
        # Generic fallbacks
        elif 'drugs' in data:
            items = data['drugs']
        elif 'drugbank' in data:
            items = data['drugbank'] if isinstance(data['drugbank'], list) else [data['drugbank']]
        else:
            # Take the first large list/dict found
            items = next((v for v in data.values() if isinstance(v, list) and len(v) > 10), [data])
    else:
        items = [data]
    
    print(f"Processing {len(items)} items...")
    
    chunk_id = 0
    for i, item in enumerate(tqdm(items, desc="Processing records")):
        # Create semantic chunks from drug entry
        chunks = chunk_drug_entry(item)
        
        for chunk in chunks:
            text = chunk["text"]
            
            if text.strip():  # Only process non-empty texts
                documents.append(text)
                
                # Create detailed metadata for medical data
                metadata = {
                    "record_id": i,
                    "chunk_id": chunk_id,
                    "drug_id": chunk["drug_id"],
                    "drug_name": chunk["drug_name"],
                    "section": chunk["section"],
                    "text_length": len(text),
                    "chunk_type": "semantic_section"
                }
                
                metadatas.append(metadata)
                ids.append(f"chunk_{chunk_id}")
                chunk_id += 1
                
                # Process in batches
                if len(documents) >= batch_size:
                    # Generate embeddings
                    embeddings = model.encode(documents).tolist()
                    
                    # Add to collection
                    collection.add(
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    
                    # Reset batch
                    documents = []
                    metadatas = []
                    ids = []
    
    # Process remaining items
    if documents:
        embeddings = model.encode(documents).tolist()
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    print(f"Successfully created vector database with {collection.count()} records")
    return collection

def main():
    # Configuration
    json_file_path = "drugbank.json"
    collection_name = "drugbank"
    persist_directory = "./chroma_db"
    
    # Check if JSON file exists
    if not os.path.exists(json_file_path):
        print(f"Error: {json_file_path} not found!")
        return
    
    try:
        # Load JSON data
        data = load_json_data(json_file_path)
        
        # Create vector database
        collection = create_vector_database(
            data, 
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        
        print(f"Vector database created successfully!")
        print(f"Collection: {collection_name}")
        print(f"Records: {collection.count()}")
        print(f"Stored in: {persist_directory}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()