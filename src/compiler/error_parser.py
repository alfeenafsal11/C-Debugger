import re

SYSTEM_HEADER_PATTERNS = ("/usr/include", "/usr/lib", "include/c++", "bits/", "/usr/local/include")

def parse_gcc_errors(stderr: str, filter_system_headers: bool = True):
    """
    Parses GCC/Clang stderr output into structured diagnostic dictionaries.
    
    Format expected: file:line:col: severity: message
    """
    diagnostics = []

    pattern = re.compile(
        r"((?:[a-zA-Z]:)?[^:]+):(\d+):(\d+):\s+(warning|error|note):\s+(.*)",
        re.MULTILINE
    )

    for line in stderr.splitlines():
        match = pattern.match(line)
        if match:
            file_path, line_no, column_no, severity, message = match.groups()

            # Skip diagnostics originating from internal C++ system headers
            if filter_system_headers and any(sys_pat in file_path.replace("\\", "/") for sys_pat in SYSTEM_HEADER_PATTERNS):
                continue

            diagnostics.append({
                "file": file_path,
                "line": int(line_no),
                "column": int(column_no),
                "severity": severity,
                "message": message.strip()
            })

    return diagnostics
