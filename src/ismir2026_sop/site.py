"""Write the static site.

    index.html                      Menu
    <session>/index.html            The Idea
    <session>/runsheet/index.html   Runsheet (?mode=...&roles=a,b)
    static/                         CSS and JS
"""

import shutil
from html import escape
from pathlib import Path

from . import md
from .datatype import Role, Session, SoP
from .slug import slugify

REPO_URL = 'https://github.com/Daniel-Chin/ISMIR2026-SoP'
SITE_TITLE = 'ISMIR 2026 Session SoP'
STATIC_DIR = Path(__file__).parent / 'static'


def build_site(sop: SoP, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STATIC_DIR, out / 'static')
    (out / '.nojekyll').touch()
    roles = {r.name: r for r in sop.roles}

    _write(out / 'index.html', _menu_page(sop))
    for session in sop.sessions:
        slug = slugify(session.name)
        _write(out / slug / 'index.html', _idea_page(session, roles))
        _write(out / slug / 'runsheet' / 'index.html', _runsheet_page(session, roles))


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
<footer class="site-footer">
  Edit this SoP via <a href="{REPO_URL}">this repo</a>{source_link}
</footer>
{scripts}
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


def _menu_page(sop: SoP) -> str:
    items = '\n'.join(
        f'''<li>
  <h2>{escape(s.name)}</h2>
  <p class="staffing-summary">{_staffing_summary(s)}</p>
  <p class="menu-links"><a href="{slugify(s.name)}/">The Idea</a> <a href="{slugify(s.name)}/runsheet/">Runsheet</a></p>
</li>'''
        for s in sop.sessions
    )
    body = f'<h1>Session types</h1>\n<ul class="menu">\n{items}\n</ul>'
    return _page(SITE_TITLE, '', body)


def _idea_page(session: Session, roles: dict[str, Role]) -> str:
    root = '../'
    link_for = _mention_linker(session, roles, root)
    idea = Path(session.the_idea_markdown_path).read_text(encoding='utf-8')
    staff = '\n'.join(
        f'''<section class="role" id="{slugify(s.role)}">
  <h3>{s.count}× {escape(s.role)}</h3>
  <p class="role-links"><a href="{filtered_runsheet_href(root, session, s.role)}">Cheatsheet: runsheet for this role</a></p>
  <div class="prose">{md.render(roles[s.role].job_description, link_for)}</div>
</section>'''
        for s in session.staffing
    )
    body = f'''{_session_header(session, root, 'idea')}
<article class="prose idea">
{md.render(idea, link_for)}
</article>
<h2>Staffing</h2>
{staff}'''
    return _page(session.name, root, body, source=session.the_idea_markdown_path)


def _runsheet_page(session: Session, roles: dict[str, Role]) -> str:
    root = '../../'
    link_for = _mention_linker(session, roles, root)
    checkboxes = '\n'.join(
        f'<label><input type="checkbox" value="{slugify(s.role)}"> {escape(s.role)}</label>'
        for s in session.staffing
    )
    rows = []
    for job in session.runsheet:
        chips = ' '.join(
            f'<a class="role-chip" data-role="{slugify(r)}" href="../#{slugify(r)}">{escape(r)}</a>'
            for r in job.roles
        )
        details = ''
        if job.long_description.strip():
            details = (
                '<details><summary>More</summary>'
                f'<div class="prose">{md.render(job.long_description, link_for)}</div></details>'
            )
        rows.append(f'''<tr class="job" data-roles="{' '.join(slugify(r) for r in job.roles)}">
  <td class="time">{escape(job.time_info)}</td>
  <td class="who">{chips}</td>
  <td class="what"><div class="short">{md.render_inline(job.short_description, link_for)}</div>{details}</td>
</tr>''')
    body = f'''{_session_header(session, root, 'runsheet')}
<form class="controls" id="controls" hidden>
  <label class="mode">Mode
    <select id="mode">
      <option value="totality">totality</option>
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
<table class="runsheet">
<thead><tr><th>Time</th><th>Who</th><th>What</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>'''
    return _page(
        f'{session.name} runsheet', root, body,
        scripts=f'<script src="{root}static/runsheet.js"></script>',
    )
