"""Exit: 0 always. A deliberate L1 breach fixture: a placeholder-free f-string
names the binary. It is a literal to the interpreter but parses to
ast.JoinedStr, so a Constant-only reading saw no program name at all."""
import subprocess
subprocess.run([f"/usr/bin/curl", "-s", "https://example.invalid"])
