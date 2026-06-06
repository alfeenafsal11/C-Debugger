import subprocess
import os
import tempfile
import time

def execute_binary(binary_path: str, timeout: int = 5):
    """
    Executes a binary and captures its output and behavior.
    
    Returns:
        dict: {
            "stdout": str,
            "stderr": str,
            "returncode": int,
            "timeout": bool,
            "error": str
        }
    """
    if not os.path.exists(binary_path):
        return {"error": f"Binary not found: {binary_path}"}

    try:
        start_time = time.time()
        result = subprocess.run(
            [binary_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duration = time.time() - start_time
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "timeout": False,
            "duration": duration
        }
    except subprocess.TimeoutExpired:
        return {
            "error": "Execution timed out",
            "timeout": True,
            "returncode": -1
        }
    except Exception as e:
        return {
            "error": str(e),
            "returncode": -1
        }
