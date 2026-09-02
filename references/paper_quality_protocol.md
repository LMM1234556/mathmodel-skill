# Paper quality protocol

Use this protocol in Stage 8 after the numerical/modeling artifacts are stable.
The objective is a paper whose important sentences can be checked, not prose
that merely resembles an award paper.

## Build the evidence map before prose

Create `paper_workspace/claim_evidence_matrix.md`:

| Claim ID | Claim | Requirement IDs | Evidence path | Figure/table/equation | Validation | Scope/limitation | Target section |
|---|---|---|---|---|---|---|---|

Include every abstract result, recommendation, comparison, “better than”,
“stable”, “optimal”, “significant”, and causal-sounding explanation. A claim
without evidence is either removed, weakened to match the evidence, or sent
back to the relevant modeling stage.

## Write result cards

For each subproblem, prepare a compact card before drafting paragraphs:

- question and requirement IDs;
- model actually implemented, not the originally planned name;
- main quantitative answer with units and scope;
- baseline/comparator under the same data and constraints;
- validation evidence and failure boundary;
- one useful figure/table and its registry ID;
- what the result does not establish.

Write sections from these cards. Do not create new numeric results, citations,
or model mechanisms during prose generation.

## Paragraph and section discipline

Each technical paragraph should have a clear job: define, justify, formulate,
report, interpret, compare, or limit. A strong results paragraph usually follows
`claim → evidence → interpretation → boundary`; it need not use those labels.

- Put the answer before implementation trivia.
- Separate observed facts, model outputs, assumptions, and interpretation.
- Explain why a modeling choice was necessary and what would change under a
  credible alternative.
- Use precise model names. Do not add “improved”, “adaptive”, “hybrid”, or
  “intelligent” unless the implemented mechanism and comparison justify it.
- Replace vague praise (“效果良好”, “具有实际意义”) with a metric, condition,
  decision implication, or a narrower statement.
- Cite sources for external facts and methods; do not cite the model's own
  computed results as external facts.
- Keep notation and scenario names identical to the decision log and code.

## Abstract written from locked evidence

Write the abstract/summary last. For each subproblem state the actual method and
the most decision-relevant verified result. Every number and comparative word
must map to a Claim ID and body location. Include one material validation signal
and one honest boundary when space permits. Do not promise a method or result
that appears nowhere in the body.

## Three review passes

1. **Technical pass:** equations, units, definitions, assumptions, result files,
   validation, and source claims are correct.
2. **Reader pass:** a judge can recover the problem, route, answer, evidence, and
   limitation without reverse-engineering the code.
3. **Line pass:** remove repetition, inflated novelty, dangling references,
   vague pronouns, inconsistent terms, and sentences whose subject or logical
   relation is unclear.

After editing, create `paper_workspace/reverse_outline.md`: one line per
paragraph stating its job and Claim/Requirement IDs. Adjacent paragraphs with
the same job should be merged or differentiated; paragraphs with no job should
be removed.

## Reverse traceability gate

Before Stage 9:

- every source requirement maps to a section and final deliverable;
- every headline claim maps to a saved result and validation record;
- every figure/table maps to a claim and generating artifact;
- the abstract maps only to locked body evidence;
- limitations identify affected conclusions and conditions, not generic
  self-criticism;
- no unresolved high-severity contradiction remains between problem spec,
  decision log, code, results, figures, and prose.

If a writing review uncovers a modeling error, backtrack to the source stage.
Editing the sentence is not an acceptable fix when the evidence itself is wrong.
