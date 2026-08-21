"""Server half - restates the same two '#'-leading facts."""

DEFAULT_COLOR = "#0B5FFF"
SUPPRESSION = "# nosec"


def render(chosen=None):
    return {"fill": chosen or DEFAULT_COLOR, "suppression": SUPPRESSION}
