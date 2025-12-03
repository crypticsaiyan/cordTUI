#!/usr/bin/env python3
"""
Kiro IRC Bridge - DevOps AI Bot
Connects IRC to Kiro CLI with MCP tools for automated DevOps assistance.
"""

import asyncio
import json
import subprocess
import sys
from typing import Optional
import miniirc


class KiroIRCBridge:
    """Bridge between IRC and Kiro CLI with MCP tools."""
    
    def __init__(self, config: dict):
        self.config = config
        self.irc = None
        self.sessions = {}  # Track conversation context per channel/user
        
    def connect(self):
        """Connect to IRC server."""
        server = self.config["irc"]
        
        self.irc = miniirc.IRC(
            ip=server["host"],
            port=server["port"],
            nick=server["nick"],
            channels=server["channels"],
            ssl=server.get("ssl", False),
            debug=server.get("debug", False),
            quit_message="Kiro bridge shutting down"
        )
        
        # Register message handler
        @self.irc.Handler('PRIVMSG')
        def handle_message(irc, hostmask, args):
            nick = hostmask[0]
            target = args[0]  # Channel or bot nick (for DMs)
            message = args[1]
            
            # Ignore our own messages
            if nick == server["nick"]:
                return
            
            # Check if this is a command for us
            is_dm = target == server["nick"]
            is_command = message.startswith(self.config["command_prefix"])
            
            if is_command or is_dm:
                asyncio.create_task(self._handle_ai_request(
                    nick, target, message, is_dm
                ))
        
        print(f"✓ Connected to {server['host']}:{server['port']} as {server['nick']}")
        print(f"✓ Joined channels: {', '.join(server['channels'])}")
        print(f"✓ Listening for commands: {self.config['command_prefix']}<prompt>")
        print("✓ Bridge is running. Press Ctrl+C to stop.\n")
    
    async def _handle_ai_request(self, nick: str, target: str, message: str, is_dm: bool):
        """Handle an AI request from IRC."""
        # Extract the prompt
        if message.startswith(self.config["command_prefix"]):
            prompt = message[len(self.config["command_prefix"]):].strip()
        else:
            prompt = message.strip()
        
        if not prompt:
            return
        
        # Determine where to respond
        reply_target = nick if is_dm else target
        
        # Show typing indicator
        self.irc.msg(reply_target, f"🤖 Processing: {prompt[:50]}...")
        
        try:
            # Call Kiro with MCP tools
            result = await self._call_kiro(nick, reply_target, prompt)
            
            # Send response back to IRC
            self._send_multiline(reply_target, result)
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.irc.msg(reply_target, error_msg)
            print(f"Error processing request: {e}", file=sys.stderr)
    
    async def _call_kiro(self, user: str, channel: str, prompt: str) -> str:
        """Call Kiro CLI with MCP tools."""
        # Build the full prompt with context
        full_prompt = self._build_prompt(user, channel, prompt)
        
        # Prepare Kiro CLI command
        kiro_config = self.config.get("kiro", {})
        agent = kiro_config.get("agent", "ops-ai")
        
        # Call Kiro CLI as subprocess
        # Note: Adjust this command based on your Kiro CLI installation
        cmd = [
            "kiro",
            "chat",
            "--agent", agent,
            "--once",  # Single response mode
            "--json"   # JSON output for parsing
        ]
        
        try:
            # Run Kiro CLI
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(input=full_prompt.encode())
            
            if process.returncode != 0:
                error = stderr.decode().strip()
                return f"Kiro CLI error: {error}"
            
            # Parse JSON response
            response = json.loads(stdout.decode())
            return self._format_response(response)
            
        except FileNotFoundError:
            return "❌ Kiro CLI not found. Please install Kiro first."
        except json.JSONDecodeError:
            # Fallback: return raw output
            return stdout.decode().strip()
    
    def _build_prompt(self, user: str, channel: str, prompt: str) -> str:
        """Build a full prompt with context for Kiro."""
        context = f"""You are a DevOps AI assistant in IRC channel {channel}.
User {user} asked: {prompt}

Use MCP tools to investigate and provide a concise summary:
- @filesystem: Read logs from /var/log/
- @postgres: Query production database (READ ONLY)
- @docker: Check container status

IMPORTANT:
- Be concise (IRC has line limits)
- Use bullet points for clarity
- Suggest actionable next steps
- NEVER run destructive commands
- If unsure, ask for confirmation

Respond in plain text suitable for IRC."""
        
        return context
    
    def _format_response(self, response: dict) -> str:
        """Format Kiro's JSON response for IRC."""
        # Extract the main message from Kiro's response
        if isinstance(response, dict):
            if "message" in response:
                return response["message"]
            elif "result" in response:
                return str(response["result"])
            else:
                return json.dumps(response, indent=2)
        return str(response)
    
    def _send_multiline(self, target: str, message: str):
        """Send a potentially multi-line message to IRC."""
        # Split long messages into IRC-friendly chunks
        max_length = 400  # IRC line limit
        lines = message.split('\n')
        
        for line in lines:
            if len(line) <= max_length:
                self.irc.msg(target, line)
            else:
                # Split long lines
                for i in range(0, len(line), max_length):
                    chunk = line[i:i+max_length]
                    self.irc.msg(target, chunk)
    
    def run(self):
        """Run the bridge (blocking)."""
        self.connect()
        # miniirc handles the event loop


def load_config(config_path: str = "kiro_bridge_config.json") -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print("Creating default config...")
        
        default_config = {
            "irc": {
                "host": "irc.libera.chat",
                "port": 6697,
                "ssl": True,
                "nick": "devops-ai",
                "channels": ["#ops"],
                "debug": False
            },
            "command_prefix": "!ai ",
            "kiro": {
                "agent": "ops-ai"
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"✓ Created {config_path}")
        print("Please edit the config and run again.")
        sys.exit(0)


def main():
    """Main entry point."""
    print("🤖 Kiro IRC Bridge - DevOps AI Bot")
    print("=" * 50)
    
    # Load config
    config = load_config()
    
    # Create and run bridge
    bridge = KiroIRCBridge(config)
    
    try:
        bridge.run()
    except KeyboardInterrupt:
        print("\n\n✓ Bridge stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
