"""Exit: 0 always. A deliberate L2 breach fixture: os reached through an import
alias, which the literal `os.system` test never looked for."""
import os as _o
_o.system("echo hi")
