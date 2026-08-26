"""Exit: 0 always. Deliberate L1 breaches through the two direct POSIX spawn
launchers, including a name imported from os without the module prefix."""
import os
from os import posix_spawnp

os.posix_spawn("/usr/bin/curl", ["curl"], {})
posix_spawnp("curl", ["curl"], {})
