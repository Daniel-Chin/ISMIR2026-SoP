# ISMIR 2026 Session SOP

Live: https://daniel-chin.github.io/ISMIR2026-SoP/

The standard operation procedure for each type of ISMIR 2026 session: how it runs, who staffs it, and who does what when. This then supports volunteer handbook and attendance guides.

## Editing the SOP (organizers)

Everything lives in [content/](content/):

```
content/
  roles.json                     every role, its job description, and its guides (by title)
  guides/
    for-all-volunteers.md           a guide; first line `# For All Volunteers`; online volunteers get "For Online Volunteers" automatically
    ...
  sessions/
    11-opening-session.json         name, staffing, runsheet
    11-opening-session.md           The Idea
    12-...
  images/                         images used in any markdown
ai_generated/                     per-role views of The Idea, written by an LLM; see ai_generated/readme.md
```

- **Add a session type**: add a `.json` + `.md` pair in `content/sessions/`. The menu lists sessions in file-name order (hence the number prefixes); the page address comes from the session's `name`, not the file name.
- **Roles** are defined once in `roles.json`. Sessions refer to them by exact name in `staffing` and in each job's `roles`. Every role in a runsheet must also be in that session's staffing. Each role has a page, `roles/<role-address>/`, with its description and its guides in full.
- **Add a guide**: write `content/guides/<title-address>.md` starting with the line `# <Title>`, where the address is the title lowercased with non-alphanumerics replaced by `-` (e.g. "About Webinar Q&A" → `about-webinar-q-a.md`). List the title in the `guides` of each role that needs it. Guides appear in full on the All guides page and on the page of each role that lists them. (The volunteer guides were imported from the 2026 volunteer Google Doc.)
- **Edited The Idea of a session?** Regenerate its AI views; see [ai_generated/readme.md](ai_generated/readme.md). `build` warns about stale ones.
- **Mention a role** in any markdown text (The Idea, job descriptions, short and long descriptions) by writing `[[Role Name]]`.
- **Images**: compress and put the file in `content/images/` and write `![description](images/stage-layout.png)` in any markdown text. The path is always `images/...`, whichever page the text ends up on.
- `uptime` (optional, default 1) on a `staffing` entry is the fraction of the session the role actually works, in (0, 1]. It scales the person-hours on the Roles page.
- `time_info` is free text, e.g. `"T−15 min"`. `more_info` may be `""`.

## Testing and building

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv run ismir2026-sop serve      # build, then preview at http://localhost:8000
uv run ismir2026-sop build      # static check, then write the site to _site/
```

Pushing to `main` builds and deploys to GitHub Pages ([.github/workflows/pages.yml](.github/workflows/pages.yml)); pull requests are built and checked but not deployed. In the repo settings, set Pages → Source to "GitHub Actions".

## Runsheet links

A session page's view (mode and roles, applied to both Staffing and the Runsheet) is kept in the URL, so a cheatsheet can be bookmarked or shared.
