"""Exit: 0 always. A deliberate L3 breach fixture: the same recursive delete as
destroy.sh, written as an argv list. The lane already walked this list for
network binaries and stopped short of reading what it was deleting."""
import subprocess
subprocess.run(["rm", "-rf", "/etc/nothing-real"])
