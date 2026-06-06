# """
# Test MCP Server Connection
# ---------------------------
# Connects to the MCP server (ABH_Server) running on port 8003
# via SSE transport and tests its tools.

# Prerequisites:
#     1. Start the MCP server from the current directory:
#        cd "C:\\Users\\Alfeen K Afsal\\Desktop\\A1_Submission"
#        python server/mcp_server.py

#     2. Then run this test:
#        python Code/test_mcp_connection.py
# """

# import asyncio
# import sys

# from fastmcp import Client


# SERVER_URL = "http://localhost:8003/sse"


# async def test_connection():
#     """Connect to the running MCP server and call its tools."""

#     print(f"Connecting to MCP server at {SERVER_URL} ...")

#     try:
#         async with Client(SERVER_URL) as client:
#             print("[OK] Connected successfully!\n")

#             # -- List available tools --
#             print("=" * 50)
#             print("  Available Tools")
#             print("=" * 50)
#             tools = await client.list_tools()
#             for tool in tools:
#                 print(f"  - {tool.name}")
#             print()

#             # -- Test: add --
#             print("-" * 50)
#             print("  Test: add(3, 5)")
#             result = await client.call_tool("add", {"a": 3, "b": 5})
#             print(f"  Result: {result}")
#             assert str(8) in str(result), f"Expected 8, got {result}"
#             print("  [PASSED]\n")

#             # -- Test: multiply --
#             print("-" * 50)
#             print("  Test: multiply(4, 7)")
#             result = await client.call_tool("multiply", {"a": 4, "b": 7})
#             print(f"  Result: {result}")
#             assert str(28) in str(result), f"Expected 28, got {result}"
#             print("  [PASSED]\n")

#             # -- Test: sine --
#             print("-" * 50)
#             print("  Test: sine(90)")
#             result = await client.call_tool("sine", {"a": 90})
#             print(f"  Result: {result}")
#             assert "1" in str(result), f"Expected ~1.0, got {result}"
#             print("  [PASSED]\n")

#             # -- Test: list_files_and_folders --
#             print("-" * 50)
#             print("  Test: list_files_and_folders()")
#             result = await client.call_tool("list_files_and_folders", {})
#             print(f"  Result: {result}")
#             print("  [PASSED]\n")

#             # -- Summary --
#             print("=" * 50)
#             print("  All connection tests PASSED!")
#             print("=" * 50)

#     except Exception as e:
#         print(f"[ERROR] {type(e).__name__}: {e}")
#         print("\nMake sure the MCP server is running:")
#         print('  cd "C:\\Users\\Alfeen K Afsal\\Desktop\\A1_Submission"')
#         print("  python server/mcp_server.py")
#         sys.exit(1)


# if __name__ == "__main__":
#     print("=" * 50)
#     print("  MCP Server Connection Test")
#     print("=" * 50)
#     print()
#     asyncio.run(test_connection())




#Minimal test:
import asyncio
from fastmcp import Client

SERVER_URL = "http://localhost:8003/sse"


async def test_connection():

    async with Client(SERVER_URL) as client:

        tools = await client.list_tools()

        print("\nAVAILABLE TOOLS:\n")

        for tool in tools:
            print(tool.name)


if __name__ == "__main__":
    asyncio.run(test_connection())