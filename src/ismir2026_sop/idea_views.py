"""AI-generated per-role views of a session, in ai_generated/<session>/<role>.md.

A view merges the session's Idea with the role's job_description. Each view starts with a stamp line
naming the hash of both sources it was generated from:

    <!-- generated from content/sessions/13-oral.md sha256:0123456789ab -->

so a view whose Idea has changed since is reported as stale.
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .datatype import SOP
from .load import idea_view_path

STAMP_RE = re.compile(r'\A<!-- generated from (\S+) sha256:([0-9a-f]+) -->\n')


def idea_hash(idea_text: str, job_description: str) -> str:
    """Hash of the sources of a view: the session's Idea and the role's job_description."""
    return hashlib.sha256(f'{idea_text}\0{job_description}'.encode('utf-8')).hexdigest()[:12]


def stamp_line(idea_path: str, idea_hash_: str) -> str:
    return f'<!-- generated from {idea_path} sha256:{idea_hash_} -->\n'


def strip_stamp(text: str) -> str:
    return STAMP_RE.sub('', text, count=1)


@dataclass(frozen=True)
class ViewStatus:
    session: str
    role: str
    path: str
    # 'ok', 'stale', 'unstamped' or 'missing'
    state: str


def view_statuses(sop: SOP, ai_dir: Path) -> list[ViewStatus]:
    """Every staffed (session, role) pair of a session that has an Idea worth a view."""
    jobs = {r.name: r.job_description for r in sop.roles}
    out = []
    for session in sop.sessions:
        idea = Path(session.the_idea_markdown_path).read_text(encoding='utf-8')
        for s in session.staffing:
            path = idea_view_path(ai_dir, session.name, s.role)
            if s.role not in session.idea_views:
                state = 'missing'
            else:
                m = STAMP_RE.match(path.read_text(encoding='utf-8'))
                state = 'unstamped' if not m else 'ok' if m.group(2) == idea_hash(idea, jobs[s.role]) else 'stale'
            out.append(ViewStatus(session.name, s.role, path.as_posix(), state))
    return out


def restamp(sop: SOP, paths: list[Path]) -> None:
    """Mark the given views as generated from the current Idea of their session and job_description of their role."""
    jobs = {r.name: r.job_description for r in sop.roles}
    by_path = {
        Path(p).resolve(): (session, role)
        for session in sop.sessions for role, p in session.idea_views.items()
    }
    for path in paths:
        session, role = by_path.get(path.resolve(), (None, None))
        if session is None:
            raise ValueError(f'{path}: not a view of a staffed role in ai_generated/<session>/<role>.md')
        idea = Path(session.the_idea_markdown_path).read_text(encoding='utf-8')
        body = strip_stamp(path.read_text(encoding='utf-8'))
        path.write_text(stamp_line(session.the_idea_markdown_path, idea_hash(idea, jobs[role])) + body, encoding='utf-8')
