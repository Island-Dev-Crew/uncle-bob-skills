"""Exit: 0 always. Deliberate L1 breaches: constant container composition and
indexing remain direct literals when they supply executable names."""
import os
import subprocess

os.posix_spawn(*(("/usr/bin/curl",) + (["curl"], {})))
subprocess.run([f"{('curl',)[0]}", "https://example.invalid"])
subprocess.run([f"{('safe', 'curl')[True]}", "https://example.invalid"])
