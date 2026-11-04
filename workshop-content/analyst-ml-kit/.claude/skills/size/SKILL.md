---
name: size
description: Checks whether the history is long enough to both train and judge the result, then sets the test start date, the gap, the list length when it's open, and which columns to keep. Writes scripts/03_size.py on the first run. Runs inside /run-steps after the panel step; use /size to re-check after a change.
---

# Is there enough history?

**Start the reply with these two lines:**

```
Skill: /size · Enough history? · Script: projects/<name>/scripts/03_size.py
Purpose: Make sure the result can be trusted before training anything.
```

**Before each command, show it on its own line** as `Running: <the exact command>`. Read `.claude/skills/run-steps/contract.md` before writing the script; follow `checks.md` on the first run.

Inputs: `runs/02_panel.csv`, `runs/02_panel.json`, the spec. Outputs: `runs/03_size.json`, `runs/03_size.md`.

## Method

Both rules count events, because the events are the budget: some must teach the model, the rest must judge it. **Events** are distinct (entity, event period) pairs, counted with `distinct_events`, never label rows: one event marks several snapshots.

1. **List length.** `k` from the spec. If `k` is `auto`, stop before this script: `02_panel.json` has `typical_positives_per_snapshot`. Ask the analyst: "A list of `<n>` `<rows>` would cover a typical `<period>`'s `<event>`s. Can `<actor>` handle a list that long?" Write their answer to `metric.k`, then ask question 11 of `/frame`.
2. **The gap to see.** `g = extra_hits / k`.
3. **What the test needs:**
   - picks: `picks_factor / g²` (a share among picks is accurate to about ±1/√picks)
   - events: `events_factor / g²` (the ranking quality is accurate to about ±0.6/√events)
4. **Test start.** Labelled snapshots sorted. Take the last `j` snapshots as the test side, for `j` from `min_test_snapshots` up. Stop at the first `j` where `k × j ≥ picks needed` and test events `≥ events needed`. `test_from` is the earliest of those `j` snapshots.
5. **Training side:** snapshots before `test_from − gap_periods`. Training events counted the same way.
6. **Feature cap:** `floor(training events / events_per_feature)`. Model columns are counted after text columns become one yes/no column per value (`model_matrix`).
7. **Keeping columns.** If the panel has more model columns than the cap: score each panel column on the training side alone, with precision@K in both directions (high first and low first; empty cells filled with the training median; for a text column, its best yes/no column). Add columns from the highest score down, ties by name, while the total model columns stay within the cap. Record the kept list.
8. **When it doesn't fit.** If no `j` meets step 4 before the training side runs out, or the cap is below `min_features`: the data can't meet both needs. Compute the smallest `extra_hits` the data could support (for each `j`: the smallest g with enough picks and events, given a cap of at least `min_features`; the best of these, times `k`, rounded up), and exit non-zero with that number in the `.json`.

The `.json` holds: `g`, picks and events needed, `test_from`, test snapshots, test picks, test events, training events, feature cap, model columns before and after, `keep` (the kept columns, or empty when all fit), `dropped` (with each column's score), and when it fails, `smallest_extra_hits`.

**Built-in checks:** the last training snapshot plus `gap_periods` is before `test_from`; training and test snapshots don't overlap.

## After the script

The results are kit decisions. Write `split.test_from`, `split.gap_periods`, `metric.g` and `features.keep` to the spec, and log each in `decisions.md` as `kit`, with the reason in one line (for example, "the test needs about `<n>` `<event>`s to show a difference of `<extra_hits>` per list").

Report, in plain words and no statistics: the test covers `<first>` to `<last>`, with `<n>` `<event>`s; training uses `<from>` to `<to>`; `<m>` columns were set aside because there are too few `<event>`s to learn from all of them (name them only if asked). Don't stop.

## When it doesn't fit: business choices only

Explain in one sentence: "There isn't enough history yet to both learn and check a difference of `<extra_hits>` `<event>`s per list." Then offer:

1. **Accept a bigger difference:** "The check can only show it if the list finds at least `<smallest_extra_hits>` more real `<event>`s than today's way." If yes, write `metric.extra_hits`, log it as `analyst`, and re-run this step.
2. **Wait for more history,** and run again later.
3. **Stop here.**

Never offer method settings (fewer columns, a different test size). The kit already set aside every column it could.
