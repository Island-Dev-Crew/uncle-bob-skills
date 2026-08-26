"""Exit: 0 always. Deliberate L1 breaches through Python launcher argv: one
wrapped command and one nested shell command."""
import subprocess

subprocess.run(["timeout", "2s", "curl", "https://example.invalid"])
subprocess.run(["bash", "-c", "wget https://example.invalid"])
