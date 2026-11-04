---
name: step-train
description: Step 6 of /run-steps. Fits the kit's one model, a logistic regression, on the training side only, and reports what it learned in plain words. Writes scripts/06_train.py on the first run, then runs the shuffled-label check. Use when /run-steps reaches training, or for /step-train.
---

# Step 6 · Train

**Start the reply with these two lines:**

```
Skill: /step-train · Step 6 · Train · Script: projects/<name>/scripts/06_train.py
Purpose: Learn, from the past, which signs came before `<event>`.
```

Follow `.claude/skills/run-steps/contract.md` and, on the first run, `checks.md`.

Inputs: the spec, `runs/02_panel.csv`. Outputs: `runs/06_model.joblib`, `runs/06_columns.json`, `runs/06_train.json`, `runs/06_train.md`.

## Method

- **Rows:** the training side only (same rule as step 4). **Refuse** if any row's snapshot is on or after `split.test_from − split.gap_periods`.
- **Columns:** `features.keep` if not empty, else every feature column (never `entity_id`, snapshot, `label`, `event_period`). Built with `model_matrix`; the column list saved to `06_columns.json`.
- **Model:** `logistic(spec)` from `common.py`: empty cells filled with the training median, every column scaled, logistic regression with `defaults.logistic`. This is the only model.
- **`--shuffle-seed s`** (for the trust check only): before fitting, shuffle the training labels with a generator seeded with `s`. Everything else is the same.
- `.json`: rows, distinct events, model columns, events per model column, the 12 largest weights (on scaled columns) with their sign, the intercept.

The `.md`, plain words: what it learned from (`<rows>`, `<event>`s, columns), then the largest weights as sentences: "higher `<column>`, more likely to `<event>`" or "less likely". One caution line: weights show what went together, not what causes what.

**Built-in check:** the training side has at least one event and one non-event.

## After the first run

Run the shuffled-label check in `checks.md` §2.

## Report

Quote the `.md`. Don't stop.
