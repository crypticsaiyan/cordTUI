#!/usr/bin/env python3
"""Test the DevOps Health Bot functionality."""

import asyncio
from src.core.devops_health_bot import DevOpsHealthBot


async def test_health_check():
    """Test basic health check functionality."""
    print("🧪 Testing DevOps Health Bot\n")
    print("=" * 50)
    
    # Create bot instance
    bot = DevOpsHealthBot()
    
    # Test 1: Check all containers
    print("\n📋 Test 1: Check all Docker containers")
    print("-" * 50)
    result = await bot.check_health("")
    print(result)
    
    # Test 2: Check with environment filter
    print("\n\n📋 Test 2: Check 'prod' containers")
    print("-" * 50)
    result = await bot.check_health("prod")
    print(result)
    
    # Test 3: Check with service filter
    print("\n\n📋 Test 3: Check 'web' service")
    print("-" * 50)
    result = await bot.check_health("web")
    print(result)
    
    # Test 4: Combined filter
    print("\n\n📋 Test 4: Check 'staging api'")
    print("-" * 50)
    result = await bot.check_health("staging api")
    print(result)
    
    print("\n" + "=" * 50)
    print("✅ Tests complete!")


if __name__ == "__main__":
    asyncio.run(test_health_check())
