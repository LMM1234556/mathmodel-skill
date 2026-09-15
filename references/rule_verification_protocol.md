# Rule verification protocol

Read this protocol only in Stage 0, Stage 8, and Stage 9. Its purpose is to stop a
repository note, search snippet, or prior-year document from being mistaken for
the rules that govern the team's current submission.

## 1. Identify before searching

Obtain the contest and target year from the participant and write them to
`decision_log.json` before loading a competition pack. Do not offer rule versions
as the first choice and do not infer a default contest.

## 2. Build one source-backed snapshot

Copy `templates/shared/rules_snapshot.json` to
`<cwd>/state/rules_snapshot.json`. Open the selected contest's official pages and
files, then record every source with a unique ID, title, URL, access time, year of
applicability, and `official=true`.

Repository files and search-result snippets may help locate a source, but they are
not rule authority. If an official PDF or downloaded rule file controls the
submission, preserve its URL and file hash in the source record or notes.

For each category, use exactly one status:

- `confirmed`: record concrete facts and the official source IDs that support them;
- `unknown`: the current official material does not yet resolve the category;
- `not_applicable`: an official source establishes that the category does not
  apply; record both the source and rationale.

The required categories are eligibility/team, schedule, problem/download,
official template/cover, typography/paragraphs, pagination/page limits,
anonymity, appendix/supporting materials, submission files, submission process,
AI use, and citation/originality. Never collapse the format categories into one
generic “format checked” statement, and never turn silence about AI into
`not_applicable`.

For format-sensitive categories, inspect the official opening notice, paper
format specification, standard document/template, submission manual, and the
selected problem statement. Record “the reviewed documents do not state a
total-paper limit” as a sourced fact; do not convert it into a guessed limit or
confuse it with the abstract page limit. A missing current-year document leaves
the affected category `unknown` and blocks final submission.

## 3. Expose gaps and conflicts to the participant

Before continuing, show a compact table containing category, status, decisive
fact, source, and impact. List unresolved items separately with the phases they
block. If repository guidance differs from an official source, add the mismatch
to `conflicts`, follow the official source, and repair the repository note before
the affected phase continues.

When current-year material is incomplete, ask the participant whether to wait or
use a clearly named prior-year rehearsal basis. A prior-year basis requires:

- `basis_status=prior_year_provisional`;
- `basis_year < competition_year`;
- `replacement_required=true`;
- `participant_decision.status=approved_provisional` with actor and timestamp.

It can support preparation and internal preview only. It cannot authorize final
submission.

## 4. Run deterministic gates

After updating the snapshot, run:

```bash
python <skill>/scripts/audit_ruleset.py \
  --snapshot state/rules_snapshot.json \
  --decision-log state/decision_log.json \
  --phase kickoff
```

Repeat with `--phase writing` before Stage 8 drafting and `--phase final` before
the Stage 9 panel. Warnings preserve visible uncertainty; any error blocks that
phase. The final phase requires current-year official rules, no unknown category,
no unresolved item that blocks final, no source conflict, and agreement between
the snapshot and decision log.

Write the derived status and latest audit result back to
`decision_log.compliance.ruleset`. Do not manually label the project
`current_confirmed` when the audit reports an error.

## 5. Reverification triggers

Re-open official sources when any of these occurs:

- the contest publishes an opening notice, problem package, standard document,
  AI rule, correction, or deadline change;
- the team changes contest or target year;
- Stage 8 begins;
- the final PDF or submission package is about to be approved.

The newest applicable official notice overrides both the snapshot and repository
baseline. Preserve the old decision in the event log rather than silently
rewriting history.
