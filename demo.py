"""Demo script for showcasing phosphor features."""

import asyncio
import time


async def simulate_server_death():
    """Simulate a server dying with increasing error rates."""
    print("🎬 Starting demo: Server Death Simulation")
    print("=" * 50)
    
    # Normal operations
    print("\n✅ Phase 1: Normal Operations")
    for i in range(5):
        print(f"[INFO] Request processed successfully (200 OK)")
        await asyncio.sleep(0.5)
    
    # Warning signs
    print("\n⚠️  Phase 2: Warning Signs")
    for i in range(3):
        print(f"[WARN] Slow query detected (500ms)")
        await asyncio.sleep(0.3)
    
    # Errors start
    print("\n❌ Phase 3: Errors Emerging")
    for i in range(5):
        print(f"[ERROR] Database connection timeout (500)")
        await asyncio.sleep(0.2)
    
    # Critical failure
    print("\n💥 Phase 4: Critical Failure")
    for i in range(10):
        print(f"[CRITICAL] Service unavailable! Error rate: {(i+1)*10}%")
        await asyncio.sleep(0.1)
    
    print("\n💀 Server is dead. Geiger counter should be crackling wildly!")
    print("=" * 50)


async def demo_wormhole():
    """Demo the wormhole file transfer."""
    print("\n🌀 Wormhole Demo")
    print("=" * 50)
    print("1. Type: /send config.json")
    print("2. Code generated: 7-guitar-ocean")
    print("3. Teammate types: /grab 7-guitar-ocean")
    print("4. File transfers peer-to-peer (no cloud!)")
    print("=" * 50)


async def demo_teletext():
    """Demo the teletext dashboard."""
    print("\n📺 Teletext Dashboard Demo")
    print("=" * 50)
    print("Press F1 to toggle between:")
    print("  • Modern chat interface")
    print("  • Retro Ceefax-style metrics dashboard")
    print("=" * 50)


async def main():
    """Run the full demo."""
    print("🚀 phosphor DEMO SCRIPT")
    print("=" * 50)
    print("This script simulates the key features:")
    print("1. Teletext Dashboard (F1)")
    print("2. Wormhole File Transfer (/send, /grab)")
    print("3. Geiger Counter Audio Feedback")
    print("=" * 50)
    
    await demo_teletext()
    await asyncio.sleep(2)
    
    await demo_wormhole()
    await asyncio.sleep(2)
    
    await simulate_server_death()


if __name__ == "__main__":
    asyncio.run(main())
