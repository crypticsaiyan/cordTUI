#!/usr/bin/env python3
"""Test bottom with proper wait loop."""

import asyncio
import bottom

client = bottom.Client(host='irc.libera.chat', port=6667, ssl=False)

@client.on('client_connect')
async def on_connect(**kwargs):
    print("[EVENT] client_connect")
    await client.send('NICK', nick='cord_wait_test')
    await client.send('USER', nick='cord_wait_test', mode='0', realname='Test')

@client.on('ping')
async def on_ping(message, **kwargs):
    print(f"[EVENT] ping")
    await client.send('PONG', message=message)

@client.on('privmsg')
def on_privmsg(nick, target, message, **kwargs):
    print(f"[EVENT] privmsg from {nick}: {message}")

@client.on('*')
def on_any(event, **kwargs):
    if event not in ['client_connect', 'ping']:
        print(f"[EVENT] {event}")

async def main():
    print("Connecting...")
    await client.connect()
    print("Connected! Waiting for disconnect...")
    
    # This should process all incoming messages
    try:
        await asyncio.wait_for(client.wait('client_disconnect'), timeout=10)
    except asyncio.TimeoutError:
        print("Timeout - disconnecting")
    
    await client.disconnect()
    print("Done!")

if __name__ == '__main__':
    asyncio.run(main())
