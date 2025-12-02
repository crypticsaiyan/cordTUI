#!/usr/bin/env python3
"""Test script to verify IRC connection to Libera.Chat."""

import asyncio
from src.core.irc_client import IRCClient


async def test_connection():
    """Test connecting to Libera.Chat and joining a channel."""
    print("🔌 Connecting to irc.libera.chat...")
    
    client = IRCClient(
        host="irc.libera.chat",
        port=6667,
        nick="cord_test_user",
        ssl=False
    )
    
    # Set up message callback
    def on_message(nick, target, message):
        print(f"📨 [{target}] <{nick}> {message}")
    
    def on_members(channel, members):
        print(f"👥 Members in {channel}: {', '.join(members[:10])}")
        if len(members) > 10:
            print(f"   ... and {len(members) - 10} more")
    
    client.set_message_callback(on_message)
    client.set_members_callback(on_members)
    
    # Connect
    await client.connect()
    print("✅ Connected!")
    
    # Wait for connection to establish
    await asyncio.sleep(3)
    
    # Join a test channel
    print("📡 Joining #python...")
    client.join_channel("#python")
    
    # Wait to receive member list and messages
    print("⏳ Listening for 5 seconds...")
    await asyncio.sleep(5)
    
    # Send a test message
    print("📤 Sending test message...")
    client.send_message("#python", "Hello from cord.tui! Testing IRC connection.")
    
    await asyncio.sleep(1)
    
    # Disconnect
    print("👋 Disconnecting...")
    await client.disconnect()
    print("✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_connection())
