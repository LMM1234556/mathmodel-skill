---
stage: 8
name: writing
duration_h: 12-30
inputs: ["decision_log.stages.0-7", "decision_log.task_type"]
outputs:
  - "stage.8.{section_word_counts, figures_per_subproblem, tables_per_subproblem, abstract_drafts, ai_use_log, compliance}"
  - "paper_workspace/*.md"
  - "paper_workspace/{claim_evidence_matrix.md,reverse_outline.md}"
  - "paper.tex"
loads_reference:
  - "references/rule_verification_protocol.md"
  - "competitions/huawei/current_rules.md"
  - "competitions/huawei/provisional_rules.json (only after participant approval)"
  - "competitions/huawei/winning_patterns.md"
  - "competitions/huawei/phrase_bank.md"
  - "competitions/huawei/empirical.json"
  - "references/paper_quality_protocol.md"
  - "references/visualization_protocol.md"
loads_template:
  - "templates/shared/rules_snapshot.json"
  - "competitions/huawei/paper_skeleton.md"
  - "competitions/huawei/abstract_template.md"
  - "templates/latex/huawei/ (internal review only)"
feedback: ["L1", "L2_at_end"]
next: stage_09_review
---

# Stage 8 — Assemble the paper

Turn the validated Stage 0–7 outputs into one coherent paper. Do not invent new results while writing. If the paper exposes a modeling contradiction, record it and trigger a targeted L2 backtrack.

Before drafting prose, read `references/paper_quality_protocol.md` and build the
claim-evidence matrix. Before inserting figures, read
`references/visualization_protocol.md` and verify the figure registry.

## 1. Lock the current rules first

1. Read `references/rule_verification_protocol.md` and the existing `state/rules_snapshot.json`.
2. Re-open the linked official rules and confirm they are still current for the contest year; add newly published notices and files as distinct source IDs.
3. Update every affected category, unresolved item, and conflict in the snapshot, then synchronize its summary to `decision_log.compliance.ruleset`.
4. Run `audit_ruleset.py --phase writing --snapshot state/rules_snapshot.json --decision-log state/decision_log.json`. Any error blocks drafting; warnings remain visible in the paper plan.
5. If the repository baseline conflicts with the official source, follow the official source and flag the repository mismatch.

Do not treat empirical distributions, `winning_patterns.md`, or rubric scores as official rules. They are writing aids only.

## 2. Load only the Huawei Cup pack

Read from `competitions/huawei/`:

- `paper_skeleton.md`
- `abstract_template.md`
- `winning_patterns.md`
- `phrase_bank.md`
- `empirical.json`

`empirical.json` records `n=0`. Do not generate empirical percentiles, award probabilities, preferred figure counts, or paper-length targets from it.

## 3. Write into a stable workspace contract

Create these files under `<cwd>/paper_workspace/`:

| File | Content |
|---|---|
| `01_abstract.md` | Abstract or Summary Sheet, written last |
| `02_problem_restate.md` | Problem context and restatement |
| `03_analysis.md` | Decomposition and technical route |
| `04_assumptions.md` | Supported assumptions |
| `05_notation.md` | Unique symbols and units |
| `06_models.md` | Models, algorithms, results, and interpretation |
| `07_sensitivity.md` | Robustness and failure regions |
| `08_evaluation.md` | Strengths, limitations, and transfer conditions |
| `09_references.md` | Verified references, including AI tools when required |
| `10_appendix.md` | Essential code and supporting-material manifest |
| `claim_evidence_matrix.md` | Internal claim → source/result/validation traceability; not rendered by default |
| `reverse_outline.md` | Internal paragraph jobs and Claim/Requirement IDs; not rendered by default |

`01_abstract.md` contains abstract content without a top-level heading because the template supplies its wrapper. Files `02`–`10` each own one clear top-level Markdown heading.

First create result cards and `claim_evidence_matrix.md`; then write the body,
references, and appendices. Write the abstract/summary last from locked Claim
IDs. Every number and comparative word in the abstract must point to a result
already present in the body.

## 4. Keep one evidence chain

For every subproblem, preserve this chain:

`question → assumptions → formulation → solver → result → validation → interpretation`

Before moving on, verify:

- symbols match Stage 4;
- chosen models match Stage 3;
- reported values match stored results rather than regenerated prose;
- figures have readable labels, units, captions, and source paths;
- every quantitative figure used by the paper has `renderer=MATLAB`, a `.m` generator, a chart-type rationale, a `figure_registry.json` entry, and final-PDF-size inspection;
- claims and citations are verifiable;
- limitations name a concrete failure mode and mitigation.

After the first complete draft, build `reverse_outline.md` with one line per
paragraph: paragraph location, its job, and Requirement/Claim IDs. Remove or
repair paragraphs that have no identifiable job or evidence relationship.

## 5. Apply the Huawei Cup document contract

The verified invitation fixes the contest schedule, not the final paper layout. Until the target-year format and AI files are obtained, the verified 2025 rules may guide provisional content organization, anonymity, citations, font/page-number rehearsal, and AI annotations. Record `prior_year_provisional`; do not copy 2025 dates, filename digits, attachment limits, logos, or templates into a current-year submission. The repository LaTeX remains internal-review only.

Problem-specific deliverables follow the current official prompt and standard document, never another contest's conventions.

## 6. Maintain the AI-use ledger

Because this skill itself uses an AI agent, keep `decision_log.compliance.ai_usage` current. For each material use, record:

- tool, provider, and model/version;
- use date, stage, and purpose;
- key prompt and key response, or paths to those records;
- what was adopted;
- human changes and verification performed.

Do not invent a Huawei Cup disclosure format. Compare the ledger with the target-year official AI notice and record the manual check. Never place API keys, tokens, private data, or credentials in the ledger.

For a Huawei Cup rehearsal using the 2025 provisional baseline, also check that
AI-assisted data analysis is annotated next to the result, AI-assisted programs
carry a header comment with tool/version/provider/release date, model and formula
sources are independently verified, and the team has recorded any problem-required
prompt/output processing details. These are provisional checks, not proof of 2026
compliance.

## 7. Render without detached sections

From the user project root, call the installed script explicitly:

```bash
python <skill>/scripts/render_paper.py \
  --competition huawei \
  --workspace paper_workspace/ \
  --output-dir paper_output/
```

The renderer creates an internal review PDF only. A generated PDF with missing sections is a failure even if LaTeX exits successfully; it is never the formal submission unless the current official standard document has been integrated and separately verified.

## 8. Score using the active overlay

Use the five Stage 8 dimensions from `competitions/huawei/rubric_overlay.json`. They are internal quality checks, not official judging weights.

## Exit conditions

- all required sections and problem-specific deliverables exist;
- every source requirement maps to a paper section or explicit deliverable;
- `claim_evidence_matrix.md` and `reverse_outline.md` exist and have no unresolved high-severity gap;
- every inserted figure is registered, reproducible, truthful to its source data, and readable at final size;
- the paper agrees with the Stage 0–7 decision log;
- the rules snapshot was rechecked and the writing-phase audit has no error;
- AI uses and citations are logged;
- the active competition's renderer includes every section;
- L1 passes and the final L2 consistency check has no unresolved high-severity conflict.

Then enter `stage_09_review.md`.
