"""Exit: 0 always. Green controls: network and rm spellings passed as data to
echo/printf are not commands and must not create a lane breach."""
import subprocess

subprocess.run(["echo", "curl"])
subprocess.run(["printf", "%s\\n", "rm -rf ."])
