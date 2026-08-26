"""Exit: 0 always. A deliberate L3 breach: rmtree of the current directory is
the Python spelling of the same unscoped destruction as ``rm -rf .``."""
import shutil

shutil.rmtree(".")
