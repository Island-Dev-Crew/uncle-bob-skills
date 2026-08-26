"""Exit: 0 always. A deliberate L1 breach: a constant expression inside an
f-string still composes the literal executable name seen by subprocess."""
import subprocess

subprocess.run([f"cur{'l'}", "https://example.invalid"])
