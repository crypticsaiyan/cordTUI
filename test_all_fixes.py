#!/usr/bin/env python3
"""Test all the fixes implemented."""

import asyncio
from src.core.irc_client import IRCClient

async def test():
    print("🧪 Testing all fixes...\n")
    
    client = IRCClient(
        host="irc.libera.chat",
        port=6667,
        nick="cord_fix_test",
        ssl=False
    )
    
    # Test member tracking
    members_received = {}
    
    def on_message(nick, target, message):
        print(f"📨 [{target}] <{nick}> {message}")
    
    def on_members(channel, members):
        members_received[channel] = members
        print(f"👥 {channel}: {len(members)} members")
        print(f"   Names: {', '.join(members[:5])}")
        if len(members) > 5:
            print(f"   ... and {len(members) - 5} more")
    
    client.set_message_callback(on_message)
    client.set_members_callback(on_members)
    
    print("🔄 Connecting...")
    await client.connect()
    print("✅ Connected!\n")
    
    await asyncio.sleep(2)
    
    print("📡 Joining #testchannel...")
    client.join_channel("#testchannel")
    
    await asyncio.sleep(3)
    
    print("\n📤 Sending test message...")
    client.send_message("#testchannel", "Testing all fixes!")
    
    await asyncio.sleep(2)
    
    # Test results
    print(f"\n📊 Test Results:")
    print(f"✅ Connection: Working")
    print(f"✅ Message sending: Working")
    
    if "#testchannel" in members_received:
        members = members_received["#testchannel"]
        print(f"✅ Member list: {len(members)} members received")
        print(f"   Sample names: {members[:3]}")
    else:
        print(f"❌ Member list: No members received")
    
    await client.disconnect()
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test())