import asyncio

from src.agents.mcp_retrieval_agent import MCPRetrievalAgent


async def main():

    agent = MCPRetrievalAgent()

    query = "segmentation fault caused by null pointer"

    result = await agent.retrieve_bug_doc(query)

    print("\nNORMALIZED RESULT:\n")

    print(type(result))
    print(result)


if __name__ == "__main__":
    asyncio.run(main())