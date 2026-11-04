---
name: ml-pipeline
description: Runs the whole ML pipeline from ml_spec.yaml with scripts/pipeline.py: check the data, feature engineering, split, today's rule, train, evaluate, leakage check, score. Step by step with a stop at each decision, or all at once with auto, and can compare the numbers with an earlier run. Use for /ml-pipeline.
---

# The ML pipeline, end to end

**Start the reply with these two lines:**

```
Skill: /ml-pipeline · The whole ML pipeline
Purpose: Run every step of the ML pipeline from ml_spec.yaml, the same way every time.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

## Choose the mode

- **Step by step** (the default): run one step at a time, report it the way that step's skill does, ask its question, and wait for the answer before the next step.
- **All at once**: when the command is followed by `auto`, or when asked to run everything without stopping.

## Step by step

Steps 1 and 2 have no script. Read the question, decision, target, eligibility and measures, and today's rule, from `ml_spec.yaml`. Show them, and ask the step 1 question: **"Will anyone act on this answer?"**

Then run the steps in this order, each with `--from` and `--to` set to the same step:

```
.venv/bin/python scripts/pipeline.py --spec ml_spec.yaml --out runs/latest --from audit --to audit
```

| Order | `--from` / `--to` | Pipeline step | Ask |
|---|---|---|---|
| 1 | `audit` | 3 · Check the data | Go or no-go? |
| 2 | `build_panel` | 4 · Feature engineering | Could I have known this before the trial started? |
| 3 | `split` | 5 · Split | Do both sides look sensible? |
| 4 | `baseline` | 2 · Today's rule, scored | Is this really how trials are picked today? |
| 5 | `train` | 6 · Train | Enough buyers per feature? Do the weights and groups make business sense? |
| 6 | `evaluate` | 7 · Evaluate | Which model do we use? (Write `final_model` after a yes.) |
| 7 | `leakage` | 7 · Leakage check | Any feature we couldn't have known before the trial? |
| 8 | `score` | 8 · Score | Would you give CSMs this list? |

Today's rule is step 2 of the pipeline, but it is scored after the split, because it is measured on the same test months as the models.

## All at once

If `final_model` is empty, the run scores with the model `/evaluate` suggests and says so. Report that, and that the analyst should confirm the choice.

If `runs/latest/00_pipeline.json` exists, run into a new folder and compare, to show whether the numbers repeat:

```
.venv/bin/python scripts/pipeline.py --spec ml_spec.yaml --out runs/rerun --compare runs/latest
```

Otherwise:

```
.venv/bin/python scripts/pipeline.py --spec ml_spec.yaml --out runs/latest
```

Report the key results table from `00_pipeline.md`, every warning from `06_eval.md`, and the comparison if there is one. If the numbers match, say so plainly: same spec, same data, same numbers. If they differ, show which, and check whether the spec or the data changed (`manifest.json` holds their fingerprints).
