"""MCP (Model Context Protocol) client for AI integration."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

from src.core.devops_health_bot import DevOpsHealthBot


class MCPClient:
    """Client for executing MCP commands."""
    
    def __init__(self):
        self.tools = {
            "analyze-db": self._analyze_db,
            "docker-stats": self._docker_stats,
            "docker-health": self._docker_health,
            "system-info": self._system_info,
            "list-files": self._list_files,
            "read-file": self._read_file,
            "search-files": self._search_files,
        }
        
        # Initialize DevOps Health Bot
        self.health_bot = DevOpsHealthBot(mcp_tools={})
    
    async def execute(self, prompt: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an MCP command based on natural language prompt."""
        # Parse the prompt to determine which tool to use
        prompt_lower = prompt.lower().strip()
        
        # If empty prompt or generic health check, default to docker health
        if not prompt_lower or prompt_lower in ["health", "check", "status"]:
            # Default behavior: check Docker health
            return await self._docker_health({"prompt": prompt_lower})
        
        # Match prompt to tools
        # Priority: Docker health checks for most queries
        if any(keyword in prompt_lower for keyword in ["docker", "container", "health", "check", "status", "prod", "staging"]):
            tool = "docker-health"
        elif "stats" in prompt_lower and "docker" in prompt_lower:
            tool = "docker-stats"
        elif "system" in prompt_lower or "uname" in prompt_lower or "os" in prompt_lower:
            tool = "system-info"
        elif "database" in prompt_lower or "db" in prompt_lower:
            tool = "analyze-db"
        elif "list" in prompt_lower or "ls" in prompt_lower or "dir" in prompt_lower:
            tool = "list-files"
        elif "read" in prompt_lower or "cat" in prompt_lower or "show" in prompt_lower:
            tool = "read-file"
        elif "search" in prompt_lower or "find" in prompt_lower:
            tool = "search-files"
        elif "help" in prompt_lower:
            return {"message": self._get_help_text()}
        else:
            # Default to docker health for ambiguous queries
            tool = "docker-health"
        
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
    
    def _get_help_text(self) -> str:
        """Get help text for available commands."""
        return """🤖 DevOps Health Bot - Available Commands:

**Docker Health (Default):**
• /ai - Check all Docker containers
• /ai prod - Check production containers
• /ai staging web - Check staging web containers
• /ai docker health - Full health report

**Other Tools:**
• /ai docker-stats - Raw Docker statistics
• /ai system-info - System information
• /ai list-files [path] - List directory contents
• /ai read-file <path> - Read file contents

**Examples:**
• /ai
• /ai prod api
• /ai check docker health"""
    
    async def _analyze_db(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze database (dummy implementation)."""
        return {
            "status": "healthy",
            "tables": 42,
            "connections": 15,
            "query_time_avg": "23ms"
        }
    
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
