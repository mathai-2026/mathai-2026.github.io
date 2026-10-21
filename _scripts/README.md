# Organizer scripts

OpenReview helpers used to run the workshop, listed in the order they come up
during the review cycle. Every OpenReview script is **read-only**: none of them
invite reviewers, post notes, or change anything on OpenReview.

Run everything from the repository root. Outputs that contain submission PDFs,
reviewer lists, or audits go to `openreview/` (git-ignored and excluded from the
Jekyll build). Only `export_openreview.py` writes into the website (`_data/`).

## Setup

```sh
conda create -y -n mathai-openreview python=3.11
conda activate mathai-openreview
python -m pip install -U openreview-py pymupdf
```

Credentials are read from the environment (or prompted for by
`export_openreview.py`), so passwords never go into files:

```sh
export OPENREVIEW_USERNAME='your-openreview-login'
export OPENREVIEW_PASSWORD='your-password'
```

**Reusing next year:** every OpenReview script accepts `--venue`; its default is
this year's venue ID. Update the defaults with
`grep -rl 'NeurIPS.cc/2026' _scripts` (and the year in the printed headings).

## 1. Reviewer recruitment

Plain-text helpers for OpenReview ID lists (one `~Profile_ID1` per line); they
do not talk to OpenReview.

- `comma_ids_to_lines.py <ids.txt> [out.txt]`: turn a comma-separated ID list
  (e.g. an OpenReview group export) into one ID per line.
- `dedupe_invite_ids.py <candidates.txt> --invited invited_ids.txt`: drop IDs
  that were already invited; writes `<candidates>_new.txt` and
  `<candidates>_duplicates.txt` next to the input.

## 2. Submission triage (after the submission deadline)

```sh
python _scripts/mathai_submission_triage.py
```

Downloads every active submission's PDF and flags likely page-limit and
anonymity problems. Writes `openreview/mathai_triage_output/mathai_triage.csv`
(sort by `triage` and start with `MANUAL_CHECK_HIGH_PRIORITY`), a field
inventory CSV, and `pdfs/`.

This is a triage tool, not an auto-desk-reject tool. The rule is 4 pages of
*content* with unlimited references and supplementary material, so page
checking is heuristic and every flagged paper must be opened manually.

## 3. Reciprocal reviewers

```sh
python _scripts/mathai_active_reciprocal_reviewers.py [--skip-pdfs]
```

Lists every active submission with its `reciprocal_reviewer` and
`reciprocal_reviewing_agreement` fields, resolves the reviewers' profiles, and
flags missing reviewers, missing agreements, reviewers nominated by more than
one submission, and unresolved profiles. Writes to `openreview/mathai_active/`
(`summary.txt`, `reciprocal_reviewer_by_submission.csv`,
`reciprocal_reviewers_unique.csv`, `active_submissions.csv`, `pdfs/`). Review
these before inviting anyone.

```sh
python _scripts/mathai_reciprocal_response_audit.py [--exempt 12 34]
```

After invitations go out: checks each reciprocal reviewer against the
Reviewers / Invited / Declined groups and writes ID lists of pending, declined,
and not-found reviewers (for reminders) to
`openreview/mathai_reciprocal_response_audit/`. Pass `--exempt` with the
numbers of submissions exempted from reciprocal reviewing.

## 4. Assignment readiness

```sh
python _scripts/mathai_affinity_audit.py
```

Before running the matcher: counts, for every active paper, how many current
reviewers have a positive affinity score and no conflict, and lists papers with
fewer than 4 (the matcher's demand). Writes to
`openreview/mathai_affinity_audit/`.

## 5. Website export (after decisions)

```sh
python _scripts/export_openreview.py
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
  assignments, completed counts, and missing submission numbers.

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
Inspect the generated website data and the completion audit before committing.
