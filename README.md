# Model Context Protocol (MCP)

I Created this sample project to test MCP protocol. This project is mainly focusing on connecting to tools from the MCP Server.

## Table of Contents

- [What is MCP?](#what-is-mcp)
- [Benefits](#benefits)
- [Architecture Overview](#architecture-overview)
- [Transport Methods](#transport-methods)
  - [STDIO Transport](#stdio-transport)
  - [SSE Transport](#sse-transport)
- [Getting Started](#getting-started)
- [Examples](#examples)
- [Use Cases](#use-cases)

---

## What is MCP?

**Model Context Protocol (MCP)** is a standardized protocol that enables AI applications and language models to securely connect to external data sources and tools. It provides a unified interface for:

- **Tool Discovery**: Discover available tools/functions from servers
- **Tool Execution**: Execute tools with proper parameters
- **Resource Access**: Access external data sources and APIs
- **Prompt Management**: Manage and retrieve prompts from servers

MCP acts as a bridge between AI applications and external capabilities, allowing models to extend their functionality beyond their training data.

---

## Benefits

### **Standardized Interface**

- Single protocol for connecting to diverse tools and data sources
- Consistent API regardless of the underlying implementation
- Reduces integration complexity

### **Security**

- Controlled access to external resources
- Server-side validation and authentication
- Isolated execution environment

### **Extensibility**

- Easy to add new tools and capabilities
- No need to modify the AI application
- Plug-and-play architecture

### **Flexibility**

- Multiple transport methods (STDIO, SSE, HTTP)
- Works with various programming languages
- Supports both local and remote servers

### **Tool Discovery**

- Dynamic tool registration
- Automatic schema validation
- Rich metadata and descriptions

### **Separation of Concerns**

- AI logic separate from tool implementation
- Easy to maintain and update tools independently
- Better code organization

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────┐
│   AI Client     │
│  (Application)  │
└────────┬────────┘
         │
         │ MCP Protocol
         │ (JSON-RPC)
         │
    ┌────▼────┐
    │  MCP    │
    │ Client  │
    └────┬────┘
         │
         │ Transport Layer
         │ (STDIO/SSE/HTTP)
         │
    ┌────▼────┐
    │  MCP    │
    │ Server  │
    └────┬────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │        │          │          │
┌───▼───┐ ┌─▼───┐  ┌───▼───┐  ┌───▼───┐
│ Tool  │ │Tool │  │ Data  │  │ API   │
│  1    │ │  2  │  │Source │  │       │
└───────┘ └─────┘  └───────┘  └───────┘
```

### MCP Communication Flow

```
Client                    Server
  │                         │
  │  1. Initialize          │
  ├────────────────────────>│
  │                         │
  │  2. List Tools          │
  ├────────────────────────>│
  │                         │
  │  3. Tools Response      │
  │<────────────────────────┤
  │                         │
  │  4. Call Tool           │
  ├────────────────────────>│
  │                         │
  │  5. Execute Tool        │
  │     (Server-side)       │
  │                         │
  │  6. Tool Result         │
  │<────────────────────────┤
  │                         │
```

---

## Transport Methods

MCP supports multiple transport methods, each suited for different use cases:

### STDIO Transport

**STDIO (Standard Input/Output)** transport uses process communication via stdin/stdout. The client spawns the server as a subprocess and communicates through pipes.

#### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Client Process                       │
│  ┌──────────────┐                                      │
│  │ MCP Client   │                                      │
│  └──────┬───────┘                                      │
│         │                                              │
│         │ spawns subprocess                            │
│         │                                              │
└─────────┼──────────────────────────────────────────────┘
          │
          │ stdin/stdout pipes
          │
┌─────────┼──────────────────────────────────────────────┐
│         │         Server Process                       │
│         │  ┌──────────────┐                          │
│         ├─▶│ MCP Server   │                          │
│         │  └──────┬───────┘                          │
│         │         │                                   │
│         │  ┌──────▼───────┐                          │
│         │  │   Tools      │                          │
│         │  │  - add()     │                          │
│         │  │  - subtract()│                          │
│         │  └──────────────┘                          │
└─────────┼──────────────────────────────────────────────┘
          │
          │ JSON-RPC Messages
          │ (stdin/stdout)
```

#### Characteristics

- ✅ **Simple**: No network configuration needed
- ✅ **Secure**: Process isolation
- ✅ **Automatic**: Client manages server lifecycle
- ✅ **Local**: Best for local development and tools
- ❌ **Single Client**: One client per server instance
- ❌ **Process-bound**: Server tied to client process

#### Example Usage

**Server** (`mcp/server-stdio.py`):

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="Calculator")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

**Client** (`mcp/client-stdio.py`):

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command='python',
    args=['server-stdio.py']
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool('add', arguments={"a": 2, "b": 3})
```

#### Running STDIO Example

```bash
# Client automatically spawns the server
cd mcp
python client-stdio.py
```

---

### SSE Transport

**SSE (Server-Sent Events)** transport uses HTTP with Server-Sent Events for real-time communication. The server runs as a standalone HTTP server.

#### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Client Process                       │
│  ┌──────────────┐                                      │
│  │ MCP Client   │                                      │
│  └──────┬───────┘                                      │
│         │                                              │
│         │ HTTP + SSE                                   │
│         │ (http://localhost:8050/sse)                  │
└─────────┼──────────────────────────────────────────────┘
          │
          │ Network (HTTP)
          │
┌─────────┼──────────────────────────────────────────────┐
│         │         Server Process                       │
│         │  ┌──────────────────────┐                   │
│         │  │   HTTP Server        │                   │
│         │  │   (Port 8050)        │                   │
│         │  └──────────┬───────────┘                   │
│         │             │                                │
│         │  ┌──────────▼───────────┐                   │
│         │  │   MCP Server         │                   │
│         │  └──────────┬───────────┘                   │
│         │             │                                │
│         │  ┌──────────▼───────────┐                   │
│         │  │   Tools              │                   │
│         │  │  - add()             │                   │
│         │  │  - subtract()        │                   │
│         │  └─────────────────────┘                   │
└─────────┼──────────────────────────────────────────────┘
          │
          │ Multiple clients can connect
```

#### Characteristics

- ✅ **Multi-Client**: Multiple clients can connect simultaneously
- ✅ **Network**: Works over network (local or remote)
- ✅ **Persistent**: Server runs independently
- ✅ **HTTP**: Standard HTTP protocol
- ❌ **Setup**: Requires server to be running separately
- ❌ **Network**: Requires network configuration

#### Example Usage

**Server** (`mcp/server-sse.py`):

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="Calculator",
    host='0.0.0.0',
    port=8050
)

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport='sse')
```

**Client** (`mcp/client-sse.py`):

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client('http://localhost:8050/sse') as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool('add', arguments={"a": 2, "b": 3})
```

#### Running SSE Example

**Terminal 1 - Start Server:**

```bash
cd mcp
python server-sse.py
```

**Terminal 2 - Run Client:**

```bash
cd mcp
python client-sse.py
```

---

## Transport Comparison

| Feature              | STDIO                    | SSE                       |
| -------------------- | ------------------------ | ------------------------- |
| **Setup Complexity** | Low                      | Medium                    |
| **Network Required** | No                       | Yes                       |
| **Multiple Clients** | No                       | Yes                       |
| **Server Lifecycle** | Managed by client        | Independent               |
| **Use Case**         | Local tools, development | Production, remote access |
| **Security**         | Process isolation        | Network security needed   |
| **Latency**          | Low (local pipes)        | Medium (network)          |

---

## Getting Started

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt
```

### Basic Setup

1. **Create an MCP Server**:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="MyServer")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run(transport='stdio')  # or 'sse'
```

2. **Create an MCP Client**:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command='python',
    args=['server.py']
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool('my_tool', arguments={"param": "value"})
```

---

## Examples

This repository contains several examples:

### 1. Basic Calculator (`mcp/`)

- **STDIO Example**: `server-stdio.py` + `client-stdio.py`
- **SSE Example**: `server-sse.py` + `client-sse.py`
- Simple add/subtract operations

### 2. OpenAI Integration (`mcp_openai_integration/`)

- **Server**: Knowledge base server with Q&A pairs
- **Client**: Integrates MCP tools with OpenAI GPT-4
- Demonstrates how to use MCP tools in AI applications

**Run the OpenAI integration:**

```bash
cd mcp_openai_integration
python client.py
```

---

## Use Cases

### 1. **Database Access**

Connect AI applications to databases securely:

```python
@mcp.tool()
def query_database(query: str) -> str:
    """Execute database query"""
    # Database logic here
    return results
```

### 2. **API Integration**

Integrate with external APIs:

```python
@mcp.tool()
def fetch_weather(location: str) -> dict:
    """Get weather data for location"""
    # API call logic
    return weather_data
```

### 3. **File Operations**

Provide file system access:

```python
@mcp.tool()
def read_file(path: str) -> str:
    """Read file contents"""
    with open(path, 'r') as f:
        return f.read()
```

### 4. **Knowledge Bases**

Access structured knowledge:

```python
@mcp.tool()
def get_knowledge_base() -> str:
    """Retrieve knowledge base content"""
    # Load and format knowledge base
    return formatted_kb
```

### 5. **Code Execution**

Execute code in controlled environments:

```python
@mcp.tool()
def execute_code(code: str, language: str) -> str:
    """Execute code safely"""
    # Sandboxed execution
    return output
```

---

## MCP Protocol Flow

### Tool Discovery and Execution

```
┌─────────────────────────────────────────────────────────────┐
│                    Tool Discovery Flow                       │
└─────────────────────────────────────────────────────────────┘

Client                          Server
  │                               │
  │  initialize()                 │
  ├──────────────────────────────>│
  │                               │
  │  list_tools()                 │
  ├──────────────────────────────>│
  │                               │
  │                               │  Query registered tools
  │                               │  ┌──────────────┐
  │                               │  │ @mcp.tool()  │
  │                               │  │ def add()    │
  │                               │  └──────────────┘
  │                               │
  │  tools: [                     │
  │    {name: "add", ...},        │
  │    {name: "subtract", ...}    │
  │  ]                            │
  │<──────────────────────────────┤
  │                               │

┌─────────────────────────────────────────────────────────────┐
│                    Tool Execution Flow                      │
└─────────────────────────────────────────────────────────────┘

Client                          Server
  │                               │
  │  call_tool("add",             │
  │    {a: 2, b: 3})              │
  ├──────────────────────────────>│
  │                               │
  │                               │  Execute add(2, 3)
  │                               │  ┌──────────────┐
  │                               │  │ return 5     │
  │                               │  └──────────────┘
  │                               │
  │  result: {content: "5"}       │
  │<──────────────────────────────┤
  │                               │
```

---

## Best Practices

### Server Design

1. **Clear Tool Descriptions**: Provide detailed docstrings
2. **Type Hints**: Use type hints for better validation
3. **Error Handling**: Return meaningful error messages
4. **Resource Management**: Clean up resources properly

### Client Design

1. **Connection Management**: Use context managers (`async with`)
2. **Error Handling**: Handle connection and execution errors
3. **Tool Validation**: Verify tools exist before calling
4. **Resource Cleanup**: Always clean up connections

### Security

1. **Input Validation**: Validate all inputs on the server
2. **Authentication**: Implement authentication for SSE transport
3. **Rate Limiting**: Add rate limiting for production use
4. **Sandboxing**: Isolate tool execution when possible

---

## Resources

- [MCP Specification](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

---

This project is provided as-is for educational and demonstration purposes

Emi Roberti
