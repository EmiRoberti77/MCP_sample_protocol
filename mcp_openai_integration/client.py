import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any, Dict, List

import nest_asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI
from openai.types.beta import assistant
from openai.types.responses import ToolChoiceShellParam

load_dotenv()
nest_asyncio.apply()
# gloabal variables
session = None
exit_stack = AsyncExitStack()
openai_client = AsyncOpenAI()
model = 'gpt-4o'
stdio = None
write = None

async def connect_to_server(server_script_path:str = 'server.py'):
    """
    Connect to MCP server:
    Args:
        server_script_path: Path to the script
    """
    global session, stdio, write, exit_stack
    # server configuration
    server_params = StdioServerParameters(
        command='python',
        args=[server_script_path]
    )
    # connect to the server
    stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport
    session = await exit_stack.enter_async_context(ClientSession(stdio, write))
    # Initialise the connection
    await session.initialize()
    tools_list = await session.list_tools()
    print(f'connected to server and list of tools')
    for tool in tools_list.tools:
        print(f' - {tool.name}: {tool.description}')
    
async def get_mcp_tools() -> List[Dict[str, Any]]:
    """
    Get avaliable tools from MCP server in openai format
    returns:
        A list of tools in openai format
    """
    global session
    tools_result = await session.list_tools()

    return [
        {
            "type":"function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            },
        }
        for tool in tools_result.tools
    ]


async def process_query(query:str) -> str:
    """
    Process a query using OpenAI and avaliable MCP tools.
    Args:
        query: the user query
    Returns:
        The response from openai
    """
    global session, openai_client, model
    # get avaliable tools
    tools = await get_mcp_tools()
    # Init OpenAI
    response = await openai_client.chat.completions.create(
        model=model,
        messages=[{"role":"user", "content":query }],
        tools=tools,
        tool_choice="auto"
    )
    # get assistans response
    assistant_message = response.choices[0].message
    print(f'{assistant_message=}')
    # initialise conversation
    messages = [
        {"role":"user", "content":query},
        assistant_message
    ]

    # Handle tool calls if present
    if assistant_message.tool_calls:
        # excecute each tool
        for tool_call in assistant_message.tool_calls:
            # execute the tool call
            result = await session.call_tool(
                tool_call.function.name,
                arguments=json.loads(tool_call.function.arguments)
            )
            # add tool response to conversation
            messages.append(
                {
                    "role":"tool",
                    "tool_call_id":tool_call.id,
                    "content":result.content[0].text
                }
            )
        # get final response from OpenAI tool resuls
        final_response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="none"
        )
        return final_response.choices[0].message.content
    
    # no tool calls return the direct reponse
    return assistant_message.content

async def cleanup():
    """Clean up resources."""
    global exit_stack
    await exit_stack.aclose()

async def main():
    """Main entry point for the client."""
    await connect_to_server("server.py")

    # Example: Ask about company vacation policy
    query = "What is our company's vacation policy?"
    print(f"\nQuery: {query}")

    response = await process_query(query)
    print(f"\nResponse: {response}")

    await cleanup()


if __name__ == "__main__":
    asyncio.run(main())