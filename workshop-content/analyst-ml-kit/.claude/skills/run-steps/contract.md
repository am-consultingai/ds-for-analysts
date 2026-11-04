# The code contract: rules every script follows

Every step skill points here. The skill gives the method; this file gives the rules the code must follow. Read both before writing a script.

## Where things go

| | Path (from the kit folder) |
|---|---|
| Step scripts | `projects/<name>/scripts/NN_<step>.py` |
| Shared helpers | `projects/<name>/scripts/common.py` |
| Check scripts | `projects/<name>/checks/*.py` |
| Outputs | `projects/<name>/runs/NN_<step>.json` (for the next step) and `NN_<step>.md` (to read). Large tables: `runs/NN_<step>.csv` |
| Fingerprints | `projects/<name>/manifest.json` |

The steps and their numbers: `00_profile`, `01_audit`, `02_panel`, `03_size`, `04_split`, `05_baseline`, `06_train`, `07_evaluate`, `08_leakage`, `09_score`.

Every script runs from the kit folder as:

```
.venv/bin/python projects/<name>/scripts/NN_<step>.py --project projects/<name> [--out <folder>]
```

`--out` defaults to `<project>/runs`. A step reads earlier steps' outputs from the same `--out` folder, except where its skill says otherwise.

## `common.py`

Write it together with the first script of the project (`00_profile.py`), with all of these functions, so it never needs changing later. It is frozen like the step scripts.

| Function | Does |
|---|---|
| `load_spec(project)` | Reads `<project>/ml_spec.yaml` and returns it as a dict |
| `read_csv(path)` | Reads a CSV with only empty cells as missing (`keep_default_na=False, na_values=[""]`), so text such as "NA" stays text |
| `periods(spec, series)` | Converts the time column to pandas periods at `spec["period"]` |
| `write_step(out, name, result, markdown)` | Writes `name.json` (sorted keys, indent 1, floats rounded to 6 decimals, no timestamps, no absolute paths) and `name.md` |
| `read_step(out, name)` | Reads an earlier step's `.json` |
| `rank_order(score, entity_ids)` | The order used everywhere: score high to low, ties broken by entity ID ascending |
| `precision_at_k(y, score, snapshot, entity_ids, k)` | Per snapshot, the share of events among the top k; then the mean over snapshots |
| `recall_at_k(y, score, snapshot, entity_ids, k)` | Events found in the top k of every snapshot, over all events on those snapshots |
| `hits_per_snapshot(y, score, snapshot, entity_ids, k)` | Events in each snapshot's top k, as `{snapshot: count}` |
| `auc(y, score)` | `sklearn.metrics.roc_auc_score`. Used by the checks only |
| `model_matrix(panel, spec, columns)` | The model's input: the chosen panel columns, text columns turned into one yes/no column per value (`pd.get_dummies`, `dtype=float`), columns sorted by name |
| `align(X, columns)` | Reindexes a matrix to the training columns, filling new columns with 0 |
| `logistic(spec)` | `make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C, max_iter, random_state=seed))` with values from `spec["defaults"]["logistic"]` and `spec["seed"]` |
| `distinct_events(panel)` | The number of distinct (entity, event period) pairs behind the rows whose label is 1 |
| `update_manifest(project, script_path, step)` | Records sha256 fingerprints: the script, `common.py`, the spec and every data file, under `steps.<step>`; and the script under `scripts` |

## Rules for every script

1. **No values in the code.** Every column name, date, threshold, list length and seed is read from `ml_spec.yaml`. The only words typed into the code are file names of outputs, step names and spec keys. After writing a script, search it for every column name, date and number in the spec; any found as a literal must be replaced by a read from the spec.
2. **Deterministic.** Set `seed` from the spec wherever randomness exists. Sort before any operation whose order matters. Two runs on the same spec and data must write identical `.json` files.
3. **Count every row.** Each step that filters keeps a list of `{step, rows_before, rows_after, reason}` and writes it in its `.json` and `.md`. Rows in = rows out + rows dropped, checked with an `assert`.
4. **Fail loudly.** A built-in check that fails ends the script with a non-zero exit and one plain sentence saying what failed. Never write outputs after a failed check.
5. **Plain markdown.** The `.md` uses the nouns from `terms:` in the spec, short sentences and tables. No entity rows, except the ranked list at `09_score`.
6. **Internal numbers stay internal.** Values used only by the checks (such as `test_auc`) go in the `.json` under `internal`, never in the `.md`.
7. **Only installed packages:** the standard library, pandas, numpy, scikit-learn, scipy, statsmodels, joblib, PyYAML, matplotlib, seaborn.
8. **Paths:** relative to the kit folder, read from the spec or built from `--project` and `--out`. Nothing outside the kit folder except the data folder in the spec.
9. **End by calling `update_manifest`**, after the outputs are written.

## Refusals: the script must exit with an error, not continue

- `split.method` is anything but `time`.
- Any model is fitted on a row from the test side, except the final refit at `09_score`.
- A feature uses a value from after its snapshot period.

## First run of a step

1. Write the script (and `common.py` with the first one). Check rule 1.
2. Run it. If it fails, fix the script and run it again. Until the step passes step 4 below, fixes need no yes.
3. **Run twice:** run it again with `--out projects/<name>/runs/_rerun`, then `cmp` each `.json` against the first run. They must be identical. For a step that reads earlier outputs, copy those into `_rerun` first.
4. **Independent calculation:** follow `checks.md`.
5. Record the step as verified: add `"verified": true` under `steps.<step>` in `manifest.json`. From now on the script is **frozen**.

## Later runs

1. `sha256sum` the script, `common.py` and the step's check scripts, and compare with `manifest.json`. If any differs, stop and tell the analyst, in plain words, that the code changed since it was checked, and ask before running.
2. Run it. Quote its `.md`.
