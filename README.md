# ISMIR 2026 Session SoP

The standard procedure for each type of ISMIR 2026 session: how it runs, who staffs it, and who does what when. See [design.md](design.md) for the full design.

## Editing the SoP (organizers)

Everything lives in [content/](content/):

```
content/
  roles.json                     every role and its job description
  sessions/
    01-oral-session.json         name, staffing, runsheet
    01-oral-session.md           The Idea
    02-poster-session.json
    02-poster-session.md
```

- **Add a session type**: add a `.json` + `.md` pair in `content/sessions/`. The menu lists sessions in file-name order (hence the number prefixes); the page address comes from the session's `name`, not the file name.
- **Roles** are defined once in `roles.json`. Sessions refer to them by exact name in `staffing` and in each job's `roles`. Every role in a runsheet must also be in that session's staffing.
- **Mention a role** in any markdown text (The Idea, job descriptions, short and long descriptions) by writing `[[Role Name]]`.
- `time_info` is free text, e.g. `"T−15 min"` or `"5 min"`. `more_info` may be `""`.

The shape of the data is defined in [src/ismir2026_sop/datatype.py](src/ismir2026_sop/datatype.py).

## Checking and building

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv run ismir2026-sop check      # report problems, e.g. a misspelled [[Role]] mention
uv run ismir2026-sop build      # check, then write the site to _site/
uv run ismir2026-sop serve      # build, then preview at http://localhost:8000
```

Pushing to `main` builds and deploys to GitHub Pages ([.github/workflows/pages.yml](.github/workflows/pages.yml)); pull requests are built and checked but not deployed. In the repo settings, set Pages → Source to "GitHub Actions".

## Runsheet links

A runsheet's view is kept in the URL, so a cheatsheet can be bookmarked or shared:

```
<site>/oral-session/runsheet/?mode=filter&roles=zoom-volunteer
<site>/oral-session/runsheet/?mode=highlight&roles=session-chair,room-volunteer
```

`mode` is `mastermind`, `highlight` or `filter`; `roles` are role names in address form (lowercase, non-alphanumerics → `-`).
