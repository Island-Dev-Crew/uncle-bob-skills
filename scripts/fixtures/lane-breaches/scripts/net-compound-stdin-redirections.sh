#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: redirection attached to a compound
# command is inherited by the literal Bash invocation inside that command.
{ bash; } <<'GROUP_HEREDOC'
curl https://example.invalid
GROUP_HEREDOC

( bash ) <<'SUBSHELL_HEREDOC'
curl https://example.invalid
SUBSHELL_HEREDOC

if true; then
    bash
fi <<'IF_HEREDOC'
curl https://example.invalid
IF_HEREDOC

{ bash; } <<< 'curl https://example.invalid'
( bash ) <<< 'curl https://example.invalid'
if true; then bash; fi <<< 'curl https://example.invalid'

# Redirecting stderr does not replace inherited stdin; the body still executes.
{ bash 2>/dev/null; } <<'STDERR_ONLY'
curl https://example.invalid
STDERR_ONLY
{ bash 2>/dev/null; } <<< 'curl https://example.invalid'
