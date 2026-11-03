"""Consistency checks, including the role-mention "spellcheck"."""

from collections import defaultdict
from pathlib import Path

from .datatype import ONLINE_VOLUNTEER_GUIDE, SOP
from .idea_views import view_statuses
from .load import AI_GENERATED_DIR, GUIDES_DIR
from .md import find_images, find_mentions
from .slug import slugify

# Top-level output paths that a session address must not take.
RESERVED_SLUGS = {'static', 'images', 'roles', 'guides', 'schedule-for-venue-av-it'}


def find_problems(sop: SOP, content: Path) -> list[str]:
    problems: list[str] = []
    role_names = {r.name for r in sop.roles}

    problems += _slug_problems('role', [r.name for r in sop.roles])
    problems += _slug_problems('session', [s.name for s in sop.sessions])
    for s in sop.sessions:
        if slugify(s.name) in RESERVED_SLUGS:
            problems.append(f'session {s.name!r}: address {slugify(s.name)!r} is reserved')

    def check_mentions(text: str, where: str) -> None:
        for name in find_mentions(text):
            if name not in role_names:
                problems.append(f'{where}: unknown role mention [[{name}]]')
        for src in find_images(text):
            if not (content / src).is_file():
                problems.append(f'{where}: image {src} not found in {content / "images"}')

    guide_titles = {g.title for g in sop.guides}
    if ONLINE_VOLUNTEER_GUIDE not in guide_titles:
        problems.append(f'{content / GUIDES_DIR}: missing guide {ONLINE_VOLUNTEER_GUIDE!r}')
    for r in sop.roles:
        for t in r.guides:
            if t not in guide_titles:
                problems.append(f'role {r.name!r} guides: unknown guide {t!r}')
        check_mentions(r.job_description, f'role {r.name!r} job_description')
    for g in sop.guides:
        expected = f'{slugify(g.title)}.md'
        if Path(g.markdown_path).name != expected:
            problems.append(f'{g.markdown_path}: title {g.title!r} needs the file name {expected!r}')
        check_mentions(g.body, g.markdown_path)

    for s in sop.sessions:
        where = f'session {s.name!r}'
        staffed: set[str] = set()
        for st in s.staffing:
            if st.role not in role_names:
                problems.append(f'{where} staffing: unknown role {st.role!r}')
            if st.role in staffed:
                problems.append(f'{where} staffing: role {st.role!r} listed twice')
            if st.count < 1:
                problems.append(f'{where} staffing: role {st.role!r} has count {st.count}')
            if not 0 < st.uptime <= 1:
                problems.append(f'{where} staffing: role {st.role!r} has uptime {st.uptime}, expected in (0, 1]')
            staffed.add(st.role)
        for i, job in enumerate(s.runsheet):
            job_where = f'{where} runsheet[{i}] ({job.time_info})'
            if not job.roles:
                problems.append(f'{job_where}: no roles')
            for name in job.roles:
                if name not in role_names:
                    problems.append(f'{job_where}: unknown role {name!r}')
                elif name not in staffed:
                    problems.append(f'{job_where}: role {name!r} is not in this session\'s staffing')
            check_mentions(job.short_description, f'{job_where} short_description')
            check_mentions(job.more_info, f'{job_where} more_info')
        try:
            idea = Path(s.the_idea_markdown_path).read_text(encoding='utf-8')
        except FileNotFoundError:
            problems.append(f'{where}: The Idea file {s.the_idea_markdown_path} not found')
        else:
            check_mentions(idea, s.the_idea_markdown_path)
        for path in s.idea_views.values():
            check_mentions(Path(path).read_text(encoding='utf-8'), path)

    ai_dir = content.parent / AI_GENERATED_DIR
    views = {Path(p).resolve() for s in sop.sessions for p in s.idea_views.values()}
    for path in sorted(ai_dir.glob('*/*.md')):
        if path.resolve() not in views:
            problems.append(f'{path}: no staffed role of a session matches this <session>/<role> address')

    return problems


def find_warnings(sop: SOP, content: Path) -> list[str]:
    """Not fatal: AI-generated views of The Idea that are out of date."""
    return [
        f'{v.path}: {v.state}; The Idea of {v.session!r} or the job_description of {v.role!r} changed since this view was generated'
        if v.state == 'stale' else f'{v.path}: no generation stamp on its first line'
        for v in view_statuses(sop, content.parent / AI_GENERATED_DIR) if v.state in ('stale', 'unstamped')
    ]


def _slug_problems(kind: str, names: list[str]) -> list[str]:
    by_slug: defaultdict[str, list[str]] = defaultdict(list)
    for name in names:
        by_slug[slugify(name)].append(name)
    problems = []
    for slug, group in by_slug.items():
        if not slug:
            problems.append(f'{kind} {group[0]!r}: name gives an empty address')
        elif len(group) > 1:
            problems.append(f'{kind}s {group} all get the same address {slug!r}')
    return problems
