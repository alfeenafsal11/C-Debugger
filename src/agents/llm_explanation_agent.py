"""
Agent 4 -- LLM Explanation Agent
Uses Google Gemini (via llama-index) to generate human-readable
explanations of detected bugs, enriched with MCP documentation.

Input:
  - code snippet
  - bug line + bug type + detail
  - documentation retrieved from MCP server

Output:
  A natural-language explanation of:
    1. Why the line is buggy
    2. What rule is violated
    3. Reference to documentation
    4. Clear explanation for developers
"""

import os
import re as _re


_PROMPT_TEMPLATE = """You are a C++ static debugger and code reviewer specializing in Infineon SmartRDI test APIs.

Code:
```
{code}
```

Bug detected at line {line}.
Bug type: {bug_type}
Bug detail: {detail}

Documentation retrieved from the MCP server:
{documentation}

Instructions:
Explain the bug in the code in the exact conversational, developer-focused style often written by engineers in defect reports. Focus on identifying the exact variables, methods (e.g., rdi.dc().vForce()), and logic errors instead of broadly stating "violates a rule."
Identify the specific issue (e.g., "method order of arguments", "vForce set to 35V which is out of range", "BUG: Logical api changes", "Missing return statement..."). Use the provided Bug detail to inform the output, but make it read like a natural human review comment.
Match the style, brevity, and focus of these example explanations:
- "BUG : Replacing the lifecycle order and calling RDI_END before RDI_BEGIN inverts the intended session/transaction scope and will typically cause runtime failures or no-ops."
- "iClamp low and high values are exchanged,method order of arguments"
- "vForce set to 35V which is not one of the allowed range according to the above documentation for an assumed AVI64,Specification of AVI64"
- "the order of function calling is smartVec().burstUpload(), burstUpload will help to reduce the result uploading time. The results of multiple smartVec read commands,"

IMPORTANT:
- Return ONLY the explanation string itself.
- Do NOT include intro phrases, titles, or formatting (like "**Bug Explanation:**" or "The indicated line is buggy because...").
- Do NOT include code fixes, only explain what the bug is and why it's a bug.

Explanation:"""

# Retry configuration
MAX_RETRIES = 3
BASE_RETRY_DELAY = 60  # seconds


import asyncio

class LLMExplanationAgent:

    def __init__(self, token=None, model="meta-llama/Meta-Llama-3-8B-Instruct"):
        self.token = token or os.environ.get("HF_TOKEN")
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.cache = {}
        
        if self.token and self.token != "dummy_token":
            from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
            self.llm = HuggingFaceInferenceAPI(
                model_name=model,
                token=self.token,
                timeout=60,
                temperature=0.1,
                max_tokens=120,
                top_p=0.9
            )
        elif self.anthropic_key:
            from anthropic import AsyncAnthropic
            self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_key)
            self.llm = None
        else:
            self.llm = None
            self.anthropic_client = None

    async def explain(
        self,
        code: str,
        bug_line: int,
        bug_type: str,
        bug_detail: str,
        documentation: str = "",
        
    ) -> str:
        """
        Generate a natural-language explanation for a bug.
        Includes retry logic for rate-limited API calls.
        """
        cache_key = f"{bug_type}-{bug_line}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        lines = code.splitlines()
        start = max(0, bug_line - 3)
        end = min(len(lines), bug_line + 2)
        snippet = "\n".join(lines[start:end])

        prompt = _PROMPT_TEMPLATE.format(
            code=snippet,
            line=bug_line,
            bug_type=bug_type,
            detail=bug_detail,
            documentation=documentation if documentation else "No documentation available.",
        )

        for attempt in range(MAX_RETRIES + 1):
            try:
                if self.token and self.token != "dummy_token" and self.llm:
                    response = await self.llm.acomplete(prompt)
                    explanation = response.text.strip()
                elif self.anthropic_key and self.anthropic_client:
                    response = await self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=120,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    explanation = response.content[0].text.strip()
                else:
                    raise ValueError("No valid LLM credentials available (need HF_TOKEN or ANTHROPIC_API_KEY)")
                
                # Strip markdown bolding and intro phrases if the LLM ignores instructions
                explanation = _re.sub(r'^\*\*.*?\*\*\s*', '', explanation)
                for prefix in ["Explanation:", "explanation:", "The indicated line is buggy because", "Bug Explanation:"]:
                    if explanation.startswith(prefix):
                        explanation = explanation[len(prefix):].strip()
                        
                # Ensure it starts with a capital letter
                if explanation:
                    explanation = explanation[0].upper() + explanation[1:]
                    
                self.cache[cache_key] = explanation
                return explanation
            except Exception as e:
                error_str = str(e)
                if ("429" in error_str or "503" in error_str) and attempt < MAX_RETRIES:
                    # Extract retry delay from error if available
                    delay = BASE_RETRY_DELAY
                    match = _re.search(r'retry in (\d+)', error_str)
                    if match:
                        delay = int(match.group(1)) + 5  # add buffer
                    print(f"    Rate limited. Waiting {delay}s before retry {attempt + 1}/{MAX_RETRIES}...")
                    await asyncio.sleep(delay)
                else:
                    raise

    async def explain_bug(self, code: str, bug: dict, doc: dict = None) -> str:
        """
        Convenience method accepting Agent 2 bug dict and Agent 3 doc dict.

        Args:
            code: source code string
            bug: dict with "line", "type", "detail" from StaticBugDetector
            doc: dict from MCPRetrievalAgent (optional)

        Returns:
            Explanation string
        """
        documentation = ""
        if doc:
            parts = []
            if doc.get("name"):
                parts.append(f"Bug Name: {doc['name']}")
            if doc.get("description"):
                parts.append(f"Description: {doc['description']}")
            if doc.get("example"):
                parts.append(f"Example: {doc['example']}")
            if doc.get("explanation_template"):
                parts.append(f"Template: {doc['explanation_template']}")
            documentation = "\n".join(parts)

        return await self.explain(
            code=code,
            bug_line=bug["line"],
            bug_type=bug["type"],
            bug_detail=bug["detail"],
            documentation=documentation,
        )


# ------------------------------------------------------------------
# Standalone test
# ------------------------------------------------------------------
if __name__ == "__main__":
    sample_code = """int main() {
    int x;
    cout << x;
    return 0;
}"""
    agent = LLMExplanationAgent()
    explanation = asyncio.run(agent.explain(
    code=sample_code,
    bug_line=3,
    bug_type="uninitialized_variable",
    bug_detail="Variable 'x' used at line 3 but declared uninitialized at line 2",
    documentation="Using uninitialized variables in C++ results in undefined behavior."
))
