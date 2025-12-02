#!/usr/bin/env python3
"""Test that the app receives IRC messages."""

import asyncio
from src.core.irc_client import IRCClient

async def test():
    print("🔌 Testing IRC message reception...")
    
    client = IRCClient(
        host="irc.libera.chat",
        port=6667,
        nick="cord_app_test",
        ssl=False
    )
    
    messages_received = []
    
    def on_message(nick, target, message):
        print(f"✅ RECEIVED: [{target}] <{nick}> {message}")
        messages_received.append((nick, target, message))
    
    def on_members(channel, members):
        print(f"👥 {channel}: {len(members)} members")
    
    client.set_message_callback(on_message)
    client.set_members_callback(on_members)
    
    await client.connect()
    print("✅ Connected!\n")
    
    await asyncio.sleep(2)
    
    print("📡 Joining #testchannel...")
    client.join_channel("#testchannel")
    
    await asyncio.sleep(3)
    
    print("📤 Sending test message...\n")
    client.send_message("#testchannel", "Testing message reception - please reply!")
    
    print("⏳ Waiting 20 seconds for responses...")
    print("   (Send a message to #testchannel on Libera.Chat to test)\n")
    
    await asyncio.sleep(20)
    
    print(f"\n📊 Results:")
    print(f"   Messages received: {len(messages_received)}")
    if messages_received:
        print(f"   ✅ SUCCESS! Message reception is working!")
        for nick, target, msg in messages_received:
            print(f"      - {nick}: {msg[:50]}")
    else:
        print(f"   ⚠️  No messages received (channel might be quiet)")
    
    await client.disconnect()
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test())
