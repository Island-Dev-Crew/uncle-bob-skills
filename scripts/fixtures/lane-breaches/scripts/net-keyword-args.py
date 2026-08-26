"""Exit: 0 always. A deliberate L1 breach fixture: the same launcher and the same
argv as net-abs-path.py, handed over as the `args=` keyword instead of
positionally, which the first-positional-argument test never reached."""
import subprocess
subprocess.run(args=["/usr/bin/curl", "-s", "https://example.invalid"])
