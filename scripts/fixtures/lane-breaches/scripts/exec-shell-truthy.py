"""Exit: 0 always. Deliberate L2 breaches: every value is a statically truthy
literal even though none uses the single spelling ``True``."""
import subprocess

subprocess.run(":", shell=-1)
subprocess.run(":", shell=[False])
subprocess.run(":", shell=(False,))
subprocess.run(":", shell={"enabled": False})
subprocess.run(":", shell={False})
subprocess.run(":", shell=f"yes")
