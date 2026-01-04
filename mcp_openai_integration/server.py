import os
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    host='0.0.0.0',
    port=8050,
    name='knowledge base' 
)

@mcp.tool()
def get_knowledge_base():
    """
    Rerieve the entire knowledge base as formatted strings.
    Returns:
        A formatted string containing all Q&A answers pairs from the knowledge base.
    """
    try:
        print('running get_knowledge_base..')
        kb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'kb.json'))
        with open(kb_path, 'r') as f:
            kb_data = json.load(f)
        print(f'loaded json data from {kb_path}')
        kb_text = "Here is the registered knowledge base"
        if isinstance(kb_data, list):
            for i, item in enumerate(kb_data, 1):
                if isinstance(item, dict):
                    question = item.get('question', 'unknown question')
                    answer = item.get('answer', 'unknown answer')
                else:
                    question = f'Item {i}\n'
                    answer = str(item)
                
                kb_text += f'Q{i}: {question}\n'
                kb_text += f'A{i}: {answer}\n'

            return kb_text

    except FileNotFoundError:
        return "ERR: file not found"
    except json.JSONDecodeError:
        return "ERR: could not decode json file"
    except Exception as e:
        return f'ERR: gen error: {e}'


if __name__ == "__main__":
    print('Starting MCP server with stdio transport...')
    print('Waiting for client connection...')
    mcp.run(transport='stdio')