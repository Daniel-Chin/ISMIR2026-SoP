"""Write the static site.

    index.html                      Menu
    roles/index.html                All roles and the session types they appear in
    <session>/index.html            The Idea
    <session>/runsheet/index.html   Runsheet (?mode=...&roles=a,b)
    schedule-for-venue-av-it/       Date x time grid of events staffed by Venue AV/IT
    static/                         CSS and JS
    images/                         copied from content/images/
"""

import os
import shutil
from html import escape
from pathlib import Path

from . import md, schedule
from .datatype import Role, Session, SoP
from .slug import slugify

# Set automatically by GitHub Actions; absent in local builds, where the repo links are omitted.
REPO_URL = (
    f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}"
    if 'GITHUB_REPOSITORY' in os.environ
    else None
)
SITE_TITLE = 'ISMIR 2026 Session SoP'
STATIC_DIR = Path(__file__).parent / 'static'
VENUE_AV_IT = 'Venue AV/IT'


def build_site(sop: SoP, out: Path, content: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STATIC_DIR, out / 'static')
    if (content / 'images').is_dir():
        shutil.copytree(content / 'images', out / 'images')
    (out / '.nojekyll').touch()
    roles = {r.name: r for r in sop.roles}

    _write(out / 'index.html', _menu_page(sop))
    events = schedule.load_events() if schedule.EVENTS_CSV.exists() else None
    _write(out / 'roles' / 'index.html', _roles_page(sop, roles, events))
    for session in sop.sessions:
        slug = slugify(session.name)
        _write(out / slug / 'index.html', _idea_page(session, roles))
        _write(out / slug / 'runsheet' / 'index.html', _runsheet_page(session, roles))
    if schedule.EVENTS_CSV.exists():
        _write(
            out / 'schedule-for-venue-av-it' / 'index.html',
            _venue_av_it_schedule_page(sop, schedule.load_events()),
        )
    else:
        print(f'warning: {schedule.EVENTS_CSV} not found; skipping schedule pages')


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def filtered_runsheet_href(root: str, session: Session, role: str) -> str:
    """The role's cheatsheet; uses the same URL parameters as the runsheet controls."""
    return f'{root}{slugify(session.name)}/runsheet/?mode=filter&roles={slugify(role)}'


def _mention_linker(session: Session, roles: dict[str, Role], root: str) -> md.MentionLinker:
    """Mentions link to this session's runsheet filtered to the role, if it is staffed here."""
    staffed = {s.role for s in session.staffing}

    def link_for(name: str) -> str | None:
        if name not in roles:
            raise KeyError(f'unknown role mention [[{name}]] (session {session.name!r})')
        if name not in staffed:
            return None
        return filtered_runsheet_href(root, session, name)

    return link_for


def _page(title: str, root: str, body: str, *, scripts: str = '', source: str = '') -> str:
    head_title = f'{title} · {SITE_TITLE}' if title != SITE_TITLE else SITE_TITLE
    source_link = (
        f' · <a href="{REPO_URL}/blob/main/{escape(source)}">source of this page</a>' if source else ''
    )
    footer = (
        f'''<footer class="site-footer">
  Edit this SoP via <a href="{REPO_URL}">this repo</a>{source_link}
</footer>
'''
        if REPO_URL
        else ''
    )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(head_title)}</title>
<link rel="stylesheet" href="{root}static/style.css">
</head>
<body>
<header class="site-header">
  <a class="site-name" href="{root or './'}">{escape(SITE_TITLE)}</a>
</header>
<main>
{body}
</main>
{footer}{scripts}
</body>
</html>
'''


def _session_header(session: Session, root: str, current: str) -> str:
    slug = slugify(session.name)
    tabs = [('idea', 'The Idea', f'{root}{slug}/'), ('runsheet', 'Runsheet', f'{root}{slug}/runsheet/')]
    links = ''.join(
        f'<a href="{href}" aria-current="page">{label}</a>' if key == current
        else f'<a href="{href}">{label}</a>'
        for key, label, href in tabs
    )
    return f'<h1>{escape(session.name)}</h1>\n<nav class="tabs">{links}</nav>'


def _staffing_summary(session: Session) -> str:
    return ', '.join(f'{s.count}× {escape(s.role)}' for s in session.staffing)


def _top_tabs(root: str, current: str) -> str:
    tabs = [('sessions', 'All session types', root or './'), ('roles', 'All roles', f'{root}roles/'),
            ('schedule-for-venue-av-it', 'Schedule for Venue AV/IT', f'{root}schedule-for-venue-av-it/')]
    links = ''.join(
        f'<a href="{href}" aria-current="page">{label}</a>' if key == current
        else f'<a href="{href}">{label}</a>'
        for key, label, href in tabs
    )
    return f'<nav class="tabs">{links}</nav>'


def _menu_page(sop: SoP) -> str:
    items = '\n'.join(
        f'''<li>
  <h2><a href="{slugify(s.name)}/">{escape(s.name)}</a></h2>
  <p class="staffing-summary">{_staffing_summary(s)}</p>
