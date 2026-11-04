# The trust checks

The analyst can't review the code, so these checks do. Every check script lives in `projects/<name>/checks/`, is written once, frozen and fingerprinted in `manifest.json` like the step scripts. A failed check stops the run.

## 1. Independent calculation (first run of every step)

A second, separate calculation of the step's key numbers, written without seeing the first script.

1. Start a subagent (Agent tool). Give it only:
   - the path of the step's `SKILL.md` (the method) and of this kit's `contract.md`,
   - the path of `ml_spec.yaml` and of the step's input files (the data folder, or earlier `runs/` outputs listed under "Inputs" in the step skill),
   - the step's key numbers from the table below,
   - the output path `projects/<name>/checks/NN_<step>_check.py`, which must write `projects/<name>/checks/NN_<step>_check.json`.
   
   Tell it: **do not open `projects/<name>/scripts/` or this step's outputs in `runs/`**; write a short, separate script that computes only the key numbers; run it with `.venv/bin/python`; report the path of the `.json`.
2. Compare the two `.json` files key by key. Counts, dates and ID lists must be equal; shares and scores must be equal to 3 decimals. Write the comparison with a check script, `checks/compare.py` (written once, then frozen), run as:
   ```
   .venv/bin/python projects/<name>/checks/compare.py --project projects/<name> --step NN_<step>
   ```
   It reads the key list for the step from the `key_numbers` block of `checks/key_numbers.yaml` (written with it, from the table below), prints a table of both values, and exits non-zero on any difference.
3. If they differ, find out which is wrong by re-reading the method. Fix the wrong script, then re-run both. Never change the method to match a script.

| Step | Key numbers |
|---|---|
| `00_profile` | per file: rows, columns, distinct entity IDs, first and last period |
| `01_audit` | per file: duplicate entity × period rows, rows after the event, columns at least `many_missing` empty |
| `02_panel` | rows, distinct entities, snapshots, label share, distinct events, model columns |
| `03_size` | `test_from`, test snapshots, test picks, test events, training events, feature cap |
| `04_split` | per side: rows, distinct entities, distinct events, label share, first and last snapshot |
| `05_baseline` | today's rule on the test side: precision@K, recall@K, rows flagged per snapshot |
| `06_train` | training rows, training events, model columns |
| `07_evaluate` | the model on the test side: precision@K, recall@K; the same on the training side |
| `08_leakage` | the three columns with the highest single-column precision@K, with their values |
| `09_score` | rows scored, the snapshot scored, the set of IDs on the list |

## 2. Shuffled labels (once, after the first run of `06_train`)

The model must learn nothing from random labels. If it does, information about the answer is reaching it some other way.

For each seed `s` from 1 to `defaults.shuffles`:

```
.venv/bin/python projects/<name>/scripts/06_train.py --project projects/<name> --shuffle-seed s --out projects/<name>/runs/_shuffle_s
.venv/bin/python projects/<name>/scripts/07_evaluate.py --project projects/<name> --out projects/<name>/runs/_shuffle_s
```

(Copy `02_panel.*`, `03_size.json` and `04_split.json` into each `_shuffle_s` folder first.) Then `checks/shuffle_check.py` reads `internal.test_auc` from each `07_evaluate.json`, and the test events from `04_split.json`. It passes when the mean AUC is within `0.5 ± 0.6/√(test events)`. It writes `checks/shuffle_check.json` and exits non-zero on a fail.

On a fail, tell the analyst in plain words that the model finds a pattern even when the answers are shuffled, so something in the data gives the answer away, and run the leakage step before anything else.

## 3. Planted leak (once, at the first run of `08_leakage`)

The leakage step must catch a leak we know is there.

```
.venv/bin/python projects/<name>/scripts/08_leakage.py --project projects/<name> --plant-leak --out projects/<name>/runs/_planted
```

(Copy `02_panel.*`, `03_size.json`, `04_split.json` and `05_baseline.json` into `_planted` first.) `--plant-leak` adds a column `_planted_leak`: a copy of the label with `defaults.planted_flip` of its values flipped, chosen with the spec's seed. `checks/planted_check.py` passes when `_planted_leak` is marked suspect in `_planted/08_leakage.json`. It writes `checks/planted_check.json` and exits non-zero on a fail. A fail means the leakage step doesn't work: fix it before trusting any leakage result.

## 4. Every number comes from a script output (every report)

Before writing any reply or report, take every number from a `runs/` or `checks/` file. If a number you need isn't in one, it must be added to a script, not worked out by hand.
