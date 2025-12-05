

"""Magic Wormhole integration for peer-to-peer file transfers."""

import asyncio
import subprocess
from typing import Optional, Callable


class WormholeClient:
    """Client for Magic Wormhole file transfers."""
    
    def __init__(self):
        self.status_callback: Optional[Callable] = None
    
    async def send_file(self, filepath: str) -> str:
        """Send a file and return the wormhole code."""
        try:
            # wormhole outputs to stderr, so we merge stderr into stdout
            process = await asyncio.create_subprocess_exec(
                "wormhole", "send", "--hide-progress", filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Read output to find the code
            code = None
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                
                if self.status_callback:
                    self.status_callback(f"[wormhole] {line_str}")
                
                # Look for the wormhole code in various formats
                # Format: "Wormhole code is: 7-guitar-ocean"
                if "wormhole code is:" in line_str.lower():
                    parts = line_str.split(":")
                    if len(parts) >= 2:
                        code = parts[-1].strip()
                        break
                # Format: "wormhole receive 7-guitar-ocean"
                elif "wormhole receive" in line_str.lower():
                    parts = line_str.split()
                    if len(parts) >= 2:
                        code = parts[-1].strip()
                        break
            
            if code:
                if self.status_callback:
                    self.status_callback(f"File ready! Code: {code}")
                return code
            else:
                # Check if process had an error
                await process.wait()
                return "error-generating-code"
                
        except FileNotFoundError:
            if self.status_callback:
                self.status_callback("Error: wormhole not installed")
            return "wormhole-not-found"
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error: {str(e)}")
            return f"error: {str(e)}"
    
    async def receive_file(self, code: str, output_dir: str = ".") -> bool:
        """Receive a file using a wormhole code."""
        try:
            # Auto-accept the file with --accept-file
            process = await asyncio.create_subprocess_exec(
                "wormhole", "receive", "--accept-file", "--hide-progress", code,
                cwd=output_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Stream output for status updates
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                if line_str and self.status_callback:
                    self.status_callback(f"[wormhole] {line_str}")
            
            await process.wait()
            
            if process.returncode == 0:
                if self.status_callback:
                    self.status_callback("File received successfully!")
                return True
            else:
                if self.status_callback:
                    self.status_callback("Failed to receive file")
                return False
                
        except FileNotFoundError:
            if self.status_callback:
                self.status_callback("Error: wormhole not installed")
            return False
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error: {str(e)}")
            return False
    
    def set_status_callback(self, callback: Callable):
        """Set callback for status updates."""
        self.status_callback = callback
