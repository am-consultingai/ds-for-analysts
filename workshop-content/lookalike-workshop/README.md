# Look-alike workshop

Which accounts will buy Audiences after a 30-day trial? On the 1st of each month, CSMs can start trials with 20 accounts. Build the answer with Claude, through the same ML pipeline as the churn project.

## Start

You need the workshop environment from the setup command. Then, in this folder:

```bash
./link-env.sh
claude
```

## The ML pipeline

| Step | In Claude |
|---|---|
| 1 · Define the question | `/frame` |
| 2 · Today's rule | `/baseline` |
| 3 · Check the data | `/data-audit` |
| 4 · Feature engineering | `/build-panel` |
| 5 · Split | `/split` |
| 6 · Train | `/train` |
| 7 · Evaluate | `/evaluate`, `/leakage-check` |
| 8 · Score | `/score` |
| All of it | `/ml-pipeline` (add `auto` to run without stopping) |

## What's here

| | |
|---|---|
| `ml_spec.yaml` | Every decision: the target, dates, features, split, today's rule, the models, the measures |
| `CLAUDE.md` | How Claude works in this project |
| `scripts/` | The calculations. Each one also runs without Claude: `.venv/bin/python scripts/audit.py --spec ml_spec.yaml` |
| `data/churn/` | The account and monthly tables (the same as the churn project): the features come from them |
| `data/lookalike/` | The trials (one row per trial, with the outcome) and the Audiences purchases. Synthetic, shaped like AppsFlyer's |
| `runs/latest/` | Each step's results: `.md` to read, `.json` for the next step |
