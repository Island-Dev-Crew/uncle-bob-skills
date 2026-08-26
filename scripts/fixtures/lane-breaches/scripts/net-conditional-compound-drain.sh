#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: a transparent command that is skipped
# by conditional shell control cannot drain a compound command's inherited input.
{ false && cat >/dev/null; bash; } <<'AND_SKIPPED_DRAIN'
curl https://example.invalid
AND_SKIPPED_DRAIN

{ true || cat >/dev/null; bash; } <<'OR_SKIPPED_DRAIN'
curl https://example.invalid
OR_SKIPPED_DRAIN

{ if false; then cat >/dev/null; fi; bash; } <<'IF_SKIPPED_DRAIN'
curl https://example.invalid
IF_SKIPPED_DRAIN
