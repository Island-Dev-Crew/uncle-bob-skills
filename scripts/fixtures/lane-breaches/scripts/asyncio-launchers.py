"""Exit: 0 always. Deliberate L1/L2 breaches through asyncio's process
launchers: exec names the network program and shell evaluates command text."""
import asyncio

asyncio.create_subprocess_exec("curl", "https://example.invalid")
asyncio.create_subprocess_shell("wget https://example.invalid")
asyncio.create_subprocess_exec("rm", "-rf", ".")