</li>'''
        for s in sop.sessions
    )
    body = f'{_top_tabs("", "sessions")}\n<ul class="menu">\n{items}\n</ul>'
    return _page(SITE_TITLE, '', body)


MIC_RUNNER_QA_FRACTION = 0.3
SETTER_OF_LBD_SCENE_HOURS_PER_SESSION = 20 / 60


def _person_hours(role: str, session: str, count: int, hours: dict[str, float], counts: dict[str, int]) -> float:
    """Person-hours of `role` (staffed `count` per session) across all events of the session type."""
    if role == 'Mic Runner':  # only works during Q&A
        return count * hours.get(session, 0) * MIC_RUNNER_QA_FRACTION
    if role == 'Setter of LBD Scene':  # a short stint per session, not the whole session
        return count * counts.get(session, 0) * SETTER_OF_LBD_SCENE_HOURS_PER_SESSION
    return count * hours.get(session, 0)


def _roles_page(sop: SoP, roles: dict[str, Role], events: list[schedule.Event] | None) -> str:
    root = '../'

    def link_for(name: str) -> str | None:
        if name not in roles:
            raise KeyError(f'unknown role mention [[{name}]] (roles.json)')
        return f'#{slugify(name)}'

    if events is not None:
        hours = schedule.total_hours_by_session_type(events)
        counts = schedule.count_by_session_type(events)
    sections = []
    for role in sop.roles:
        appears = [
            (session, s.count) for session in sop.sessions for s in session.staffing if s.role == role.name
        ]
        # Counts are only worth showing when they vary from the default of one.
        show_counts = any(count > 1 for _, count in appears)
        session_links = ', '.join(
            f'<a href="{filtered_runsheet_href(root, session, role.name)}">{escape(session.name)}</a>{f" ({count} per session)" if show_counts else ""}'
            for session, count in appears
        ) or '<em>none</em>'
        person_hours = (
            f' · {sum(_person_hours(role.name, session.name, count, hours, counts) for session, count in appears):g} (person ྾ hour)s in total'
            if events is not None else ''
        )
        sections.append(f'''<section class="role" id="{slugify(role.name)}">
  <h3>{escape(role.name)}{' <span class="volunteer-chip">Volunteer</span>' if role.is_volunteer else ''}{_anchor(slugify(role.name))}</h3>
  <p class="role-attrs">{'On-Site (In-Person)' if role.is_onsite else 'Online (Remote)'}{person_hours}</p>
  <div class="prose">{md.render(role.job_description, link_for, root, anchor_prefix=f'{slugify(role.name)}-')}</div>{_job_for_who(role)}
  <p class="role-sessions"><strong>Session types:</strong> {session_links}</p>
</section>''')
    body = f'{_top_tabs(root, "roles")}\n' + '\n'.join(sections)
    return _page('Roles', root, body, source='content/roles.json')


def _anchor(id: str) -> str:
    """Clickable `#` that links to element `id`; matches the markdown headings' permalinks."""
    return f'<a class="anchor" href="#{id}" title="Link to this section">#</a>'


def _job_for_who(role: Role) -> str:
    if not role.job_for_who:
        return ''
    return f'\n  <p class="job-for-who"><strong>Job for who:</strong> {escape(role.job_for_who)}</p>'


def _idea_page(session: Session, roles: dict[str, Role]) -> str:
    root = '../'
    link_for = _mention_linker(session, roles, root)
    idea = Path(session.the_idea_markdown_path).read_text(encoding='utf-8')
    staff = '\n'.join(
        f'''<section class="role" id="{slugify(s.role)}">
  <h3>{s.count}× <a href="{filtered_runsheet_href(root, session, s.role)}">{escape(s.role)}</a>{' <span class="volunteer-chip">Volunteer</span>' if roles[s.role].is_volunteer else ''}{_anchor(slugify(s.role))}</h3>
  <div class="prose">{md.render(roles[s.role].job_description, link_for, root)}</div>{_job_for_who(roles[s.role])}
</section>'''
        for s in session.staffing
    )
    body = f'''{_session_header(session, root, 'idea')}
<article class="prose idea">
{md.render(idea, link_for, root, anchor_prefix='')}
</article>
<h2 id="staffing">Staffing{_anchor("staffing")}</h2>
{staff}'''
    return _page(session.name, root, body, source=session.source_path)


def _runsheet_page(session: Session, roles: dict[str, Role]) -> str:
    root = '../../'
    link_for = _mention_linker(session, roles, root)
    checkboxes = '\n'.join(
        f'<label><input type="checkbox" value="{slugify(s.role)}"> {escape(s.role)}</label>'
        for s in session.staffing
    )
    role_descs = '\n'.join(
        f'''<section class="role role-desc" data-role="{slugify(s.role)}" hidden>
  <h3>{escape(s.role)}</h3>
  <div class="prose">{md.render(roles[s.role].job_description, link_for, root)}</div>{_job_for_who(roles[s.role])}
