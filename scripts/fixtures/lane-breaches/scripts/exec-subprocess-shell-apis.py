"""Exit: 0 always. Direct subprocess command-string helpers are L2 breaches."""
import subprocess

subprocess.getoutput("printf safe")
subprocess.getstatusoutput("printf safe")
