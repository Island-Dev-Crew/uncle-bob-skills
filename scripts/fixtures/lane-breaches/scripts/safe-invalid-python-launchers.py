#!/usr/bin/env python3
"""Exit 0 always. Provably invalid argv shapes fail before the named binary executes."""
import asyncio
import os
import subprocess

os.posix_spawn("/usr/bin/curl", [], {})
os.posix_spawn("/usr/bin/curl", (), {})
os.posix_spawn("/usr/bin/curl", [""], {})
subprocess.run([], executable="/usr/bin/curl", check=False)
asyncio.create_subprocess_exec(executable="/usr/bin/curl")
os.execv("/usr/bin/curl", [])
os.execv("/usr/bin/curl", [""])
os.spawnv(os.P_WAIT, "/usr/bin/curl", [])
os.spawnv(os.P_WAIT, "/usr/bin/curl", [""])
os.execl("/usr/bin/curl", "")
os.execle("/usr/bin/curl", "", {})
os.spawnl(os.P_WAIT, "/usr/bin/curl", "")
