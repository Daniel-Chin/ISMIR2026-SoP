from dataclasses import dataclass, field

RoleName = str
ONLINE_VOLUNTEER_GUIDE = 'For Online Volunteers'

@dataclass(frozen=True)
class Guide:
    # From the file's first line, `# Title`; the file name is the title's address.
    title: str
    # The markdown after the title line.
    body: str
    # Repo path of content/guides/<title-address>.md.
    markdown_path: str

@dataclass(frozen=True)
class Role:
    name: RoleName
    is_volunteer: bool
    is_onsite: bool
    job_description: str
    job_for_who: str = ''
    # Extra guides, by title; online volunteers also get ONLINE_VOLUNTEER_GUIDE automatically.
    guides: list[str] = field(default_factory=list)

    @property
    def is_online(self) -> bool:
        return not self.is_onsite

@dataclass(frozen=True)
class Staffing:
    role: RoleName
    count: int
    # Fraction of the session's duration that the role is actually working.
    uptime: float = 1.0

@dataclass(frozen=True)
class Job:
    time_info: str
    roles: list[RoleName]
    short_description: str
    more_info: str

@dataclass(frozen=True)
class Session:
    name: str
    the_idea_markdown_path: str
    staffing: list[Staffing]
    runsheet: list[Job]
    # Repo path of the session's JSON file; set by the loader, not read from the JSON.
    source_path: str = field(default='', metadata={'derived': True})
    # Role name -> repo path of the AI-generated view of The Idea for that role, where one exists;
    # set by the loader from ai_generated/<session>/<role>.md.
    idea_views: dict[RoleName, str] = field(default_factory=dict, metadata={'derived': True})

@dataclass(frozen=True)
class SOP:
    sessions: list[Session]
    roles: list[Role]
    guides: list[Guide] = field(default_factory=list)
