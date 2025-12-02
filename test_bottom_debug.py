#!/usr/bin/env python3
"""Test bottom with debug logging."""

import asyncio
import bottom
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

client = bottom.Client(host='irc.libera.chat', port=6667, ssl=False)

@client.on('*')
def on_any(event, **kwargs):
    print(f"[EVENT] {event}: {kwargs}")

async def main():
    print("Connecting...")
    await client.connect()
    print("Connected!")
    
    await asyncio.sleep(2)
    
    print("Sending NICK...")
    await client.send('NICK', nick='cord_debug_test')
    
    await asyncio.sleep(1)
    
    print("Sending USER...")
    await client.send('USER', nick='cord_debug_test', mode='0', realname='Test')
    
    print("Waiting...")
    await asyncio.sleep(5)
    
    await client.disconnect()
    print("Done!")

if __name__ == '__main__':
    asyncio.run(main())
