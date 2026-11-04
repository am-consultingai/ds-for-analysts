---
name: report
description: Writes the one-page result: the question in the analyst's words, the new list next to today's rule, the warnings, the checks, and who decided what. Every number is quoted from the runs. Use for /report, at the end of /ml-pipe-design, or after a re-run.
---

# The one-page report

**Start the reply with these two lines:**

```
Skill: /report · The one-page report · Script: none (quotes the runs)
Purpose: One page you can hand on: what was asked, what was found, and how far to trust it.
```

Write `projects/<name>/report.md`. **Every number is copied from a file in `runs/` or `checks/`**; if a number isn't in one, don't write it. Use the nouns from `terms:`.

## The page, in this order

1. **The question:** `question` from the spec, then `decision`.
2. **The answer, in one sentence:** from `07_evaluate.json`: the new list finds `<beats by>` more real `<event>`s per list of `<k>` than today's way; the analyst asked for at least `<extra_hits>`. Then the go or no-go from `decisions.md`.
3. **Side by side** (test side, from `05_baseline.json` and `07_evaluate.json`): today's way and the new list, as real `<event>`s per list and share of all `<event>`s found, and the per-snapshot hits.
4. **Warnings:** every flag from `07_evaluate.json`, the mix warnings from `04_split.json` and `05_baseline.json`, the suspects from `08_leakage.json` and what the analyst decided about each. If none, say "No warnings."
5. **How it was checked:** one line each: the test stretch and its `<event>`s (`03_size.json`); the code was run twice with the same result; an independent calculation agreed; shuffled answers gave nothing (`checks/shuffle_check.json`); a planted leak was caught (`checks/planted_check.json`). Mark any that didn't run.
6. **Today's list:** where `runs/09_ranked.csv` is, and the expected `<event>`s in the top `<k>` from `09_score.json`. Don't copy the list into the report.
7. **Who decided what:** the analyst's answers, one line each, then "and `<n>` choices made by the kit's fixed rules; see `/decisions`."

Keep it to one page: short sentences, tables where they help, no method terms. Show the analyst the page and where it's saved.
