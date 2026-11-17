# AI in Finance coursework

## AI authorship and sources

**OpenAI Codex wrote this README and did the implementation and verification work described here.** Zach Doran supplied the course materials, selected SMH for Project 2, and requested the app features. Codex added stock and fund lookup, company-name matching, the SEC filing links, and the discrepancy display to the existing Legend Panel. The underlying financial statements and fund identifiers come from SEC filings and directories. The saved SMH holding snapshot cites VanEck. The Buffett, Cathie Wood, and Michael Burry checks are classroom interpretations of their investing approaches. The named investors did not author or endorse them.

## Run the Legend Panel

From the repository root, using Python 3.14 as in the local environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run class_python/panel_app.py --server.address 127.0.0.1 --server.port 8505
```

Open [the local app](http://127.0.0.1:8505). The app needs internet access to retrieve SEC data. Search by stock ticker or company name, or enter a U.S. ETF or mutual fund ticker found in SEC EDGAR. Try `GOLF` for the Project 1 cross-check, `NVDA` for the saved SMH holding analysis, or `SMH` and `VFIAX` for the fund lookup.

A checkout needs the full set of panel modules in `class_python/`, including `security_lookup.py`, the investor-check script links under `.agents/skills/`, and Cathie Wood's `thresholds.json`. Keep these files in their repository-relative paths. The saved sample memos and holdings snapshot live under `lab18/` and `lab19/`.

## What the app validates

- **Company results.** The panel reads annual U.S.-dollar facts tagged in SEC 10-K filings. **10-K sources and calculation lineage** shows the XBRL tag, fiscal period, filing date, accession, raw dollars, and original filing link for each available reported number.
- **Calculation discrepancies.** The **Data validation** table compares stored and recomputed return on equity and owner earnings. It shows input values, result units, both calculations, and their difference. A company identifier mismatch or a calculation discrepancy pauses the investor checks. Missing inputs appear as unavailable.
- **Fund results.** The app shows the SEC registrant, series and share-class identifiers and flags conflicting directory matches. Fund-level performance, expenses, and holdings require separate analysis using the fund's filings or sponsor data. Enter a holding ticker for the operating-company checks.
- **Checked example.** For Acushnet (GOLF), the panel matched the Project 1 figures from the FY2025 10-K filed February 27, 2026. In USD millions, revenue was 2,558.730, operating cash flow was 194.370, and capital spending was 74.342. All three differences were zero. The local 26-test suite also passed. [SEC filing](https://www.sec.gov/Archives/edgar/data/1672013/000167201326000057/golf-20251231.htm)

## Limits, local data, and course submission

- The panel supports research and coursework. Verify figures against the cited filing before relying on them. SEC coverage depends on the security and available tags. The company checks use 10-K data, and later filings can restate earlier periods. Treat the displayed history as current SEC history rather than a point-in-time trading record.
- Saved AI memos can contain mistakes. The numeric scanner checks whether a number appears in the printed facts. Check its metric, period, units, and interpretation separately. Saved judgments appear when a memo exists.
- The app contacts SEC EDGAR and caches responses locally. It can write local reports, memo edits, threshold changes, and personal trust decisions. Before publishing a copy, review the SEC request contact in `class_python/edgar_facts.py` and review local memos, decisions, caches, logs, archives, and credentials for personal information.
- This README documents the Legend Panel and Codex's contribution. The [Lab 20 readiness record](writeups/lab20.md) tracks the separate Project 2 deliverables, including the partner cold run, human-authored locked prediction, decision output, memo, validation record, and submission links. Use the course's reporting requirements when submitting.

## Where your files are

| Folder | Contents |
|---|---|
| `class_python/` | **All class Python source files**: the apps, calculation modules and investor-check scripts you work on or submit. |
| `writeups/` | Lab 15, 18, 19 and 20 write-ups, plus the submission copy of `skills.md`. |
| `investor_profiles/` | Warren Buffett, Cathie Wood and Michael Burry profile documents. |
| `lab18/` | SEC reports, saved memos, your trust decisions and valuation inputs/results. |
| `lab19/` | Panel reports, three-investor memos, fund selection and saved discussion/decisions. |
| `previous_projects/Doran/` | Your earlier Project 1 documents and their original guidance file. |
| `archives/` | The original Doran ZIP, a backup from before this reorganization and the move manifest. |
| `tests/` | Automated verification scripts, separate from class deliverables. |
| `.agents/skills/` | Discoverable AI skills and workflow references. Their script entry points link to the actual source files in `class_python/`. |

Project setup files stay here: `requirements.txt`, `.gitignore`, `AGENTS.md`, and `.venv/`. `.runtime/` holds local app logs only.

## Run an app

Run these commands **from this project folder**:

```sh
.venv/bin/python -m streamlit run class_python/panel_app.py --server.port 8505
```

| App | File | Local address when running |
|---|---|---|
| Lab 19 investor panel | [panel_app.py](class_python/panel_app.py) | http://localhost:8505 |
| Updated Buffett app with valuation | [updated_app.py](class_python/updated_app.py) | http://localhost:8504 |
| Original Buffett app | [buffett_app.py](class_python/buffett_app.py) | http://localhost:8503 |
| Point-in-time rates app | [asof_app.py](class_python/asof_app.py) | http://localhost:8501 |
| Lab 15 portfolio app | [app.py](class_python/app.py) | Choose a free Streamlit port |

Change the file and port in the command to run another app. The app files belong together with their helper modules; submit the required supporting files as well as the main app.

## Class scripts and checks

```sh
.venv/bin/python class_python/portfolio.py
.venv/bin/python class_python/asof.py
.venv/bin/python class_python/edgar_facts.py COST
.venv/bin/python class_python/panel_data.py COST --check-memos
.venv/bin/python class_python/panel_data.py NVDA --check-memos
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q
```

Your Project 2 fund is **SMH**. The Lab 19 holding selection is **NVDA**, based on the dated VanEck holdings snapshot in `lab19/fund_selection.json`.

Write-ups: [Lab 15](writeups/lab15.md), [Lab 18](writeups/lab18.md), [Lab 19](writeups/lab19.md), [skills.md](writeups/skills.md).
