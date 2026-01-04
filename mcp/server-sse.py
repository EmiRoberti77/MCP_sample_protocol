from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

import os
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
print(OPENAI_API_KEY)

print('starting mcp')
mcp = FastMCP(
    name="Calculator",
    host='0.0.0.0',
    port=8050,
    stateless_http=True
)
print('started mcp')

@mcp.tool()
def add(a:int, b:int)->int:
    """Add two numbers together"""
    return a + b

@mcp.tool()
def subtract(a:int, b:int)->int:
    """Subtract two numbers together"""
    return a - b

if __name__ == "__main__":
    transport = "sse"
    if transport == 'stdio':
        print('Running server with stdio transport')
        mcp.run(transport='stdio')
    elif transport == 'sse':
        print('Running server with SSE transport')
        mcp.run(transport='sse')
    else:
        raise ValueError(f'Err:incorrect transport. {transport=}')