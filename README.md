# ISMIR 2026 Session SoP

Live: https://daniel-chin.github.io/ISMIR2026-SoP/

The standard procedure for each type of ISMIR 2026 session: how it runs, who staffs it, and who does what when. This then supports volunteer handbook and attendance guides.

## Editing the SoP (organizers)

Everything lives in [content/](content/):

```
content/
  roles.json                     every role and its job description
  sessions/
    11-opening-session.json         name, staffing, runsheet
    11-opening-session.md           The Idea
    12-...
```

- **Add a session type**: add a `.json` + `.md` pair in `content/sessions/`. The menu lists sessions in file-name order (hence the number prefixes); the page address comes from the session's `name`, not the file name.
- **Roles** are defined once in `roles.json`. Sessions refer to them by exact name in `staffing` and in each job's `roles`. Every role in a runsheet must also be in that session's staffing.
- **Mention a role** in any markdown text (The Idea, job descriptions, short and long descriptions) by writing `[[Role Name]]`.
- **Images**: compress and put the file in `content/images/` and write `![description](images/stage-layout.png)` in any markdown text. The path is always `images/...`, whichever page the text ends up on.
- `time_info` is free text, e.g. `"T−15 min"`. `more_info` may be `""`.

## Testing and building

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv run ismir2026-sop serve      # build, then preview at http://localhost:8000
uv run ismir2026-sop build      # static check, then write the site to _site/
```

Pushing to `main` builds and deploys to GitHub Pages ([.github/workflows/pages.yml](.github/workflows/pages.yml)); pull requests are built and checked but not deployed. In the repo settings, set Pages → Source to "GitHub Actions".

## Runsheet links

A runsheet's view is kept in the URL, so a cheatsheet can be bookmarked or shared.
