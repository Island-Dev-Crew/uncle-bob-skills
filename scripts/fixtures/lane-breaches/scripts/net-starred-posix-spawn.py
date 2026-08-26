"""Exit: 0 always. Deliberate L1 breaches: a literal starred call still exposes
both the POSIX spawn path and a shell's literal command argv."""
import os

os.posix_spawn(*("/usr/bin/curl", ["curl"], {}))
os.posix_spawn(*("/bin/sh", ["sh", "-c", "curl https://example.invalid"], {}))
