import asyncio
import nest_asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

nest_asyncio.apply()

async def main():
    # define server parameters
    server_params = StdioServerParameters(
        command='python', 
        args=['server.py']
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # initialize the connection
            await session.initialize()

            tools_result = await session.list_tools()
            print('Available tools')
            for tool in tools_result.tools:
                print(f' -  {tool.name}: {tool.description}')
            
            # call our tool
            a, b = 2, 3
            result = await session.call_tool('add', arguments={"a":a, "b":b})
            print(f'calling (add):{a}+{b}={result.content[0].text}')

            result = await session.call_tool('subtract', arguments={"a":a, "b":b})
            print(f'calling (subtract):{a}-{b}={result.content[0].text}')

if __name__ == "__main__":
    asyncio.run(main())
            