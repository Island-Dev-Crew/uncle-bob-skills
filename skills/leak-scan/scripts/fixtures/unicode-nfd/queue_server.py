"""Consumer half. Same queue name, saved by an editor as NFD.

Byte-different, character-identical: the fix that folds it is one call to
unicodedata.normalize in scalar_key().
"""
QUEUE_NAME = "queue-région-café"
