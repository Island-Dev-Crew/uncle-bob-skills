"""Exit: 0 always. Deliberate L1 breaches: every execl/spawnl family member
launches a network binary even though the program occupies a different slot."""
import os

os.execl("/usr/bin/curl", "curl", "https://example.invalid")
os.execle("/usr/bin/curl", "curl", "https://example.invalid", {})
os.execlp("curl", "curl", "https://example.invalid")
os.execlpe("curl", "curl", "https://example.invalid", {})
os.spawnl(os.P_WAIT, "/usr/bin/curl", "curl", "https://example.invalid")
os.spawnle(os.P_WAIT, "/usr/bin/curl", "curl", "https://example.invalid", {})
os.spawnlp(os.P_WAIT, "curl", "curl", "https://example.invalid")
os.spawnlpe(os.P_WAIT, "curl", "curl", "https://example.invalid", {})

# These two exercise the same launcher families against L3 rather than L1.
os.execl("/bin/rm", "rm", "-rf", ".")
os.spawnl(os.P_WAIT, "/bin/rm", "rm", "-rf", "~")
