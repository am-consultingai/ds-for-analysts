---
name: run-steps
description: Runs the steps in order (audit, panel, size, split, today's rule, train, evaluate, leakage, score), writing and checking each step's script on its first run and reusing it after. Stops only at business checkpoints and failed checks. Use for /run-steps, after /frame, or to re-run after a change to the spec.
---

# The steps

**Start the reply with these two lines:**

```
Skill: /run-steps · The steps, in order
Purpose: Build, check and judge the list, stopping only where a business answer is needed.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

Read first: `contract.md` (rules for every script) and `checks.md` (the trust checks), both in this folder.

## The order

| # | Skill | Script | Stops to ask the analyst when |
|---|---|---|---|
| 1 | `step-audit` | `01_audit.py` | the time column can't be used |
| 2 | `step-panel` | `02_panel.py` | a column restates the event (confirm); `k: auto` (list length) |
| 3 | `size` | `03_size.py` | there isn't enough history |
| 4 | `step-split` | `04_split.py` | never |
| 5 | `step-baseline` | `05_baseline.py` | today's rule flags nothing |
| 6 | `step-train` | `06_train.py` | never (then the shuffled-label check) |
| 7 | `step-evaluate` | `07_evaluate.py` | always: does it beat today's way by enough? |
| 8 | `step-leakage` | `08_leakage.py` | a column is suspect, or a date column needs a "when is it filled in?" (then the planted-leak check) |
| 9 | `step-score` | `09_score.py` | always: would `<actor>` act on this list? Go or no-go |

For each step, read its `SKILL.md` and follow it.

- **First run of a step** (no script yet): write the script, run it, run it twice, run the independent calculation, record it as verified. See `contract.md`.
- **Later runs:** check the fingerprints, run, quote.
- **A failed built-in check or trust check stops the run.** Explain in plain words and offer only business choices.

## Re-running after a change

A change to the spec means re-running from the first step that reads it, and every step after:

| Changed | Re-run from |
|---|---|
| `data_folder`, `tables`, `entity_id`, `time_column`, `period` | `/profile-data`, then step 1 |
| `label`, `snapshot_every`, `eligibility`, `columns`, `extra_features`, feature defaults | step 2 |
| `metric.k`, `metric.extra_hits`, sizing defaults | step 3 |
| `baseline` | step 5 |
| `defaults.logistic`, `seed` | step 6 |
| `max_gap`, `too_good` | step 7 |
| `suspect` | step 8 |

## The end

After step 9, ask the go or no-go question in step 9's skill, log the answer in `decisions.md` (`analyst`), then run `/report`.
