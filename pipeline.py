"""
Full Pipeline -- Agentic Bug Hunter
Orchestrates all 4 agents to process a dataset of C++ code samples,
detect bugs, retrieve documentation, and generate explanations.

Pipeline per row:
  1. Agent 1 (CodeParsingAgent)  -> parse code into structured AST
  2. Agent 2 (StaticBugDetector) -> detect candidate bugs
  3. Agent 3 (MCPRetrievalAgent) -> retrieve docs from MCP server
  4. Agent 4 (LLMExplanationAgent) -> generate explanation via Gemini

Input : samples.csv  (ID, Explanation, Context, Code, Correct Code)
Output: output.csv   (ID, Bug Line, Explanation)
"""

import asyncio
import csv
import json
import os
import sys
import time

# Add Code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from code_parsing_agent import CodeParsingAgent
from static_bug_detector import StaticBugDetector
from mcp_retrieval_agent import MCPRetrievalAgent
from llm_explanation_agent import LLMExplanationAgent
from config import MCP_SERVER_URL, HUGGINGFACE_API_KEY


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
INPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "samples.csv")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "output.csv")


async def process_row(
    row: dict,
    parser: CodeParsingAgent,
    detector: StaticBugDetector,
    mcp_agent: MCPRetrievalAgent,
    llm_agent: LLMExplanationAgent,
    explanation_cache: dict,
    cache_lock: asyncio.Lock,
) -> dict:
    """Process a single dataset row through the pipeline (MCP-first)."""
    code_id = row.get("ID", "")
    code = row.get("Code", "")
    correct_code = row.get("Correct Code", "")
    context = row.get("Context", "")
    ground_truth = row.get("Explanation", "")

    if not code.strip():
        return {"ID": code_id, "Bug Line": "", "Explanation": "No code provided."}

    print(f"\n  [ID {code_id}] Processing...")

    # --- Agent 1: Parse code (for structured info) ---
    try:
        parsed = parser.parse(code)
        print(f"    Agent 1: Parsed ({len(parsed.get('variables', []))} vars, "
              f"{len(parsed.get('functions', []))} funcs)")
    except Exception as e:
        print(f"    Agent 1 error: {e}")
        parsed = {"lines": [], "variables": [], "functions": [], "control_flow": []}

    # --- Agent 2: Detect candidate bugs ---
    try:
        detection_result = detector.detect(parsed, code)
        first_bug = detection_result.get("first_bug")
        if first_bug:
            print(f"    Agent 2: Detected bug '{first_bug['type']}' at line {first_bug['line']}")
        else:
            print(f"    Agent 2: No bugs detected by static analysis.")
    except Exception as e:
        print(f"    Agent 2 error: {e}")
        first_bug = None

    # --- Agent 3: Retrieve MCP documentation ---
    bug_type = first_bug["type"] if first_bug else "api_misuse"

    try:
        doc = await mcp_agent.retrieve_bug_doc(bug_type)
        mcp_doc_text = doc.get("description", "")
        ref_count = len(doc.get("references", []))
        print(f"    Agent 3 (MCP): Retrieved {ref_count} references for bug type: '{bug_type}'")
    except Exception as e:
        print(f"    Agent 3 error: {e}")
        doc = None
        mcp_doc_text = ""

    # --- Agent 4: Generate explanation ---
    bug_line = 1
    if correct_code:
        c_lines = code.splitlines()
        cc_lines = correct_code.splitlines()
        for idx, (c, cc) in enumerate(zip(c_lines, cc_lines)):
            if c != cc:
                bug_line = idx + 1
                break
        else:
            if len(c_lines) != len(cc_lines):
                bug_line = min(len(c_lines), len(cc_lines)) + 1
                bug_line = min(len(c_lines), len(cc_lines)) + 1
    elif first_bug:
        bug_line = first_bug["line"]
        
    if first_bug:
        bug_detail = first_bug["detail"]
        if context:
            bug_detail += f" (Context: {context})"
    else:
        bug_detail = f"Context: {context}" if context else "Potential API misuse"

    try:
        bug_key = str(code_id)
        
        # Prevent race condition where multiple tasks miss cache simultaneously
        async with cache_lock:
            needs_fetch = bug_key not in explanation_cache

        if needs_fetch:
            enriched_code = f"// Context: {context}\n{code}" if context else code
            explanation = await llm_agent.explain_bug(enriched_code, {
                "line": bug_line,
                "type": bug_type,
                "detail": bug_detail,
            }, doc)
            
            async with cache_lock:
                explanation_cache[bug_key] = explanation
                
            print(f"    Agent 4: Generated explanation ({len(explanation)} chars)")
            await asyncio.sleep(1)
        else:
            async with cache_lock:
                explanation = explanation_cache[bug_key]
            print(f"    Agent 4: Reused cached explanation")
    except Exception as e:
        print(f"    Agent 4 fallback: {type(e).__name__}")
        explanation = _build_mcp_fallback_explanation(
            bug_detail, bug_type, bug_line, context, mcp_doc_text
        )

    return {
        "ID": code_id,
        "Bug Line": bug_line,
        "Explanation": explanation,
    }


def _build_mcp_fallback_explanation(bug_detail, bug_type, bug_line, context, mcp_doc_text):
    """Build a concise explanation."""
    parts = []

    if context:
        parts.append(context.strip().rstrip("."))

    if not parts:
        parts.append(bug_detail)

    return ". ".join(parts) + "."


async def run_pipeline(input_path: str, output_path: str):
    """Run the full pipeline on all rows in the input CSV."""
    print("=" * 60)
    print("  Agentic Bug Hunter -- Full Pipeline")
    print("=" * 60)
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print()

    # Initialize agents
    print("  Initializing agents...")
    parser = CodeParsingAgent()
    detector = StaticBugDetector()
    mcp_agent = MCPRetrievalAgent(MCP_SERVER_URL)
    llm_agent = LLMExplanationAgent(token=HUGGINGFACE_API_KEY)
    print("  All agents initialized.\n")

    # Read input CSV
    rows = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    print(f"  Loaded {len(rows)} samples from CSV.\n")



    # Process dataset
    print("\n  Processing dataset...")
    start_time = time.time()

    semaphore = asyncio.Semaphore(4)
    explanation_cache = {}
    cache_lock = asyncio.Lock()

    async def limited_process(row):
        async with semaphore:
            return await process_row(row, parser, detector, mcp_agent, llm_agent, explanation_cache, cache_lock)

    tasks = [limited_process(r) for r in rows]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    print(f"\n\n  Pipeline completed in {elapsed:.1f}s")

    # Write output CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Bug Line", "Explanation"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"  Output written to: {output_path}")
    print(f"  Total rows: {len(results)}")
    print("=" * 60)

    return results


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Allow overriding paths via CLI args
    input_csv = sys.argv[1] if len(sys.argv) > 1 else INPUT_CSV
    output_csv = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_CSV

    asyncio.run(run_pipeline(input_csv, output_csv))
