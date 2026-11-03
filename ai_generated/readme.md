# AI-generated role views

The Idea of a session (`content/sessions/*.md`) is written for the organizers and covers every role.
A role's `job_description` (`content/roles.json`) is written once for every session the role appears in.
A volunteer who only runs a mic needs neither the stage laptop setup nor a generic job description.

So, for each role staffed in a session, an LLM writes a **view**: a briefing bespoke to that role in that
session, which merges The Idea with the role's `job_description`:

    ai_generated/<session>/<role>.md

(`<session>` and `<role>` are the page addresses: the names lowercased, non-alphanumerics replaced by `-`.)

## What a view shows, and what it replaces

A session page shows the view, titled "For the <role>", when exactly one role with a view is ticked. In
that case **neither The Idea nor the role's Staffing card (its `job_description`) is displayed**. The view
is all the volunteer reads above the Runsheet, so it must carry everything they need from both. The page
adds the role's guide links and a link to its role page under the view. In mastermind mode, when several
roles are ticked, or for a role without a view, the page shows the full Idea and the "Selected Roles" Staffing
cards as before.

## How to write a view

- Open with one or two lines on what the session is: format, length, place, how it is streamed.
- Then `### Your job`: the `job_description` applied to this session. Name the session's own people,
  questions and tools rather than repeating the generic text, and drop parts that do not apply here.
- Then only the designs, formats and technical details of The Idea that the role acts on.
- Drop every clause the role cannot act on, even inside a sentence that is otherwise kept (e.g. which
  other team presents what, or "the setup is the same as <another session>": state the setup itself).
- Do not repeat the Runsheet step by step: it is shown below the view.
- Do not add facts that are not in The Idea, the `job_description` or the Runsheet.

Views are not worth having for a placeholder Idea or a session with a single role.

Do not edit views by hand: edit the master Idea or the `job_description`, then regenerate.

## Whoever edits an Idea or a job_description: regenerate its views

The first line of each view stamps the hash of the Idea and the `job_description` it was made from.
`build` and `check` warn about views whose sources have changed since. To regenerate:

1. Ask an LLM (e.g. Claude Code in this repo) to rewrite the affected `ai_generated/<session>/<role>.md`
   from `content/sessions/<...>.md`, the session's JSON and `content/roles.json`, following the rules
   above. A changed `job_description` affects that role's view in every session.
2. Stamp the new views, then review the diff:

       uv run ismir2026-sop idea-views --stamp ai_generated/<session>/*.md

`uv run ismir2026-sop idea-views` lists every view as `ok`, `stale`, `unstamped` or `missing`.
