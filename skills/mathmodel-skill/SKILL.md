---
name: mathmodel-skill
description: Plugin shim for the Huawei Cup mathmodel-skill workflow. Use when Codex invokes this plugin for the Huawei Cup China Postgraduate Mathematical Contest in Modeling, including per-question interpretation/data approval, candidate-model comparison, MATLAB figures, contest-paper writing, compliance, or final submission review. Do not use for CUMCM, MCM/ICM, Diangong Cup, generic data analysis, or non-competition paper review.
---

# mathmodel-skill plugin shim

This wrapper exists so Codex plugins can discover the skill from the official `./skills/` plugin layout.

Before doing any work, read `../../SKILL.md` and treat it as the primary workflow. Resolve `references/`, `competitions/`, `templates/`, `scripts/`, and `config/` relative to `../..`.

Do not duplicate workflow rules here; the root `SKILL.md` is the source of truth.
