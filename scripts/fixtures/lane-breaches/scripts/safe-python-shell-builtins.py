#!/usr/bin/env python3
"""Exit 0 always. Shell builtins named as subprocess executables do not run later argv."""
import subprocess

subprocess.run(["builtin", "command", "curl"], check=False)
subprocess.run(["exec", "curl"], check=False)
subprocess.run(["LC_ALL=C", "curl"], check=False)
