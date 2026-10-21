"""Call a Blender MCP tool through the official blender-mcp server (stdio), for scripting/testing.

Usage:
    mcp_call.py <tool> [json-args]
    mcp_call.py execute_blender_code --file script.py   # sends the file as {"code": ...}
"""
import asyncio
import base64
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# the MCP server is a per-machine install, like Rook: %LOCALAPPDATA%\BlenderMCP\{app,venv}
SERVER = os.environ.get("BLENDER_MCP_EXE") or os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local")),
    "BlenderMCP", "venv", "Scripts", "blender-mcp.exe")


async def main():
    tool = sys.argv[1]
    if len(sys.argv) > 3 and sys.argv[2] == "--file":
        with open(sys.argv[3], encoding="utf-8") as f:
            args = {"code": f.read()}
    else:
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    params = StdioServerParameters(command=SERVER, args=[], env={**os.environ})
    with open(os.devnull, "w") as devnull:
        async with stdio_client(params, errlog=devnull) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                res = await s.call_tool(tool, args)
                for c in res.content:
                    if c.type == "text":
                        print(c.text)
                    elif c.type == "image":
                        out = os.environ.get("MCP_IMAGE_OUT", os.path.join(os.getcwd(), "mcp_image.png"))
                        with open(out, "wb") as f:
                            f.write(base64.b64decode(c.data))
                        print("image saved:", out)
                return res.isError

if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
