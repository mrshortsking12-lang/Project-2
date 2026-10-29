"""Lab 17: compare current FRED observations with an ALFRED vintage.
Run: python -m streamlit run asof_app.py
"""
from datetime import date, datetime, timezone
from io import StringIO
import re
import math

import plotly.graph_objects as go
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

SERIES = {
    "BAA": "Moody's Baa corporate bond yield",
    "FEDFUNDS": "Federal funds rate",
    "DGS10": "10-year Treasury yield",
    "MORTGAGE30US": "30-year mortgage rate",
}


def read_download(url, params):
    """Read one CSV request; vintage columns carry a date suffix."""
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text), na_values=["."])
    if len(frame.columns) != 2:
        raise ValueError("Expected a date column and one value column from FRED.")
    dates = pd.to_datetime(frame.iloc[:, 0], errors="raise")
    values = pd.to_numeric(frame.iloc[:, 1], errors="raise")
    observations = pd.Series(values.to_numpy(), index=dates, name=params["id"])
    observations.index.name = "Date measured"
    observations = observations.dropna().sort_index()
    if observations.index.has_duplicates:
        raise ValueError("The download contains duplicate observation dates.")
    return observations, datetime.now(timezone.utc).isoformat(timespec="seconds")


@st.cache_data(ttl=3600, show_spinner=False)
def download_current(series_id, download_day):
    """Cache today's public FRED download for each series (no API key)."""
    return read_download("https://fred.stlouisfed.org/graph/fredgraph.csv", {"id": series_id})


@st.cache_data(ttl=3600, show_spinner=False)
def download_vintage(series_id, as_of, download_day):
    """Ask ALFRED for the values available on the requested calendar date."""
    observations, fetched_at = read_download(
        "https://alfred.stlouisfed.org/graph/alfredgraph.csv",
        {"id": series_id, "vintage_date": as_of.isoformat()},
    )
    # The vintage parameter selects publication history; this date filter alone
    # would NOT prevent revisions leaking from today's download.
    return observations.loc[observations.index <= pd.Timestamp(as_of)], fetched_at


def audit(current, vintage):
    """Compare full histories, excluding missing values in either snapshot."""
    last_then = None if vintage.empty else vintage.index[-1]
    last_now = None if current.empty else current.index[-1]
    common = current.index.intersection(vintage.index)
    revised = int((current.loc[common] != vintage.loc[common]).sum())
    return {
        "Last measured date known then": last_then,
        "Value known then": None if vintage.empty else float(vintage.iloc[-1]),
        "Last measured date today": last_now,
        "Value today": None if current.empty else float(current.iloc[-1]),
        "Later observations today": len(current) if last_then is None else int((current.index > last_then).sum()),
        "Revised shared observations": revised,
    }


def history_chart(observations, start, end):
    """Keep every observation available while setting only the initial viewport."""
    visible = observations.loc[str(start):str(end)]
    if visible.empty:
        visible = observations
    low, high = float(visible.min()), float(visible.max())
    padding = max((high - low) * 0.05, abs(high) * 0.005, 0.01)
    y_min, y_max = math.floor(low), high + padding
    # WebGL draws the full history without thousands of SVG marks or
    # recomputing nearest-point Voronoi regions on each zoom operation.
    figure = go.Figure(go.Scattergl(
        x=[timestamp.isoformat() for timestamp in observations.index],
        y=observations.tolist(),
        mode="lines", name=observations.name or "Value",
        line={"width": 1.5, "color": "#3b82f6"},
        hovertemplate="%{x|%Y-%m-%d}<br>Value: %{y:,.3~f}<extra></extra>",
    ))
    figure.update_layout(
        height=300, margin={"l": 55, "r": 15, "t": 15, "b": 40},
        paper_bgcolor="#000000", plot_bgcolor="#000000",
        font={"color": "#e5e7eb"},
        hoverlabel={"bgcolor": "#111827", "font_color": "#f9fafb"},
        hovermode="x", hoverdistance=-1, spikedistance=-1,
        dragmode="pan",
        uirevision=f"{observations.name}-{start}-{end}",
        xaxis={
            "title": "Date measured", "range": [str(start), str(end)],
            "minallowed": "1950-01-01", "maxallowed": "2030-12-31",
            "gridcolor": "#262626", "zerolinecolor": "#525252",
            "showspikes": True, "spikemode": "across", "spikesnap": "cursor",
            "spikedash": "dash", "spikecolor": "#64748b", "spikethickness": 1,
        },
        yaxis={"title": "Value (units on FRED series page)",
               "gridcolor": "#262626", "zerolinecolor": "#525252",
               "range": [y_min, y_max], "fixedrange": True},
    )
    return figure



