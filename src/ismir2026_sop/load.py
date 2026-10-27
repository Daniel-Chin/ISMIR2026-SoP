"""Read the organizer-edited content directory into a `SoP`.

Layout:
    content/roles.json              list of roles
    content/sessions/<any>.json     one session each; menu order = file name order
    content/sessions/<any>.md       The Idea, referenced from the session JSON
                                    by a path relative to that JSON file
"""

import dataclasses
import json
from pathlib import Path
from typing import Any

from .datatype import Job, Role, Session, SoP, Staffing


class SoPError(Exception):
    pass


def load_sop(content_dir: Path) -> SoP:
    roles_path = content_dir / 'roles.json'
    roles_data = _expect(_read_json(roles_path), list, str(roles_path))
    roles = [_role(d, f'{roles_path}[{i}]') for i, d in enumerate(roles_data)]
    session_paths = sorted((content_dir / 'sessions').glob('*.json'))
    if not session_paths:
        raise SoPError(f'no session files found in {content_dir / "sessions"}')
    sessions = [_session(p) for p in session_paths]
    return SoP(sessions=sessions, roles=roles)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise SoPError(f'{path}: file not found')
    except json.JSONDecodeError as e:
        raise SoPError(f'{path}: invalid JSON: {e}')


def _expect(value: Any, type_: type, where: str) -> Any:
    if type_ is int and isinstance(value, bool) or not isinstance(value, type_):
        raise SoPError(f'{where}: expected {type_.__name__}, got {json.dumps(value)}')
    return value


def _fields(cls: type, data: Any, where: str) -> dict[str, Any]:
    data = _expect(data, dict, where)
    keys = [f.name for f in dataclasses.fields(cls)]
    missing = [k for k in keys if k not in data]
    unexpected = [k for k in data if k not in keys]
    if missing or unexpected:
        raise SoPError(f'{where}: missing keys {missing}, unexpected keys {unexpected}')
    return data


def _str_list(value: Any, where: str) -> list[str]:
    return [_expect(v, str, f'{where}[{i}]') for i, v in enumerate(_expect(value, list, where))]


def _role(data: Any, where: str) -> Role:
    d = _fields(Role, data, where)
    return Role(
        name=_expect(d['name'], str, f'{where}.name'),
        is_volunteer=_expect(d['is_volunteer'], bool, f'{where}.is_volunteer'),
        job_description=_expect(d['job_description'], str, f'{where}.job_description'),
    )


def _staffing(data: Any, where: str) -> Staffing:
    d = _fields(Staffing, data, where)
    return Staffing(
        role=_expect(d['role'], str, f'{where}.role'),
        count=_expect(d['count'], int, f'{where}.count'),
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
    )
