"""Exit: 0 always. Deliberate L1 breaches: integer indexing into literal
containers remains literal in path, argv, executable override, and execv slots."""
import os
import subprocess

os.posix_spawn(("/usr/bin/curl",)[0], ["curl", "https://example.invalid"], {})
subprocess.run((["curl", "https://example.invalid"],)[0])
subprocess.run(["ignored"], executable=("/usr/bin/curl",)[0])
os.execv(("/usr/bin/curl",)[0], ["curl", "https://example.invalid"])
