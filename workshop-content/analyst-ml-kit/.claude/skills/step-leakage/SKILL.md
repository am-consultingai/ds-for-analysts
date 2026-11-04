---
name: step-leakage
description: Step 8 of /run-steps. Looks for columns that already know the answer, and asks the analyst when the suspect values and the date columns were filled in. Writes scripts/08_leakage.py on the first run, then runs the planted-leak check. Use when /run-steps reaches the leakage check, or for /step-leakage.
---

# Step 8 · Look for a leak

**Start the reply with these two lines:**

```
Skill: /step-leakage · Step 8 · Look for a leak · Script: projects/<name>/scripts/08_leakage.py
Purpose: Make sure no column already knows the answer.
```

Follow `.claude/skills/run-steps/contract.md` and, on the first run, `checks.md`.

Inputs: the spec, `runs/02_panel.csv`, `runs/05_baseline.json`. Outputs: `runs/08_leakage.json`, `runs/08_leakage.md`.

## Method

- **Rows:** the training side only.
- **Each model column alone** (after `model_matrix`, using every feature column, not only `features.keep`): empty cells filled with its training median; skip columns with one value; precision@K ranking high first and low first; keep the higher.
- **Suspect:** at or above max(`defaults.suspect`, 2 × today's rule's training precision from `05_baseline.json`).
- **Date columns:** every `days_since_<c>` column, listed whatever its score: dates in the entities file are often filled in when the data was pulled, so they may see the future.
- Each entry names the source column and file (the way `02_panel.json` records it).
- **`--plant-leak`** (for the trust check only): before scoring, add `_planted_leak`, a copy of `label` with `defaults.planted_flip` of the training rows flipped, chosen with a generator seeded from `seed`.

The `.md`: today's rule's training precision, then the 10 strongest single columns (column, made from, share of each list it finds on its own, suspect yes or no), then the date columns.

## After the first run

Run the planted-leak check in `checks.md` §3.

## Ask the analyst (business questions)

For each suspect column and each date column, one at a time:

**"When is `<source column>` filled in? Is it known at the start of each `<period>`, or only later, after things happen?"**

- Known in time: keep it; log as `analyst`.
- Filled in later, or not sure: add the source column to `columns.excluded`, log as `analyst`, and re-run from step 2 (see the re-run table in `/run-steps`).

If there are no suspects and no date columns, say so and don't stop.
