#!/usr/bin/env python3
"""Test LIST command directly."""

import asyncio
from src.core.irc_client import IRCClient

async def test():
    print("Testing LIST command...")
    
    client = IRCClient(
        host="irc.libera.chat",
        port=6667,
        nick="cord_list_test",
        ssl=False
    )
    
    channels_received = []
    
    def on_channel_list(channels):
        channels_received.extend(channels)
        print(f"✅ Received {len(channels)} channels!")
        for ch in channels[:5]:
            print(f"  - {ch['name']} ({ch['users']} users)")
        if len(channels) > 5:
            print(f"  ... and {len(channels) - 5} more")
    
    client.set_channel_list_callback(on_channel_list)
    
    print("Connecting...")
    await client.connect()
    print("Connected!")
    
    # Wait a bit for connection to stabilize
    print("Waiting 5 seconds for connection to stabilize...")
    await asyncio.sleep(5)
    
    print("Sending LIST command...")
    client.list_channels()
    
    # Wait for response
    print("Waiting 10 seconds for LIST response...")
    await asyncio.sleep(10)
    
    print(f"\nFinal result: {len(channels_received)} channels received")
    
    await client.disconnect()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(test())