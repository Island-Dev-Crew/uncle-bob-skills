"""Exit: 0 always. Green controls: these shell values are statically false and
must not be treated as arbitrary shell execution."""
import subprocess

flag = ""
subprocess.run(["echo", "safe"], shell=0)
subprocess.run(["echo", "safe"], shell="")
subprocess.run(["echo", "safe"], shell=[])
subprocess.run(["echo", "safe"], shell=())
subprocess.run(["echo", "safe"], shell={})
subprocess.run(["echo", "safe"], shell=f"{flag}")
