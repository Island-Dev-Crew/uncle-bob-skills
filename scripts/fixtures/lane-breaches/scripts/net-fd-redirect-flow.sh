#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: a literal here input on a nonzero file
# descriptor reaches a shell program through a dup chain or an explicit source.
bash 3<<< 'curl https://example.invalid' 0<&3
bash 3<<< 'curl https://example.invalid' 4<&3 0<&4
bash 3<<< 'curl https://example.invalid' 0<&3-

bash 3<<'FD_HEREDOC' 0<&3
curl https://example.invalid
FD_HEREDOC

bash -c 'source /dev/fd/3' 3<<< 'curl https://example.invalid'

bash -c 'source /dev/fd/3' 3<<'SOURCE_FD_HEREDOC'
curl https://example.invalid
SOURCE_FD_HEREDOC

bash 3<<'MOVED_FD_HEREDOC' 0<&3-
curl https://example.invalid
MOVED_FD_HEREDOC
