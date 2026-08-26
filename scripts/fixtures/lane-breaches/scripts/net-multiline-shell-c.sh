#!/bin/sh
# Exit 0: unreachable multiline shell-program fixture.

bash -c 'echo safe
curl https://example.invalid'
