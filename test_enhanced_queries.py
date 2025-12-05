#!/usr/bin/env python3
"""Test enhanced Azure query responses"""

import asyncio
from src.core.mcp_client import MCPClient


async def test_queries():
    print("=" * 70)
    print("Testing Enhanced Azure Queries")
    print("=" * 70)
    print()
    
    mcp = MCPClient()
    
    # Test various query types
    queries = [
        ("list containers", "Basic list"),
        ("show status", "Status summary"),
        ("what are the IPs?", "IP addresses"),
        ("show ports", "Port information"),
        ("show resources", "CPU/Memory"),
        ("where are containers?", "Locations"),
        ("check health", "Health check"),
        ("show images", "Docker images"),
        ("restart counts", "Restart info"),
        ("tell me about kirocontainer", "Specific container"),
    ]
    
    for query, description in queries:
        print(f"\n{'='*70}")
        print(f"📝 {description}: '{query}'")
        print('='*70)
        
        result = await mcp.execute(query)
        
        if "message" in result:
            print(result["message"])
        elif "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(result)
        
        print()
        input("Press Enter for next query...")


if __name__ == "__main__":
    asyncio.run(test_queries())
