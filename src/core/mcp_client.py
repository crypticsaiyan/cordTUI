"""MCP (Model Context Protocol) client for AI integration."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

from src.core.devops_health_bot import DevOpsHealthBot
from src.core.azure_bot_client import AzureBotClient


class MCPClient:
    """Client for executing MCP commands."""
    
    def __init__(self):
        self.tools = {
            "analyze-db": self._analyze_db,
            "docker-stats": self._docker_stats,
            "docker-health": self._docker_health,
            "azure-containers": self._azure_containers,
            "system-info": self._system_info,
            "list-files": self._list_files,
            "read-file": self._read_file,
            "search-files": self._search_files,
        }
        
        # Initialize DevOps Health Bot
        self.health_bot = DevOpsHealthBot(mcp_tools={})
        
        # Initialize Azure Bot Client
        self.azure_client = AzureBotClient()
        
        # Print Azure status
        if self.azure_client.is_available():
            print(f"🔵 Azure integration: {self.azure_client.get_status()}")
        else:
            print("⚪ Azure integration: Not configured (using Docker fallback)")
    
    async def execute(self, prompt: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an MCP command based on natural language prompt."""
        # Parse the prompt to determine which tool to use
        prompt_lower = prompt.lower().strip()
        
        # PRIORITY 1: If Azure is configured, use it for container queries
        if self.azure_client.is_available():
            # Check if this is a container-related query
            container_keywords = ["container", "list", "ip", "port", "status", "running", 
                                "health", "check", "show", "what", "region", "location",
                                "resource", "cpu", "memory", "azure"]
            
            # If empty prompt or contains container keywords, use Azure
            if not prompt_lower or any(keyword in prompt_lower for keyword in container_keywords):
                # Route to Azure
                return await self.azure_client.query(prompt)
        
        # FALLBACK: If Azure not configured or query is not container-related
        
        # If empty prompt or generic health check, default to docker health
        if not prompt_lower or prompt_lower in ["health", "check", "status"]:
            # Default behavior: check Docker health (fallback)
            return await self._docker_health({"prompt": prompt_lower})
        
        # Check if this is a question (starts with what, why, how, explain, etc.)
        question_words = ["what", "why", "how", "explain", "tell me", "show me", "describe", "when", "where", "who"]
        is_question = any(prompt_lower.startswith(word) for word in question_words)
        
        if is_question:
            # Handle questions with helpful responses
            return self._handle_question(prompt, prompt_lower)
        
        # Match prompt to tools
        # Be more specific about Docker health checks
        if any(keyword in prompt_lower for keyword in ["docker"]):
            # Docker-related queries (explicit)
            if "stats" in prompt_lower:
                tool = "docker-stats"
            else:
                tool = "docker-health"
        elif any(keyword in prompt_lower for keyword in ["prod", "staging", "dev"]) and not is_question:
            # Environment filters for health checks
            tool = "docker-health"
        elif "system" in prompt_lower or "uname" in prompt_lower or "os" in prompt_lower:
            tool = "system-info"
        elif "database" in prompt_lower or "db" in prompt_lower:
            tool = "analyze-db"
        elif "list" in prompt_lower or "ls" in prompt_lower or "dir" in prompt_lower:
            tool = "list-files"
        elif "read" in prompt_lower or "cat" in prompt_lower:
            tool = "read-file"
        elif "search" in prompt_lower or "find" in prompt_lower:
            tool = "search-files"
        elif "help" in prompt_lower:
            return {"message": self._get_help_text()}
        else:
            # For ambiguous queries, provide guidance instead of defaulting
            return self._handle_ambiguous_query(prompt)
        
        if tool not in self.tools:
            return {
                "error": f"I don't understand '{prompt}'. Try: /ai help"
            }
        
        try:
            # Extract arguments from prompt
            prompt_args = prompt.split(maxsplit=1)
            if len(prompt_args) > 1:
                args = args or {}
                args["prompt"] = prompt_args[1].strip()
            else:
                args = args or {}
                args["prompt"] = prompt_lower
            
            result = await self.tools[tool](args or {})
            # Add a friendly message
            if "error" not in result:
                result["command"] = tool
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _handle_question(self, prompt: str, prompt_lower: str) -> Dict[str, Any]:
        """Handle question-type queries with helpful responses."""
        # Docker health-related questions
        if "healthy" in prompt_lower or "health" in prompt_lower:
            return {"message": self._explain_health_status()}
        elif "restart" in prompt_lower:
            return {"message": self._explain_restarts()}
        elif "log" in prompt_lower:
            return {"message": self._explain_logs()}
        elif "container" in prompt_lower or "docker" in prompt_lower:
            return {"message": self._explain_docker_basics()}
        else:
            # Generic question response
            return {"message": f"""I'm a DevOps Health Bot focused on Docker container monitoring.

Your question: "{prompt}"

I can help with:
• Docker container health checks
• Container status and restarts
• System information
• File operations

For Docker health: /ai check docker
For help: /ai help

Note: I don't have a general AI model to answer arbitrary questions.
I'm specialized in DevOps monitoring tasks."""}
    
    def _handle_ambiguous_query(self, prompt: str) -> Dict[str, Any]:
        """Handle ambiguous queries that don't match any tool."""
        return {"message": f"""I'm not sure what to do with: "{prompt}"

I can help with:

**Docker Health Checks:**
• /ai - Check all containers
• /ai prod - Check production
• /ai staging web - Check staging web

**Questions I Can Answer:**
• /ai private explain what "healthy" means
• /ai private explain restart counts
• /ai private explain how to check logs

**File Operations:**
• /ai list-files [path]
• /ai read-file <path>

**Other:**
• /ai system-info
• /ai help

Try one of these commands or ask a specific question about Docker health!"""}
    
    def _explain_health_status(self) -> str:
        """Explain Docker health status."""
        return """**Docker Health Status Explained:**

**Healthy** ✅
- Container is running
- Health check command succeeds (exit code 0)
- Has been passing consistently

**Unhealthy** ❌
- Container is running
- Health check command fails (exit code 1)
- May indicate service issues

**Starting** 🔄
- Container just started
- Health check hasn't completed yet
- Wait a moment and check again

**No Health Check** ⚪
- Container has no HEALTHCHECK defined
- Status based on running/stopped only

**Example Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \\
  CMD curl -f http://localhost/ || exit 1
```

This checks every 30 seconds if the web server responds.

**To check your containers:**
/ai check docker health"""
    
    def _explain_restarts(self) -> str:
        """Explain container restart counts."""
        return """**Container Restart Count Explained:**

**What it means:**
The restart count shows how many times Docker has automatically restarted a container.

**Why containers restart:**
1. **Crash** - Process exits with non-zero code
2. **Health check failure** - Repeated health check failures
3. **OOM (Out of Memory)** - Container runs out of memory
4. **Manual restart** - You or a script restarted it

**What's normal:**
• 0 restarts = Good! Container is stable
• 1-2 restarts = Acceptable (maybe during deployment)
• 3+ restarts = Warning! Something is wrong
• 10+ restarts = Critical! Container is crash-looping

**How to investigate:**
```bash
# Check logs for errors
docker logs <container-name>

# Check exit code
docker inspect <container-name> | grep ExitCode

# Check resource usage
docker stats <container-name>
```

**To check your containers:**
/ai check docker health"""
    
    def _explain_logs(self) -> str:
        """Explain how to check container logs."""
        return """**How to Check Container Logs:**

**View recent logs:**
```bash
docker logs <container-name>
```

**Follow logs in real-time:**
```bash
docker logs -f <container-name>
```

**Show last 100 lines:**
```bash
docker logs --tail 100 <container-name>
```

**Show logs with timestamps:**
```bash
docker logs -t <container-name>
```

**Show logs since a time:**
```bash
docker logs --since 10m <container-name>  # Last 10 minutes
docker logs --since 2h <container-name>   # Last 2 hours
```

**Common log locations inside containers:**
- `/var/log/` - System logs
- `/var/log/nginx/` - Nginx logs
- `/var/log/apache2/` - Apache logs
- Application-specific locations

**To see which containers need attention:**
/ai check docker health

Then check logs for any unhealthy or restarting containers."""
    
    def _explain_docker_basics(self) -> str:
        """Explain Docker basics."""
        return """**Docker Container Basics:**

**What is a container?**
A lightweight, standalone package that includes everything needed to run an application: code, runtime, libraries, and dependencies.

**Container States:**
• **Running** - Container is active and executing
• **Exited** - Container stopped (may be normal or error)
• **Restarting** - Container is restarting (may indicate issues)
• **Paused** - Container is paused (rare)

**Common Commands:**
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Check container health
docker inspect <container-name>

# View container logs
docker logs <container-name>

# Check resource usage
docker stats <container-name>

# Start a stopped container
docker start <container-name>

# Stop a running container
docker stop <container-name>

# Restart a container
docker restart <container-name>
```

**To check your containers with this bot:**
/ai check docker health"""
    
    def _get_help_text(self) -> str:
        """Get help text for available commands."""
        azure_status = ""
        if self.azure_client.is_available():
            azure_status = "\n**🔵 Azure Container Instances (Active):**\n• /ai list containers - List all Azure containers\n• /ai what is the IP of <name>? - Get container IP\n• /ai check health - Check container health\n• /ai show status - Show container status\n• /ai what ports are exposed? - List exposed ports\n"
        
        return f"""🤖 DevOps Health Bot - Available Commands:
{azure_status}
**Docker Health Checks:**
• /ai docker - Check all Docker containers
• /ai docker prod - Check production containers
• /ai docker staging web - Check staging web containers

**Questions I Can Answer:**
• /ai private explain what "healthy" means
• /ai private explain restart counts
• /ai private explain how to check logs

**File Operations:**
• /ai list-files [path] - List directory contents
• /ai read-file <path> - Read file contents
• /ai search-files <pattern> - Search for files

**Other Tools:**
• /ai docker-stats - Raw Docker statistics
• /ai system-info - System information

**Examples:**
• /ai list containers (Azure if configured, Docker otherwise)
• /ai docker prod api (explicitly Docker)
• /ai private explain healthy
• /ai list-files /var/log

**Note:** {'Azure integration active! Container queries go to Azure.' if self.azure_client.is_available() else 'Azure not configured. Using Docker fallback.'}"""
    
    async def _analyze_db(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze database (dummy implementation)."""
        return {
            "status": "healthy",
            "tables": 42,
            "connections": 15,
            "query_time_avg": "23ms"
        }
    
    async def _azure_containers(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Query Azure Container Instances."""
        prompt = args.get("prompt", "list containers")
        return await self.azure_client.query(prompt)
    
    async def _docker_health(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check Docker container health using DevOps Health Bot."""
        user_prompt = args.get("prompt", "")
        try:
            health_report = await self.health_bot.check_health(user_prompt)
            return {"message": health_report}
        except Exception as e:
            return {"error": f"Health check failed: {str(e)}"}
    
    async def _docker_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get Docker container stats."""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                stats = [json.loads(line) for line in lines if line]
                return {"containers": stats}
            elif "permission denied" in result.stderr.lower():
                return {"error": "Docker permission denied. See FIX_DOCKER_PERMISSIONS.md"}
            return {"error": "Docker not available"}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"error": "Docker not available"}
    
    async def _system_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information."""
        try:
            result = subprocess.run(
                ["uname", "-a"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return {"system": result.stdout.strip()}
        except Exception as e:
            return {"error": str(e)}
    
    async def _list_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a directory using filesystem."""
        path = args.get("path", ".")
        try:
            target_path = Path(path)
            if not target_path.exists():
                return {"error": f"Path not found: {path}"}
            
            if target_path.is_file():
                return {"error": f"{path} is a file, not a directory"}
            
            files = []
            dirs = []
            for item in sorted(target_path.iterdir()):
                if item.is_dir():
                    dirs.append(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    files.append(f"📄 {item.name} ({size_str})")
            
            result = {
                "path": str(path),
                "directories": len(dirs),
                "files": len(files),
                "items": dirs + files
            }
            
            # Format as readable message
            items_str = "\n".join(result["items"][:20])  # Limit to 20 items
            if len(result["items"]) > 20:
                items_str += f"\n... and {len(result['items']) - 20} more items"
            
            return {
                "message": f"**Directory: {path}**\n\n{items_str}\n\n{len(dirs)} directories, {len(files)} files"
            }
        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}
    
    async def _read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents using filesystem."""
        path = args.get("path")
        if not path:
            return {"error": "Please specify a file path. Example: /ai read-file README.md"}
        
        try:
            file_path = Path(path)
            if not file_path.exists():
                return {"error": f"File not found: {path}"}
            
            if file_path.is_dir():
                return {"error": f"{path} is a directory. Use list-files instead."}
            
            # Read file with size limit
            max_size = 50000  # 50KB limit for display
            if file_path.stat().st_size > max_size:
                return {"error": f"File too large ({self._format_size(file_path.stat().st_size)}). Max: 50KB"}
            
            content = file_path.read_text(encoding='utf-8', errors='replace')
            
            # Limit lines for display
            lines = content.split('\n')
            if len(lines) > 100:
                content = '\n'.join(lines[:100]) + f"\n\n... ({len(lines) - 100} more lines)"
            
            return {
                "message": f"**File: {path}**\n\n```\n{content}\n```"
            }
        except UnicodeDecodeError:
            return {"error": f"Cannot read {path}: binary file"}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    async def _search_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files by pattern."""
        pattern = args.get("path", "")
        if not pattern:
            return {"error": "Please specify a search pattern. Example: /ai search-files *.py"}
        
        try:
            matches = list(Path(".").rglob(pattern))[:50]  # Limit to 50 results
            
            if not matches:
                return {"message": f"No files found matching: {pattern}"}
            
            files_str = "\n".join([f"📄 {m}" for m in matches])
            return {
                "message": f"**Found {len(matches)} files matching '{pattern}':**\n\n{files_str}"
            }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
