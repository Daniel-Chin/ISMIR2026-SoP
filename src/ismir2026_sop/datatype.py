from dataclasses import dataclass

RoleName = str

@dataclass(frozen=True)
class Role:
    name: RoleName
    job_description: str

@dataclass(frozen=True)
class Staffing:
    role: RoleName
    count: int

@dataclass(frozen=True)
class Job:
    time_info: str
    roles: list[RoleName]
    short_description: str
    long_description: str

@dataclass(frozen=True)
class Session:
    name: str
    the_idea_markdown_path: str
    staffing: list[Staffing]
    runsheet: list[Job]

@dataclass(frozen=True)
class SoP:
    sessions: list[Session]
    roles: list[Role]
