"""
Test suite for the MCP Retrieval Agent (Agent 3).
Requires the MCP server to be running at localhost:8003.
"""

import asyncio
import json
import sys

from src.agents.mcp_retrieval_agent import MCPRetrievalAgent


SERVER_URL = "http://localhost:8003/sse"


async def test_single_bug_type():
    print("\n" + "=" * 60)
    print("  Test 1 - Retrieve doc for 'uninitialized_variable'")
    print("=" * 60)
    agent = MCPRetrievalAgent(SERVER_URL)
    doc = await agent.retrieve_bug_doc("uninitialized_variable")
    print(json.dumps(doc, indent=2, default=str))

    assert doc["bug_type"] == "uninitialized_variable"
    assert doc["name"] == "Uninitialized Variable"
    assert doc["explanation_template"] != ""
    assert isinstance(doc["references"], list)
    print("  [PASSED]")
    return doc


async def test_multiple_bug_types():
    print("\n" + "=" * 60)
    print("  Test 2 - Retrieve docs for multiple bug types")
    print("=" * 60)
    agent = MCPRetrievalAgent(SERVER_URL)
    sample_bugs = [
        {"line": 3, "type": "uninitialized_variable", "detail": "..."},
        {"line": 5, "type": "out_of_bounds_access", "detail": "..."},
        {"line": 7, "type": "divide_by_zero", "detail": "..."},
    ]
    docs = await agent.retrieve_all_bug_docs(sample_bugs)
    print(f"  Retrieved {len(docs)} docs for {len(sample_bugs)} bugs")

    assert len(docs) == 3, f"Expected 3, got {len(docs)}"
    types_retrieved = [d["bug_type"] for d in docs]
    assert "uninitialized_variable" in types_retrieved
    assert "out_of_bounds_access" in types_retrieved
    assert "divide_by_zero" in types_retrieved

    for d in docs:
        print(f"  [{d['bug_type']}] refs={len(d['references'])}")
    print("  [PASSED]")
    return docs


async def test_dedup_bug_types():
    print("\n" + "=" * 60)
    print("  Test 3 - Deduplication of same bug type")
    print("=" * 60)
    agent = MCPRetrievalAgent(SERVER_URL)
    sample_bugs = [
        {"line": 3, "type": "uninitialized_variable", "detail": "x"},
        {"line": 8, "type": "uninitialized_variable", "detail": "y"},
    ]
    docs = await agent.retrieve_all_bug_docs(sample_bugs)
    assert len(docs) == 1, f"Expected 1 (dedup), got {len(docs)}"
    print(f"  Correctly deduplicated: {len(docs)} doc for 2 bugs")
    print("  [PASSED]")


async def test_unknown_bug_type():
    print("\n" + "=" * 60)
    print("  Test 4 - Unknown bug type (graceful fallback)")
    print("=" * 60)
    agent = MCPRetrievalAgent(SERVER_URL)
    doc = await agent.retrieve_bug_doc("some_unknown_bug")
    print(json.dumps(doc, indent=2, default=str))

    assert doc["bug_type"] == "some_unknown_bug"
    assert doc["name"] == "Some Unknown Bug"
    assert doc["explanation_template"] != ""
    print("  [PASSED]")


async def run_all():
    tests = [
        ("Test 1 - Single bug type", test_single_bug_type),
        ("Test 2 - Multiple bug types", test_multiple_bug_types),
        ("Test 3 - Dedup bug types", test_dedup_bug_types),
        ("Test 4 - Unknown bug type", test_unknown_bug_type),
    ]
    passed = 0
    failed = 0
    for name, test in tests:
        try:
            await test()
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
    return failed


if __name__ == "__main__":
    print("=" * 60)
    print("  MCP Retrieval Agent Tests")
    print("  (Requires MCP server running at localhost:8003)")
    print("=" * 60)
    failed = asyncio.run(run_all())
    sys.exit(1 if failed else 0)
