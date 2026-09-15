# Huawei Cup competition pack

This pack targets the “华为杯”中国研究生数学建模竞赛, not the 电工杯.

Status on 2026-09-15:

- the official invitation and schedule are verified in `current_rules.md`;
- the 2026 paper standard, AI rules, and problems are not yet available in the
  checked official notice list;
- the official 2025 paper-format and AI-use rules are recorded as a provisional
  rehearsal baseline only; they never make a 2026 artifact submission-ready;
- format verification is split into official template/cover,
  typography/paragraphs, pagination/page limits, and appendix/supporting
  materials; the checked 2025 documents state an abstract limit but no total
  paper page limit;
- `provisional_rules.json` is the machine-readable fallback profile and keeps
  `submission_authorized=false` until replaced by the current-year documents;
- `empirical.json` has `n=0`; writing and review material is maintainer guidance,
  not an award predictor;
- the LaTeX file is an internal review template only. Final submission must use
  the official standard document released for the contest.

Update the pack after the official files are published and preserve their URLs,
dates, and hashes. Do not copy requirements from CUMCM or Diangong merely because
all three use Chinese papers.

For a new 2026 workspace, `init_project.py --competition huawei --year 2026`
must leave the problem ID, subproblem count, rule basis, and official-source list
empty. Those fields are populated only after the current problem and official
documents are actually opened; the initializer never enables the 2025 fallback.
