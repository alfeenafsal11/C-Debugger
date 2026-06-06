import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.compiler.gcc_runner import compile_cpp

def test_compiler_diagnostics():
    print("================ COMPILER DIAGNOSTICS TEST ================")
    
    code = """
int main() {
    int x = "hello";
}
"""
    print(f"\nTEST CODE:\n{code}")
    
    try:
        result = compile_cpp(code)
        
        print("\nCOMPILE RESULT:")
        print(f"Return Code: {result['returncode']}")
        
        if result['returncode'] != 0:
            print("\n[OK] Compilation failed as expected.")
            print("\nSTDERR (Diagnostics):")
            print(result['stderr'])
            
            # GCC/Clang common error patterns for this case
            if "invalid conversion" in result['stderr'].lower() or \
               "cannot convert" in result['stderr'].lower() or \
               "type mismatch" in result['stderr'].lower() or \
               "incompatible types" in result['stderr'].lower():
                print("\n[PASSED] Type mismatch diagnostic detected.")
            else:
                print("\n[WARNING] Compilation failed, but specific type mismatch message not found in stderr.")
        else:
            print("\n[FAILED] Compilation succeeded unexpectedly!")
            
    except FileNotFoundError:
        print("\n[WARNING] g++ not found. Please ensure MinGW/GCC is installed and in your PATH.")
        try:
            import pytest
            pytest.skip("g++ not found. Skipping compiler test.")
        except ImportError:
            sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_compiler_diagnostics()
