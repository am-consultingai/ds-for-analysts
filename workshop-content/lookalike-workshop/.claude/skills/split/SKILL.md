---
name: split
description: Step 5 of the ML pipeline, split. Runs scripts/split.py to split the trials by start date: the models learn on earlier trials and are tested on later months they have never seen. Use for /split or to explain how the models are tested.
---

# Step 5 · Split

**Start the reply with these two lines:**

```
Skill: /split · Step 5 · Split
Purpose: Learn on earlier trials, test on later months the models have never seen.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

## Run

Needs `runs/latest/02_panel.csv`. If it's missing, run `/build-panel` first.

```
.venv/bin/python scripts/split.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/03_split.md` and report, for each side: the months, the trials, how many bought and the rate, and how many trials today's rule would have picked. Explain in one sentence why there is no gap: each trial's outcome is known 30 days after it starts, by the start of the next round.

## Rules

- Split by time only. If a random split is requested, explain why not: trials from the test months would land in training, and the models would be tested on months they have already seen. The script refuses it too.

## Stop

Ask: **"Do both sides look sensible? Enough trials, and a similar buying rate?"** Then stop.
