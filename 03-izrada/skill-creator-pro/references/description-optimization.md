<!-- Part of a derivative work of anthropics/skills@b29e7cf6 (skills/skill-creator), by buky <webdevcom01@gmail.com>, 2026-07-30. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md. -->

# Description Optimization

Moved out of SKILL.md body by T-04 (finding N-08). Unchanged text; this whole sub-workflow runs at the end, after the skill is otherwise finished.

---

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

### Step 1: Generate trigger eval queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger. Save as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

The queries must be realistic and something a Claude Code or Claude.ai user would actually type. Not abstract requests, but requests that are concrete and specific and have a good amount of detail. For instance, file paths, personal context about the user's job or situation, column names and values, company names, URLs. A little bit of backstory. Some might be in lowercase or contain abbreviations or typos or casual speech. Use a mix of different lengths, and focus on edge cases rather than making them clear-cut (the user will get a chance to sign off on them).

Bad: `"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

Good: `"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D i think"`

For the **should-trigger** queries (8-10), think about coverage. You want different phrasings of the same intent — some formal, some casual. Include cases where the user doesn't explicitly name the skill or file type but clearly needs it. Throw in some uncommon use cases and cases where this skill competes with another but should win.

For the **should-not-trigger** queries (8-10), the most valuable ones are the near-misses — queries that share keywords or concepts with the skill but actually need something different. Think adjacent domains, ambiguous phrasing where a naive keyword match would trigger but shouldn't, and cases where the query touches on something the skill does but in a context where another tool is more appropriate.

The key thing to avoid: don't make should-not-trigger queries obviously irrelevant. "Write a fibonacci function" as a negative test for a PDF skill is too easy — it doesn't test anything. The negative cases should be genuinely tricky.

### Step 2: Review with user

Present the eval set to the user for review using the HTML template:

1. Save the JSON array of eval items to a file (e.g. `/tmp/eval_queries_<skill-name>.json`)
2. Render the template with `scripts/render_eval_review.py` — don't substitute the placeholders by hand. The eval query text is freeform natural language (often lifted from real user scenarios) and the description may not have passed validation yet, so raw text substitution risks corrupting the page or, if a query happens to contain `</script>`, breaking out of the script block entirely. The script escapes both cases correctly:
   ```bash
   cd <skill-creator-path>   # `-m` needs the skill on sys.path
   python -B -m scripts.render_eval_review \
     --skill-name <skill-name> \
     --skill-description "<current description>" \
     --eval-data /tmp/eval_queries_<skill-name>.json \
     --output /tmp/eval_review_<skill-name>.html
   ```
3. Open it: `open /tmp/eval_review_<skill-name>.html`
4. The user can edit queries, toggle should-trigger, add/remove entries, then click "Export Eval Set"
5. The file downloads to `~/Downloads/eval_set.json` — check the Downloads folder for the most recent version in case there are multiple (e.g., `eval_set (1).json`)

This step matters — bad eval queries lead to bad descriptions.

### Step 3: Run the optimization loop

Tell the user: "This will take some time — I'll run the optimization loop in the background and check on it periodically."

Save the eval set to the workspace, then run in the background:

```bash
# from the skill-creator directory: the `-m` form needs it on sys.path,
# and -B keeps __pycache__ out of the skill (it would change its checksum).
cd <skill-creator-path>
python -B -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

Use the model ID from your system prompt (the one powering the current session) so the triggering test matches what the user actually experiences.

**Tell the user the size of the run before starting it.** With the defaults above and the 20 queries this file prescribes, that command starts **up to 308 `claude -p` processes** (20 x 3 runs x 5 iterations, plus 4 description rewrites and up to 4 rewrite retries). The script prints its own plan on the first line of stderr before making any call, and refuses to start at all if the plan exceeds `--max-calls` (default 500). Read that line back to the user rather than paraphrasing it.

If the user wants a money figure, pass `--cost-per-call <their rate>`; the script will not guess one, because the real rate depends on the model, plan and context length, and a made-up number would read as measured.

**Known limitation — there is no retry or backoff.** A run that fails (rate limit, timeout, process crash) is counted as an error and the loop moves on. That run is paid for if it reached the model, and its evidence is gone, so the winning description gets chosen on a smaller sample than planned. The script reports how many runs were lost and what share of the attempted total that is; if the share is large, treat the result as provisional and re-run rather than trusting it. Retry was deliberately not added: retrying blindly doubles spend at exactly the moment something is already going wrong, and no measurement of the failure behaviour exists to size it against.

While it runs, periodically tail the output to give the user updates on which iteration it's on and what the scores look like.

This handles the full optimization loop automatically. It splits the eval set into 60% train and 40% held-out test, evaluates the current description (running each query 3 times to get a reliable trigger rate), then calls Claude to propose improvements based on what failed. It re-evaluates each new description on both train and test, iterating up to 5 times. When it's done, it opens an HTML report in the browser showing the results per iteration and returns JSON with `best_description` — selected by test score rather than train score to avoid overfitting.

### How skill triggering works

Understanding the triggering mechanism helps design better eval queries. Skills appear in Claude's `available_skills` list with their name + description, and Claude decides whether to consult a skill based on that description. The important thing to know is that Claude only consults skills for tasks it can't easily handle on its own — simple, one-step queries like "read this PDF" may not trigger a skill even if the description matches perfectly, because Claude can handle them directly with basic tools. Complex, multi-step, or specialized queries reliably trigger skills when the description matches.

This means your eval queries should be substantive enough that Claude would actually benefit from consulting a skill. Simple queries like "read file X" are poor test cases — they won't trigger skills regardless of description quality.

### Step 4: Apply the result

Take `best_description` from the JSON output and update the skill's SKILL.md frontmatter. Show the user before/after and report the scores.

---

### Package and Present (only if a file-delivery tool is available)

Check whether you have access to a tool that presents files to the user — `present_files`, or `SendUserFile` in Cowork remote. If you have neither, skip this step. If you do, package the skill and send the user the resulting `.skill` file with that tool:

```bash
cd <skill-creator-path>
python -B -m scripts.package_skill <path/to/skill-folder>
```

The presented `.skill` (or bare `SKILL.md`) file card shows a **Save skill** button when the user's org allows skill creation; clicking it installs the skill into their profile.

---
