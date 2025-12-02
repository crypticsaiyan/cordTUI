#!/usr/bin/env python3
"""Test miniirc-based IRC client."""

import asyncio
from src.core.irc_client import IRCClient


async def test():
    print("🔌 Connecting to irc.libera.chat...")
    
    client = IRCClient(
        host="irc.libera.chat",
        port=6667,
        nick="cord_mini_test",
        ssl=False
    )
    
    def on_message(nick, target, message):
        print(f"✅ MESSAGE: [{target}] <{nick}> {message}")
    
    def on_members(channel, members):
        print(f"👥 Members in {channel}: {len(members)} users")
        print(f"   {', '.join(members[:10])}")
    
    client.set_message_callback(on_message)
    client.set_members_callback(on_members)
    
    await client.connect()
    print("✅ Connected!")
    
    await asyncio.sleep(3)
    
    print("\n📡 Joining #testchannel...")
    client.join_channel("#testchannel")
    
    await asyncio.sleep(3)
    
    print("\n📤 Sending message...")
    client.send_message("#testchannel", "Hello from cord.tui with miniirc!")
    
    print("\n⏳ Listening for 15 seconds...")
    await asyncio.sleep(15)
    
    print("\n👋 Disconnecting...")
    await client.disconnect()
    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(test())
