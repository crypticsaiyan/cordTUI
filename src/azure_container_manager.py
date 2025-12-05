#!/usr/bin/env python3
"""
Azure Container Manager - Fetches container metadata and health status
"""

import os
import time
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.resource import ResourceManagementClient


class AzureContainerManager:
    """Manages Azure container queries with caching and health checks"""
    
    def __init__(self, subscription_id: str, client_id: str, 
                 client_secret: str, tenant_id: str, resource_group: str):
        """
        Initialize Azure Container Manager
        
        Args:
            subscription_id: Azure subscription ID
            client_id: Service Principal client ID
            client_secret: Service Principal secret
            tenant_id: Azure AD tenant ID
            resource_group: Resource group containing containers
        """
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        
        # Authenticate with Service Principal
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Initialize Azure clients
        self.container_client = ContainerInstanceManagementClient(
            self.credential, 
            subscription_id
        )
        
        # Cache for container metadata (TTL: 30 seconds)
        self.cache = {}
        self.cache_ttl = 30
        self.last_cache_time = None
        
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self.last_cache_time is None:
            return False
        return (datetime.now() - self.last_cache_time).seconds < self.cache_ttl
    
    def get_all_containers(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all container instances in the resource group
        
        Args:
            force_refresh: Force refresh cache
            
        Returns:
            List of container metadata dictionaries
        """
        # Return cached data if valid
        if not force_refresh and self._is_cache_valid() and self.cache:
            return self.cache.get('containers', [])
        
        try:
            containers = []
            container_groups = self.container_client.container_groups.list_by_resource_group(
                self.resource_group
            )
            
            for group in container_groups:
                # Get detailed container group info with instance view
                try:
                    group_detail = self.container_client.container_groups.get(
                        self.resource_group,
                        group.name
                    )
                except Exception as e:
                    print(f"Warning: Could not get details for {group.name}: {e}")
                    group_detail = group
                
                for container in group_detail.containers:
                    # Get IP address
                    ip_address = None
                    ports = []
                    if group_detail.ip_address:
                        ip_address = group_detail.ip_address.ip
                        ports = [p.port for p in group_detail.ip_address.ports]
                    
                    # Determine actual status
                    # Priority: instance_view.current_state > provisioning_state
                    if container.instance_view and container.instance_view.current_state:
                        status = container.instance_view.current_state.state
                        start_time = container.instance_view.current_state.start_time
                        restart_count = container.instance_view.restart_count
                    else:
                        # Fallback to provisioning state
                        status = group_detail.provisioning_state
                        start_time = None
                        restart_count = 0
                    
                    container_info = {
                        'name': container.name,
                        'group_name': group_detail.name,
                        'ip': ip_address,
                        'ports': ports,
                        'state': group_detail.provisioning_state,
                        'status': status,
                        'image': container.image,
                        'cpu': container.resources.requests.cpu,
                        'memory_gb': container.resources.requests.memory_in_gb,
                        'location': group_detail.location,
                        'restart_count': restart_count,
                        'start_time': start_time.isoformat() if start_time else None
                    }
                    containers.append(container_info)
            
            # Update cache
            self.cache['containers'] = containers
            self.last_cache_time = datetime.now()
            
            # Debug output
            print(f"✅ Fetched {len(containers)} containers from Azure")
            for c in containers:
                print(f"   - {c['name']}: status={c['status']}, state={c['state']}")
            
            return containers
            
        except Exception as e:
            print(f"Error fetching containers from Azure: {e}")
            # Return cached data if available
            return self.cache.get('containers', [])
    
    def get_container_by_name(self, name: str) -> Optional[Dict]:
        """Get specific container by name"""
        containers = self.get_all_containers()
        for container in containers:
            if container['name'].lower() == name.lower():
                return container
        return None
    
    def check_container_health(self, ip: str, port: int, 
                              health_path: str = '/health',
                              timeout: int = 5) -> Dict:
        """
        Check container health via HTTP endpoint
        
        Args:
            ip: Container IP address
            port: Container port
            health_path: Health check endpoint path
            timeout: Request timeout in seconds
            
        Returns:
            Health check result dictionary
        """
        if not ip:
            return {
                'healthy': False,
                'error': 'No IP address available',
                'response_time_ms': None
            }
        
        url = f"http://{ip}:{port}{health_path}"
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                'healthy': response.status_code == 200,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
            }
            
        except requests.exceptions.Timeout:
            return {
                'healthy': False,
                'error': 'Health check timed out',
                'response_time_ms': None
            }
        except requests.exceptions.ConnectionError:
            return {
                'healthy': False,
                'error': 'Cannot connect to container',
                'response_time_ms': None
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'response_time_ms': None
            }

    
    def get_container_summary(self, detailed: bool = False) -> str:
        """Get human-readable summary of all containers"""
        containers = self.get_all_containers()
        
        if not containers:
            return "No containers found in resource group."
        
        summary_lines = [f"📦 Found {len(containers)} container(s) in Azure:"]
        summary_lines.append("")
        
        for c in containers:
            # Consider both Running and Succeeded as healthy
            is_running = c['status'] in ['Running', 'Succeeded'] or c['state'] == 'Succeeded'
            status_emoji = "✅" if is_running else "⚠️"
            
            if detailed:
                # Detailed view
                summary_lines.append(f"{status_emoji} {c['name']} ({c['group_name']})")
                summary_lines.append(f"   Status: {c['status']} | State: {c['state']}")
                summary_lines.append(f"   IP: {c['ip'] or 'No public IP'}")
                summary_lines.append(f"   Ports: {', '.join(map(str, c['ports'])) if c['ports'] else 'None'}")
                summary_lines.append(f"   Location: {c['location']}")
                summary_lines.append(f"   Resources: {c['cpu']} CPU, {c['memory_gb']} GB RAM")
                summary_lines.append(f"   Image: {c['image']}")
                if c['restart_count'] > 0:
                    summary_lines.append(f"   ⚠️  Restarts: {c['restart_count']}")
                if c['start_time']:
                    summary_lines.append(f"   Started: {c['start_time']}")
                summary_lines.append("")
            else:
                # Compact view
                ip_info = f"{c['ip']}" if c['ip'] else "No public IP"
                ports_info = f"ports {','.join(map(str, c['ports']))}" if c['ports'] else "no ports"
                summary_lines.append(f"{status_emoji} {c['name']}: {c['status']} | {ip_info} | {ports_info}")
        
        return "\n".join(summary_lines)

    
    def answer_question(self, question: str) -> str:
        """
        Answer natural language questions about containers
        
        Args:
            question: User's question
            
        Returns:
            Human-readable answer
        """
        question_lower = question.lower()
        containers = self.get_all_containers()
        
        if not containers:
            return "❌ No containers found in the Azure resource group.\n\nResource Group: " + self.resource_group + "\n\nCheck:\n• Resource group name is correct\n• Containers exist in this resource group\n• Service Principal has access"
        
        # Empty query or just "containers" - show detailed summary
        if not question_lower or question_lower in ['containers', 'container']:
            return self.get_container_summary(detailed=True)
        
        # List/show all containers
        if any(word in question_lower for word in ['list', 'show all', 'what containers', 'all containers']):
            return self.get_container_summary(detailed=True)
        
        # Detailed info request
        if any(word in question_lower for word in ['detail', 'detailed', 'full', 'complete', 'everything', 'all info']):
            return self.get_container_summary(detailed=True)
        
        # Container status
        if 'status' in question_lower or 'state' in question_lower or 'running' in question_lower:
            # Azure container states: Running, Terminated, Waiting, Succeeded
            # Provisioning states: Succeeded, Failed, Pending
            running = [c for c in containers if c['status'] in ['Running', 'Succeeded'] or c['state'] == 'Succeeded']
            stopped = [c for c in containers if c not in running]
            
            result = [f"📊 Container Status Summary (from Azure API):"]
            result.append("")
            result.append(f"✅ Running: {len(running)}")
            result.append(f"⚠️  Stopped: {len(stopped)}")
            result.append("")
            
            if running:
                result.append("Running containers:")
                for c in running:
                    uptime_info = ""
                    if c['start_time']:
                        uptime_info = f" - Started: {c['start_time']}"
                    restart_info = ""
                    if c['restart_count'] > 0:
                        restart_info = f" ⚠️  ({c['restart_count']} restarts)"
                    result.append(f"  ✅ {c['name']} ({c['location']}){uptime_info}{restart_info}")
                    result.append(f"     {c['ip'] or 'No IP'} | Ports: {', '.join(map(str, c['ports'])) if c['ports'] else 'None'}")
            
            if stopped:
                result.append("")
                result.append("Stopped containers:")
                for c in stopped:
                    result.append(f"  ⚠️  {c['name']} - {c['status']}")
            
            result.append("")
            result.append("💡 This shows Azure API status. For HTTP health checks, use 'check health'")
            
            return "\n".join(result)
        
        # IP addresses
        if 'ip' in question_lower or 'address' in question_lower:
            result = ["🌐 Container IP Addresses:"]
            result.append("")
            for c in containers:
                if c['ip']:
                    result.append(f"✅ {c['name']}: {c['ip']}")
                    if c['ports']:
                        result.append(f"   Ports: {', '.join(map(str, c['ports']))}")
                else:
                    result.append(f"⚠️  {c['name']}: No public IP")
            return "\n".join(result)
        
        # Ports
        if 'port' in question_lower:
            result = ["🔌 Container Ports:"]
            result.append("")
            for c in containers:
                if c['ports']:
                    result.append(f"✅ {c['name']}: {', '.join(map(str, c['ports']))}")
                    if c['ip']:
                        result.append(f"   Access: {c['ip']}:{c['ports'][0]}")
                else:
                    result.append(f"⚠️  {c['name']}: No exposed ports")
            return "\n".join(result)
        
        # Location/region
        if 'location' in question_lower or 'region' in question_lower or 'where' in question_lower:
            locations = {}
            for c in containers:
                loc = c['location']
                if loc not in locations:
                    locations[loc] = []
                locations[loc].append(c)
            
            result = ["📍 Container Locations:"]
            result.append("")
            for loc, conts in locations.items():
                result.append(f"🌍 {loc.upper()}:")
                for c in conts:
                    result.append(f"  • {c['name']} ({c['status']})")
            return "\n".join(result)
        
        # Resources (CPU/Memory)
        if 'resource' in question_lower or 'cpu' in question_lower or 'memory' in question_lower or 'ram' in question_lower:
            result = ["💻 Container Resources:"]
            result.append("")
            total_cpu = 0
            total_mem = 0
            for c in containers:
                result.append(f"📦 {c['name']}:")
                result.append(f"   CPU: {c['cpu']} cores")
                result.append(f"   Memory: {c['memory_gb']} GB")
                result.append(f"   Image: {c['image']}")
                total_cpu += c['cpu']
                total_mem += c['memory_gb']
            result.append("")
            result.append(f"📊 Total: {total_cpu} CPU cores, {total_mem} GB RAM")
            return "\n".join(result)
        
        # Health check
        if 'health' in question_lower:
            result = ["🏥 Container Health Check:"]
            result.append("")
            result.append("Note: Checking /health endpoint on each container...")
            result.append("")
            
            for c in containers:
                if c['ip'] and c['ports']:
                    try:
                        health = self.check_container_health(c['ip'], c['ports'][0])
                        if health['healthy']:
                            result.append(f"✅ {c['name']}: Healthy")
                            result.append(f"   URL: http://{c['ip']}:{c['ports'][0]}/health")
                            result.append(f"   Response time: {health['response_time_ms']}ms")
                        else:
                            error_msg = health.get('error', 'Unhealthy')
                            result.append(f"❌ {c['name']}: {error_msg}")
                            result.append(f"   URL: http://{c['ip']}:{c['ports'][0]}/health")
                            if 'timed out' in error_msg.lower():
                                result.append(f"   💡 Container may not have /health endpoint")
                            elif 'cannot connect' in error_msg.lower():
                                result.append(f"   💡 Check if port {c['ports'][0]} is accessible")
                    except Exception as e:
                        result.append(f"❌ {c['name']}: Error - {str(e)}")
                else:
                    result.append(f"⚠️  {c['name']}: Cannot check (no IP/port)")
                result.append("")
            
            result.append("💡 Health checks require containers to expose /health endpoint")
            result.append("   Container status from Azure API is shown in 'show status'")
            return "\n".join(result)
        
        # Image information
        if 'image' in question_lower or 'docker image' in question_lower:
            result = ["🐳 Container Images:"]
            result.append("")
            for c in containers:
                result.append(f"📦 {c['name']}: {c['image']}")
            return "\n".join(result)
        
        # Restart information
        if 'restart' in question_lower:
            result = ["🔄 Container Restart Counts:"]
            result.append("")
            has_restarts = False
            for c in containers:
                if c['restart_count'] > 0:
                    result.append(f"⚠️  {c['name']}: {c['restart_count']} restarts")
                    has_restarts = True
                else:
                    result.append(f"✅ {c['name']}: No restarts")
            
            if not has_restarts:
                result.append("")
                result.append("All containers are stable! 🎉")
            return "\n".join(result)
        
        # Specific container query (search by name)
        for c in containers:
            if c['name'].lower() in question_lower or c['group_name'].lower() in question_lower:
                result = [f"📦 Container Details: {c['name']}"]
                result.append("")
                result.append(f"Status: {c['status']} ({c['state']})")
                result.append(f"Group: {c['group_name']}")
                result.append(f"Location: {c['location']}")
                result.append("")
                result.append("Network:")
                result.append(f"  IP: {c['ip'] or 'No public IP'}")
                result.append(f"  Ports: {', '.join(map(str, c['ports'])) if c['ports'] else 'None'}")
                result.append("")
                result.append("Resources:")
                result.append(f"  CPU: {c['cpu']} cores")
                result.append(f"  Memory: {c['memory_gb']} GB")
                result.append("")
                result.append(f"Image: {c['image']}")
                result.append(f"Restarts: {c['restart_count']}")
                if c['start_time']:
                    result.append(f"Started: {c['start_time']}")
                return "\n".join(result)
        
        # Default: show detailed summary with helpful suggestions
        result = [self.get_container_summary(detailed=True)]
        result.append("")
        result.append("💡 Try asking:")
        result.append("  • 'show status' - Container status")
        result.append("  • 'what are the IPs?' - IP addresses")
        result.append("  • 'show ports' - Exposed ports")
        result.append("  • 'check health' - Health status")
        result.append("  • 'show resources' - CPU/Memory")
        result.append("  • 'where are containers?' - Locations")
        return "\n".join(result)
