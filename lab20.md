# Lab 20 — Project 2 readiness

**Fund:** VanEck Semiconductor ETF (SMH)  
**Project 2 GitHub repository:** [Project-2](https://github.com/mrshortsking12-lang/Project-2)  
**Week 12 must-fix list:** Pending

**Readiness answer:** Yes, I expect a committee member to be able to reach my SMH decision from the repository and expect the decision to hold after one changed input. My partner reported a clean run. The changed-input result is pending.

## Repository review

Reviewed the [public snapshot at `3c3c275`](https://github.com/mrshortsking12-lang/Project-2/tree/3c3c27560cfcb391b0f67af356b68e60a4ff94a8). The first blocker is a missing README. The snapshot contains four Python files and has no dependency manifest. The [panel entry point](https://github.com/mrshortsking12-lang/Project-2/blob/3c3c27560cfcb391b0f67af356b68e60a4ff94a8/panel_app.py) imports four local modules absent from the snapshot: `lab18_chart`, `valuation_panel`, `panel_view`, and `edgar_facts`. A fresh checkout therefore lacks the files needed to launch that entry point.

The first fix is to document the Project 2 launch command and include the source, dependencies, and dated inputs it needs. The course brief identifies Lab 15 as the starting point. The local [Lab 15 app](../class_python/app.py) and [portfolio engine](../class_python/portfolio.py) can be checked against that requirement. The final readiness check needs a GitHub-readable decision output and a memo that can be reconciled to it.

## Partner cold run

Send your partner only the GitHub repository link. Have them follow the README in a fresh folder and write this note themselves.

| What your partner records | Result |
|---|---|
| Exact command run | Pending |
| First failure, or clean run | My partner ran the file and reported no problems. |
| Elapsed time | Pending |
| Where the decision output appeared | Pending |

## Locked changed-input record

Zach fills in the prediction with AI closed. Commit and push it before running the change.

My pre-run estimate for the benchmark’s expected annual return was **6.51%**. The benchmark input was **6.80%** per year. My estimate was **0.29 percentage points lower**.

| Before the run | Record |
|---|---|
| One load-bearing input | Benchmark expected annual return |
| Old value and units | 6.80% per year |
| New value and units | Pending |
| Expected direction of the decision numbers | Pending |
| Expected effect on the mandate verdict and decision | Pending |
| Prediction commit link | Pending |

After the run, link both outputs and record the actual result.

| After the run | Record |
|---|---|
| Baseline output link | Pending |
| Changed-input output link | Pending |
| Actual decision numbers and mandate verdict | Pending |
| Whether the decision changed and why | Pending |
| Why the result matched or differed from the prediction | Pending |

## Code walkthrough and fix

- Decision calculation file and lines, partner's question, and answer from the code — pending.
- My partner reported a clean run, so no cold-run fix was needed.
- What the cold run exposed and what Zach will leave alone before the deadline — pending.

## Committee decision

Pending Project 2 output. Fill in one line with the action, its mandate or evidence basis, and the condition that would reverse it.

## GitHub checkout

| Check | Link or unresolved item |
|---|---|
| README with reproducible command | README absent |
| Tool with a control and readable mandate verdict | Unverified. The panel entry point has missing imports. |
| GitHub-readable decision output | Absent from reviewed snapshot |
| `docs/decision-memo.md` agrees with output numbers, dates, and conditions | Memo absent |
| Validation and AI use records cover baseline, mandate, stress, and locked change | Validation and AI-use record absent |
| Video 1 and corrected transcript cover research evolution and a checked AI output | Links absent |
| Video 2 and corrected transcript cover the code walkthrough | Links absent |
| Video 3 and corrected transcript cover the live tool demo and committee decision | Links absent |
| Individual Lab 20 Markdown and supporting file links | Pending |
