"""
Agent 2 -- Static Bug Detector
Finds candidate bug lines in C++ code using rule-based heuristics.
Takes the structured output from Agent 1 (CodeParsingAgent) as input.

Bug categories:
  1. uninitialized_variable    - declared but never assigned before use
  2. out_of_bounds_access      - array index >= declared size
  3. null_pointer_dereference   - dereference of a nullptr
  4. divide_by_zero             - division where divisor could be zero
  5. missing_return             - non-void function without return
  6. infinite_loop              - while(true) / for(;;) with no break
  7. assignment_in_condition    - if(x = 5) instead of if(x == 5)
  8. off_by_one                 - for(i=0; i<=n; i++) with array of size n

Output:
  {
    "bugs": [
      {"line": 4, "type": "uninitialized_variable", "detail": "..."},
      ...
    ],
    "first_bug": {...}  # the first manifesting bug (earliest line)
  }
"""

import re
import json


class StaticBugDetector:
    """Detects candidate bugs from parsed C++ code using heuristics."""

    def detect(self, parsed: dict, source_code: str) -> dict:
        """
        Run all heuristic rules against parsed output + raw source.

        Args:
            parsed: output dict from CodeParsingAgent.parse()
            source_code: the original C++ source string

        Returns:
            dict with "bugs" list and "first_bug"
        """
        lines = source_code.splitlines()
        bugs = []

        bugs.extend(self._check_uninitialized_variables(parsed, lines))
        bugs.extend(self._check_out_of_bounds(parsed, lines))
        bugs.extend(self._check_null_pointer_dereference(parsed, lines))
        bugs.extend(self._check_divide_by_zero(parsed, lines))
        bugs.extend(self._check_missing_return(parsed, lines))
        bugs.extend(self._check_infinite_loops(parsed, lines))
        bugs.extend(self._check_assignment_in_condition(parsed, lines))
        bugs.extend(self._check_off_by_one(parsed, lines))

        # Sort by line number
        bugs.sort(key=lambda b: b["line"])

        return {
            "bugs": bugs,
            "first_bug": bugs[0] if bugs else None,
        }

    def detect_json(self, parsed: dict, source_code: str) -> str:
        """Convenience wrapper returning pretty JSON."""
        return json.dumps(self.detect(parsed, source_code), indent=2)

    # ------------------------------------------------------------------
    # Rule 1: Uninitialized Variables
    # ------------------------------------------------------------------
    def _check_uninitialized_variables(self, parsed, lines):
        """Flag variables declared without initialization that are used later."""
        bugs = []
        for var in parsed.get("variables", []):
            if var["initialized"]:
                continue
            name = var["name"]
            decl_line = var["line"]
            # Scan lines after declaration for usage before assignment
            assigned = False
            for i in range(decl_line, len(lines)):
                line_content = lines[i].strip()
                # Check if variable is assigned on this line (lhs of =)
                assign_pattern = rf'\b{re.escape(name)}\s*='
                compare_pattern = rf'\b{re.escape(name)}\s*=='
                if re.search(assign_pattern, line_content) and not re.search(compare_pattern, line_content):
                    assigned = True
                    break
                # Check if variable is used (read) before being assigned
                if re.search(rf'\b{re.escape(name)}\b', line_content) and i + 1 != decl_line:
                    bugs.append({
                        "line": i + 1,
                        "type": "uninitialized_variable",
                        "detail": f"Variable '{name}' used at line {i + 1} but declared uninitialized at line {decl_line}",
                    })
                    break
        return bugs

    # ------------------------------------------------------------------
    # Rule 2: Out-of-Bounds Access
    # ------------------------------------------------------------------
    def _check_out_of_bounds(self, parsed, lines):
        """Detect array accesses where index >= declared size."""
        bugs = []
        # Find array declarations: int a[5];
        array_sizes = {}
        for i, line in enumerate(lines):
            match = re.search(r'\b(\w+)\s*\[(\d+)\]\s*;', line)
            if match:
                arr_name = match.group(1)
                arr_size = int(match.group(2))
                array_sizes[arr_name] = arr_size

        # Find array accesses: a[10]
        for i, line in enumerate(lines):
            for arr_name, arr_size in array_sizes.items():
                pattern = rf'\b{re.escape(arr_name)}\s*\[(\d+)\]'
                for match in re.finditer(pattern, line):
                    idx = int(match.group(1))
                    if idx >= arr_size:
                        bugs.append({
                            "line": i + 1,
                            "type": "out_of_bounds_access",
                            "detail": f"Array '{arr_name}' has size {arr_size}, but index {idx} used",
                        })
        return bugs

    # ------------------------------------------------------------------
    # Rule 3: Null Pointer Dereference
    # ------------------------------------------------------------------
    def _check_null_pointer_dereference(self, parsed, lines):
        """Detect dereference of a pointer assigned nullptr/NULL/0."""
        bugs = []
        null_ptrs = {}  # name -> declaration line

        for i, line in enumerate(lines):
            stripped = line.strip()
            # Detect pointer declarations assigned to nullptr/NULL/0
            # Handles: int* p = nullptr;  int *p = nullptr;  Type* p = NULL;
            match = re.search(
                r'(?:\w+\s*\*\s*(\w+)|\w+\*\s+(\w+))\s*=\s*(nullptr|NULL|0)\s*;',
                stripped,
            )
            if match:
                ptr_name = match.group(1) or match.group(2)
                null_ptrs[ptr_name] = i + 1

        # Check for dereferences: *p = ... or *p or p->
        for i, line in enumerate(lines):
            stripped = line.strip()
            for ptr_name in list(null_ptrs.keys()):
                decl_line = null_ptrs[ptr_name]
                if i + 1 <= decl_line:
                    continue
                # Check for dereference *p or p-> FIRST
                if re.search(rf'\*\s*{re.escape(ptr_name)}\b', stripped) or \
                   re.search(rf'\b{re.escape(ptr_name)}\s*->', stripped):
                    bugs.append({
                        "line": i + 1,
                        "type": "null_pointer_dereference",
                        "detail": f"Pointer '{ptr_name}' is nullptr (set at line {decl_line}) but dereferenced here",
                    })
                    del null_ptrs[ptr_name]
                    break
                # Check reassignment (not a dereference-write like *p = ...)
                # Only match direct assignment: p = <something>
                if re.search(rf'(?<!\*\s)(?<!\*)\b{re.escape(ptr_name)}\s*=\s*(?!nullptr|NULL|0\b)', stripped):
                    del null_ptrs[ptr_name]
                    break
        return bugs

    # ------------------------------------------------------------------
    # Rule 4: Divide by Zero
    # ------------------------------------------------------------------
    def _check_divide_by_zero(self, parsed, lines):
        """Detect division by a literal 0 or a variable known to be 0."""
        bugs = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Direct division by literal 0:  x / 0  or  x % 0
            if re.search(r'[/\%]\s*0\s*[;\s\)]', stripped):
                bugs.append({
                    "line": i + 1,
                    "type": "divide_by_zero",
                    "detail": "Division or modulo by literal 0",
                })
        return bugs

    # ------------------------------------------------------------------
    # Rule 5: Missing Return
    # ------------------------------------------------------------------
    def _check_missing_return(self, parsed, lines):
        """Detect non-void functions that lack a return statement."""
        bugs = []
        for func in parsed.get("functions", []):
            if func["return_type"] == "void":
                continue
            # Check if there's a return in control_flow within this function's range
            has_return = False
            for cf in parsed.get("control_flow", []):
                if cf["type"] == "return_statement" and \
                   func["start_line"] <= cf["line"] <= func["end_line"]:
                    has_return = True
                    break
            if not has_return:
                bugs.append({
                    "line": func["end_line"],
                    "type": "missing_return",
                    "detail": f"Function '{func['name']}' has return type '{func['return_type']}' but no return statement",
                })
        return bugs

    # ------------------------------------------------------------------
    # Rule 6: Infinite Loops
    # ------------------------------------------------------------------
    def _check_infinite_loops(self, parsed, lines):
        """Detect while(true), while(1), for(;;) without break."""
        bugs = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            is_infinite = False
            if re.search(r'\bwhile\s*\(\s*(true|1)\s*\)', stripped):
                is_infinite = True
            elif re.search(r'\bfor\s*\(\s*;\s*;\s*\)', stripped):
                is_infinite = True

            if is_infinite:
                # Look for a break in the loop body (simple heuristic)
                brace_count = 0
                has_break = False
                for j in range(i, len(lines)):
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if 'break' in lines[j] or 'return' in lines[j]:
                        has_break = True
                        break
                    if brace_count <= 0 and j > i:
                        break
                if not has_break:
                    bugs.append({
                        "line": i + 1,
                        "type": "infinite_loop",
                        "detail": "Loop has no break or return and runs indefinitely",
                    })
        return bugs

    # ------------------------------------------------------------------
    # Rule 7: Assignment in Condition
    # ------------------------------------------------------------------
    def _check_assignment_in_condition(self, parsed, lines):
        """Detect if(x = 5) — single = instead of ==."""
        bugs = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Match if(...) containing single = but not == or != or <= or >=
            match = re.search(r'\bif\s*\((.+)\)', stripped)
            if match:
                condition = match.group(1)
                # Remove all ==, !=, <=, >= first so we don't false-positive
                cleaned = re.sub(r'[!=<>]=', '', condition)
                if re.search(r'[^=!<>]\s*=\s*[^=]', cleaned):
                    bugs.append({
                        "line": i + 1,
                        "type": "assignment_in_condition",
                        "detail": f"Possible assignment instead of comparison in if-condition: '{condition.strip()}'",
                    })
        return bugs

    # ------------------------------------------------------------------
    # Rule 8: Off-by-One in Loops
    # ------------------------------------------------------------------
    def _check_off_by_one(self, parsed, lines):
        """Detect for(i=0; i<=n; i++) when iterating over array of size n."""
        bugs = []
        # Collect array sizes from source
        array_sizes = {}
        for line in lines:
            match = re.search(r'\b(\w+)\s*\[(\d+)\]\s*;', line)
            if match:
                array_sizes[match.group(1)] = int(match.group(2))

        # Also track variables assigned to array sizes: int n = 5;
        size_vars = {}
        for var in parsed.get("variables", []):
            if var["initialized"] and var["type"] == "int":
                # Try to get the value from source
                if var["line"] - 1 < len(lines):
                    src = lines[var["line"] - 1]
                    m = re.search(rf'\b{re.escape(var["name"])}\s*=\s*(\d+)', src)
                    if m:
                        size_vars[var["name"]] = int(m.group(1))

        for i, line in enumerate(lines):
            # Pattern: for(int i = 0; i <= VAR; i++)
            match = re.search(
                r'\bfor\s*\(\s*(?:int\s+)?(\w+)\s*=\s*0\s*;\s*\1\s*<=\s*(\w+)\s*;',
                line,
            )
            if match:
                loop_var = match.group(1)
                bound_var = match.group(2)
                # Check if bound is an array size or a size variable
                flagged = False
                if bound_var in array_sizes:
                    flagged = True
                elif bound_var in size_vars:
                    flagged = True
                # Check if bound is a literal: i <= 5 with arr[5]
                if bound_var.isdigit():
                    bound_val = int(bound_var)
                    for arr_name, arr_size in array_sizes.items():
                        if bound_val >= arr_size:
                            flagged = True
                            break
                if flagged:
                    bugs.append({
                        "line": i + 1,
                        "type": "off_by_one",
                        "detail": f"Loop uses '<=' with bound '{bound_var}'; likely should be '<' to avoid off-by-one",
                    })
        return bugs


# ------------------------------------------------------------------
# Standalone usage
# ------------------------------------------------------------------
if __name__ == "__main__":
    from code_parsing_agent import CodeParsingAgent

    sample = r"""int main() {
    int x;
    int a[5];
    cout << x;
    a[10] = 1;

    int* p = nullptr;
    *p = 10;

    int y = 10 / 0;

    if (x = 5) {
        y = 1;
    }

    while(true) {
    }

    for (int i = 0; i <= 5; i++) {
        a[i] = i;
    }
}
"""
    parser = CodeParsingAgent()
    parsed = parser.parse(sample)

    detector = StaticBugDetector()
    print(detector.detect_json(parsed, sample))
