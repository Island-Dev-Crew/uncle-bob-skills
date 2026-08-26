"""Exit: 0 always. A deliberate L1 breach fixture: the binary is named by
absolute path, which the bare-token test read as innocent."""
import subprocess
subprocess.run(["/usr/bin/curl", "-s", "https://example.invalid"])
