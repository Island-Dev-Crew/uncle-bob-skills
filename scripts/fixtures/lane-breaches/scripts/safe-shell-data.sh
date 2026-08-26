#!/usr/bin/env bash
# Exit: 0 always. Green controls: quoted command-looking text is data consumed
# by echo or printf, not another command in the shell program.
echo "rm -rf ."
printf '%s\n' 'rm -rf ~'
