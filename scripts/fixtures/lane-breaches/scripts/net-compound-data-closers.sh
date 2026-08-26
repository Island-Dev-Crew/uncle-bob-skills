#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: closer-shaped data inside a compound
# does not end it before the real closer and trailing inherited here input.
for x in one; do
    echo done >/dev/null
    bash
done <<'FOR_DATA_CLOSER'
curl https://example.invalid
FOR_DATA_CLOSER

if true; then
    echo fi >/dev/null
    bash
fi <<'IF_DATA_CLOSER'
curl https://example.invalid
IF_DATA_CLOSER

case x in
    x) echo esac >/dev/null; bash;;
esac <<'CASE_DATA_CLOSER'
curl https://example.invalid
CASE_DATA_CLOSER

{
    echo '}' >/dev/null
    bash
} <<'GROUP_DATA_CLOSER'
curl https://example.invalid
GROUP_DATA_CLOSER
