import re

def parse_gcc_errors(stderr: str):
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

            diagnostics.append({
                "file": file_path,
                "line": int(line_no),
                "column": int(column_no),
                "severity": severity,
                "message": message.strip()
            })

    return diagnostics
