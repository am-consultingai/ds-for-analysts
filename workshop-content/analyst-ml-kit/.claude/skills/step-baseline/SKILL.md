---
name: step-baseline
description: Step 5 of /run-steps. Scores today's rule exactly the way the model will be scored, on the same snapshots, so there is a number to beat. Writes scripts/05_baseline.py on the first run. Use when /run-steps reaches today's rule, or for /step-baseline.
---

# Step 5 · Today's rule, scored

**Start the reply with these two lines:**

```
Skill: /step-baseline · Step 5 · Today's rule · Script: projects/<name>/scripts/05_baseline.py
Purpose: Measure today's way, so we know what the new list has to beat.
```

Follow `.claude/skills/run-steps/contract.md` and, on the first run, `checks.md`.

Inputs: the spec, `runs/02_panel.csv`, `runs/04_split.json` (the sides are recomputed from the spec with the same rule as step 4). Outputs: `runs/05_baseline.json`, `runs/05_baseline.md`.

## Method

- **Flag:** `panel.eval(baseline.rule)`. **Score:** `panel.eval(baseline.score)`, empty as lowest.
- **Ranking per snapshot:** flagged rows first, by score high to low; then the rest, by score high to low; ties by entity ID.
- **No rule** (empty `baseline.rule`): rank at random, with a generator seeded from `seed`. The `.md` says "picking at random".
- On the training side and the test side: precision@K and recall@K (`common.py`), rows flagged per snapshot, events per snapshot. On the test side: events in each snapshot's top K.
- **Mix change:** the share of rows flagged on the test side divided by the training side's. Outside `defaults.mix_band`, warn with both shares. Numbers only.

The `.md`, in plain words: "Of the `<k>` `<rows>` today's way puts on each list, about `<precision × k>` really had `<event>` within `<h>` `<period>`s; that's `<recall>` of all `<event>`s." Then a table per test snapshot, then: **"The number to beat: `<precision>` of each list."**

**Built-in check:** the rule's columns exist in the panel. If not, exit naming them.

## Report

Quote the `.md`. Stop only if the rule flags no row on any snapshot: say so, read the rule back in plain words, and ask the analyst whether that's how they choose today.
