"""Conference schedule from sitedata/events.csv (pulled from the Google Sheet)."""

import csv
from dataclasses import dataclass
from pathlib import Path

EVENTS_CSV = Path('sitedata/events.csv')

# events.csv `category` -> Session Type (`Session.name`); None = no Session Type.
CATEGORY_TO_SESSION_TYPE: dict[str, str | None] = {
    'Opening': 'Opening Session',
    'All Meeting': 'Keynote',
    'Oral session': 'Oral Session',
    'Award nominee': 'Award Nominee Oral Session',
    'Poster session': 'Poster Session',
    'Special': 'Special Session',
    'LBD': 'LBD Session',
    'Awards': 'Awards and Closing Session',
    'Registration': None,
    'Tutorials': 'Tutorial',
    'Majlis': 'Majlis',
    'Social': None,
    'Lunch': None,
    'Music': 'Music Program',
    'Industry': 'Industry Panel',
    'WiMIR Meetup': 'WIMIR Session',
    'Meetup': 'ISMIR Society Meeting',
    'Unconference': 'Unconference',
}


def auditorium_display_mode(session_type: str) -> str:
    """What the auditorium screen shows during a session of this type."""
    return {
        'Opening Session': 'Projector shows: Mixed, needs switching',
        'Keynote': 'Projector shows: (trivial)',
        'Oral Session': 'Projector shows: Stage laptop',
        'Award Nominee Oral Session': 'Projector shows: Mixed, needs switching',
        'Special Session': 'Projector shows: Webinar',
    }.get(session_type, 'Projector shows: TBD')


@dataclass(frozen=True)
class Event:
    uid: str
    title: str
    start_date: str  # e.g. 2026-07-24
    start_time: str  # e.g. 8:00
    end_time: str
    category: str
    onsite_location: str

    @property
    def session_type(self) -> str | None:
        if self.category not in CATEGORY_TO_SESSION_TYPE:
            raise KeyError(f'event {self.uid}: unmapped category {self.category!r}; add it to CATEGORY_TO_SESSION_TYPE')
        return CATEGORY_TO_SESSION_TYPE[self.category]


# Events not in events.csv. This should be removed past 2026.
EXTRA_EVENTS = [
    Event(
        uid='music-program-rehearsal',
        title='Music Program Rehearsal',
        start_date='2026-11-08',
        start_time='20:00',
        end_time='22:00',
        category='Music',
        onsite_location='A6-008',
    ),
]


def load_events(path: Path = EVENTS_CSV) -> list[Event]:
    with path.open(encoding='utf-8', newline='') as f:
        return [
            Event(**{k: row[k].strip() for k in Event.__dataclass_fields__})
            for row in csv.DictReader(f)
        ] + EXTRA_EVENTS


def total_hours_by_session_type(events: list[Event]) -> dict[str, float]:
    """Sum of (end - start) in hours over all events of each Session Type."""
    totals: dict[str, float] = {}
    for e in events:
        if e.session_type is None:
            continue
        (sh, sm), (eh, em) = time_key(e.start_time), time_key(e.end_time)
        totals[e.session_type] = totals.get(e.session_type, 0) + (eh * 60 + em - sh * 60 - sm) / 60
    return totals


def count_by_session_type(events: list[Event]) -> dict[str, int]:
    """Number of events of each Session Type."""
    counts: dict[str, int] = {}
    for e in events:
        if e.session_type is not None:
            counts[e.session_type] = counts.get(e.session_type, 0) + 1
    return counts


def time_key(t: str) -> tuple[int, int]:
    h, m = t.split(':')
    return int(h), int(m)