def render_history_chart(figure):
    """Rescale the visible Y range in the browser, without rerunning downloads."""
    script = r"""
    const chart = document.getElementById('{plot_id}');
    const dates = chart.data[0].x.map(value => new Date(value).getTime());
    // Use ordinary arrays in this component so the event handler can scan them.
    const values = chart.data[0].y;
    // Preserve the initial rounded lower bound throughout zoom and pan.
    const fixedYMin = Math.floor(chart.layout.yaxis.range[0]);
    let pending;
    function fitVisible() {
        const range = chart._fullLayout.xaxis.range;
        const left = new Date(range[0]).getTime();
        const right = new Date(range[1]).getTime();
        let low = Infinity, high = -Infinity;
        function include(value) {
            if (Number.isFinite(value)) {
                low = Math.min(low, value);
                high = Math.max(high, value);
            }
        }
        for (let i = 0; i < dates.length; i++) {
            if (dates[i] >= left && dates[i] <= right) include(values[i]);
            // Include line segments crossing the viewport edges, even when
            // zoomed between two observation dates.
            if (i > 0 && dates[i] > dates[i - 1]) {
                for (const edge of [left, right]) {
                    if (dates[i - 1] < edge && edge < dates[i]) {
                        const weight = (edge - dates[i - 1]) / (dates[i] - dates[i - 1]);
                        include(values[i - 1] + weight * (values[i] - values[i - 1]));
                    }
                }
            }
        }
        if (!Number.isFinite(low)) return;
        const padding = Math.max((high - low) * 0.05, Math.abs(high) * 0.005, 0.01);
        Plotly.relayout(chart, {'yaxis.range': [fixedYMin, Math.max(high + padding, fixedYMin + 1)]});
    }
    chart.on('plotly_relayout', event => {
        if (Object.keys(event).some(key => key.startsWith('xaxis.'))) {
            clearTimeout(pending);
            pending = setTimeout(fitVisible, 30);
        }
    });
    fitVisible();
    """
    components.html(
        '<style>html,body{margin:0;background:#000;}</style>' + figure.to_html(
            full_html=False, include_plotlyjs="cdn", post_script=script,
            config={"scrollZoom": True, "displaylogo": False, "responsive": True},
        ),
        height=325,
    )


def main():
    st.set_page_config(page_title="Point-in-Time Rates Audit", layout="wide")
    today = date.today()
    st.title("Point-in-Time Rates Audit")
    st.caption(f"Data from FRED and ALFRED, Federal Reserve Bank of St. Louis, downloaded {today:%Y-%m-%d}; built with AI help, a learning demonstration, not investment advice.")
    with st.sidebar:
        st.header("Series and dates")
        selected = st.multiselect("Series", list(SERIES), default=list(SERIES),
                                  format_func=lambda key: f"{key} — {SERIES[key]}")
        extra = st.text_input("Add a FRED series ID", placeholder="PAYEMS").strip().upper()
        start = st.date_input("Chart start date", date(1990, 1, 1), min_value=date(1950, 1, 1), max_value=date(2030, 12, 30))
        end = st.date_input("Chart end date", date(2030, 12, 31), min_value=start, max_value=date(2030, 12, 31))
        as_of = st.date_input("As known on", today, min_value=date(1776, 1, 1), max_value=today)
        st.caption("Snapshots are cached for one hour. Download timestamps appear below. As-of dates refer to a calendar day, not a trade's intraday time.")
    if extra:
        if re.fullmatch(r"[A-Z0-9_]+", extra):
            selected = list(dict.fromkeys(selected + [extra]))
        else:
            st.error("Use a FRED series ID containing letters, digits, or underscores.")
    rows, snapshots = [], {}
    for series_id in selected:
        st.subheader(f"{series_id} — {SERIES.get(series_id, 'Custom FRED series')}")
        st.markdown(f"[FRED series page](https://fred.stlouisfed.org/series/{series_id})")
        try:
            current, current_time = download_current(series_id, today)
            if current.empty:
                st.info("No current observations available.")
            else:
                render_history_chart(history_chart(current, start, end))
                st.caption("Hover anywhere in the plot for the nearest date and value. Scroll to zoom; drag to pan through the full history. Double-click to reset the date range.")
            vintage, vintage_time = download_vintage(series_id, as_of, today)
            result = audit(current, vintage)
            last = result["Last measured date known then"]
            st.caption(f"Last measured date known on {as_of}: {last:%Y-%m-%d}" if last is not None else f"No observations available in this vintage on {as_of}.")
            st.caption(f"Current CSV downloaded {current_time}; vintage CSV downloaded {vintage_time}.")
            rows.append({"Series": f"https://fred.stlouisfed.org/series/{series_id}", **result})
            snapshots[series_id] = (current, vintage)
        except (requests.RequestException, ValueError, pd.errors.ParserError) as exc:
            st.error(f"{series_id}: download unavailable or invalid: {exc}")
    st.subheader("As-of audit")
    st.caption("Dates are observation dates, not publication dates. Later counts and revisions use full histories, independent of chart start. Revisions compare nonmissing values on shared dates; later observations count dates beyond the vintage's last observation.")
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, column_config={
            "Series": st.column_config.LinkColumn("Series", display_text=r"/series/(.*)$"),
            "Last measured date known then": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Last measured date today": st.column_config.DateColumn(format="YYYY-MM-DD"),
        }, use_container_width=True)
    else:
        st.info("Select a series with available data to see the audit.")
    if "PAYEMS" in snapshots:
        current, vintage = snapshots["PAYEMS"]
        with st.expander("PAYEMS probe: December 2024", expanded=True):
            probe = pd.Timestamp("2024-12-01")
            st.write({"As known then": vintage.get(probe, None), "Today's value": current.get(probe, None)})


if __name__ == "__main__":
    main()
