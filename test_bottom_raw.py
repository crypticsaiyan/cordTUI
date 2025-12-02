#!/usr/bin/env python3
"""Test bottom with raw connection monitoring."""

import asyncio
import bottom

client = bottom.Client(host='irc.libera.chat', port=6667, ssl=False)

@client.on('client_connect')
def on_connect(**kwargs):
    print("[EVENT] client_connect")
    client.send('NICK', nick='cord_raw_test')
    client.send('USER', nick='cord_raw_test', mode='0', realname='Test')

@client.on('ping')
def on_ping(message, **kwargs):
    print(f"[EVENT] ping")
    client.send('PONG', message=message)

@client.on('privmsg')
def on_privmsg(nick, target, message, **kwargs):
    print(f"[EVENT] privmsg from {nick}: {message}")

# Try numeric codes
@client.on('001')  # RPL_WELCOME
def on_welcome(**kwargs):
    print("[EVENT] 001 RPL_WELCOME")

@client.on('353')  # RPL_NAMREPLY
def on_names(**kwargs):
    print(f"[EVENT] 353 RPL_NAMREPLY: {kwargs}")

async def main():
    print("Connecting...")
    await client.connect()
    print("Connected!")
    
    # Wait a bit for registration
    await asyncio.sleep(3)
    
    print("Joining #testchannel...")
    client.send('JOIN', channel='#testchannel')
    
    # Keep alive
    print("Waiting for events (10 seconds)...")
    try:
        await asyncio.wait_for(client.wait('client_disconnect'), timeout=10)
    except asyncio.TimeoutError:
        print("Timeout")
    
    await client.disconnect()
    print("Done!")

if __name__ == '__main__':
    asyncio.run(main())
