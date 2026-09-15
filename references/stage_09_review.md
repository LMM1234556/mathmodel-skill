---
stage: 9
name: review
duration_h: 2-6
inputs: ["paper.tex", "paper.pdf", "decision_log_full"]
outputs:
  - "stage.9.{anti_patterns_check, compliance_checks, panel_scores, weakest_section, redo_log, red_team_record, final_pdf_path, submission_ready}"
loads_reference:
  - "references/rule_verification_protocol.md"
  - "competitions/huawei/current_rules.md"
  - "competitions/huawei/provisional_rules.json (rehearsal only)"
  - "competitions/huawei/anti_patterns.md"
  - "competitions/huawei/rubric_overlay.json"
  - "references/feedback_layer3_panel.md"
  - "references/problem_understanding_protocol.md"
  - "references/paper_quality_protocol.md"
  - "references/visualization_protocol.md"
loads_template: ["target-year official standard document", "templates/shared/format_audit.md", "templates/latex/huawei/ (internal review only)"]
feedback: ["L1", "L3_panel", "red_team_in_championship"]
next: SUBMIT
---

# Stage 9 — Submission review

The final gate is compliance first, content consistency second, presentation third. A polished paper that violates the current rules is not submission-ready.

## 1. Re-open the official rules

Read `references/rule_verification_protocol.md` and `competitions/huawei/current_rules.md`, reopen the official links, and compare the final artifacts against the target year. Update `state/rules_snapshot.json`, synchronize the decision-log summary, and run `audit_ruleset.py --phase final --snapshot state/rules_snapshot.json --decision-log state/decision_log.json`. Any error forces `rules_snapshot_audit_passed=false` and `submission_ready=false` before the panel begins.

Minimum Huawei Cup checks:

- when the 2026 format or AI files are unavailable, the 2025 official rules may
  be used for a rehearsal audit only; record `basis_status=prior_year_provisional`
  and `replacement_required=true`;
- the rehearsal may check content order, pagination, fonts, anonymity, citations,
  AI annotations and code comments, but 2025 dates, filename digits, attachment
  limit, logos and template are not 2026 requirements;
- use the 2026 standard document downloaded from the official contest system,
  not `templates/latex/huawei/main.tex`;
- verify the problem ZIP and final PDF with the official MD5 tool, and preserve
  which exact PDF was locked;
- obey the separate MD5 submission and PDF upload windows in
  `competitions/huawei/current_rules.md`;
- verify team number/anonymity, page/layout, file/support-material, citation,
  similarity, and AI-use requirements from the 2026 opening notice and files;
- do not import page limits, covers, or AI declarations from CUMCM or Diangong;
- if the 2026 paper standard or AI rules have not been obtained and recorded,
  the rehearsal can finish but `rules_verified=false`, `submission_ready=false`,
  and the submission branch yields `block`.

Any unresolved rule violation sets `submission_ready=false` and yields `block`.

Then open `paper_workspace/format_audit.md` and compare the actual final PDF and
supporting package row by row. A row without an official source/anchor, observed
value, and pass result is incomplete. Check fonts, heading and paragraph styles,
page size/margins, headers/page numbers, abstract and total-page limits, cover,
anonymity, appendix placement, PDF name/size/compression, and every supporting
material requirement. If the official documents do not state a total-paper limit,
record `not_stated` with the reviewed sources; never substitute another contest's
limit. Any `unknown`, `fail`, or `blocked` row keeps `submission_ready=false`.

## 2. Run the active anti-pattern checklist

Read `competitions/huawei/anti_patterns.md` and derive the count from the active file rather than copying a remembered or example count.

These are maintainer heuristics, not official scoring weights. Fix high-severity hits; record accepted medium-risk items with an explicit rationale.

## 3. Verify the evidence chain

Cross-check the final paper against `decision_log.json` and the saved artifacts:

- no abandoned model remains in the abstract or conclusion;
- no symbol changes meaning between sections;
- all headline values reproduce from stored results;
- every figure/table path resolves and its caption matches the content;
- every external claim has a verified source;
- AI-generated citations have been opened and checked manually.

Run a reverse trace from `state/problem_spec.md`: every source requirement must
land in a final answer, table, figure, recommendation, or problem-specific
deliverable. Then trace every abstract Claim ID back to a stored result and
validation record. A polished paragraph does not pass when its evidence chain is
missing.

## 4. Review presentation

- labels, units, legends, equations, and captions remain readable at final PDF size;
- fonts and colors are consistent and accessible;
- tables use consistent units and precision;
- there are no unresolved `??` references, missing glyphs, clipped figures, or large overfull boxes;
- all required sections are present in the compiled PDF, not merely on disk as detached `.tex` files.

Compare every inserted figure with `figures/figure_registry.json` and its
`.figure.json` sidecar. Re-open the underlying result file for headline figures.
Inspect at final physical size and record failures; do not approve charts from a
notebook thumbnail or source code alone.
For every quantitative figure also verify `renderer=MATLAB`, a resolvable `.m`
generator, and a credible `chart_type_rationale`; a Python/notebook screenshot
or an unjustified chart type is a high-severity issue.

## 5. Run the five-view panel

Use `references/feedback_layer3_panel.md` as the single source for panel roles and aggregation. Prefer independent parallel views when the harness supports them; otherwise run the views separately to reduce cross-contamination.

Map every high-severity concern back to one source section and apply a targeted patch. Re-run only the affected checks and panel views. Do not ask the panel to predict an award; use `ready`, `refine`, or `block` against the repository rubric.

## 6. Verify Huawei Cup AI-use disclosure

Keep the internal AI-use ledger complete, then map it to the target-year official AI notice. Do not reuse another contest's generated report or invent a mandatory file. If only the 2025 provisional baseline is available, complete a rehearsal check but keep `ai_disclosure_passed=false` and `submission_ready=false` for the target-year submission.

## 7. Compile and inspect the final PDF

Use `<skill>/scripts/render_paper.py` or the selected LaTeX engine. Compilation succeeds only when the PDF exists, includes all intended sections, and has no unresolved high-severity warnings. Visually inspect the first page, dense equations, wide tables, figure-heavy pages, references, appendices, and the AI report.

## 8. Persist the final gate

Write actual runtime-derived counts and paths. The schema is:

```json
{
  "anti_patterns_check": {
    "total": null,
    "passed": null,
    "fixed": null,
    "deferred": null
  },
  "compliance_checks": {
    "rules_verified": null,
    "rules_snapshot_audit_passed": null,
    "anonymity_passed": null,
    "page_limit_passed": null,
    "ai_disclosure_passed": null
  },
  "evidence_traceability_passed": null,
  "figure_audit_passed": null,
  "final_pdf_path": "paper_output/paper.pdf",
  "submission_ready": null
}
```

The `null` values above are schema placeholders only. Replace every one with an observed count or verified boolean before persisting Stage 9; never copy a sample result into the final gate.

## Exit conditions

- current official rules verified and the final rules-snapshot audit passed with no unresolved violation;
- anti-pattern and consistency checks completed;
- requirement-to-deliverable and claim-to-evidence reverse traces passed;
- every paper figure passed source, unit, encoding, caption, and final-size review;
- all high-severity panel findings resolved;
- PDF compiled and visually inspected, and every row of `format_audit.md` has an official basis, observed value, evidence, and pass result;
- AI disclosure and supporting materials complete when required;
- `decision_log.stages.9.submission_ready == true`.

Only then hand the final submission package back to the team.
