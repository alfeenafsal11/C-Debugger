"""
Agent 3 -- MCP Retrieval Agent
Queries the MCP server's search_documents tool to retrieve
bug-related documentation from the indexed manual.

For each bug type detected by Agent 2, this agent:
  1. Connects to the MCP server (ABH_Server) via SSE
  2. Calls `search_documents` with a query derived from the bug type
  3. Parses and structures the response into documentation format

Output per bug type:
{
    "name": "Uninitialized Variable",
    "description": "...",
    "example": "...",
    "explanation_template": "Variable {x} used before initialization",
    "references": [...]
}
"""

import asyncio
import json
from fastmcp import Client


# Human-readable names and query strings for each bug type
_BUG_TYPE_QUERIES = {
    "uninitialized_variable": {
        "name": "Uninitialized Variable",
        "query": "uninitialized variable usage before assignment declaration",
        "default_template": "Variable '{var}' is used at line {line} but was declared without initialization at line {decl_line}.",
    },
    "out_of_bounds_access": {
        "name": "Out of Bounds Access",
        "query": "array out of bounds index access buffer overflow",
        "default_template": "Array '{arr}' of size {size} is accessed at index {index}, which is out of bounds.",
    },
    "null_pointer_dereference": {
        "name": "Null Pointer Dereference",
        "query": "null pointer dereference nullptr NULL segfault",
        "default_template": "Pointer '{ptr}' is null but is dereferenced at line {line}.",
    },
    "divide_by_zero": {
        "name": "Divide by Zero",
        "query": "divide by zero division modulo arithmetic exception",
        "default_template": "Division by zero detected at line {line}.",
    },
    "missing_return": {
        "name": "Missing Return Statement",
        "query": "missing return statement non-void function undefined behavior",
        "default_template": "Function '{func}' has return type '{ret_type}' but does not return a value.",
    },
    "infinite_loop": {
        "name": "Infinite Loop",
        "query": "infinite loop while true no break condition",
        "default_template": "Infinite loop detected at line {line} with no break or return statement.",
    },
    "assignment_in_condition": {
        "name": "Assignment in Condition",
        "query": "assignment instead of comparison if condition equals operator",
        "default_template": "Possible accidental assignment (=) instead of comparison (==) in if-condition at line {line}.",
    },
    "off_by_one": {
        "name": "Off-by-One Error",
        "query": "off by one error loop boundary fence post",
        "default_template": "Off-by-one error: loop at line {line} uses '<=' which may iterate one time too many.",
    },
}


