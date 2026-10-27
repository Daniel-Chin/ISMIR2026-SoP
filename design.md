# ISMIR 2026 Session SoP — Design

## Purpose
A website that sets out the standard procedure (SoP) for each type of ISMIR 2026 session: how the session is meant to run, who staffs it, and what each person does when.

- **Organizers** edit the SoP by changing files in this repo by hand. Those files must stay easy to read and edit as plain text.
- **Everyone else** (volunteers, etc.) only views it in a browser. It also has to work as an on-the-day cheatsheet, on a phone or printed.

## Concepts
- **Role**: a job a person does (e.g. Zoom Volunteer), with a job description. Roles are defined once and reused across session types.
- **Session type**: for example, oral session or poster session. Each one has:
  - **The Idea**: a markdown document explaining the reasoning and design behind this session type.
  - **Staffing**: which roles this session needs, and how many people for each (e.g. 2× Room Volunteer).
  - **Runsheet**: an ordered list of jobs that makes up the session's timeline.
- **Job** (one runsheet entry) = time info × roles involved × short description × long description.

## Data model
The data must follow [datatype.py](src/ismir2026_sop/datatype.py). It is the source of truth for the data's shape:

- `SoP`: all roles, all sessions.
- `Role`: name, job description. Defined once, at the top level.
- `Session`: name, path to The Idea markdown, staffing, runsheet.
- `Staffing`: role name, count.
- `Job`: time info (free text, e.g. "T−15 min", "5 min"), role names, short description, long description.

A role name used in a session's staffing or runsheet must exist among the top-level roles. Every role in a runsheet must also appear in that session's staffing.

### Page addresses
Each session's address comes from its name, by a fixed and readable rule: lowercase the name, turn every run of non-alphanumeric characters into a single `-`, and trim `-` from both ends. For example, "Oral Session" → `oral-session`. Roles in URL parameters use the same rule. Two sessions (or two roles) that end up with the same address are an error.

Organizers write the content as JSON, plus markdown files for The Idea. Choose a file layout that is easy for an organizer to find their way around and edit.

## Role mentions in markdown
- In any markdown text (The Idea and job descriptions), an author refers to a role by writing `[[Role Name]]`, e.g. `[[Zoom Volunteer]]`. 
- When displayed, the mention shows just the role name: `Zoom Volunteer`. Runtime should raise KeyError on typo.
- Where the mention links to:
  - In a session's The Idea: that session's runsheet, filtered to that role.
  - In a role's job description: the job description is shown on many sessions' pages, so the link goes to the runsheet of whichever session is being viewed. If that session doesn't staff the role, the mention is shown but not linked.
- A mention that doesn't match any defined role must be easy to spot: shown as an error on the page and/or reported by a check script. This is the "spellcheck".

## Pages
The site is view-only. On the bottom, "edit this SoP via this repo" (https://github.com/Daniel-Chin/ISMIR2026-SoP)

### Menu
Lists all session types. Each links to that session's The Idea and Runsheet.

### The Idea (per session)
1. The session's The Idea markdown, rendered.
2. Below it, each role this session staffs, with its count and job description.

### Runsheet (per session)
- A table of jobs in order, showing for each: time info, roles involved, and short description. The long description can be expanded.
- Controls:
  - **Mode** dropdown with three options:
    - **mastermind**: show every job, nothing emphasized.
    - **highlight**: show every job; jobs involving the selected roles stand out and the rest are de-emphasized.
    - **filter**: show only jobs involving the selected roles.
  - **One checkbox per role** in this session, to choose the selected roles. The checkboxes are hidden in mastermind mode.
- The mode and the selected roles are kept in URL parameters. A filtered or highlighted view can then be bookmarked or shared, for example "the Zoom Volunteer's cheatsheet". Role-mention links use these same parameters.
- It should print cleanly, without the controls.

## Non-goals
- No editing in the browser, no accounts, no backend.

## Deploy
Static site. Set up gh workflow for gh pages.
