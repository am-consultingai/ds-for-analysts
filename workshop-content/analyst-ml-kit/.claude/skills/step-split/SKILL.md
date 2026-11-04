---
name: step-split
description: Step 4 of /run-steps. Splits the panel by time, with a gap, into a training side and a later test side, using the dates /size set, and reports any change in the mix between them. Writes scripts/04_split.py on the first run. Use when /run-steps reaches the split, or for /step-split.
---

# Step 4 · Split by time

**Start the reply with these two lines:**

```
Skill: /step-split · Step 4 · Split by time · Script: projects/<name>/scripts/04_split.py
Purpose: Learn from the past, judge on a later stretch the model has never seen.
```

Follow `.claude/skills/run-steps/contract.md` and, on the first run, `checks.md`.

Inputs: the spec, `runs/02_panel.csv`. Outputs: `runs/04_split.json`, `runs/04_split.md`.

## Method

- **Refuse** anything but `split.method: time`.
- **Training side:** snapshots before `split.test_from − split.gap_periods`.
- **Test side:** snapshots from `split.test_from` to the last snapshot.
- **The gap** (the snapshots in between) is used by neither side: their answers fall in the test stretch.
- Per side: rows, distinct entities, distinct events, label share, first and last snapshot, snapshots.
- **Mix change:** the test side's label share divided by the training side's. Outside `defaults.mix_band`, add a warning with both shares. Report the numbers only; never give a cause.

The `.md` is one table (side, first, last, snapshots, rows, `<rows>`, `<event>`s, share with the event), one line on the gap ("`<g>` `<period>`s left out between the two, because each answer looks `<h>` `<period>`s ahead"), and the mix warning if there is one.

**Built-in checks:** the last training snapshot + `gap_periods` < the first test snapshot; no snapshot on both sides; both sides have at least one event.

## Report

Quote the table, the gap line and any warning. Don't stop.
