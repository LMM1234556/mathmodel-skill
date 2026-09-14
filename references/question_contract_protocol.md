# Question contract protocol

Use this protocol across Stages 2, 3, and 5. Stage 2 initializes each contract
after decomposing the statement, Stage 3 completes the model/validation/initial
figure plan and obtains pre-execution approval, and Stage 5 records actual inputs
and final decisions. It prevents one subproblem from silently inheriting another
subproblem's data, interpretation, model, or figures.

The workflow remains a ten-stage contest workflow. A question contract is the
inner control loop used by Stages 2, 3, and 5 for every `Qi`.

## Required artifact

Create one contract per question under the user's project:

```text
state/questions/Q1/question_contract.json
state/questions/Q2/question_contract.json
...
```

Copy `<skill>/templates/shared/question_contract.json`; the agent maintains the
JSON and presents a human-readable summary. Never ask the team to edit JSON.

The contract records five different kinds of information. Do not merge them:

1. **Source fact** — anchored to the original statement or attachment.
2. **Team interpretation** — the agreed reading of that source.
3. **Data authorization** — the exact files, sheets/tables, fields, row scope,
   filters, exclusions, units, preprocessing, and upstream result IDs allowed for this Qi.
4. **Model decision** — comparable candidates, baseline, validation plan, and
   the team's approved pre-execution recommendation.
5. **Figure decision** — the evidence question and tentative chart candidates
   before execution; final chart types are approved only after results exist.

## Default-deny data isolation

Data access is denied by default. A Qi may use only:

- raw datasets declared in `data_contract.datasets`;
- derived results declared in `dependencies.upstream_results`;
- configuration values anchored to a Requirement ID or an approved assumption.

Declaring a file is not enough. Each dataset entry must record its sheet/table,
fields and meanings, units, row scope, filters, preprocessing, exclusions, and
purpose. Use `no_data_reason` only when the Qi genuinely uses no dataset.

Use this object shape for every declared dataset; empty lists explicitly mean
“none”, not “not checked”:

```json
{
  "path": "data/attachment1.xlsx",
  "sha256": "64-character-lowercase-sha256",
  "sheet_or_table": "Sheet1",
  "fields": [
    {"name": "time", "meaning": "observation time", "unit": "h", "role": "feature"}
  ],
  "row_scope": "rows 2:1001",
  "filters": [],
  "preprocessing": ["sort by time ascending"],
  "exclusions": ["rows with missing time"],
  "purpose": "estimate the Q1 response curve"
}
```

`observed_accesses` is populated from the actual run rather than reconstructed
from memory. Each entry records file/hash, sheet or table, fields, row scope,
filters, exclusions, and preprocessing. At final audit every observed access must match one
declared dataset and stay inside its approved fields and transformations. A new
file, field, filter, time range, join, or upstream result changes the contract
and invalidates approval.

Cross-question reuse is explicit. An upstream entry contains the producing
question, stable result ID, rationale, interface meaning, and unit. If there is
no upstream dependency, write an independence rationale. “It may help” or “the
statement does not forbid it” is not a valid dependency.

After execution, write the result IDs actually consumed to
`execution.observed_upstream_result_ids`. The final audit rejects an undeclared
ID and also rejects a declared dependency that was never recorded at runtime.

## Model shortlist and decision

Before formal implementation, provide a small set of genuinely comparable
candidates. Prefer an effective baseline, a mainstream candidate, and an
advanced candidate when all three can solve the same task. Do not pad the list
with incompatible models. If only one candidate remains after a documented
search, fill `single_candidate_justification`.

Each retained candidate records:

- mathematical family and role (`baseline`, `mainstream`, or `advanced`);
- fit to the Qi objective, constraints, and data;
- assumptions and data requirements;
- implementation route and time risk;
- validation method and failure conditions;
- verified references or theory support when the selection relies on them.

“Optimal model” means the most suitable model under the declared objective,
constraints, validation evidence, interpretability needs, and contest time. Do
not claim global optimality without a proof that applies to the actual problem.

## Figure planning

Before execution, agree on the evidence questions and plausible chart types.
Do not lock the final chart solely from the problem wording. After results are
available, choose the final MATLAB chart using the observed data structure and
`references/visualization_protocol.md`, then obtain `final_figures` approval.

Every final chart must bind to result IDs and the MATLAB figure registry.

## Human approval gates

### Gate Q-P — pre-execution approval

Present one readable execution card containing:

1. source-anchored interpretation and deliverables;
2. upstream dependencies or independence rationale;
3. exact data contract and forbidden inputs;
4. model candidates, baseline, recommendation, and rejected alternatives;
5. validation plan and failure conditions;
6. evidence questions and tentative chart types.

Ask the team to approve or request changes. Until
`approvals.pre_execution.status == "approved"`:

- do not write or run the formal solver;
- do not create official results;
- do not write paper conclusions for the Qi.

Every approval also stores `contract_digest`, generated by
`audit_question_contracts.py --digest-for <gate> --question <Qi>`. The digest
binds approval to the relevant interpretation, data, dependency, model,
validation, result, or figure fields. If one of those fields changes, the audit
rejects the old approval even when its status still says `approved`.

A tiny feasibility probe may run in Stage 3 only after the team approves the
data slice used by that probe; label it non-final and do not persist it as a
paper result.

### Gate Q-M — final model approval

After candidates have been evaluated under the same task, data contract,
constraints, and validation plan, show the comparison and recommendation. The
team chooses the paper's final model. Until `approvals.final_model` is approved,
do not mark the Qi complete or write a definitive model claim.

### Gate Q-F — final figure approval

After results exist, show the proposed MATLAB figures, alternatives, units,
uncertainty, and the claim supported by each figure. Until
`approvals.final_figures` is approved, figures remain drafts.

## Invalidation

Set `invalidation.status = "invalidated"` when any approved interpretation,
dataset, field, row scope, preprocessing step, dependency, model objective,
hard constraint, validation plan, or final result changes. Record the reason
and affected downstream questions.

Invalidation resets the affected approval to `pending`, marks downstream
results stale, and blocks paper claims that depend on those results. Never edit
an approved contract silently.

## Deterministic audit

Run the auditor automatically; the user should not need to type commands:

```bash
python <skill>/scripts/audit_question_contracts.py --workspace <cwd> --phase plan
python <skill>/scripts/audit_question_contracts.py --workspace <cwd> --phase execute --question Q1
python <skill>/scripts/audit_question_contracts.py --workspace <cwd> --phase final
python <skill>/scripts/audit_question_contracts.py --workspace <cwd> --question Q1 --digest-for pre_execution
```

- `plan` checks completeness, question IDs, dependencies, data declarations,
  model shortlist, validation plan, and preliminary figure plan.
- `execute` additionally requires pre-execution approval and verifies declared
  data files and hashes.
- `final` additionally checks observed inputs, validation, stable result IDs,
  final-model approval, and final-figure approval.

Any audit error is a high-severity issue and yields `block`. Warnings require a
recorded disposition but do not by themselves authorize execution.
