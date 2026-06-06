import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.compiler.gcc_runner import compile_cpp
from src.compiler.error_parser import parse_gcc_errors

def main():
    print("================ STRUCTURED DIAGNOSTIC PARSER TEST ================")
    
    code = r'''
int main() {
    int x = "hello";
}
'''
    print(f"\nTEST CODE:\n{code}")

    try:
        result = compile_cpp(code)

        print("\nRAW STDERR:\n")
        if result["stderr"]:
            print(result["stderr"])
        else:
            print("[EMPTY]")

        diagnostics = parse_gcc_errors(result["stderr"])

        print("\nPARSED DIAGNOSTICS:\n")
        if diagnostics:
            for diag in diagnostics:
                print(diag)
        else:
            print("[NONE FOUND]")
            
    except FileNotFoundError:
        print("\n[ERROR] g++ not found. Testing with mock stderr instead...\n")
        
        mock_stderr = """
test.cpp:3:17: error: invalid conversion from 'const char*' to 'int' [-fpermissive]
test.cpp:5:10: warning: unused variable 'y' [-Wunused-variable]
"""
        print(f"MOCK STDERR:\n{mock_stderr}")
        diagnostics = parse_gcc_errors(mock_stderr)
        
        print("\nPARSED DIAGNOSTICS (MOCK):\n")
        for diag in diagnostics:
            print(diag)

if __name__ == "__main__":
    main()
