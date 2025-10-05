"""
Testing Suite for DrugBank Clinical RAG System

This package contains comprehensive test suites for validating the clinical RAG system:
- Comprehensive functionality tests
- Fuzz testing and error injection
- Cross-module consistency validation

Usage:
    python -m testing.test_suite_comprehensive
    python -m testing.fuzz_test_suite  
    python -m testing.consistency_check
"""

__version__ = "1.0.0"
__author__ = "DrugBank RAG Team"

# Import main test functions for easy access
try:
    from .test_suite_comprehensive import main as run_comprehensive_tests
    from .fuzz_test_suite import main as run_fuzz_tests
    from .consistency_check import main as run_consistency_tests
except ImportError:
    # Handle case where modules might not be available
    pass

def run_all_tests():
    """Run all test suites in sequence"""
    print("🧪 Running All Test Suites...")
    
    print("\n1️⃣ Comprehensive Tests...")
    try:
        run_comprehensive_tests()
    except Exception as e:
        print(f"❌ Comprehensive tests failed: {e}")
    
    print("\n2️⃣ Fuzz Tests...")
    try:
        run_fuzz_tests()
    except Exception as e:
        print(f"❌ Fuzz tests failed: {e}")
    
    print("\n3️⃣ Consistency Tests...")
    try:
        run_consistency_tests()
    except Exception as e:
        print(f"❌ Consistency tests failed: {e}")
    
    print("\n✅ All test suites completed!")

if __name__ == "__main__":
    run_all_tests()