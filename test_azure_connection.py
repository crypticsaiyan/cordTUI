#!/usr/bin/env python3
"""
Test script to verify Azure connection and container access
Run this before starting the bot to ensure everything is configured correctly
"""

import os
import sys
from dotenv import load_dotenv
from src.azure_container_manager import AzureContainerManager


def test_azure_connection():
    """Test Azure authentication and container access"""
    
    print("=" * 60)
    print("Azure Connection Test")
    print("=" * 60)
    print()
    
    # Load environment
    load_dotenv()
    
    # Check required variables
    required_vars = [
        'AZURE_SUBSCRIPTION_ID',
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET',
        'AZURE_TENANT_ID',
        'AZURE_RESOURCE_GROUP'
    ]
    
    print("1. Checking environment variables...")
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"   ❌ {var}: Not set")
        else:
            # Show partial value for security
            display_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"   ✅ {var}: {display_value}")
    
    if missing:
        print()
        print("❌ Missing required environment variables!")
        print("   Please edit .env file with your Azure credentials.")
        return False
    
    print()
    
    # Test Azure authentication
    print("2. Testing Azure authentication...")
    try:
        manager = AzureContainerManager(
            subscription_id=os.getenv('AZURE_SUBSCRIPTION_ID'),
            client_id=os.getenv('AZURE_CLIENT_ID'),
            client_secret=os.getenv('AZURE_CLIENT_SECRET'),
            tenant_id=os.getenv('AZURE_TENANT_ID'),
            resource_group=os.getenv('AZURE_RESOURCE_GROUP')
        )
        print("   ✅ Authentication successful")
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
        return False
    
    print()
    
    # Test container access
    print("3. Fetching container information...")
    try:
        containers = manager.get_all_containers()
        print(f"   ✅ Found {len(containers)} container(s)")
        
        if containers:
            print()
            print("Container Details:")
            print("-" * 60)
            for c in containers:
                print(f"   Name: {c['name']}")
                print(f"   Status: {c['status']}")
                print(f"   IP: {c['ip'] or 'No public IP'}")
                print(f"   Ports: {', '.join(map(str, c['ports'])) if c['ports'] else 'None'}")
                print(f"   Location: {c['location']}")
                print(f"   Resources: {c['cpu']} CPU, {c['memory_gb']} GB RAM")
                print("-" * 60)
        else:
            print()
            print("   ⚠️  No containers found in resource group")
            print(f"   Resource Group: {os.getenv('AZURE_RESOURCE_GROUP')}")
            print()
            print("   Possible reasons:")
            print("   - Resource group is empty")
            print("   - Wrong resource group name")
            print("   - Service Principal doesn't have access")
            
    except Exception as e:
        print(f"   ❌ Failed to fetch containers: {e}")
        return False
    
    print()
    
    # Test health check (if containers have IPs)
    if containers:
        print("4. Testing health check capability...")
        tested = False
        for c in containers:
            if c['ip'] and c['ports']:
                tested = True
                print(f"   Testing {c['name']} at {c['ip']}:{c['ports'][0]}...")
                health = manager.check_container_health(c['ip'], c['ports'][0])
                
                if health['healthy']:
                    print(f"   ✅ Healthy (response time: {health['response_time_ms']}ms)")
                else:
                    print(f"   ⚠️  {health.get('error', 'Unhealthy')}")
                    print(f"      This is OK if container doesn't have /health endpoint")
        
        if not tested:
            print("   ⚠️  No containers with public IP to test")
            print("      Health checks will not work without public IPs")
    
    print()
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print()
    print("You can now start the bot:")
    print("  python3 kiro_azure_irc_bot.py")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = test_azure_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
