"""
Test suite for the Code Parsing Agent.
Parses several C++ snippets and validates the structured output.
"""

import json
import sys

from src.agents.code_parsing_agent import CodeParsingAgent


def _header(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def test_basic_example():
    """User's example: uninitialized variable + cout operation."""
    _header("Test 1 - Basic Example (uninitialized var, cout)")
    code = """int main() {
    int x;
    cout << x;
}
"""
    agent = CodeParsingAgent()
    result = agent.parse(code)
    print(json.dumps(result, indent=2))

    # Assert variable x exists and is uninitialized
    var_names = {v["name"]: v for v in result["variables"]}
    assert "x" in var_names, "Variable 'x' not found"
    assert var_names["x"]["initialized"] is False, "'x' should be uninitialized"
    assert var_names["x"]["type"] == "int", "'x' type should be int"

    # Assert function main is found
    func_names = [f["name"] for f in result["functions"]]
    assert "main" in func_names, "Function 'main' not found"

    # Assert lines are captured
    assert len(result["lines"]) == 4, f"Expected 4 lines, got {len(result['lines'])}"

    print("  [PASSED]")


def test_initialized_variable():
    """Initialized variable detection."""
    _header("Test 2 - Initialized Variable")
    code = """int main() {
    int y = 10;
    return 0;
}
"""
    agent = CodeParsingAgent()
    result = agent.parse(code)
    print(json.dumps(result, indent=2))

    var_names = {v["name"]: v for v in result["variables"]}
    assert "y" in var_names, "Variable 'y' not found"
    assert var_names["y"]["initialized"] is True, "'y' should be initialized"

    print("  [PASSED]")


def test_control_flow():
    """if, for, while, return detection."""
    _header("Test 3 - Control Flow")
    code = """int main() {
    int x = 5;
    if (x > 0) {
        x = x + 1;
    }
    for (int i = 0; i < 10; i++) {
        x = x + i;
    }
    while (x < 100) {
        x = x * 2;
    }
    return 0;
}
"""
    agent = CodeParsingAgent()
    result = agent.parse(code)
    print(json.dumps(result, indent=2))

    cf_types = [c["type"] for c in result["control_flow"]]
    assert "if_statement" in cf_types, "if_statement not detected"
    assert "for_statement" in cf_types, "for_statement not detected"
    assert "while_statement" in cf_types, "while_statement not detected"
    assert "return_statement" in cf_types, "return_statement not detected"

    print("  [PASSED]")


def test_multiple_functions():
    """Multiple function detection."""
    _header("Test 4 - Multiple Functions")
    code = """int add(int a, int b) {
    return a + b;
}

void greet() {
    return;
}

int main() {
    int result = add(1, 2);
    greet();
    return 0;
}
"""
    agent = CodeParsingAgent()
    result = agent.parse(code)
    print(json.dumps(result, indent=2))

    func_names = [f["name"] for f in result["functions"]]
    assert "add" in func_names, "Function 'add' not found"
    assert "greet" in func_names, "Function 'greet' not found"
    assert "main" in func_names, "Function 'main' not found"

    # Check params of add
    add_func = next(f for f in result["functions"] if f["name"] == "add")
    assert len(add_func["params"]) == 2, f"Expected 2 params, got {len(add_func['params'])}"
    assert add_func["return_type"] == "int", "add() return type should be int"

    print("  [PASSED]")


# ------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_basic_example,
        test_initialized_variable,
        test_control_flow,
        test_multiple_functions,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  [FAILED]: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR]: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed out of {len(tests)}")
    print(f"{'=' * 60}")
    sys.exit(1 if failed else 0)
