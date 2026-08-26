"""Exit: 0 always. Deliberate L1 breaches through an executable override and
literal starred argv in subprocess and asyncio launchers."""
import asyncio
import os
import subprocess

subprocess.run(["echo", "not-the-program"], executable="/usr/bin/curl")
subprocess.run([*["wget", "https://example.invalid"]])
subprocess.run(*[["curl", "https://example.invalid"]])
asyncio.create_subprocess_exec(*["nc", "example.invalid", "80"])
os.execl(*["/usr/bin/curl", "curl", "https://example.invalid"])
