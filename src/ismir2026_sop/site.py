"""Write the static site.

    index.html                      Menu
    roles/index.html                All roles and the session types they appear in
    roles/<role>/index.html         A role's description and guides (content/guides/)
    guides/index.html               All guides, and the roles that need each
    <session>/index.html            The Idea (or its AI-generated view for the one ticked role),
                                    Staffing, Runsheet (?mode=...&roles=a,b)
    <session>/runsheet/index.html   Redirects to <session>/#runsheet
    schedule-for-venue-av-it/       Date x time grid of events staffed by Venue AV/IT
    static/                         CSS and JS
    images/                         copied from content/images/
"""

import os
import shutil
from html import escape
from pathlib import Path

from . import md, schedule
from .datatype import ONLINE_VOLUNTEER_GUIDE, Guide, Role, Session, SOP
from .idea_views import strip_stamp
from .slug import slugify

# Set automatically by GitHub Actions (e.g. in a fork); local builds link to the main repo.
REPO_URL = (
    f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}"
    if 'GITHUB_REPOSITORY' in os.environ
    else 'https://github.com/Daniel-Chin/ISMIR2026-SoP'
)
SITE_TITLE = 'ISMIR 2026 Session SOP'
STATIC_DIR = Path(__file__).parent / 'static'
VENUE_AV_IT = 'Venue AV/IT'
ROLES_JSON = 'content/roles.json'


def build_site(sop: SOP, out: Path, content: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STATIC_DIR, out / 'static')
    if (content / 'images').is_dir():
        shutil.copytree(content / 'images', out / 'images')
    (out / '.nojekyll').touch()
    roles = {r.name: r for r in sop.roles}
    guides = {g.title: g for g in sop.guides}

    _write(out / 'index.html', _menu_page(sop))
    events = schedule.load_events() if schedule.EVENTS_CSV.exists() else None
    _write(out / 'roles' / 'index.html', _roles_page(sop, roles, events))
    for role in sop.roles:
        _write(out / 'roles' / slugify(role.name) / 'index.html', _role_page(sop, role, roles, guides))
    _write(out / 'guides' / 'index.html', _guides_page(sop, roles))
    for session in sop.sessions:
        slug = slugify(session.name)
        _write(out / slug / 'index.html', _session_page(session, roles))
        _write(out / slug / 'runsheet' / 'index.html', _runsheet_redirect_page())
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
    """The role's cheatsheet; uses the same URL parameters as the session page's controls."""
    return f'{root}{slugify(session.name)}/?mode=filter&roles={slugify(role)}'


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


def _source(path: str, attrs: str = '') -> str:
    """Link from a section to the repo file it comes from; goes right after the section's heading text."""
    if not REPO_URL:
        return ''
    return f' <a class="source" href="{REPO_URL}/blob/main/{escape(path)}" title="Edit {escape(path)} on GitHub"{attrs}>edit on GitHub</a>'


