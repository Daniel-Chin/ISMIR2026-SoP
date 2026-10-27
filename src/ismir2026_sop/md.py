"""Markdown rendering with `[[Role Name]]` mentions."""

import re
import xml.etree.ElementTree as etree
from collections.abc import Callable

import markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.util import AtomicString

MENTION_RE = r'\[\[([^\[\]\n]+?)\]\]'

# Maps a mentioned role name to the link target, or None for "shown but not linked".
# Must raise KeyError for an unknown role.
MentionLinker = Callable[[str], str | None]


def find_mentions(text: str) -> list[str]:
    return re.findall(MENTION_RE, text)


class _MentionProcessor(InlineProcessor):
    def __init__(self, link_for: MentionLinker):
        super().__init__(MENTION_RE)
        self.link_for = link_for

    def handleMatch(self, m: re.Match[str], data: str):  # type: ignore[override]
        name = m.group(1)
        href = self.link_for(name)
        el = etree.Element('a' if href is not None else 'span')
        if href is not None:
            el.set('href', href)
        el.set('class', 'mention')
        el.text = AtomicString(name)
        return el, m.start(0), m.end(0)


class _MentionExtension(Extension):
    def __init__(self, link_for: MentionLinker):
        super().__init__()
        self.link_for = link_for

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        # Above the link/reference patterns, below code spans.
        md.inlinePatterns.register(_MentionProcessor(self.link_for), 'role_mention', 175)


def render(text: str, link_for: MentionLinker) -> str:
    return markdown.markdown(
        text, extensions=['extra', 'sane_lists', _MentionExtension(link_for)],
    )


def render_inline(text: str, link_for: MentionLinker) -> str:
    """For one-liners: drop the wrapping <p> of a single paragraph."""
    html = render(text, link_for)
    if html.startswith('<p>') and html.endswith('</p>') and html.count('<p>') == 1:
        return html[3:-4]
    return html
