"""DevOps Health Bot - Automated Docker container health monitoring."""

import asyncio
import json
from typing import Dict, List, Any, Optional


class ContainerHealth:
    """Container health assessment."""
    
    def __init__(self, name: str, status: str):
        self.name = name
        self.status = status
        self.health_status = None
        self.restart_count = 0
        self.uptime = None
        self.cpu_percent = None
        self.memory_usage = None
        self.issues = []
        self.severity = "healthy"  # healthy, warning, critical
    
    def assess(self):
        """Assess overall health based on collected metrics."""
        if self.status != "running":
            self.severity = "critical"
            self.issues.append(f"Container not running (status: {self.status})")
            return
        
        if self.health_status == "unhealthy":
            self.severity = "critical"
            self.issues.append("Health check failed")
        elif self.health_status == "starting":
            self.severity = "warning"
            self.issues.append("Health check still starting")
        
        if self.restart_count > 3:
            self.severity = "critical" if self.severity != "critical" else self.severity
            self.issues.append(f"High restart count: {self.restart_count}")
        elif self.restart_count > 0:
            if self.severity == "healthy":
                self.severity = "warning"
            self.issues.append(f"Restart count: {self.restart_count}")
        
        if self.cpu_percent and self.cpu_percent > 80:
            if self.severity == "healthy":
                self.severity = "warning"
            self.issues.append(f"High CPU: {self.cpu_percent:.1f}%")
        
        if self.memory_usage:
            # Parse memory usage like "512MiB / 2GiB"
            try:
                parts = self.memory_usage.split("/")
                if len(parts) == 2:
                    used = self._parse_memory(parts[0].strip())
                    total = self._parse_memory(parts[1].strip())
                    if used and total:
                        percent = (used / total) * 100
                        if percent > 90:
                            if self.severity == "healthy":
                                self.severity = "warning"
                            self.issues.append(f"High memory: {percent:.1f}%")
            except:
                pass
    
    def _parse_memory(self, mem_str: str) -> Optional[float]:
        """Parse memory string to bytes."""
        mem_str = mem_str.strip()
        multipliers = {
            'B': 1,
            'KiB': 1024,
            'MiB': 1024**2,
            'GiB': 1024**3,
            'KB': 1000,
            'MB': 1000**2,
            'GB': 1000**3
        }
        
        for unit, mult in multipliers.items():
            if mem_str.endswith(unit):
                try:
                    value = float(mem_str[:-len(unit)].strip())
                    return value * mult
                except:
                    return None
        return None


