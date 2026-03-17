"""
Test suite for the Static Bug Detector (Agent 2).
Tests each of the 8 heuristic rules individually.
"""

import json
import sys

from code_parsing_agent import CodeParsingAgent
from static_bug_detector import StaticBugDetector


def _header(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _run(code):
    """Parse + detect in one step."""
    parser = CodeParsingAgent()
    detector = StaticBugDetector()
    parsed = parser.parse(code)
    result = detector.detect(parsed, code)
    print(json.dumps(result, indent=2))
    return result


def test_uninitialized_variable():
    _header("Test 1 - Uninitialized Variable")
    code = """int main() {
    int x;
    cout << x;
}
"""
    result = _run(code)
    types = [b["type"] for b in result["bugs"]]
    assert "uninitialized_variable" in types, "Should detect uninitialized variable"
    print("  [PASSED]")


def test_out_of_bounds():
    _header("Test 2 - Out of Bounds Access")
    code = """int main() {
    int a[5];
    a[10] = 1;
}
"""
    result = _run(code)
    types = [b["type"] for b in result["bugs"]]
    assert "out_of_bounds_access" in types, "Should detect out-of-bounds"
    print("  [PASSED]")


def test_null_pointer_dereference():
    _header("Test 3 - Null Pointer Dereference")
    code = """int main() {
    int* p = nullptr;
    *p = 10;
}
"""
    result = _run(code)
    types = [b["type"] for b in result["bugs"]]
    assert "null_pointer_dereference" in types, "Should detect null deref"
    print("  [PASSED]")


def test_divide_by_zero():
    _header("Test 4 - Divide by Zero")
    code = """int main() {
    int x = 10 / 0;
}
"""
    result = _run(code)
    types = [b["type"] for b in result["bugs"]]
    assert "divide_by_zero" in types, "Should detect divide by zero"
    print("  [PASSED]")


def test_missing_return():
    _header("Test 5 - Missing Return")
    code = """int f() {
    int x = 5;
}
"""
    result = _run(code)
    types = [b["type"] for b in result["bugs"]]
    assert "missing_return" in types, "Should detect missing return"
    print("  [PASSED]")


def test_infinite_loop():
    _header("Test 6 - Infinite Loop")
    code = """int main() {
    while(true) {
    }
    return 0;
}
"""
    result = _run(code)
    types = [b["type"] for b in result["bugs"]]
    assert "infinite_loop" in types, "Should detect infinite loop"
    print("  [PASSED]")


def test_assignment_in_condition():
    _header("Test 7 - Assignment in Condition")
    code = """int main() {
    int x = 5;
    if (x = 5) {
        x = 10;
    }
    return 0;
}
"""
    result = _run(code)
    types = [b["type"] for b in result["bugs"]]
    assert "assignment_in_condition" in types, "Should detect assignment in if"
    print("  [PASSED]")


def test_off_by_one():
    _header("Test 8 - Off-by-One Loop")
    code = """int main() {
    int n = 10;
    int a[10];
    for (int i = 0; i <= n; i++) {
        a[i] = i;
    }
    return 0;
}
"""
    result = _run(code)
    types = [b["type"] for b in result["bugs"]]
    assert "off_by_one" in types, "Should detect off-by-one"
    print("  [PASSED]")


def test_combined():
    _header("Test 9 - Combined (multiple bugs)")
    code = """int main() {
    int x;
    int a[5];
    cout << x;
    a[10] = 1;
    int* p = nullptr;
    *p = 10;
    if (x = 5) {
        x = 1;
    }
}
"""
    result = _run(code)
    types = [b["type"] for b in result["bugs"]]
    assert len(result["bugs"]) >= 4, f"Expected at least 4 bugs, got {len(result['bugs'])}"
    assert result["first_bug"] is not None, "first_bug should not be None"
    print(f"  first_bug: line {result['first_bug']['line']} - {result['first_bug']['type']}")
    print("  [PASSED]")


if __name__ == "__main__":
    tests = [
        test_uninitialized_variable,
        test_out_of_bounds,
        test_null_pointer_dereference,
        test_divide_by_zero,
        test_missing_return,
        test_infinite_loop,
        test_assignment_in_condition,
        test_off_by_one,
        test_combined,
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
            print(f"  [ERROR]: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed out of {len(tests)}")
    print(f"{'=' * 60}")
    sys.exit(1 if failed else 0)