def _page(title: str, root: str, body: str, *, scripts: str = '') -> str:
    head_title = f'{title} · {SITE_TITLE}' if title != SITE_TITLE else SITE_TITLE
    footer = (
        f'''<footer class="site-footer">
  Edit this SOP via <a href="{REPO_URL}">this repo</a>
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


def _staffing_summary(session: Session) -> str:
    return ', '.join(f'{s.count}× {escape(s.role)}' for s in session.staffing)


def _top_tabs(root: str, current: str) -> str:
    tabs = [('sessions', 'All session types', root or './'), ('roles', 'All roles', f'{root}roles/'),
            ('guides', 'All guides', f'{root}guides/'),
            ('schedule-for-venue-av-it', 'Schedule for Venue AV/IT', f'{root}schedule-for-venue-av-it/')]
    links = ''.join(
        f'<a href="{href}" aria-current="page">{label}</a>' if key == current
        else f'<a href="{href}">{label}</a>'
        for key, label, href in tabs
    )
    return f'<nav class="tabs">{links}</nav>'


def _menu_page(sop: SOP) -> str:
    items = '\n'.join(
        f'''<li>
  <h2><a href="{slugify(s.name)}/">{escape(s.name)}</a></h2>
  <p class="staffing-summary">{_staffing_summary(s)}</p>
</li>'''
        for s in sop.sessions
    )
    body = f'{_top_tabs("", "sessions")}\n<ul class="menu">\n{items}\n</ul>'
    return _page(SITE_TITLE, '', body)


def _role_href(root: str, role: str) -> str:
    return f'{root}roles/{slugify(role)}/'


def _guide_id(title: str) -> str:
    return f'guide-{slugify(title)}'


def _role_title(role: Role, root: str, *, link: bool) -> str:
    name = f'<a href="{_role_href(root, role.name)}">{escape(role.name)}</a>' if link else escape(role.name)
    chip = ' <span class="volunteer-chip">Volunteer</span>' if role.is_volunteer else ''
    return name + chip


def _roles_page(sop: SOP, roles: dict[str, Role], events: list[schedule.Event] | None) -> str:
    root = '../'

    def link_for(name: str) -> str | None:
        if name not in roles:
            raise KeyError(f'unknown role mention [[{name}]] (roles.json)')
        return f'#{slugify(name)}'

    if events is not None:
        hours = schedule.total_hours_by_session_type(events)
    sections = []
    for role in sop.roles:
        appears = [
            (session, s) for session in sop.sessions for s in session.staffing if s.role == role.name
        ]
        # Counts are only worth showing when they vary from the default of one.
        show_counts = any(s.count > 1 for _, s in appears)
        session_links = ', '.join(
            f'<a href="{filtered_runsheet_href(root, session, role.name)}">{escape(session.name)}</a>{f" ({s.count} per session)" if show_counts else ""}'
            for session, s in appears
        ) or '<em>none</em>'
        person_hours = (
            f' · {sum(s.count * s.uptime * hours.get(session.name, 0) for session, s in appears):g} (person ྾ hour)s in total'
            if events is not None else ''
        )
        sections.append(f'''<section class="role" id="{slugify(role.name)}">
  <h3>{_role_title(role, root, link=True)}{_anchor(slugify(role.name))}{_source(ROLES_JSON)}</h3>
  <p class="role-attrs">{'On-Site (In-Person)' if role.is_onsite else 'Online (Remote)'}{person_hours}</p>
  <div class="prose">{md.render(role.job_description, link_for, root, anchor_prefix=f'{slugify(role.name)}-')}</div>{_job_for_who(role)}{_guides(role, root)}
  <p class="role-sessions"><strong>Appears in:</strong> {session_links}</p>
</section>''')
    body = f'{_top_tabs(root, "roles")}\n' + '\n'.join(sections)
    return _page('Roles', root, body)


def _anchor(id: str) -> str:
    """Clickable `#` that links to element `id`; matches the markdown headings' permalinks."""
    return f'<a class="anchor" href="#{id}" title="Link to this section">#</a>'


def _job_for_who(role: Role) -> str:
    if not role.job_for_who:
        return ''
    return f'\n  <p class="job-for-who"><strong>Job for who:</strong> {escape(role.job_for_who)}</p>'


def guide_titles(role: Role) -> list[str]:
    return ([ONLINE_VOLUNTEER_GUIDE] if role.is_volunteer and role.is_online else []) + role.guides


def _guides(role: Role, root: str) -> str:
    """Links to the guides, which are rendered on the role's page."""
    titles = guide_titles(role)
    if not titles:
        return ''
    href = _role_href(root, role.name)
    links = ', '.join(f'<a href="{href}#{_guide_id(t)}">{escape(t)}</a>' for t in titles)
    return f'\n  <p class="role-guides"><strong>Guides:</strong> {links}</p>'


def _role_page(sop: SOP, role: Role, roles: dict[str, Role], guides: dict[str, Guide]) -> str:
    """One shareable page per role: its description and its guides in full."""
    root = '../../'

    def link_for(name: str) -> str | None:
        if name not in roles:
            raise KeyError(f'unknown role mention [[{name}]] (role page of {role.name!r})')
        return None if name == role.name else _role_href(root, name)

    sections = []
    for title in guide_titles(role):
        guide = guides[title]
        gid = _guide_id(title)
        text = guide.body
        sections.append(f'''<section class="guide" id="{gid}">
<h2>{escape(title)}{_anchor(gid)}{_source(guide.markdown_path)}</h2>
<article class="prose idea">
{md.render(text, link_for, root, anchor_prefix=f'{gid}-', baselevel=2)}
</article>
</section>''')
    toc = ''
    if sections:
        items = ''.join(f'<li><a href="#{_guide_id(t)}">{escape(t)}</a></li>' for t in guide_titles(role))
        toc = f'\n<p class="role-guides"><strong>Table of Contents</strong></p>\n<ol class="guide-toc">{items}</ol>'
    body = f'''{_top_tabs(root, 'roles')}
<h1>{_role_title(role, root, link=False)}{_source(ROLES_JSON)}</h1>
<p class="role-attrs">{'On-Site (In-Person)' if role.is_onsite else 'Online (Remote)'}</p>
<div class="prose">{md.render(role.job_description, link_for, root)}</div>{_job_for_who(role)}{toc}
{chr(10).join(sections)}'''
    return _page(role.name, root, body)


def _guides_page(sop: SOP, roles: dict[str, Role]) -> str:
    """Every guide in full, in order of first use by the roles, each with the roles that need it."""
    root = '../'

    def link_for(name: str) -> str | None:
        if name not in roles:
            raise KeyError(f'unknown role mention [[{name}]] (guides page)')
        return _role_href(root, name)

    users: dict[str, list[Role]] = {g.title: [] for g in sop.guides}
    for role in sop.roles:
        for title in guide_titles(role):
            users[title].append(role)
    by_title = {g.title: g for g in sop.guides}
    first_use = dict.fromkeys(title for role in sop.roles for title in guide_titles(role))
    order = [by_title[t] for t in first_use] + [g for g in sop.guides if g.title not in first_use]
    sections = []
    for guide in order:
        gid = slugify(guide.title)
        who = ', '.join(f'<a href="{_role_href(root, r.name)}#{_guide_id(guide.title)}">{escape(r.name)}</a>'
                        for r in users[guide.title]) or '<em>no role</em>'
        sections.append(f'''<section class="guide" id="{gid}">
<h2>{escape(guide.title)}{_anchor(gid)}{_source(guide.markdown_path)}</h2>
<p class="role-sessions"><strong>For:</strong> {who}</p>
<article class="prose idea">
{md.render(guide.body, link_for, root, anchor_prefix=f'{gid}-', baselevel=2)}
</article>
</section>''')
    items = ''.join(f'<li><a href="#{slugify(g.title)}">{escape(g.title)}</a></li>' for g in order)
    body = f'''{_top_tabs(root, 'guides')}
<ol class="guide-toc">{items}</ol>
{chr(10).join(sections)}'''
    return _page('Guides', root, body)


def _session_page(session: Session, roles: dict[str, Role]) -> str:
    """The Idea, Staffing, and Runsheet, under one Mode/Roles panel."""
    root = '../'
    link_for = _mention_linker(session, roles, root)
    idea = Path(session.the_idea_markdown_path).read_text(encoding='utf-8')
    # The full Idea; runsheet.js swaps in a role's view when exactly that one role is ticked.
    ideas = [f'''<article class="prose idea" data-idea="">
{md.render(idea, link_for, root, anchor_prefix='')}
</article>''']
    for role_name, path in session.idea_views.items():
        view = strip_stamp(Path(path).read_text(encoding='utf-8'))
        rslug = slugify(role_name)
        ideas.append(f'''<article class="prose idea" data-idea="{rslug}" hidden>
{md.render(view, link_for, root, anchor_prefix=f'{rslug}-')}{_guides(roles[role_name], root)}
  <p class="role-page"><a href="{_role_href(root, role_name)}">All about the {escape(role_name)}</a></p>
</article>''')
    # One source link per version of The Idea; runsheet.js shows the one of the version shown.
    idea_sources = _source(session.the_idea_markdown_path, ' data-idea-source=""') + ''.join(
        _source(path, f' data-idea-source="{slugify(role_name)}" hidden') for role_name, path in session.idea_views.items()
    )
    checkboxes = '\n'.join(
        f'<label><input type="checkbox" value="{slugify(s.role)}"> {escape(s.role)}</label>'
        for s in session.staffing
    )
    staff = '\n'.join(
        f'''<section class="role staff" id="{slugify(s.role)}" data-role="{slugify(s.role)}">
  <h3>{s.count}× <a href="{filtered_runsheet_href(root, session, s.role)}">{escape(s.role)}</a>{' <span class="volunteer-chip">Volunteer</span>' if roles[s.role].is_volunteer else ''}{_anchor(slugify(s.role))}</h3>
  <div class="prose">{md.render(roles[s.role].job_description, link_for, root)}</div>{_job_for_who(roles[s.role])}{_guides(roles[s.role], root)}
  <p class="role-page"><a href="{_role_href(root, s.role)}">All about the {escape(s.role)}</a></p>
</section>'''
        for s in session.staffing
    )
    rows = []
    for i, job in enumerate(session.runsheet, 1):
        chips = ' '.join(
            f'<a class="role-chip" data-role="{slugify(r)}" href="{filtered_runsheet_href(root, session, r)}">{escape(r)}</a>'
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
    body = f'''<h1>{escape(session.name)}</h1>
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
</form>
<h2 id="the-idea"><span id="idea-title">The Idea</span>{_anchor("the-idea")}{idea_sources}</h2>
{chr(10).join(ideas)}
<h2 id="staffing" class="staffing-section"><span id="staffing-title">Staffing</span>{_anchor("staffing")}{_source(session.source_path)}</h2>
<p class="status" id="staffing-status" aria-live="polite" hidden></p>
{staff}
<h2 id="runsheet">Runsheet{_anchor("runsheet")}{_source(session.source_path)}</h2>
<div class="controls runsheet-controls" id="runsheet-controls" hidden>
  <span class="status" id="status" aria-live="polite"></span>
</div>
<table class="runsheet">
<thead><tr><th>Time</th><th>Who</th><th>What</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>'''
    return _page(
        session.name, root, body,
        scripts=f'<script src="{root}static/runsheet.js"></script>',
    )


def _runsheet_redirect_page() -> str:
    """Old runsheet URL: forward to the session page's Runsheet section, keeping the query and any #row-N."""
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Redirecting…</title>
<script>location.replace('../' + location.search + (location.hash || '#runsheet'));</script>
<noscript><meta http-equiv="refresh" content="0; url=../#runsheet"></noscript>
</head>
<body><a href="../#runsheet">Runsheet</a></body>
</html>
'''


def _venue_av_it_schedule_page(sop: SOP, events: list[schedule.Event]) -> str:
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

    def event_html(e: schedule.Event) -> str:
        return f'''<strong><a href="{filtered_runsheet_href(root, staffed_types[e.session_type], VENUE_AV_IT)}">{escape(e.title)}</a></strong><br>
  {escape(e.onsite_location)}<br>
  <em>{escape(schedule.auditorium_display_mode(e.session_type))}</em>'''

    def cell(group: list[schedule.Event]) -> str:
        return ''.join(f'<div class="schedule-event">\n  {event_html(e)}\n</div>' for e in group)

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

    def day_list(d: str) -> str:
        """Phone view of one date; the table is too wide for a phone."""
        items = '\n'.join(
            f'''<li class="room-{slugify(e.onsite_location)}">
  <span class="time">{escape(e.start_time)}–{escape(e.end_time)}</span><br>
  {event_html(e)}
</li>'''
            for e in sorted((e for e in events if e.start_date == d), key=lambda e: schedule.time_key(e.start_time))
        )
        return f'<h2>{escape(d)}</h2>\n<ul>\n{items}\n</ul>'

    head = ''.join(f'<th>{escape(d)}</th>' for d in dates)
    rows = '\n'.join(row(i) for i in range(len(times) - 1))
    body = f'''{_top_tabs(root, 'schedule-for-venue-av-it')}
<p>In UTC+4 (Dubai).</p>
<table class="runsheet schedule">
<thead><tr><th>Time</th>{head}</tr></thead>
<tbody>
{rows}
</tbody>
</table>
<div class="schedule-list">
{chr(10).join(day_list(d) for d in dates)}
</div>'''
    return _page(f'Schedule for {VENUE_AV_IT}', root, body)
