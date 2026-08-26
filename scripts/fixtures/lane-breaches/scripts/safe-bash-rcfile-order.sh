#!/usr/bin/env bash
# Exit: 0 always. Bash startup options after a -c program or script filename are
# arguments, and non-Bash shells do not consume Bash rcfile/init-file options.
bash -ic ':' --rcfile /dev/stdin <<'AFTER_C_PROGRAM'
curl https://example.invalid
AFTER_C_PROGRAM

bash /dev/null --rcfile /dev/stdin -i <<'AFTER_SCRIPT'
curl https://example.invalid
AFTER_SCRIPT

sh -i --rcfile /dev/stdin -c ':' <<'SH_DATA'
curl https://example.invalid
SH_DATA

dash -i --init-file /dev/fd/0 -c ':' <<'DASH_DATA'
curl https://example.invalid
DASH_DATA

zsh -i --rcfile /proc/self/fd/0 -c ':' <<'ZSH_DATA'
curl https://example.invalid
ZSH_DATA

ksh -i --init-file /dev/stdin -c ':' <<'KSH_DATA'
curl https://example.invalid
KSH_DATA

# These invocations are invalid before -c: non-Bash shells reject the options,
# and Bash has no --rcfile=PATH spelling, so the literal curl program never runs.
bash --rcfile=/dev/stdin -ic 'curl https://example.invalid'
sh -i --rcfile /dev/stdin -c 'curl https://example.invalid'
dash -i --init-file /dev/fd/0 -c 'curl https://example.invalid'

# Bash rejects multi-character startup options that follow a single-character option.
bash -i --rcfile /dev/stdin -c ':' <<'LONG_OPTION_AFTER_SHORT'
curl https://example.invalid
LONG_OPTION_AFTER_SHORT

# --norc suppresses the chosen startup file regardless of long-option order.
bash --norc --rcfile /dev/stdin -ic ':' <<'NORC_BEFORE_RCFILE'
curl https://example.invalid
NORC_BEFORE_RCFILE

bash --rcfile /dev/stdin --norc -ic ':' <<'NORC_AFTER_RCFILE'
curl https://example.invalid
NORC_AFTER_RCFILE

bash --norc --init-file /dev/fd/0 -ic ':' <<'NORC_INIT_FILE'
curl https://example.invalid
NORC_INIT_FILE

# Bash uses only the last rc/init-file path.
bash --rcfile /dev/stdin --rcfile /dev/null -ic ':' <<'LAST_RCFILE_WINS'
curl https://example.invalid
LAST_RCFILE_WINS

bash --init-file /dev/stdin --rcfile /dev/null -ic ':' <<'LAST_MIXED_STARTUP_WINS'
curl https://example.invalid
LAST_MIXED_STARTUP_WINS

# -O/+O/-o/+o are short options; a later GNU long option makes the invocation invalid.
bash -O extglob --rcfile /dev/stdin -ic ':' <<'SHORT_CAP_O_BEFORE_LONG'
curl https://example.invalid
SHORT_CAP_O_BEFORE_LONG

bash +O extglob --rcfile /dev/stdin -ic ':' <<'SHORT_PLUS_CAP_O_BEFORE_LONG'
curl https://example.invalid
SHORT_PLUS_CAP_O_BEFORE_LONG

bash -o posix --rcfile /dev/stdin -ic ':' <<'SHORT_O_BEFORE_LONG'
curl https://example.invalid
SHORT_O_BEFORE_LONG

bash +o posix --rcfile /dev/stdin -ic ':' <<'SHORT_PLUS_O_BEFORE_LONG'
curl https://example.invalid
SHORT_PLUS_O_BEFORE_LONG
