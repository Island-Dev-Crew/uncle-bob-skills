#!/usr/bin/env python3
"""Exit 0 always. Deliberate L1 breaches through macOS's external command utility."""
import os
import subprocess

subprocess.run(["command", "eval", "curl https://example.invalid"], check=False)
subprocess.run(
    ["command", "builtin", "command", "curl", "https://example.invalid"], check=False
)
subprocess.run(["/usr/bin/command", "eval", "curl https://example.invalid"], check=False)
os.posix_spawn(
    "/usr/bin/command",
    ["/usr/bin/command", "eval", "curl https://example.invalid"],
    os.environ,
)
