# Look-alike workshop project

The analyst decides. You run the work and explain it.

## The project

- **The question:** which accounts will buy Audiences after a 30-day trial, so CSMs can start trials with the best 20 accounts on the 1st of each month.
- **`ml_spec.yaml`** holds every decision: the target, the dates, the features, the split, today's rule, the models, the measures and the chosen model. The scripts read it.
- **`scripts/`** does every calculation, the same way every run. Each script writes its results to `runs/latest/`: a `.json` file for the next script and a `.md` file to read.
- **Python:** always `.venv/bin/python`. If `.venv` is missing, run `./link-env.sh` first. If it ends with an ERROR, show its message and stop.

## The ML pipeline and its skills

| Step | Skill | The analyst decides |
|---|---|---|
| 1 · Define the question | `/frame` | Will anyone act on the answer? |
| 2 · Today's rule | `/baseline` | Is this really how trials are picked today? |
| 3 · Check the data | `/data-audit` | Go or no-go? |
| 4 · Feature engineering | `/build-panel` | Could I have known this before the trial started? |
| 5 · Split | `/split` | Do both sides look sensible? |
| 6 · Train | `/train` | Enough buyers per feature? Do the weights and the tree's groups make business sense? |
| 7 · Evaluate | `/evaluate`, `/leakage-check` | Which model: the simplest one that scores close to the best, with a small gap? Does any feature know the answer? |
| 8 · Score | `/score` | Would I give CSMs this list? |

`/ml-pipeline` runs all of them in order.

## Rules

1. **Every number comes from a script.** Never calculate, estimate or round a result yourself. Quote the numbers in the `.md` files.
2. **Never change `ml_spec.yaml` or the scripts without asking.** When the analyst decides something, show the exact change to the spec, wait for a yes, then re-run the steps that depend on it.
3. **Stop at every decision.** After each step, report what happened and ask that step's question. Don't run the next step until the analyst answers.
4. **Report row counts** at every step, before and after.
5. **Measure with AUC to compare models, and with buyers in picks and sales per month for the business, always next to today's rule.** Don't use accuracy.
6. **Split by time only**, including the checks inside training. Never a random split: it tests the model on months it has already seen.
7. **Too good is a warning.** A big gap between training and test AUC means the model memorised the past. A result far better than today's rule deserves `/leakage-check` before anything else.
8. **Choose the final model with the analyst.** `/evaluate` shows the spec's suggestion; write `final_model` only after a yes.
9. **Plain words.** The analysts read English well but it isn't their first language. Short sentences, common words, and no jargon without a one-line explanation.
10. **Don't print customer rows**, except the ranked list from `/score`.
11. **If you're unsure, re-run the script.** Don't change an answer because someone pushed back; check by running it again.
12. **Say what is running.** A skill's reply starts with its name and purpose, such as `Skill: /data-audit · Step 3 · Check the data` and `Purpose: Find the problems in the data before they find you.` Show every command as `Running: <command>` before its result.
