# server.py
from json import load
from mcp.server.fastmcp import FastMCP
from src import server


if __name__ == "__main__":
    
    mcp = server.get_mcp()
    mcp.run()