#!/usr/bin/env bash
# Exit: 0 always. A deliberate L3 breach fixture: GNU permutes options past
# operands, so the flags mean the same here as in destroy.sh. Deciding at the
# operand, before the flags had been read, called this line harmless.
rm /etc/nothing-real -rf
