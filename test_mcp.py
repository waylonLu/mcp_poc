import asyncio
from fastmcp import Client

async def test_simple():
    """test get all users"""
    async with Client("http://localhost:8000/sse") as client:

        tools  = await client.list_tools()
        print(f"available tools: {[tool.name for tool in tools]}")
        result = await client.call_tool("get_all_users", {})
        print(result)

# 运行
asyncio.run(test_simple())