#!/usr/bin/env python3
"""Fixture stand-in for a real per-function CRAP scorer (the live one is the
crap-gate island's). Its only job here is to EXIST, so a rule row that names it
resolves. Exits 0; this fixture proves resolution, not scoring."""
import sys

if __name__ == "__main__":
    sys.exit(0)
