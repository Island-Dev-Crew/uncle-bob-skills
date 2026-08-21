# LIMIT fixture. Byte-for-byte the same source TEXT as its twin, saved
# latin-1 instead of UTF-8 - which is what a legacy checkout hands you.
# leak-scan reads source with errors='replace', so the 0xe9 becomes U+FFFD,
# the fact stops matching, and this pair is a documented false GREEN.
QUEUE = "queue-café-région"
