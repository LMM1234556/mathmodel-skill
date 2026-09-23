# Non-official source material audit

This file records how non-official preparation material influenced the workflow.
It is not a contest rule source and does not reproduce third-party prompt text.
Official notices, attachments, the selected problem and official forum answers
always take precedence.

## 2026 AI prompt collection

Reviewed material: `2026华为杯数模研赛—AI提示词合集.docx` supplied by the user.

Adopted as workflow improvements:

- make the cross-question task, data and result dependency chain explicit;
- compare multiple feasible model routes before the team approves one;
- reject mathematical structures that the actual task does not require;
- require every exploratory analysis or chart to state the decision it informs;
- explain why observed results arise while separating association from causation;
- audit novelty claims against a baseline, implementation and comparison evidence;
- review the final paper by prioritized, executable findings.

Already covered by the existing workflow and therefore not duplicated:

- per-question interpretation, data contracts and human approval;
- baseline/candidate comparison and final-model approval;
- reproducible code, result artifacts, robustness and claim traceability;
- MATLAB-only final quantitative figures and final PDF review.

Rejected or narrowed:

- a mandatory Python implementation path: computation may use appropriate tools,
  while final quantitative figures remain MATLAB-generated;
- text described as directly ready for submission: generated prose is only a
  draft until evidence, consistency, team understanding and official AI rules pass;
- “avoid AI traces” as an objective: the workflow preserves required disclosure
  and rejects concealment;
- fixed numbers of candidate models or analyses: the count follows the problem,
  available data, meaningful alternatives and time budget;
- presentation value as a substitute for correctness: paper clarity matters only
  after task fit, data sufficiency, feasibility and validation pass.

## Evidence status

These conclusions are a maintainer assessment of a user-provided third-party
document. They are not official scoring criteria, award predictors or empirical
findings. No contest score weights were inferred from the document.
