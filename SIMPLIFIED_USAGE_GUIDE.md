# 🏥 DrugBank Clinical Decision Support - Simplified Usage Guide

## Quick Start (2 Files Only!)

The simplified system consists of just **2 main files**:

### Core Files
- **`patient_drug_analysis_single.py`** - Complete standalone analysis script
- **`bias_system.py`** - Comprehensive bias mitigation helper module

### Setup Files  
- **`.env.template`** - Configuration template (copy to `.env`)
- **`SIMPLIFIED_USAGE_GUIDE.md`** - This guide

## Installation

```bash
# Install required packages
pip install chromadb sentence-transformers torch python-dotenv

# Copy environment template
cp .env.template .env

# Edit .env with your API key (optional)
# If no AI API key, system uses heuristic parser
```

## Usage

### Step 1: Prepare Patient Data
Create `patient.json` with patient information:
```json
{
  "age": 65,
  "gender": "Female",
  "conditions": ["diabetes", "hypertension"],
  "medications": ["metformin", "lisinopril"],
  "lab_values": {
    "creatinine": "1.2 mg/dL",
    "HbA1c": "7.2%"
  }
}
```

### Step 2: Run Analysis
```bash
python patient_drug_analysis_single.py
```

### Step 3: View Results
Results saved to `patient_drug_data.json` with:
- ✅ AI-normalized patient data
- ✅ Semantic drug analysis using ChromaDB  
- ✅ Comprehensive bias mitigation (5 strategies)
- ✅ Clinical considerations and recommendations

## System Features

### 🧠 AI Input Normalizer
- Attempts AI API normalization first
- Falls back to robust heuristic parser
- Handles multiple patient data formats

### 💊 Drug Analysis Engine
- Uses existing ChromaDB embeddings (35,991+ records)
- PubMedBERT semantic similarity search
- Clinical context integration

### 🛡️ Bias Mitigation (5 Strategies)
1. **Condition Frequency Bias Correction** - Adjusts for rare/common conditions
2. **Age-Based Bias Dampening** - Pediatric/geriatric considerations  
3. **Statistical Parity Enforcement** - Gender/age equity adjustments
4. **Real-time Bias Monitoring** - Calculates comprehensive bias score
5. **Bias Testing Framework** - Quality assessment and recommendations

## Output Structure

```json
{
  "patient_summary": {
    "age": 65,
    "gender": "Female", 
    "conditions": ["diabetes", "hypertension"],
    "lab_values": {"creatinine": "1.2 mg/dL"}
  },
  "medication_analysis": [
    {
      "drug_name": "metformin",
      "similarity_scores": [92.5, 88.1, 85.7],
      "search_results": [/* ChromaDB matches */],
      "clinical_considerations": [/* Context-aware recommendations */]
    }
  ],
  "bias_mitigation": {
    "status": "completed",
    "strategies_applied": [/* All 5 strategies */],
    "metrics": {
      "bias_score": 1.05,
      "bias_level": "acceptable",
      "total_corrections": 3
    },
    "quality_assessment": {
      "bias_acceptable": true,
      "recommendation": "Continue monitoring"
    }
  }
}
```

## Bias Score Interpretation

- **< 1.05**: Minimal bias ✅
- **1.05-1.1**: Acceptable bias ✅
- **1.1-1.2**: Moderate bias ⚠️
- **> 1.2**: High bias ❌

## Dependencies

- `chromadb` - Vector database
- `sentence-transformers` - PubMedBERT embeddings
- `torch` - Neural network backend
- `python-dotenv` - Environment configuration

## Error Handling

The system includes comprehensive error handling:
- Missing patient.json → Clear error message
- Invalid JSON → Detailed parsing error
- ChromaDB connection issues → Connection diagnostics  
- AI API failures → Automatic fallback to heuristic parser
- Missing bias_system.py → Graceful degradation with warning

## Architecture Benefits

✅ **Single Script** - Everything in one file  
✅ **Modular Bias System** - Separate, reusable bias correction  
✅ **Zero External Dependencies** - Uses existing ChromaDB  
✅ **Comprehensive Logging** - Detailed progress tracking  
✅ **Flexible Input** - Multiple patient data formats  
✅ **Robust Fallbacks** - Continues working even with missing components