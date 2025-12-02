#!/usr/bin/env python3
"""Test script to verify IRC message reception."""

import asyncio
from src.core.irc_client import IRCClient


async def test_receive():
    """Test receiving messages from IRC."""
    print("🔌 Connecting to irc.libera.chat...")
    
    client = IRCClient(
        host="irc.libera.chat",
        port=6667,
        nick="cord_test_rx",
        ssl=False
    )
    
    messages_received = []
    
    # Set up message callback
    def on_message(nick, target, message):
        print(f"✅ MESSAGE RECEIVED!")
        print(f"   From: {nick}")
        print(f"   To: {target}")
        print(f"   Text: {message}")
        messages_received.append((nick, target, message))
    
    def on_members(channel, members):
        print(f"👥 Members in {channel}: {len(members)} users")
        print(f"   First 5: {', '.join(members[:5])}")
    
    client.set_message_callback(on_message)
    client.set_members_callback(on_members)
    
    # Connect
    await client.connect()
    print("✅ Connected!")
    
    # Wait for connection to establish
    await asyncio.sleep(3)
    
    # Join test channel
    print("\n📡 Joining #testchannel...")
    client.join_channel("#testchannel")
    
    # Wait for join and member list
    await asyncio.sleep(3)
    
    # Send a message to trigger responses
    print("\n📤 Sending test message...")
    client.send_message("#testchannel", "Hello! Testing message reception from cord.tui")
    
    # Listen for responses
    print("\n⏳ Listening for messages for 30 seconds...")
    print("   (Send messages to #testchannel on Libera.Chat to test)")
    await asyncio.sleep(30)
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Messages received: {len(messages_received)}")
    if messages_received:
        print(f"   ✅ Message reception is WORKING!")
    else:
        print(f"   ⚠️  No messages received (channel might be quiet)")
    
    # Disconnect
    print("\n👋 Disconnecting...")
    await client.disconnect()
    print("✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_receive())
