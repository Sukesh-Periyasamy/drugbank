# Testing Suite for DrugBank Clinical RAG System

This directory contains comprehensive test suites to validate the robustness, consistency, and reliability of the clinical RAG system.

## Test Files Overview

### 🧪 Core Test Suites

#### `test_suite_comprehensive.py`
**Purpose:** Basic functionality testing across different patient scenarios
- Simple/low-risk patients (single drug, normal labs)
- Polypharmacy patients (3-4 drugs, no organ dysfunction)
- High-risk patients (elderly, CKD, hepatic impairment, anticoagulants)
- Edge cases (no medications, malformed data)
- Fake drugs (semantic fallback testing)

**Usage:**
```bash
cd testing
python test_suite_comprehensive.py
```

#### `fuzz_test_suite.py`
**Purpose:** Advanced error injection and stress testing
- Random field deletion/renaming
- Data corruption with special characters
- Missing critical fields
- Invalid data types
- Boundary value testing
- Graceful failure validation

**Usage:**
```bash
cd testing
python fuzz_test_suite.py
```

#### `consistency_check.py`
**Purpose:** Cross-module consistency validation
- Ensures parser, analyzer, and summarizer interpret data identically
- Validates medication counts across all modules
- Checks field name flexibility consistency
- Tests data structure normalization

**Usage:**
```bash
cd testing
python consistency_check.py
```

#### `clinical_reasoning_tests.py`
**Purpose:** AI reasoning consistency validation across clinical thresholds
- Tests clinical decision-making consistency when inputs vary slightly
- Validates medical threshold behavior (age 65, eGFR 60, etc.)
- Ensures appropriate clinical reasoning triggers
- Tests combined parameter threshold interactions

**Key Thresholds Tested:**
- Age 64 vs 65 (elderly classification)
- eGFR 61 vs 59 mL/min/1.73m² (renal impairment)
- Creatinine, HbA1c, weight thresholds
- Combined risk factor scenarios

**Usage:**
```bash
cd testing
python clinical_reasoning_tests.py
```

#### `threshold_validation.py`
**Purpose:** Detailed clinical threshold behavior validation
- Precision testing of medical decision boundaries
- Validates expected vs actual threshold crossing behavior
- Tests both individual and combined threshold effects
- Includes no-change validation for stable scenarios

**Usage:**
```bash
cd testing
python threshold_validation.py
```

#### `comprehensive_reasoning_tests.py`
**Purpose:** Master test suite for all reasoning consistency tests
- Combines clinical reasoning and threshold validation
- Provides comprehensive accuracy metrics and clinical assessment
- Production readiness evaluation
- Overall system validation for clinical decision support

**Usage:**
```bash
cd testing
python comprehensive_reasoning_tests.py
```

## Test Results

### 📊 Result Files

- `test_results.json` - Comprehensive test suite results
- `fuzz_test_results.json` - Error injection test results  
- `consistency_test_results.json` - Cross-module consistency results
- `clinical_reasoning_test_results.json` - AI reasoning consistency results
- `threshold_validation_results.json` - Clinical threshold validation results
- `comprehensive_reasoning_test_results.json` - Complete reasoning test summary
- `threshold_diagnostic_results.json` - Diagnostic analysis of threshold behavior

### 🎯 Expected Outcomes

#### Comprehensive Tests
- **Target:** 100% pass rate across all patient scenarios
- **Validates:** Smart section selection, efficiency calculations, semantic search

#### Fuzz Tests
- **Target:** Graceful failure handling, no system crashes
- **Validates:** Input validation, error handling, robustness

#### Consistency Tests
- **Target:** 100% cross-module consistency
- **Validates:** Data interpretation uniformity across all components

## Test Categories

### 1. **Simple/Low-risk Patients**
- Single medication
- Normal lab values
- Expected: High efficiency (60-70% fewer queries)
- Sections: Names + Pharmacology only

### 2. **Polypharmacy (Medium Risk)**
- 3-4 medications
- No organ dysfunction
- Expected: Medium efficiency (40-50% fewer queries)
- Sections: + Interactions + Indications

### 3. **High-risk (Complex)**
- Elderly patients
- Organ impairment (CKD/liver)
- Anticoagulants
- Expected: Full analysis (0% efficiency gain)
- Sections: All 7 sections

### 4. **Edge Cases**
- No medications → Graceful "No medications found"
- Malformed JSON → Clear error messages
- Fake drugs → Semantic similarity matching

### 5. **Error Injection**
- Field corruption
- Missing data
- Invalid types
- Special characters
- Expected: No crashes, informative errors

## Running All Tests

### Quick Test Suite
```bash
# From main directory
cd testing
python test_suite_comprehensive.py
```

### Full Validation
```bash
# Run all test suites
cd testing
python test_suite_comprehensive.py
python fuzz_test_suite.py  
python consistency_check.py
```

### Automated Testing
```bash
# From main directory
python -m testing.test_suite_comprehensive
python -m testing.fuzz_test_suite
python -m testing.consistency_check
```

## Test Development Guidelines

### Adding New Tests
1. **Create test patient data** in appropriate category
2. **Define expected outcomes** (efficiency %, sections, matches)
3. **Add to appropriate test suite**
4. **Update this README** with new test description

### Test Data Format
```json
{
  "patient_id": "TEST_ID",
  "name": "Test Patient Name",
  "age": 50,
  "current_medications": [
    {"drug_name": "DrugName", "dose": "10mg"}
  ],
  "clinical_conditions": ["Condition1"],
  "allergies": ["Allergy1"]
}
```

### Expected Results Format
```python
expected = {
    "medications_count": 1,
    "sections_per_drug": 3,
    "efficiency_gain": "57.1% fewer queries",
    "total_matches": "> 0"
}
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Test Suite
  run: |
    cd testing
    python test_suite_comprehensive.py
    python consistency_check.py
```

### Local Development
```bash
# Before committing
cd testing && python *.py
```

## Troubleshooting

### Common Issues
1. **ChromaDB connection errors** → Ensure chroma_db/ exists
2. **Model loading failures** → Check internet connection for PubMedBERT
3. **JSON parsing errors** → Validate test data format
4. **Import errors** → Run from correct directory

### Debug Mode
```python
# Add to any test file for detailed output
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📈 Test Metrics

- **Total Test Cases:** 50+
- **Coverage:** Parser, Analyzer, Query Refinement, Output Generation
- **Scenarios:** Simple → Complex → Edge Cases → Error Injection
- **Success Rate Target:** 100% for comprehensive tests
- **Consistency Target:** 100% cross-module agreement

**All tests validate production readiness and enterprise-grade reliability.**