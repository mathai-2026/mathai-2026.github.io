#!/usr/bin/env python3
"""Read OpenReview; generate public website lists and a local completion audit."""
import argparse
import csv
import getpass
import json
import os
from collections import defaultdict
from pathlib import Path
import unicodedata


def unwrap(value):
    return value.get('value') if isinstance(value, dict) and 'value' in value else value


def alphabetic(name):
    return ''.join(c for c in unicodedata.normalize('NFKD', name.casefold())
                   if not unicodedata.combining(c))


def full_name(profile):
    """Profile.get_preferred_name() returns a username in some SDK versions."""
    names = unwrap(profile.content.get('names')) or []
    preferred = [n for n in names if n.get('preferred')]
    for entry in preferred + [n for n in names if not n.get('preferred')]:
        name = entry.get('fullname') or ' '.join(
            str(entry.get(part) or '').strip() for part in ('first', 'middle', 'last'))
        name = name.strip()
        if name and not name.startswith('~') and '@' not in name:
            return name
    raise ValueError(f'No full name in profile {profile.id}; refusing to display an ID.')


def collect(client, venue, profile_loader):
    config = {k: unwrap(v) for k, v in client.get_group(venue).content.items()}
    submissions = client.get_all_notes(invitation=config['submission_id'], details='directReplies')
    if not submissions:
        raise ValueError('No submissions visible. Log in with an organizer account.')
    by_id = {n.id: n for n in submissions}
    review_suffix = '/-/' + config['review_name']
    decision_suffix = '/-/' + config['decision_name']
    accepted_options = set(config['accept_decision_options'])
    excluded_statuses = {config.get('withdrawn_venue_id'), config.get('desk_rejected_venue_id')}
    papers = []
    reviews = []
    for note in submissions:
        content = {k: unwrap(v) for k, v in note.content.items()}
        replies = (note.details or {}).get('directReplies')
        if replies is None:
            raise ValueError(f'Missing replies for submission {note.number}; cannot verify completeness.')
        replies = [r for r in replies if not r.get('ddate')]
        decisions = [r for r in replies if any(i.endswith(decision_suffix) for i in r.get('invitations', []))]
        decision = ''
        if decisions:
            latest = max(decisions, key=lambda r: r.get('tmdate') or r.get('mdate') or r.get('tcdate') or 0)
            decision = unwrap(latest['content'].get(config['decision_field_name']))
        accepted = decision in accepted_options if decisions else content.get('venueid') == venue
        if accepted and not note.ddate and content.get('venueid') not in excluded_statuses:
            if not isinstance(note.number, int) or not str(content.get('title', '')).strip():
                raise ValueError('An accepted paper is missing its number or title.')
            papers.append({'number': note.number, 'title': content['title'],
                           'url': f'https://openreview.net/forum?id={note.id}'})
        reviews.extend((note.id, r) for r in replies
                       if r.get('replyto') == note.id and any(i.endswith(review_suffix) for i in r.get('invitations', [])))
    papers.sort(key=lambda p: p['number'])
    if not papers or len({p['number'] for p in papers}) != len(papers):
        raise ValueError('No accepted papers found, or duplicate submission numbers. Website data was not changed.')

    assignments = client.get_all_edges(invitation=config['reviewers_assignment_id'])
    assigned = defaultdict(set)
    for edge in assignments:
        if edge.ddate:
            continue
        if edge.head not in by_id:
            raise ValueError('An assignment references an inaccessible submission. Use an organizer account.')
        assigned[edge.tail].add(edge.head)
    if not assigned:
        raise ValueError('No assignments visible. Website data was not changed.')
    profiles = profile_loader(client, list(assigned), as_dict=True)
    canonical = {}
    for identity in assigned:
        profile = profiles.get(identity)
        if profile is None:
            raise ValueError(f'Cannot resolve assigned reviewer {identity}.')
        canonical[identity] = profile.id
    required = defaultdict(set)
    for identity, paper_ids in assigned.items():
        required[canonical[identity]].update(paper_ids)
    submitted = defaultdict(set)
    group_cache = {}
    for paper_id, review in reviews:
        identities = set()
        for signature in review.get('signatures', []):
            if signature.startswith('~'):
                identities.add(signature)
            elif signature.startswith(venue + '/'):
                if signature not in group_cache:
                    group_cache[signature] = client.get_group(signature).members
                members = group_cache[signature]
                if len(members) != 1:
                    raise ValueError(f'Review signature {signature} does not resolve to one reviewer.')
                member = members[0]
                identities.add(canonical.get(member, member))
        if len(identities) != 1:
            raise ValueError(f'Cannot uniquely identify the author of review {review["id"]}.')
        submitted[identities.pop()].add(paper_id)
    profile_by_id = {p.id: p for p in profiles.values() if p}
    reviewers = []
    audit = []
    for identity, paper_ids in sorted(required.items()):
        missing = paper_ids - submitted[identity]
        name = full_name(profile_by_id[identity])
        if not missing:
            reviewers.append({'name': name})
        audit.append({'profile_id': identity, 'name': name, 'assigned': len(paper_ids),
                      'completed': len(paper_ids & submitted[identity]),
                      'eligible': not missing,
                      'missing_submission_numbers': ';'.join(str(n) for n in sorted(by_id[p].number for p in missing))})
    reviewers.sort(key=lambda r: alphabetic(r['name']))
    if not reviewers:
        raise ValueError('No reviewers verified as complete. Website data was not changed.')
    return papers, reviewers, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--venue', default='NeurIPS.cc/2026/Workshop/MATH-AI')
    parser.add_argument('--output-root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    import openreview
    import openreview.api
    import openreview.tools
    token = os.environ.get('OPENREVIEW_TOKEN')
    credentials = {'token': token} if token else {
        'username': os.environ.get('OPENREVIEW_USERNAME') or input('OpenReview login: ').strip(),
        'password': os.environ.get('OPENREVIEW_PASSWORD') or getpass.getpass('OpenReview password: ')}
    client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', **credentials)
    papers, reviewers, audit = collect(client, args.venue, openreview.tools.get_profiles)
    data = args.output_root / '_data'
    data.mkdir(parents=True, exist_ok=True)
    # JSON is valid YAML; Jekyll loads these files without an extra Python dependency.
    for filename, rows in [('accepted_papers.yml', papers), ('reviewer_acknowledgements.yml', reviewers)]:
        (data / filename).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    audit_dir = args.output_root / 'openreview' / 'website_export'
    audit_dir.mkdir(parents=True, exist_ok=True)
    with (audit_dir / 'reviewer_completion.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(audit[0]))
        writer.writeheader()
        writer.writerows(audit)
    print(f'Generated {len(papers)} accepted papers and {len(reviewers)} completed reviewers.')
    print(f'Private completion audit: {audit_dir / "reviewer_completion.csv"}')
    print('No OpenReview data was modified. Website files are local; nothing was published.')


if __name__ == '__main__':
    main()
