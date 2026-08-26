# Source evidence

The pack's grounding rule is that no island quotes the conversation from memory: every island cites a numbered concept in [`../docs/01-CONCEPT-LEDGER.md`](../docs/01-CONCEPT-LEDGER.md), and every concept carries a short attributed quote checked against the source recording.

## What is here, and what is not

**Here:** [`frames-notable/`](frames-notable/) — eleven stills sampled from the video, the ones that carry information the words alone do not (the bathrobe the running joke is about, the moment the costume changes, the book held up at the close). They are documentary excerpts, cited frame by frame in [`../docs/00-EXTRACTION.md`](../docs/00-EXTRACTION.md).

**Not here:** the full transcript and the complete timestamped caption file. Both are the whole of someone else's recorded conversation, and this repository does not redistribute them. The ledger's short attributed quotes are ordinary citation; a full transcript is a copy.

## Regenerate the transcript — two commands

The evidence stays reproducible — pull it yourself, and every verification in this repo can be re-run against it. Two deterministic steps: `yt-dlp` fetches the captions, then a short Python filter flattens them into the prose transcript. Neither is wrapped in a script, because a wrapper here would be one more thing to trust; run them in order and read what each does.

**Step 1 — fetch the captions.**

```bash
yt-dlp --skip-download --write-auto-sub --sub-lang en --sub-format srt \
       -o "zcLPGC-tvgk.%(ext)s" "https://www.youtube.com/live/zcLPGC-tvgk"
```

That writes `zcLPGC-tvgk.en.srt` beside this README, and nothing else — it is not yet the transcript the ledger cites.

**Step 2 — flatten them.** This produces `transcript.txt`, the file every quote check in this repo runs against, by stripping cue numbers, timestamps and the rolling repeats auto-captions emit:

```bash
python3 - <<'EOF' > transcript.txt
import re, pathlib
srt = next(pathlib.Path('.').glob('zcLPGC-tvgk*.srt')).read_text(encoding='utf-8')
lines = [l for l in srt.splitlines()
         if l.strip() and not l.strip().isdigit() and '-->' not in l]
seen, out = set(), []
for l in lines:                      # auto-captions repeat rolling lines
    if l not in seen:
        seen.add(l); out.append(l)
print(' '.join(out))
EOF
```

## Verify the quotes

Every quote in the ledger should be findable in the regenerated transcript. Auto-captions stutter and garble, and the ledger preserves that faithfully — stutters are marked `[sic]` rather than smoothed, and known garbles are corrected once in the ledger header (the C.R.A.P. metric, Dex Horthy, John Ousterhout, CLAUDE.md).

```bash
grep -c "They are fast with code. I am slow with code" transcript.txt   # expect 1
```

## Provenance

Robert C. Martin ("Uncle Bob") in conversation with Matt Pocock, ~57 minutes, retrieved 2026-08-19: https://www.youtube.com/live/zcLPGC-tvgk

The conversation is Martin's and Pocock's work. The full recording, transcript, and captions are not reproduced here; the short quotations and eleven cited still excerpts above are third-party source material outside this repository's MIT grant. Their inclusion is documentation, not a license, legal clearance, or endorsement. The skills are Island Development Crew's independent interpretation. See [`../NOTICE.md`](../NOTICE.md).
