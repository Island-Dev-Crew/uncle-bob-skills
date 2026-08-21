"""Client half - two facts whose TEXT starts with '#', both owned elsewhere."""

BRAND = "#0B5FFF"           # colour token published by the design system
SUPPRESS = "# nosec"        # spelling owned by the bandit tool


def badge(label):
    return {"swatch": BRAND, "label": label, "waiver": SUPPRESS}