</section>'''
        for s in session.staffing
    )
    rows = []
    for i, job in enumerate(session.runsheet, 1):
        chips = ' '.join(
            f'<a class="role-chip" data-role="{slugify(r)}" href="../#{slugify(r)}">{escape(r)}</a>'
            for r in job.roles
        )
        details = ''
        if job.more_info.strip():
            details = (
                '<details open><summary>More</summary>'
                f'<div class="prose">{md.render(job.more_info, link_for, root)}</div></details>'
            )
        rows.append(f'''<tr class="job" id="row-{i}" data-roles="{' '.join(slugify(r) for r in job.roles)}">
  <td class="time">{md.render_inline(job.time_info, link_for, root).replace(chr(10), '<br>')}{_anchor(f'row-{i}')}</td>
  <td class="who">{chips}</td>
  <td class="what"><div class="short">{md.render_inline(job.short_description, link_for, root)}</div>{details}</td>
</tr>''')
    body = f'''{_session_header(session, root, 'runsheet')}
<form class="controls" id="controls" hidden>
  <label class="mode">Mode
    <select id="mode">
      <option value="mastermind">mastermind</option>
      <option value="highlight">highlight</option>
      <option value="filter">filter</option>
    </select>
  </label>
  <fieldset id="role-picker">
    <legend>Roles</legend>
    {checkboxes}
  </fieldset>
  <button type="button" id="expand-all">Expand all</button>
</form>
<p class="status" id="status" aria-live="polite"></p>
{role_descs}
<table class="runsheet">
<thead><tr><th>Time</th><th>Who</th><th>What</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>'''
    return _page(
        f'{session.name} runsheet', root, body,
        scripts=f'<script src="{root}static/runsheet.js"></script>',
        source=session.source_path,
    )


def _venue_av_it_schedule_page(sop: SoP, events: list[schedule.Event]) -> str:
    """Grid of the events whose Session Type staffs Venue AV/IT: dates across, time down; each cell spans its event."""
    root = '../'
    staffed_types = {sess.name: sess for sess in sop.sessions if any(s.role == VENUE_AV_IT for s in sess.staffing)}
    events = [e for e in events if e.session_type in staffed_types]
    dates = sorted({e.start_date for e in events})
    # Rows are the intervals between consecutive start/end times; an event's cell spans its rows.
    times = sorted({t for e in events for t in (e.start_time, e.end_time)}, key=schedule.time_key)
    row_of = {t: i for i, t in enumerate(times)}
    blocks: dict[tuple[str, int], tuple[int, list[schedule.Event]]] = {}  # (date, first row) -> (rowspan, events)
    for e in events:
        first, last = row_of[e.start_time], row_of[e.end_time]
        span, group = blocks.setdefault((e.start_date, first), (last - first, []))
        if span != last - first:
            raise ValueError(f'event {e.uid} shares its start with an event of different length; cannot merge cells')
        group.append(e)
    covered: dict[str, set[int]] = {d: set() for d in dates}
    for (date, first), (span, group) in blocks.items():
        rows_ = set(range(first, first + span))
        if rows_ & covered[date]:
            raise ValueError(f'overlapping events on {date}: {[e.uid for e in group]}')
        covered[date] |= rows_

    def cell(group: list[schedule.Event]) -> str:
        return ''.join(
            f'''<div class="schedule-event">
  <strong><a href="{filtered_runsheet_href(root, staffed_types[e.session_type], VENUE_AV_IT)}">{escape(e.title)}</a></strong><br>
  {escape(e.onsite_location)}<br>
  <em>{escape(schedule.auditorium_display_mode(e.session_type))}</em>
</div>'''
            for e in group
        )

    def row(i: int) -> str:
        tds = []
        for d in dates:
            if (d, i) in blocks:
                span, group = blocks[(d, i)]
                room = slugify(group[0].onsite_location)
                tds.append(f'<td class="schedule-cell room-{room}" rowspan="{span}">{cell(group)}</td>')
            elif i not in covered[d]:
                tds.append('<td></td>')
        return f'<tr><td class="time">{escape(times[i])}–{escape(times[i + 1])}</td>{"".join(tds)}</tr>'

    head = ''.join(f'<th>{escape(d)}</th>' for d in dates)
    rows = '\n'.join(row(i) for i in range(len(times) - 1))
    body = f'''{_top_tabs(root, 'schedule-for-venue-av-it')}
<p>In UTC+4 (Dubai).</p>
<table class="runsheet schedule">
<thead><tr><th>Time</th>{head}</tr></thead>
<tbody>
{rows}
</tbody>
</table>'''
    return _page(f'Schedule for {VENUE_AV_IT}', root, body)