class MCPRetrievalAgent:
    """Retrieves bug documentation from the MCP server."""

    def __init__(self, server_url: str = "http://localhost:8003/sse"):
        self.server_url = server_url
        self.cache = {}

    async def retrieve_bug_doc(self, bug_type: str) -> dict:
        """
        Query the MCP server for documentation on a specific bug type.

        Args:
            bug_type: one of the 8 bug type strings from Agent 2

        Returns:
            dict with name, description, example, explanation_template, references
        """
        # CACHE HIT
        if bug_type in self.cache:
            return self.cache[bug_type]

        meta = _BUG_TYPE_QUERIES.get(bug_type, {
            "name": bug_type.replace("_", " ").title(),
            "query": bug_type.replace("_", " "),
            "default_template": f"Bug of type '{bug_type}' detected at line {{line}}.",
        })

        try:
            async with Client(self.server_url) as client:
                result = await client.call_tool(
                    "search_documents", {"query": meta["query"]}
                )
                docs = self._parse_mcp_response(result)
        except Exception as e:
            docs = {
                "retrieved_texts": [],
                "error": f"{type(e).__name__}: {e}",
            }

        output = {
            "bug_type": bug_type,
            "name": meta["name"],
            "description": self._build_description(docs),
            "example": self._extract_example(docs),
            "explanation_template": meta["default_template"],
            "references": docs.get("retrieved_texts", []),
        }
        
        # STORE CACHE
        self.cache[bug_type] = output
        
        return output

    async def retrieve_all_bug_docs(self, bug_list: list) -> list:
        """
        Retrieve documentation for every bug in a list from Agent 2.

        Args:
            bug_list: list of bug dicts from StaticBugDetector output
                      (each with "type", "line", "detail")

        Returns:
            list of documentation dicts, one per unique bug type
        """
        seen_types = set()
        results = []
        for bug in bug_list:
            btype = bug["type"]
            if btype in seen_types:
                continue
            seen_types.add(btype)
            doc = await self.retrieve_bug_doc(btype)
            results.append(doc)
        return results

    # -- helpers --------------------------------------------------------

    @staticmethod
    def _parse_mcp_response(result) -> dict:
        """Extract text content from the MCP tool response."""
        texts = []
        try:
            # FastMCP returns CallToolResult with content list
            if hasattr(result, "content"):
                for item in result.content:
                    if hasattr(item, "text"):
                        try:
                            parsed = json.loads(item.text)
                            if isinstance(parsed, list):
                                for entry in parsed:
                                    if isinstance(entry, dict) and "text" in entry:
                                        texts.append({
                                            "text": entry["text"],
                                            "score": entry.get("score", 0),
                                        })
                            elif isinstance(parsed, dict) and "text" in parsed:
                                texts.append({
                                    "text": parsed["text"],
                                    "score": parsed.get("score", 0),
                                })
                        except json.JSONDecodeError:
                            texts.append({"text": item.text, "score": 0})
            # Also check structured content / data
            if hasattr(result, "data") and result.data:
                data = result.data
                if isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict) and "text" in entry:
                            texts.append({
                                "text": entry["text"],
                                "score": entry.get("score", 0),
                            })
        except Exception:
            pass
        # Sort by score descending, keep top 5
        texts.sort(key=lambda t: t.get("score", 0), reverse=True)
        return {"retrieved_texts": texts[:5]}

    @staticmethod
    def _build_description(docs: dict) -> str:
        """Build a description from the retrieved documents."""
        texts = docs.get("retrieved_texts", [])
        if not texts:
            return "No documentation found in the bug manual."
        # Use the highest-scoring document as the description
        best = texts[0]["text"]
        # Truncate to a reasonable length
        if len(best) > 500:
            return best[:500] + "..."
        return best

    @staticmethod
    def _extract_example(docs: dict) -> str:
        """Try to extract a code example from the retrieved texts."""
        texts = docs.get("retrieved_texts", [])
        for t in texts:
            content = t["text"]
            # Look for code-like patterns
            for marker in ["example:", "Example:", "```", "int ", "void "]:
                idx = content.find(marker)
                if idx != -1:
                    snippet = content[idx:idx + 200]
                    return snippet.strip()
        return "No example found in documentation."


# ------------------------------------------------------------------
# Standalone usage
# ------------------------------------------------------------------
if __name__ == "__main__":
    async def main():
        agent = MCPRetrievalAgent()

        # Test with a single bug type
        print("=" * 60)
        print("  Retrieving doc for: uninitialized_variable")
        print("=" * 60)
        doc = await agent.retrieve_bug_doc("uninitialized_variable")
        print(json.dumps(doc, indent=2, default=str))

        # Test with a bug list from Agent 2
        print("\n" + "=" * 60)
        print("  Retrieving docs for multiple bug types")
        print("=" * 60)
        sample_bugs = [
            {"line": 3, "type": "uninitialized_variable", "detail": "..."},
            {"line": 5, "type": "out_of_bounds_access", "detail": "..."},
            {"line": 7, "type": "null_pointer_dereference", "detail": "..."},
        ]
        docs = await agent.retrieve_all_bug_docs(sample_bugs)
        for d in docs:
            print(f"\n  [{d['bug_type']}] {d['name']}")
            print(f"  Description: {d['description'][:100]}...")

    asyncio.run(main())
