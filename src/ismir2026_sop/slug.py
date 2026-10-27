import re


def slugify(name: str) -> str:
    """Page address / URL-parameter form of a name, e.g. "Oral Session" -> "oral-session"."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
