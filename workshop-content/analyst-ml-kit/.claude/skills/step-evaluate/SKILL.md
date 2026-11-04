---
name: step-evaluate
description: Step 7 of /run-steps. Scores the model and today's rule on the same test snapshots, says whether the model beats today's way by the margin the analyst asked for, and flags results too good to trust. Writes scripts/07_evaluate.py on the first run. Use when /run-steps reaches evaluation, or for /step-evaluate.
---

# Step 7 · Judge it

**Start the reply with these two lines:**

```
Skill: /step-evaluate · Step 7 · Judge it · Script: projects/<name>/scripts/07_evaluate.py
Purpose: Does the new list beat today's way, on a stretch it has never seen?
```

Follow `.claude/skills/run-steps/contract.md` and, on the first run, `checks.md`.

Inputs: the spec, `runs/02_panel.csv`, `runs/05_baseline.json`, `runs/06_model.joblib`, `runs/06_columns.json` (all from `--out`). Outputs: `runs/07_evaluate.json`, `runs/07_evaluate.md`.

## Method

- Build both sides' matrices with `model_matrix`, then `align` them to `06_columns.json`.
- The model's chance for each row; precision@K and recall@K on the training side and the test side; events in each test snapshot's top K.
- Today's rule: the numbers from `05_baseline.json`.
- **Beats by:** (model test precision − rule test precision) × k, as "more real `<event>`s per list". **Enough:** beats by ≥ `metric.extra_hits`.
- **Warnings** (each a plain sentence in `flags`):
  - doesn't beat today's way: model test precision ≤ the rule's;
  - memorised or leaking: training precision − test precision > `defaults.max_gap`;
  - too good: training precision > max(`defaults.too_good`, 2 × the rule's training precision).
- `internal.test_auc`: `auc` on the test side. For the checks only; never in the `.md`.

The `.md`: a table with three rows (today's way, the new list, the difference) and columns "real `<event>`s per list of `<k>`" (precision × k) and "share of all `<event>`s found" (recall), on the test side; then the per-snapshot hits; then one line: "The new list finds `<beats by>` more real `<event>`s per list than today's way. You asked for at least `<extra_hits>`." Then the warnings, if any, first.

## Report

If there's a "too good" or "memorised or leaking" warning, say it **first**, and say the next step checks for a leak.

Then stop and ask: **"The new list finds `<beats by>` more per list than today's way; you asked for `<extra_hits>`. Is that worth switching for?"** Then continue to the leakage step whatever the answer: the analyst's go or no-go comes at the end.
