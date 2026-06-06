import asyncio
from fastmcp import Client

SERVER_URL = "http://localhost:8003/sse"


async def test_retrieval():

    async with Client(SERVER_URL) as client:

        result = await client.call_tool(
            "search_documents",
            {
                "query": "segmentation fault caused by null pointer"
            }
        )

        print("\nRAW RESULT:\n")
        print(result)


if __name__ == "__main__":
    asyncio.run(test_retrieval())