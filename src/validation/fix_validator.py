import os
from ..compiler.gcc_runner import compile_cpp
from ..compiler.error_parser import parse_gcc_errors
from ..compiler.runtime_executor import execute_binary

class FixValidator:
    """ Validates a suggested code fix by comparing compilation and execution results. """

    def validate_fix(self, original_code: str, fixed_code: str) -> dict:
        """
        Performs end-to-end validation of a fix.
        
        Returns:
            dict: Validation results according to the recommended schema.
        """
        # 1. Baseline (Original Code)
        baseline_compile = compile_cpp(original_code, cleanup_binary=False)
        baseline_errors = parse_gcc_errors(baseline_compile["stderr"])
        baseline_run = None
        
        if baseline_compile["binary_path"]:
            baseline_run = execute_binary(baseline_compile["binary_path"])
            # Cleanup baseline binary
            if os.path.exists(baseline_compile["binary_path"]):
                os.remove(baseline_compile["binary_path"])

        # 2. Validation (Fixed Code)
        fixed_compile = compile_cpp(fixed_code, cleanup_binary=False)
        fixed_errors = parse_gcc_errors(fixed_compile["stderr"])
        fixed_run = None
        
        compile_success = fixed_compile["returncode"] == 0
        runtime_success = False
        execution_output = ""

        if fixed_compile["binary_path"]:
            fixed_run = execute_binary(fixed_compile["binary_path"])
            runtime_success = fixed_run.get("returncode") == 0
            execution_output = fixed_run.get("stdout", "")
            # Cleanup fixed binary
            if os.path.exists(fixed_compile["binary_path"]):
                os.remove(fixed_compile["binary_path"])

        # 3. Success Determination
        # A fix is considered validated if:
        # - It compiles successfully (if the original didn't, or if the original had errors)
        # - It reduces the number of error/warning diagnostics
        # - It fixes a runtime crash (if the original crashed)
        
        error_reduction = len([e for e in fixed_errors if e["severity"] == "error"]) < \
                         len([e for e in baseline_errors if e["severity"] == "error"])
        
        # If both compile, check if runtime behavior improved
        runtime_improvement = False
        if baseline_run and fixed_run:
            if baseline_run.get("returncode") != 0 and fixed_run.get("returncode") == 0:
                runtime_improvement = True

        validated = compile_success and (error_reduction or runtime_improvement or (not baseline_compile["binary_path"] and compile_success))

        return {
            "compile_success": compile_success,
            "runtime_success": runtime_success,
            "diagnostics_remaining": fixed_errors,
            "execution_output": execution_output,
            "validated": validated,
            "comparison": {
                "errors_reduced": error_reduction,
                "runtime_improved": runtime_improvement,
                "baseline_diagnostics": baseline_errors
            }
        }
