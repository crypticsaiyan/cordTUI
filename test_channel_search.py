#!/usr/bin/env python3
"""Test channel search and join functionality."""

import asyncio
from src.core.irc_client import IRCClient

async def test():
    print("Testing channel search and join functionality...\n")
    
    client = IRCClient(
        host="irc.libera.chat",
        port=6667,
        nick="cord_search_test",
        ssl=False
    )
    
    channels_received = []
    
    def on_channel_list(channels):
        channels_received.extend(channels)
        print(f"Received {len(channels)} channels:")
        for ch in channels[:5]:
            print(f"  {ch['name']} ({ch['users']} users) - {ch['topic'][:50]}")
        if len(channels) > 5:
            print(f"  ... and {len(channels) - 5} more")
    
    client.set_channel_list_callback(on_channel_list)
    
    print("Connecting...")
    await client.connect()
    print("Connected!\n")
    
    await asyncio.sleep(2)
    
    print("Requesting channel list...")
    client.list_channels()
    
    # Wait for channel list
    await asyncio.sleep(5)
    
    print(f"\nTotal channels received: {len(channels_received)}")
    
    # Test joining a new channel
    print("\nTesting channel join...")
    test_channel = "#cord_test_channel"
    client.join_channel(test_channel)
    
    await asyncio.sleep(2)
    
    print(f"Joined {test_channel}")
    
    await client.disconnect()
    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(test())