class DevOpsHealthBot:
    """AI bot for automated Docker health monitoring."""
    
    def __init__(self, mcp_tools: Dict[str, Any] = None):
        """Initialize with MCP tools."""
        self.mcp_tools = mcp_tools or {}
    
    async def check_health(self, user_prompt: str = "") -> str:
        """
        Main entry point for health checks.
        
        Args:
            user_prompt: Optional user hint (e.g., "prod", "web-api", "check docker")
        
        Returns:
            IRC-friendly health summary
        """
        # Parse user intent
        filter_env = None
        filter_service = None
        
        prompt_lower = user_prompt.lower()
        if "prod" in prompt_lower:
            filter_env = "prod"
        elif "staging" in prompt_lower or "stage" in prompt_lower:
            filter_env = "staging"
        elif "dev" in prompt_lower:
            filter_env = "dev"
        
        # Extract service name hints
        for keyword in ["web", "api", "db", "database", "worker", "redis", "nginx", "payments"]:
            if keyword in prompt_lower:
                filter_service = keyword
                break
        
        # Step 1: Discover containers
        containers = await self._discover_containers()
        
        if not containers:
            return """❌ No Docker containers found or Docker permission denied.

If you can run 'sudo docker ps' but not 'docker ps', you need to:

1. Add yourself to docker group:
   sudo usermod -aG docker $USER

2. Log out and back in (or run: newgrp docker)

3. Verify: docker ps

See FIX_DOCKER_PERMISSIONS.md for details."""
        
        # Step 2: Filter containers based on user hint
        filtered = self._filter_containers(containers, filter_env, filter_service)
        
        if not filtered:
            # Get container names properly - handle both formats
            available_names = []
            for c in containers[:5]:
                name = c.get("Names", c.get("name", c.get("ID", "unknown")))
                if name and name != "unknown":
                    available_names.append(name[:20])
            available = ", ".join(available_names) if available_names else "none"
            return f"No containers matched your query.\n\nAvailable: {available}"
        
        # Step 3: Inspect each container's health
        health_results = []
        for container in filtered:
            health = await self._inspect_container_health(container)
            health_results.append(health)
        
        # Step 4: Format IRC-friendly response
        return self._format_health_report(health_results, user_prompt)
    
    async def _discover_containers(self) -> List[Dict[str, Any]]:
        """Discover Docker containers using MCP tool."""
        if "list_containers" not in self.mcp_tools:
            # Fallback: try subprocess
            return await self._fallback_list_containers()
        
        try:
            tool = self.mcp_tools["list_containers"]
            result = await tool(all=True)  # List all containers, not just running
            
            if isinstance(result, dict) and "containers" in result:
                return result["containers"]
            elif isinstance(result, list):
                return result
            
            return []
        except Exception as e:
            print(f"Error listing containers: {e}")
            return await self._fallback_list_containers()
    
    async def _fallback_list_containers(self) -> List[Dict[str, Any]]:
        """Fallback: use docker CLI directly."""
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                containers = []
                for line in lines:
                    if line:
                        try:
                            containers.append(json.loads(line))
                        except:
                            pass
                return containers
            elif "permission denied" in result.stderr.lower():
                print("Docker permission denied. Run: sudo usermod -aG docker $USER")
                print("Then log out and back in. See FIX_DOCKER_PERMISSIONS.md")
        except Exception as e:
            print(f"Fallback list failed: {e}")
        
        return []
    
    def _filter_containers(
        self,
        containers: List[Dict[str, Any]],
        env: Optional[str],
        service: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Filter containers based on environment and service hints."""
        if not env and not service:
            return containers  # No filter, return all
        
        filtered = []
        for container in containers:
            name = container.get("Names", container.get("name", "")).lower()
            labels = container.get("Labels", {})
            
            # Labels might be a string (comma-separated) or dict, normalize it
            if isinstance(labels, str):
                # Parse comma-separated labels like "env=prod,app=web"
                label_dict = {}
                for label in labels.split(","):
                    if "=" in label:
                        key, val = label.split("=", 1)
                        label_dict[key.strip()] = val.strip()
                labels = label_dict
            elif not isinstance(labels, dict):
                labels = {}
            
            # Check environment filter
            if env:
                env_match = (
                    env in name or
                    labels.get("environment", "").lower() == env or
                    labels.get("env", "").lower() == env
                )
                if not env_match:
                    continue
            
            # Check service filter
            if service:
                service_match = service in name
                if not service_match:
                    continue
            
            filtered.append(container)
        
        return filtered
    
    async def _inspect_container_health(self, container: Dict[str, Any]) -> ContainerHealth:
        """Inspect a single container's health."""
        container_id = container.get("ID", container.get("id", ""))
        name = container.get("Names", container.get("name", ""))
        if not name:
            name = container_id[:12] if container_id else "unknown"
        status = container.get("State", container.get("status", "unknown")).lower()
        
        health = ContainerHealth(name, status)
        
        # Try to extract uptime from Status field (e.g., "Up 4 minutes")
        status_text = container.get("Status", "")
        if status_text and status_text.startswith("Up "):
            health.uptime = status_text[3:]  # Remove "Up " prefix
        
        # Try to get detailed inspection
        if "inspect_container" in self.mcp_tools:
            try:
                tool = self.mcp_tools["inspect_container"]
                details = await tool(container_id=container_id)
                
                # Extract health info from inspection
                if isinstance(details, dict):
                    state = details.get("State", {})
                    health.restart_count = state.get("RestartCount", 0)
                    
                    # Health status
                    health_info = state.get("Health", {})
                    health.health_status = health_info.get("Status")
                    
                    # Uptime
                    started_at = state.get("StartedAt")
                    if started_at:
                        health.uptime = self._calculate_uptime(started_at)
            except Exception as e:
                print(f"Error inspecting {name}: {e}")
        
        # Try to get stats
        if "get_container_stats" in self.mcp_tools:
            try:
                tool = self.mcp_tools["get_container_stats"]
                stats = await tool(container_id=container_id)
                
                if isinstance(stats, dict):
                    health.cpu_percent = stats.get("cpu_percent")
                    health.memory_usage = stats.get("memory_usage")
            except Exception as e:
                print(f"Error getting stats for {name}: {e}")
        
        # Assess overall health
        health.assess()
        
        return health
    
    def _calculate_uptime(self, started_at: str) -> str:
        """Calculate uptime from ISO timestamp."""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            now = datetime.now(start.tzinfo)
            delta = now - start
            
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            
            if days > 0:
                return f"{days}d {hours}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "unknown"
    
    def _format_health_report(self, health_results: List[ContainerHealth], user_prompt: str) -> str:
        """Format health results for IRC."""
        # Count by severity
        healthy = sum(1 for h in health_results if h.severity == "healthy")
        warning = sum(1 for h in health_results if h.severity == "warning")
        critical = sum(1 for h in health_results if h.severity == "critical")
        
        # Build summary
        lines = []
        lines.append("🏥 Docker Health Check")
        lines.append("=" * 40)
        
        # Overall summary
        if critical > 0:
            emoji = "🔴"
        elif warning > 0:
            emoji = "🟡"
        else:
            emoji = "🟢"
        
        lines.append(f"{emoji} Summary: {healthy} healthy, {warning} warning, {critical} critical")
        lines.append("")
        
        # Details for each container
        lines.append("Details:")
        for h in health_results:
            emoji = {"healthy": "✅", "warning": "⚠️", "critical": "❌"}[h.severity]
            
            status_parts = [h.status.upper()]
            if h.health_status:
                status_parts.append(f"health={h.health_status}")
            if h.uptime:
                status_parts.append(f"up {h.uptime}")
            if h.restart_count > 0:
                status_parts.append(f"restarts={h.restart_count}")
            
            status_str = ", ".join(status_parts)
            lines.append(f"{emoji} {h.name}: {status_str}")
            
            # Add issues if any
            for issue in h.issues:
                lines.append(f"   └─ {issue}")
        
        # Recommendations
        if critical > 0 or warning > 0:
            lines.append("")
            lines.append("Recommended actions:")
            
            if critical > 0:
                lines.append("• Check logs for critical containers: docker logs <container>")
                lines.append("• Investigate recent deployments or config changes")
            
            if warning > 0:
                lines.append("• Monitor warned containers for degradation")
                lines.append("• Consider scaling if resource usage is high")
        
        return "\n".join(lines)
