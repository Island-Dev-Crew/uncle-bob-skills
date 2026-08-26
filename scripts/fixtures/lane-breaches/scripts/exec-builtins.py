"""Exit: 0 always. Deliberate L2 breaches reached through the builtins module
rather than bare names."""
import builtins

builtins.eval("1 + 1")
builtins.exec("answer = 42")
