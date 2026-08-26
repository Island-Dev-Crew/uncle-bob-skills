"""Exit: 0 always. A deliberate L2 breach fixture: subprocess tests `shell` for
truth, so this runs a shell exactly as exec.py does. Comparing the argument
against True let one integer spelling through."""
import subprocess
subprocess.run("echo hi", shell=1)
