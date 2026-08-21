#!/usr/bin/env python3
"""covgate — fixture module: stands in for a real `python3 -m covgate` coverage gate.

Its only job is to exist under the harness root, so the clean fixture's `-m`
module resolves without depending on any package being installed on the host.
"""
import sys


def main() -> int:
    return 0


if __name__ == "__main__":
    sys.exit(main())
