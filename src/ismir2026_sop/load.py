"""Read the organizer-edited content directory into a `SOP`.

Layout:
    content/roles.json              list of roles
    content/guides/<slug>.md        one guide each; first line `# Title`, where the
                                    title slugifies to <slug>; roles refer to the title
    content/sessions/<any>.json     one session each; menu order = file name order
    content/sessions/<any>.md       The Idea, referenced from the session JSON
                                    by a path relative to that JSON file
    content/videos.json             optional {session name: {role name: YouTube link}}
    ai_generated/<session>/<role>.md
                                    optional LLM-written view of a session's Idea for one
                                    role (slugs of the names); next to content/
"""

import dataclasses
import json
from pathlib import Path
from typing import Any

from .datatype import Guide, Job, Role, Session, SOP, Staffing
from .slug import slugify

GUIDES_DIR = 'guides'
AI_GENERATED_DIR = 'ai_generated'


class SOPError(Exception):
    pass


def load_sop(content_dir: Path) -> SOP:
    roles_path = content_dir / 'roles.json'
    roles_data = _expect(_read_json(roles_path), list, str(roles_path))
    roles = [_role(d, f'{roles_path}[{i}]') for i, d in enumerate(roles_data)]
    guides = [_guide(p) for p in sorted((content_dir / GUIDES_DIR).glob('*.md'))]
    session_paths = sorted((content_dir / 'sessions').glob('*.json'))
    if not session_paths:
        raise SOPError(f'no session files found in {content_dir / "sessions"}')
    sessions = [_with_idea_views(_session(p), content_dir.parent / AI_GENERATED_DIR) for p in session_paths]
    sessions = _with_videos(sessions, content_dir / 'videos.json')
    return SOP(sessions=sessions, roles=roles, guides=guides)


def _with_videos(sessions: list[Session], path: Path) -> list[Session]:
    if not path.is_file():
        return sessions
    data = _expect(_read_json(path), dict, str(path))
    by_name = {s.name: s for s in sessions}
    out = {s.name: {} for s in sessions}
    for name, videos in data.items():
        if name == 'dev_comment':
            continue
        if name not in by_name:
            raise SOPError(f'{path}: unknown session {json.dumps(name)}')
        staffed = {s.role for s in by_name[name].staffing}
        for role, url in _expect(videos, dict, f'{path}.{name}').items():
            if role not in staffed:
                raise SOPError(f'{path}.{name}: role {json.dumps(role)} is not staffed in this session')
            out[name][role] = _expect(url, str, f'{path}.{name}.{role}')
    return [dataclasses.replace(s, videos=out[s.name]) for s in sessions]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise SOPError(f'{path}: file not found')
    except json.JSONDecodeError as e:
        raise SOPError(f'{path}: invalid JSON: {e}')


def _expect(value: Any, type_: type, where: str) -> Any:
    if type_ is int and isinstance(value, bool) or not isinstance(value, type_):
        raise SOPError(f'{where}: expected {type_.__name__}, got {json.dumps(value)}')
    return value


def _fields(cls: type, data: Any, where: str) -> dict[str, Any]:
    data = _expect(data, dict, where)
    keys = [f.name for f in dataclasses.fields(cls) if not f.metadata.get('derived')]
    optional = {f.name for f in dataclasses.fields(cls) if f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING}
    missing = [k for k in keys if k not in data and k not in optional]
    # `dev_comment` is a free-form note for organizers, allowed on any object and ignored.
    unexpected = [k for k in data if k not in keys and k != 'dev_comment']
    if missing or unexpected:
        raise SOPError(f'{where}: missing keys {missing}, unexpected keys {unexpected}')
    return data


def _str_list(value: Any, where: str) -> list[str]:
    return [_expect(v, str, f'{where}[{i}]') for i, v in enumerate(_expect(value, list, where))]


def _float(value: Any, where: str) -> float:
    return float(value) if type(value) is int else _expect(value, float, where)


def _role(data: Any, where: str) -> Role:
    d = _fields(Role, data, where)
    return Role(
        name=_expect(d['name'], str, f'{where}.name'),
        is_volunteer=_expect(d['is_volunteer'], bool, f'{where}.is_volunteer'),
        is_onsite=_expect(d['is_onsite'], bool, f'{where}.is_onsite'),
        job_description=_expect(d['job_description'], str, f'{where}.job_description'),
        job_for_who=_expect(d.get('job_for_who', ''), str, f'{where}.job_for_who'),
        guides=_str_list(d.get('guides', []), f'{where}.guides'),
    )


def _guide(path: Path) -> Guide:
    first, _, body = path.read_text(encoding='utf-8').partition('\n')
    if not first.startswith('# '):
        raise SOPError(f'{path}: the first line must be the title, as `# Title`')
    # Stored relative to the working directory, so it is also the repo path.
    return Guide(title=first[2:].strip(), body=body.lstrip('\n'), markdown_path=path.as_posix())


def idea_view_path(ai_dir: Path, session_name: str, role_name: str) -> Path:
    return ai_dir / slugify(session_name) / f'{slugify(role_name)}.md'


def _with_idea_views(session: Session, ai_dir: Path) -> Session:
    views = {}
    for s in session.staffing:
        path = idea_view_path(ai_dir, session.name, s.role)
        if path.is_file():
            views[s.role] = path.as_posix()
    return dataclasses.replace(session, idea_views=views)


def _staffing(data: Any, where: str) -> Staffing:
    d = _fields(Staffing, data, where)
    return Staffing(
        role=_expect(d['role'], str, f'{where}.role'),
        count=_expect(d['count'], int, f'{where}.count'),
        uptime=_float(d.get('uptime', 1.0), f'{where}.uptime'),
    )


def _job(data: Any, where: str) -> Job:
    d = _fields(Job, data, where)
    return Job(
        time_info=_expect(d['time_info'], str, f'{where}.time_info'),
        roles=_str_list(d['roles'], f'{where}.roles'),
        short_description=_expect(d['short_description'], str, f'{where}.short_description'),
        more_info=_expect(d['more_info'], str, f'{where}.more_info'),
    )


def _session(path: Path) -> Session:
    d = _fields(Session, _read_json(path), str(path))
    idea = _expect(d['the_idea_markdown_path'], str, f'{path}.the_idea_markdown_path')
    staffing = _expect(d['staffing'], list, f'{path}.staffing')
    runsheet = _expect(d['runsheet'], list, f'{path}.runsheet')
    return Session(
        name=_expect(d['name'], str, f'{path}.name'),
        # Stored relative to the working directory, so it is also the repo path.
        the_idea_markdown_path=(path.parent / idea).as_posix(),
        staffing=[_staffing(s, f'{path}.staffing[{i}]') for i, s in enumerate(staffing)],
        runsheet=[_job(j, f'{path}.runsheet[{i}]') for i, j in enumerate(runsheet)],
        source_path=path.as_posix(),
    )
