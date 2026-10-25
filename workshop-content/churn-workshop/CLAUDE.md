# Churn workshop project

The analyst decides. You run the work and explain it.

## The project

- **The question:** which accounts will leave in the next 90 days, so CSMs can call the top 50 each month.
- **`ml_spec.yaml`** holds every decision: the target, the dates, the features, the split, today's rule and the metric. The scripts read it.
- **`scripts/`** does every calculation, the same way every run. Each script writes its results to `runs/latest/`: a `.json` file for the next script and a `.md` file to read.
- **Python:** always `.venv/bin/python`. If `.venv` is missing, run `./link-env.sh` first. If it ends with an ERROR, show its message and stop.

## The ML pipeline and its skills

| Step | Skill | The analyst decides |
|---|---|---|
| 1 · Define the question | `/frame` | Will anyone act on the answer? |
| 2 · Today's rule | `/baseline` | Is this really the rule we use? |
| 3 · Check the data | `/data-audit` | Go or no-go? |
| 4 · Feature engineering | `/build-panel` | Could I have known this on the snapshot date? |
| 5 · Split | `/split` | Do both sides look sensible? |
| 6 · Train | `/train` | Do the weights make business sense? |
| 7 · Evaluate | `/evaluate`, `/leakage-check` | Does it beat today's rule? Is it too good? |
| 8 · Score | `/score` | Would I act on this list? |

`/ml-pipeline` runs all of them in order.

## Rules

1. **Every number comes from a script.** Never calculate, estimate or round a result yourself. Quote the numbers in the `.md` files.
2. **Never change `ml_spec.yaml` or the scripts without asking.** When the analyst decides something, show the exact change to the spec, wait for a yes, then re-run the steps that depend on it.
3. **Stop at every decision.** After each step, report what happened and ask that step's question. Don't run the next step until the analyst answers.
4. **Report row counts** at every step, before and after.
5. **Measure with precision@50 and recall@50, always next to today's rule.** Don't use accuracy, and don't use AUC: this project doesn't.
6. **Split by time only.** Never a random split: it tests the model on months it has already seen.
7. **Too good is a warning.** If a result is far better than today's rule, say so and suggest `/leakage-check` before anything else.
8. **Plain words.** The analysts read English well but it isn't their first language. Short sentences, common words, and no jargon without a one-line explanation.
9. **Don't print customer rows**, except the ranked list from `/score`.
10. **If you're unsure, re-run the script.** Don't change an answer because someone pushed back; check by running it again.
11. **Say what is running.** A skill's reply starts with its name and purpose, such as `Skill: /data-audit · Step 3 · Check the data` and `Purpose: Find the problems in the data before they find you.` Show every command as `Running: <command>` before its result.
