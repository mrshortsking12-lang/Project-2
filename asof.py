"""Lab 16: filter publication records to what was knowable on a date."""

from datetime import date


# Editable inputs: (original row number, ticker, month measured, published on, price).
DECISION_DATE = "2026-03-31"
TABLE = [
    (1, "AAA", "2026-01", "2026-02-10", 101.0),
    (2, "AAA", "2026-02", "2026-03-10", 104.0),
    (3, "AAA", "2026-03", "2026-04-10", 109.0),
    (4, "AAA", "2026-02", "2026-03-25", 103.0),
    (5, "BBB", "2026-01", "2026-02-10", 98.0),
    (6, "BBB", "2026-02", "2026-03-10", 97.0),
    (7, "BBB", "2026-02", "2026-03-10", 97.0),
    (8, "BBB", "2026-03", "2026-04-10", 92.0),
    (9, "CCC", "2026-01", "2026-02-10", 110.0),
    (10, "CCC", "2026-02", "2026-04-05", 112.0),
    (11, "", "2026-02", "2026-03-10", 99.0),
    (12, "CCC", "2026-02", "2026-03-10", 111.0),
]


def latest_publications(rows):
    """Rule 4: callers first exclude publications beyond their cutoff."""
    latest = {}
    for row in rows:
        key = (row[1], row[2])  # One group for each ticker and measured month.
        if key not in latest or row[3] > latest[key][3]:
            latest[key] = row  # Replace the older publication in this group.
    return sorted(latest.values(), key=lambda row: row[0])


def filter_rows(table, decision_date):
    cutoff = date.fromisoformat(decision_date)
    funnel = []
    rows = list(table)

    removed = [row for row in rows if not row[1].strip()]
    rows = [row for row in rows if row[1].strip()]
    funnel.append(("Quarantined: no ticker", removed))

    seen = set()
    unique, removed = [], []
    for row in rows:
        record = row[1:]  # Original row number is lineage, not record content.
        if record in seen:
            removed.append(row)
        else:
            seen.add(record)
            unique.append(row)
    funnel.append(("Exact duplicate", removed))

    # Naive comparison still excludes missing tickers and exact duplicates.
    naive = latest_publications(unique)
    removed = [row for row in unique if date.fromisoformat(row[3]) > cutoff]
    rows = [row for row in unique if date.fromisoformat(row[3]) <= cutoff]
    funnel.append(("Published after " + decision_date, removed))

    panel = latest_publications(rows)
    kept_ids = {row[0] for row in panel}
    funnel.append(("Older vintage replaced by a revision",
                   [row for row in rows if row[0] not in kept_ids]))
    return panel, naive, funnel


def signals(panel):
    results = {}
    for ticker in sorted({row[1] for row in panel}):
        months = {row[2]: row[4] for row in panel if row[1] == ticker}
        latest = max(months)
        year, month = map(int, latest.split("-"))
        previous = f"{year - 1:04d}-12" if month == 1 else f"{year:04d}-{month - 1:02d}"
        change = None
        if previous in months and months[previous] != 0:
            change = (months[latest] / months[previous] - 1) * 100
        results[ticker] = (latest, change)
    return results


def main():
    panel, naive, funnel = filter_rows(TABLE, DECISION_DATE)
    print(f"Decision date: {DECISION_DATE}\nStarting rows: {len(TABLE)}")
    for label, removed in funnel:
        numbers = ", ".join(str(row[0]) for row in removed) or "none"
        print(f"{label}: {len(removed)} removed; rows {numbers}")
    print(f"\nAs-of panel: {len(panel)} rows")
    print("Row  Ticker  Month    Published   Price")
    for number, ticker, month, published, price in panel:
        print(f"{number:3}  {ticker:6}  {month}  {published}  {price:.1f}")
    for label, records in (("As-of", panel), ("Naive", naive)):
        print(f"\n{label} signals:")
        for ticker, (month, change) in signals(records).items():
            value = "unavailable (previous calendar month missing or zero)" if change is None else f"{change:+.2f}%"
            print(f"{ticker}: {value} ({month})")


if __name__ == "__main__":
    main()


# CORRECTED TRAINING DATA — as of 2026-03-31
# This is a separate, illustrative dataset. The original TABLE above stays intact
# so the script continues to reproduce the lab's known answer.
#
# Provenance errors and their corrections:
# - Row 11: missing ticker; quarantined, because its fund cannot be inferred.
# - Row 7: exact duplicate of row 6; removed, retaining the original row number.
# - Rows 3, 8, 10: published after the decision date; excluded from this panel.
#   They are future publications, not necessarily erroneous source records.
# - Row 2: superseded by row 4's February revision, published before the cutoff.
#
# Economic errors under the exercise's assumptions:
# - Rows 1, 4, 9, 12: prices above 100 imply negative zero-coupon yields.
# - Rows 9, 12: CCC is priced above AAA and BBB, reversing the required ordering.
#
# Assumed repairs (not verified source values):
# - Row 1: 101.0 -> 100.0; row 4: 103.0 -> 99.0.
# - Row 9: 110.0 -> 95.0; row 12: 111.0 -> 94.0.
# These choices give nonnegative yields and AAA > BBB > CCC in each month.
# Rows 5 and 6 need no price correction. Publication dates and lineage are kept.
# In real data, quarantine suspect prices until the source confirms a correction;
# passing these checks alone does not establish that an assumed price is true.
#
# Same columns as TABLE: row, ticker, month measured, published on, price.
CORRECTED_ASOF_TABLE = [
    (1, "AAA", "2026-01", "2026-02-10", 100.0),
    (4, "AAA", "2026-02", "2026-03-25", 99.0),
    (5, "BBB", "2026-01", "2026-02-10", 98.0),
    (6, "BBB", "2026-02", "2026-03-10", 97.0),
    (9, "CCC", "2026-01", "2026-02-10", 95.0),
    (12, "CCC", "2026-02", "2026-03-10", 94.0),
]
