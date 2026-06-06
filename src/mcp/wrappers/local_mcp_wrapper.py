# from huggingface_hub import snapshot_download
from pathlib import Path

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.core.retrievers import VectorIndexRetriever

import math
import os
from fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parent

embedding_path = BASE_DIR / "embedding_model"
storage_path = BASE_DIR / "storage"

if not embedding_path.exists():
    raise FileNotFoundError(
        f"Embedding model path missing: {embedding_path}"
    )

if not storage_path.exists():
    raise FileNotFoundError(
        f"Storage path missing: {storage_path}"
    )

embed_model = HuggingFaceEmbedding(
    model_name=str(embedding_path)
)
Settings.embed_model = embed_model

storage_context = StorageContext.from_defaults(persist_dir=str(storage_path))
index = load_index_from_storage(storage_context=storage_context)
retriever = VectorIndexRetriever(index=index, similarity_top_k=20)

print(f"Embedding path: {embedding_path}")
print(f"Storage path: {storage_path}")
print("Retriever initialized successfully.")

# nodes = retriever.retrieve("what is the range of vForceRange parameters")
# for ele in nodes:
#     print(ele,"\n\n")


mcp= FastMCP("ABH_Server",port=8003)

@mcp.tool()
def add(a: int, b: int) -> int:
   print(f"Server received add request: {a}, {b}")
   return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
   print(f"Server received multiply request: {a}, {b}")
   return a * b

@mcp.tool()
def sine(a: int) -> float:
    print(f"Server received sine request: {a}")
    radians = math.radians(a)  # Convert from degrees to radians
    result = math.sin(radians)
    print(f"Sine of {a} degrees (radians: {radians}): {result}")
    return result

@mcp.tool()
def list_files_and_folders() -> list:
    """
    Lists all files and directories in the current working directory.
    Returns:
        A list of strings, each representing a file or folder.
    """
    print("Server received request to list files and folders.")
    try:
        # Get all files and directories in the current working directory
        items = os.listdir(".")
        print(f"Files and Folders in Current Directory: {items}")
        return items
    except Exception as e:
        print(f"Error listing files and folders: {e}")
        return [f"Error: {str(e)}"]
    
@mcp.tool()
def search_documents(query: str) -> list:
    """
    Searches documents using vector similarity retrieval.
    
    Args:
        query (str): The search query string to find relevant documents.
        
    Returns:
        list: A list of dictionaries, each containing:
            - text (str): The retrieved document text content
            - score (float): The similarity score of the document to the query
    """
    print(f"Server received search_documents request: {query}")
    nodes = retriever.retrieve(query)
    return [{"text" : ele.get_text(), "score" : ele.get_score()} for ele in nodes]

if __name__ =="__main__":
   print("Starting MCP Server....")
   mcp.run(transport="sse")
#    mcp.run(transport="stdio")