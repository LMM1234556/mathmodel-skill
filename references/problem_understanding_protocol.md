# Problem understanding protocol

Use this protocol in Stage 2 before selecting models. Its purpose is not to
produce a polished restatement. It is to make every interpretation traceable to
the actual problem statement and to stop the workflow when a consequential
ambiguity remains unresolved.

## Required artifacts

Create under the user project:

- `state/problem_spec.md`, based on
  `<skill>/templates/shared/problem_spec.md`;
- `state/problem_source_manifest.json`, containing the source path, file SHA-256,
  extraction time, page count when observable, and attachment paths;
- `state/interpretation_review.md`, containing the independent second read and
  reconciliation record;
- `state/questions/<Qi>/question_contract.json`, initialized from
  `<skill>/templates/shared/question_contract.json` for every subproblem and
  completed according to `references/question_contract_protocol.md`.

The source hash identifies the problem version; it does not prove that the file
is official. Record the download page or official source separately when known.

## Pass A: source-anchored extraction

Read the original statement and attachments, not another team's paraphrase.
Split the statement into atomic requirements. An atomic row should contain one
action, definition, given fact, constraint, or deliverable.

For every row record:

- a stable ID such as `R01`;
- the shortest useful source anchor: page plus paragraph, table, equation, or
  attachment field;
- a short source excerpt;
- the team's interpretation;
- type: `ask`, `given`, `definition`, `constraint`, `data`, or `deliverable`;
- variables, units, scope, and quantifiers;
- downstream subproblem/model/output affected;
- confidence and any competing interpretation.

Never use an AI paraphrase as the source anchor. If PDF extraction is garbled,
inspect the rendered page and anchor to the page/table manually.

## Pass B: independent read

Perform a second read without copying Pass A's decomposition. Reconstruct:

1. what must be delivered for each question;
2. what is given versus what must be estimated or assumed;
3. all hard constraints, units, time ranges, populations, and exclusions;
4. dependencies between questions;
5. ambiguous words whose interpretation would change the model or answer.

Compare Pass B with the requirement table. Record omissions and conflicts in
`state/interpretation_review.md`; do not silently merge them.

The second read may be performed by another teammate, an independent agent
view, or the same agent in a fresh pass. Independence means it starts from the
source, not from the first interpretation.

## Reconciliation and adversarial checks

For each conflict, choose one of:

- resolved from an explicit source anchor;
- resolved by a documented domain convention with a citation;
- converted into a stated assumption and tested later;
- asked of the user/team because it changes the requested deliverable;
- unresolved and blocking.

Then run these checks:

- **Negation:** did words such as “不得”, “仅”, “至少”, “分别”, “同时”, or
  “不考虑” disappear in the interpretation?
- **Scope:** does a condition apply globally or only to one scenario/question?
- **Unit:** are time, currency, power/energy, percentage, and normalized values
  distinguished?
- **Object:** is the entity being predicted, ranked, optimized, or evaluated the
  same as in the source?
- **Deliverable:** does every requested table, recommendation, letter, policy,
  or file have an owner and evidence path?
- **Attachment:** is every used column mapped to its source meaning, and is every
  unused relevant field explained?
- **Counterexample:** state one plausible but wrong reading for each high-impact
  sentence and explain which source detail rules it out.

## Coverage gate

Stage 2 cannot pass unless:

- every imperative/request in the source maps to exactly one or more planned
  deliverables;
- every model objective and hard constraint points back to a requirement ID;
- every attachment field used by the model has a unit and meaning;
- the independent read has been reconciled;
- every Qi has its own data boundary and upstream dependency/independence record;
- the team has explicitly approved each Qi interpretation, deliverable, data
  boundary, and dependency before model selection;
- no unresolved ambiguity can materially change the model family, constraint
  set, evaluation metric, or final deliverable.

An unresolved consequential ambiguity is a high-severity issue and yields
`block`. Low-impact wording uncertainty may proceed only when recorded as an
assumption with a later validation action.
