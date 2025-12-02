#!/usr/bin/env python3
"""Test channel-specific message filtering."""

import asyncio
from src.core.irc_client import IRCClient

async def test():
    print("🧪 Testing channel-specific message filtering...\n")
    
    client = IRCClient(
        host="irc.libera.chat",
        port=6667,
        nick="cord_filter_test",
        ssl=False
    )
    
    # Track messages by channel
    messages_by_channel = {}
    
    def on_message(nick, target, message):
        if target not in messages_by_channel:
            messages_by_channel[target] = []
        messages_by_channel[target].append((nick, message))
        print(f"📨 [{target}] <{nick}> {message}")
    
    client.set_message_callback(on_message)
    
    await client.connect()
    print("✅ Connected!\n")
    
    await asyncio.sleep(2)
    
    # Join multiple channels
    print("📡 Joining #testchannel and #python...")
    client.join_channel("#testchannel")
    client.join_channel("#python")
    
    await asyncio.sleep(3)
    
    # Send messages to different channels
    print("\n📤 Sending messages to different channels...")
    client.send_message("#testchannel", "Message for testchannel")
    client.send_message("#python", "Message for python")
    
    print("\n⏳ Listening for 15 seconds...")
    await asyncio.sleep(15)
    
    # Summary
    print(f"\n📊 Messages received by channel:")
    for channel, msgs in messages_by_channel.items():
        print(f"   {channel}: {len(msgs)} messages")
        for nick, msg in msgs[:3]:
            print(f"      - {nick}: {msg[:50]}")
    
    await client.disconnect()
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test())
