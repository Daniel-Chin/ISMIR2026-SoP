"""Markdown rendering with `[[Role Name]]` mentions."""

import re
import xml.etree.ElementTree as etree
from collections.abc import Callable

import markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor
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


IMAGE_PREFIX = 'images/'


class _ImageRootProcessor(Treeprocessor):
    """`images/x.png` is relative to the site root; prefix it with the page's path to the root."""

    def __init__(self, md: markdown.Markdown, root: str):
        super().__init__(md)
        self.root = root

    def run(self, root_el: etree.Element) -> None:
        for img in root_el.iter('img'):
            src = img.get('src', '')
            if src.startswith(IMAGE_PREFIX):
                img.set('src', self.root + src)


class _ImageRootExtension(Extension):
    def __init__(self, root: str):
        super().__init__()
        self.root = root

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        md.treeprocessors.register(_ImageRootProcessor(md, self.root), 'image_root', 0)


def find_images(text: str) -> list[str]:
    """Site-root-relative image paths, e.g. `images/stage.png`."""
    return re.findall(r'!\[[^\]]*\]\(\s*<?(' + IMAGE_PREFIX + r'[^\s)>]+)', text)


def render(text: str, link_for: MentionLinker, root: str = '') -> str:
    return markdown.markdown(
        text, extensions=['extra', 'sane_lists', _MentionExtension(link_for), _ImageRootExtension(root)],
    )


def render_inline(text: str, link_for: MentionLinker, root: str = '') -> str:
    """For one-liners: drop the wrapping <p> of a single paragraph."""
    html = render(text, link_for, root)
    if html.startswith('<p>') and html.endswith('</p>') and html.count('<p>') == 1:
        return html[3:-4]
    return html
