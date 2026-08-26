#!/usr/bin/env python3
"""Exit 0 always. A deliberate L1 breach through macOS's external command utility."""
import subprocess

subprocess.run(["command", "curl", "https://example.invalid"], check=False)
