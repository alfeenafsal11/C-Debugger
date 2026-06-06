from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.pipeline.pipeline import DebuggingPipeline

app = FastAPI(title="Agentic Bug Hunter API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline once on startup
pipeline = DebuggingPipeline()

class DebugRequest(BaseModel):
    code: str
    context: Optional[str] = ""

class DebugResponse(BaseModel):
    ID: str
    Bug_Line: int
    Explanation: str

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "Agentic Bug Hunter"}

@app.post("/debug")
async def debug_code(req: DebugRequest):
    """
    Exposes the multi-agent debugging pipeline as a stateless API endpoint.
    """
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="Code snippet cannot be empty.")

    try:
        # Run the pipeline asynchronously
        result = await pipeline.run_async(
            code=req.code,
            context=req.context,
            code_id="api_request"
        )
        
        # Format response keys to match Pydantic model (and conventional JSON style)
        return {
            "ID": result.get("ID"),
            "Bug_Line": result.get("Bug Line"),
            "Explanation": result.get("Explanation"),
            "compiler_diagnostics": result.get("compiler_diagnostics", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
