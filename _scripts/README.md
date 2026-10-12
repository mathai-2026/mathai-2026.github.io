# Export the workshop website lists

Run from the repository root using the existing OpenReview environment:

```sh
/Users/psong/anaconda3/envs/mathai-openreview/bin/python _scripts/export_openreview.py
```

Log in with a workshop organizer account at the terminal prompts. The password
prompt is hidden. Credentials are never written to files. Alternatively, the
script reads `OPENREVIEW_TOKEN`, or `OPENREVIEW_USERNAME` and
`OPENREVIEW_PASSWORD`, from the environment.

The script only reads OpenReview. It writes these local files after all checks
succeed:

- `_data/accepted_papers.yml`: all accepted titles and forum links, sorted by
  numeric submission number, including oral and poster decisions.
- `_data/reviewer_acknowledgements.yml`: preferred full names of reviewers who
  have at least one current assignment and submitted an official review for
  every current assignment, sorted alphabetically by displayed full name.
- `openreview/website_export/reviewer_completion.csv`: a private audit of
  assignments, completed counts, and missing submission numbers. This directory
  is ignored by Git and excluded from the Jekyll build.

Full names come from the profile's `names[].fullname` field, prioritizing the
preferred name entry. The exporter rejects profile IDs as display names.
If an older export contains IDs, rerun this script to replace them with names.

The paper list uses the latest decision and excludes withdrawn and desk-rejected
submissions. If no decision is visible, an accepted venue status is used.
Reviewer completion covers all current assignments, including rejected papers;
removed assignments are not counted. Anonymous review signatures are resolved
through organizer-visible groups. Missing access or unresolved identities stop
the export instead of silently producing an incomplete list.

The page uses sequential list numbering, matching the 2025 layout; submission
numbers determine ordering. The script never publishes or pushes changes.
After running, ask Codex to inspect the generated website data and completion
audit before committing or publishing.
