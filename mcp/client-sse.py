import asyncio
from random import randint
import nest_asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

nest_asyncio.apply()

"""
1. Make sure the server is running before running this client
2. Make sure the server is configured to be on transport=sse
3. Make sure the server is running on port 8050

to run the server:
>> uv python server-sse.py
"""

async def main():
    async with sse_client('http://localhost:8050/sse') as (read_stream, writer_stream):
        async with ClientSession(read_stream, writer_stream) as session:
            await session.initialize()
            # list tools
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                print(f' - {tool.name}: {tool.description}')
            # call tool
            a = randint(1,500)
            b = randint(1,500)
            result = await session.call_tool('add', arguments={"a":a, "b":b})
            print(f'calling add:{a}+{b}={result.content[0].text}')

if __name__ == "__main__":
    asyncio.run(main())