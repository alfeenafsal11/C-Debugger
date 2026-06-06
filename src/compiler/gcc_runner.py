import subprocess
import tempfile
import os


def compile_cpp(code: str, cleanup_binary: bool = True):
    with tempfile.NamedTemporaryFile(
        suffix=".cpp",
        delete=False,
        mode="w",
        encoding="utf-8"
    ) as f:
        f.write(code)
        temp_path = f.name

    output_exe = temp_path + ".exe"
    try:
        result = subprocess.run(
            ["g++", temp_path, "-std=c++17", "-Wall", "-Wextra", "-o", output_exe],
            capture_output=True,
            text=True
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "binary_path": output_exe if result.returncode == 0 else None
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if cleanup_binary and os.path.exists(output_exe):
            os.remove(output_exe)
