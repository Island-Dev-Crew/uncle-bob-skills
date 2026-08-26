---
name: unsafe-setup-state-island
description: A hostile proof fixture whose Bash setup and annotated compounds try four persistent shell-state mutations around allowlisted proofs. The mutations must be refused while ordinary setup remains replayable. Never distributed; exists only as a captured regression. Trigger phrases - "unsafe proof setup state", "function shadow proof".
---

# Unsafe setup state cannot shadow a proof

Each of the first four blocks changes which program a later allowlisted row reaches while
preserving the documented exit code. A verifier that replays those setup rows reports a false
green. The last two blocks are controls: normal fixture output and an ordinary assignment must
still replay.

- `enforced`: verify-proofs.py refuses four setup rows, marks their four downstream candidates
  unsequenced, and runs two independent controls.
- `enforced`: closed-stream-check.py inherits the refusal gaps, probes only the two controls,
  and returns the non-verdict exit 2.
- `advisory`: nothing else here is real.

```bash
python3 () { return 7; }
python3 -c "raise SystemExit(7)"   # exit 7
```

```bash
printf -v PATH '%s' /proof-verifier-no-such-path
python3 -c "raise SystemExit(127)"   # exit 127
```

```bash
printf x%n PATH
python3 -c "raise SystemExit(127)"   # exit 127
```

```bash
printf x >/dev/null; function python3 { return 0; }; python3 -c "raise SystemExit(1)"   # exit 0
python3 -c "raise SystemExit(0)"   # exit 0
```

```bash
D=$(mktemp -d)
printf '%s\n' ok > "$D/value"
python3 -c "import pathlib,sys; raise SystemExit(0 if pathlib.Path(sys.argv[1]).read_text() == 'ok\n' else 9)" "$D/value"   # exit 0
```

```bash
VALUE=ok
python3 -c "import sys; raise SystemExit(0 if sys.argv[1] == 'ok' else 9)" "$VALUE"   # exit 0
```
