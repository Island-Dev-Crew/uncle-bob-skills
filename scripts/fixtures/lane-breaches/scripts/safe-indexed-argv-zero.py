"""Exit: 0 always. A green control: argv[0] does not replace the explicit safe
POSIX spawn path, even when that argv is obtained through literal indexing."""
import os

os.posix_spawn("/usr/bin/printf", (["curl", "https://example.invalid"],)[0], {})
