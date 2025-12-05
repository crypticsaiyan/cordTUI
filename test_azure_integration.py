#!/usr/bin/env python3
"""Test Azure integration with MCP client"""

import asyncio
from src.core.mcp_client import MCPClient


async def test_azure():
    print("=" * 60)
    print("Testing Azure Integration with MCP Client")
    print("=" * 60)
    print()
    
    # Initialize MCP client
    mcp = MCPClient()
    
    # Test queries
    queries = [
        "list containers",
        "what containers are running?",
        "show me the IPs",
        "check health",
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        result = await mcp.execute(query)
        
        if "message" in result:
            print(result["message"])
        elif "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(result)
        print()


if __name__ == "__main__":
    asyncio.run(test_azure())
