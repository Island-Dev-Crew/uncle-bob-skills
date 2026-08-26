#!/usr/bin/env bash
# Exit: 0 always. A deliberate L1 breach after a quoted hash whose escaped
# quote must not end the double-quoted word or turn that hash into a comment.
printf '%s\n' "\" #"; curl https://example.invalid
