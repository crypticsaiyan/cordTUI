#!/usr/bin/env python3
"""
Azure Bot Client - Integrates Azure Container Manager with MCP
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv


class AzureBotClient:
    """Client for querying Azure Container Instances"""
    
    def __init__(self):
        """Initialize Azure Bot Client"""
        load_dotenv()
        
        # Check if Azure is configured
        self.azure_configured = all([
            os.getenv('AZURE_SUBSCRIPTION_ID'),
            os.getenv('AZURE_CLIENT_ID'),
            os.getenv('AZURE_CLIENT_SECRET'),
            os.getenv('AZURE_TENANT_ID'),
            os.getenv('AZURE_RESOURCE_GROUP')
        ])
        
        self.azure_manager = None
        
        if self.azure_configured:
            try:
                # Import here to avoid errors if Azure SDK not installed
                import sys
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from src.azure_container_manager import AzureContainerManager
                
                self.azure_manager = AzureContainerManager(
                    subscription_id=os.getenv('AZURE_SUBSCRIPTION_ID'),
                    client_id=os.getenv('AZURE_CLIENT_ID'),
                    client_secret=os.getenv('AZURE_CLIENT_SECRET'),
                    tenant_id=os.getenv('AZURE_TENANT_ID'),
                    resource_group=os.getenv('AZURE_RESOURCE_GROUP')
                )
                print("✅ Azure Container Manager initialized")
            except ImportError as e:
                print(f"⚠️  Azure SDK not installed: {e}")
                print("   Install with: pip install azure-identity azure-mgmt-containerinstance")
                self.azure_configured = False
            except Exception as e:
                print(f"⚠️  Failed to initialize Azure: {e}")
                self.azure_configured = False
    
    def is_available(self) -> bool:
        """Check if Azure integration is available"""
        return self.azure_configured and self.azure_manager is not None
    
    async def query(self, prompt: str) -> Dict[str, Any]:
        """
        Query Azure containers
        
        Args:
            prompt: User's question
            
        Returns:
            Dictionary with 'message' or 'error'
        """
        if not self.is_available():
            return {
                "error": "Azure not configured. Please set up .env with Azure credentials."
            }
        
        try:
            # Get answer from Azure Container Manager
            answer = self.azure_manager.answer_question(prompt)
            
            return {
                "message": answer,
                "source": "azure"
            }
            
        except Exception as e:
            return {
                "error": f"Azure query failed: {str(e)}"
            }
    
    def get_status(self) -> str:
        """Get Azure integration status"""
        if not self.azure_configured:
            return "❌ Azure not configured"
        
        if not self.azure_manager:
            return "❌ Azure manager not initialized"
        
        try:
            containers = self.azure_manager.get_all_containers()
            return f"✅ Azure connected ({len(containers)} containers)"
        except Exception as e:
            return f"⚠️  Azure error: {str(e)}"
