"""Explore Meridian or uploaded monthly prices: streamlit run class_python/app.py."""

import hashlib
import io

import streamlit as st

from portfolio import (
    CORRELATIONS,
    OBJECTIVE_RETURN,
    SLEEVES,
    estimate_from_csv,
    lowest_risk_mix,
)

st.set_page_config(page_title="Meridian portfolio explorer", layout="wide")
st.title("Meridian portfolio explorer")
st.caption("Built with AI help, a learning demonstration, not investment advice.")

with st.sidebar:
    objective = st.number_input(
        "Objective return (%)", value=OBJECTIVE_RETURN * 100, step=0.1, format="%.2f"
    ) / 100
    reserve_minimum = st.number_input(
        "Reserve minimum (%)", min_value=0.0, max_value=100.0,
        value=3.0, step=1.0, format="%.2f"
    ) / 100
    upload = st.file_uploader("Upload prices.csv", type=["csv"])
    last_36 = st.toggle("Use only the last 36 months", disabled=upload is None)
    st.caption("CSV: date first (YYYY-MM-DD), then one column per ticker; monthly prices, oldest first.")

try:
    if upload is None:
        baseline_sleeves = [dict(sleeve) for sleeve in SLEEVES]
        baseline_correlations = CORRELATIONS
        selected_sleeves = [dict(sleeve) for sleeve in SLEEVES]
        selected_correlations = CORRELATIONS
        source_key = "meridian"
        baseline_label = "Meridian inputs as loaded"
    else:
        data = upload.getvalue()
        source_key = hashlib.sha256(data).hexdigest()
        csv_text = data.decode("utf-8-sig")
        baseline_sleeves, baseline_correlations = estimate_from_csv(io.StringIO(csv_text))
        selected_sleeves, selected_correlations = estimate_from_csv(
            io.StringIO(csv_text), last_36_months=last_36
        )
        baseline_label = "CSV inputs as loaded · all months"
        st.caption("CSV reserve eligibility starts unchecked. Select eligible tickers below. "
                   "The 36-month switch uses up to the last 36 monthly returns.")

    st.subheader("Edit annual expected return estimates and reserve eligibility")
    for i, sleeve in enumerate(selected_sleeves):
        left, right = st.columns([3, 2])
        with left:
            sleeve["expected_return"] = st.number_input(
                f"{sleeve['name']} — expected return estimate (%)",
                value=float(sleeve["expected_return"] * 100), step=0.1, format="%.2f",
                key=f"return_{source_key}_{last_36}_{i}",
            ) / 100
        with right:
            sleeve["reserve_eligible"] = st.checkbox(
                f"{sleeve['name']} — reserve-eligible",
                value=sleeve["reserve_eligible"], key=f"reserve_{source_key}_{i}",
            )

    current = lowest_risk_mix(selected_sleeves, selected_correlations, objective, reserve_minimum)
    baseline = lowest_risk_mix(baseline_sleeves, baseline_correlations, objective, reserve_minimum)

    def show_result(title, result, sleeves):
        st.subheader(title)
        if result is None:
            st.write("no mix meets the objective")
            return
        st.table({"Asset": [sleeve["name"] for sleeve in sleeves],
                  "Weight": [f"{weight:.2%}" for weight in result["weights"]]})
        st.metric("Expected annual return estimate", f"{result['expected_return']:.2%}")
        st.metric("Annual volatility", f"{result['volatility']:.2%}")
        st.metric("Reserve-eligible weight", f"{result['reserve_eligible_weight']:.2%}")

    left, right = st.columns(2)
    with left:
        show_result("Lowest-risk mix · edited inputs", current, selected_sleeves)
    with right:
        show_result(baseline_label, baseline, baseline_sleeves)
    if current is not None and baseline is not None:
        changes = [abs(a - b) * 100 for a, b in zip(current["weights"], baseline["weights"])]
        largest = max(range(len(changes)), key=changes.__getitem__)
        st.metric("Largest weight change (percentage points)", f"{changes[largest]:.2f}",
                  help=selected_sleeves[largest]["name"])
        st.caption(f"Asset: {selected_sleeves[largest]['name']}")
    else:
        st.caption("Largest weight change: unavailable unless both mixes meet the constraints.")
    st.caption("Fully invested, long-only mixes in 5-percentage-point steps. "
               "Both results use the sidebar objective and reserve minimum.")
except (ValueError, TypeError, UnicodeError, OverflowError) as error:
    st.error(str(error))
