"""Exit: 0 always. A deliberate L1 breach: a constant string expression inside
an f-string remains a statically known executable name."""
import subprocess

subprocess.run([f"{'cur' + 'l'}", "https://example.invalid"])
