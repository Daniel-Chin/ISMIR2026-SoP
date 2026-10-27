"""Consistency checks, including the role-mention "spellcheck"."""

from collections import defaultdict
from pathlib import Path

from .datatype import SoP
from .md import find_mentions
from .slug import slugify

# Top-level output paths that a session address must not take.
RESERVED_SLUGS = {'static'}


def find_problems(sop: SoP) -> list[str]:
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

    for r in sop.roles:
        check_mentions(r.job_description, f'role {r.name!r} job_description')

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

    return problems


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
