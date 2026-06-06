"""
Agent 1 — Code Parsing Agent
Converts a C++ code snippet into a structured JSON representation
using libclang (Clang AST).

Output schema:
{
    "lines": [{"line_number": int, "content": str}, ...],
    "variables": [{"name": str, "type": str, "initialized": bool, "line": int}, ...],
    "functions": [{"name": str, "return_type": str, "params": [...], "start_line": int, "end_line": int}, ...],
    "control_flow": [{"type": str, "line": int, "detail": str}, ...]
}
"""

import json
import os
import tempfile
from clang.cindex import Index, CursorKind, Config


class CodeParsingAgent:
    """Parses C++ source code into a structured representation via libclang."""

    # Cursor kinds that represent control-flow statements
    _CONTROL_FLOW_KINDS = {
        CursorKind.IF_STMT: "if_statement",
        CursorKind.FOR_STMT: "for_statement",
        CursorKind.WHILE_STMT: "while_statement",
        CursorKind.DO_STMT: "do_while_statement",
        CursorKind.SWITCH_STMT: "switch_statement",
        CursorKind.RETURN_STMT: "return_statement",
        CursorKind.BREAK_STMT: "break_statement",
        CursorKind.CONTINUE_STMT: "continue_statement",
    }

    def __init__(self):
        self.index = Index.create()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, cpp_code: str) -> dict:
        """Parse a C++ snippet and return a structured dict."""
        tu = self._get_translation_unit(cpp_code)
        root_cursor = tu.cursor

        return {
            "lines": self._extract_lines(cpp_code),
            "variables": self._extract_variables(root_cursor, cpp_code),
            "functions": self._extract_functions(root_cursor, cpp_code),
            "control_flow": self._extract_control_flow(root_cursor, cpp_code),
        }

    def parse_json(self, cpp_code: str) -> str:
        """Convenience wrapper — returns a pretty-printed JSON string."""
        return json.dumps(self.parse(cpp_code), indent=2)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_translation_unit(self, cpp_code: str):
        """Write code to a temp file and parse it with libclang."""
        tmp = tempfile.NamedTemporaryFile(
            suffix=".cpp", delete=False, mode="w", encoding="utf-8"
        )
        try:
            tmp.write(cpp_code)
            tmp.close()
            tu = self.index.parse(tmp.name, args=["-std=c++17"])
            return tu
        finally:
            # Defer removal to allow libclang to read the file
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

    # --- Lines --------------------------------------------------------

    @staticmethod
    def _extract_lines(cpp_code: str) -> list:
        """Split source into numbered line objects."""
        lines = cpp_code.splitlines()
        return [
            {"line_number": i + 1, "content": line}
            for i, line in enumerate(lines)
        ]

    # --- Variables ----------------------------------------------------

    def _extract_variables(self, cursor, cpp_code: str) -> list:
        """Walk AST to find variable declarations."""
        variables = []
        self._walk_variables(cursor, variables, cpp_code)
        return variables

    def _walk_variables(self, cursor, result: list, cpp_code: str):
        # Only consider nodes from the main file (skip headers / builtins)
        if cursor.location.file and not cursor.location.file.name.endswith(".cpp"):
            return

        if cursor.kind == CursorKind.VAR_DECL:
            # A VAR_DECL with children means it has an initializer
            children = list(cursor.get_children())
            has_init = any(
                c.kind not in (CursorKind.ANNOTATE_ATTR,)
                for c in children
            )
            result.append({
                "name": cursor.spelling,
                "type": cursor.type.spelling,
                "initialized": has_init,
                "line": cursor.location.line,
            })

        for child in cursor.get_children():
            self._walk_variables(child, result, cpp_code)

    # --- Functions ----------------------------------------------------

    def _extract_functions(self, cursor, cpp_code: str) -> list:
        """Walk AST to find function declarations / definitions."""
        functions = []
        self._walk_functions(cursor, functions, cpp_code)
        return functions

    def _walk_functions(self, cursor, result: list, cpp_code: str):
        if cursor.location.file and not cursor.location.file.name.endswith(".cpp"):
            return

        if cursor.kind == CursorKind.FUNCTION_DECL:
            params = []
            for child in cursor.get_children():
                if child.kind == CursorKind.PARM_DECL:
                    params.append({
                        "name": child.spelling,
                        "type": child.type.spelling,
                    })
            result.append({
                "name": cursor.spelling,
                "return_type": cursor.result_type.spelling,
                "params": params,
                "start_line": cursor.extent.start.line,
                "end_line": cursor.extent.end.line,
            })

        for child in cursor.get_children():
            self._walk_functions(child, result, cpp_code)

    # --- Control Flow -------------------------------------------------

    def _extract_control_flow(self, cursor, cpp_code: str) -> list:
        """Walk AST to find control-flow statements."""
        flow = []
        self._walk_control_flow(cursor, flow, cpp_code)
        return flow

    def _walk_control_flow(self, cursor, result: list, cpp_code: str):
        if cursor.location.file and not cursor.location.file.name.endswith(".cpp"):
            return

        if cursor.kind in self._CONTROL_FLOW_KINDS:
            detail = self._get_control_flow_detail(cursor, cpp_code)
            result.append({
                "type": self._CONTROL_FLOW_KINDS[cursor.kind],
                "line": cursor.location.line,
                "detail": detail,
            })

        for child in cursor.get_children():
            self._walk_control_flow(child, result, cpp_code)

    @staticmethod
    def _get_control_flow_detail(cursor, cpp_code: str) -> str:
        """Try to extract a human-readable detail from the source for the
        control-flow node (e.g. the condition of an if/while)."""
        children = list(cursor.get_children())
        if not children:
            return ""
        # For if / while / for — the first child is typically the condition
        first = children[0]
        start = first.extent.start
        end = first.extent.end
        lines = cpp_code.splitlines()
        if start.line == end.line and start.line <= len(lines):
            return lines[start.line - 1][start.column - 1 : end.column - 1]
        return ""


# ------------------------------------------------------------------
# Quick standalone usage
# ------------------------------------------------------------------
if __name__ == "__main__":
    sample = r"""
#include <iostream>
using namespace std;

int main() {
    int x;
    int y = 10;
    cout << x;

    if (x > 0) {
        y = x + 1;
    }

    for (int i = 0; i < 10; i++) {
        cout << i;
    }

    return 0;
}
"""
    agent = CodeParsingAgent()
    print(agent.parse_json(sample))
