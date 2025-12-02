#!/usr/bin/env python3
"""Minimal bottom test to understand the library."""

import asyncio
import bottom

async def test():
    client = bottom.Client(host='irc.libera.chat', port=6667, ssl=False)
    
    @client.on('client_connect')
    def on_connect(**kwargs):
        print("[EVENT] client_connect")
        asyncio.create_task(client.send('NICK', nick='cord_minimal_test'))
        asyncio.create_task(client.send('USER', nick='cord_minimal_test', mode='0', realname='Test'))
        # Try joining a channel after a delay
        async def delayed_join():
            await asyncio.sleep(2)
            print("Sending JOIN...")
            await client.send('JOIN', channel='#testchannel')
        asyncio.create_task(delayed_join())
    
    @client.on('ping')
    def on_ping(message, **kwargs):
        print(f"[EVENT] ping: {message}")
        asyncio.create_task(client.send('PONG', message=message))
    
    @client.on('privmsg')
    def on_privmsg(**kwargs):
        print(f"[EVENT] privmsg: {kwargs}")
    
    @client.on('*')
    def on_any(event, **kwargs):
        print(f"[EVENT] {event}")
    
    print("Connecting...")
    await client.connect()
    print("Connected! Waiting for events...")
    
    # Keep running and processing events
    try:
        await asyncio.wait_for(client.wait('CLIENT_DISCONNECT'), timeout=10)
    except asyncio.TimeoutError:
        print("Timeout reached")
    
    print("Done!")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(test())
