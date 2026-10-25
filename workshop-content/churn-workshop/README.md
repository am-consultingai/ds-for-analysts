# Churn workshop

Which accounts will leave in the next 90 days? Build the answer with Claude, one step of the ML pipeline at a time.

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
| `ml_spec.yaml` | Every decision: the target, dates, features, split, today's rule, the metric |
| `CLAUDE.md` | How Claude works in this project |
| `scripts/` | The calculations. Each one also runs without Claude: `.venv/bin/python scripts/audit.py --spec ml_spec.yaml` |
| `data/churn/` | Four tables: accounts, and monthly ARR, traffic and product adoption. Synthetic, shaped like AppsFlyer's |
| `runs/latest/` | Each step's results: `.md` to read, `.json` for the next step |
