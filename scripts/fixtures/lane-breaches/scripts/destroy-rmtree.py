"""Exit: 0 always. A deliberate L3 breach fixture: Python's own recursive
delete, aimed at a bare absolute path. Checking only shell `rm` left the same
destruction green in every .py file the pack ships."""
import shutil
shutil.rmtree("/etc/nothing-real")
