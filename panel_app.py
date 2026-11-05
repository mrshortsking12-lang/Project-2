"""Lab 19. Run: .venv/bin/python -m streamlit run class_python/panel_app.py"""
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd
import requests
import streamlit as st
from lab18_chart import chart_html
from valuation_panel import render_valuation
from panel_view import render_panel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/skills/buffett-edgar/scripts'))
from edgar_facts import LABELS, display, load_report, transcript, unsupported_numbers

st.set_page_config(page_title='Lab 19 — Legend panel', layout='wide')
st.title('Lab 19 — Legend panel')
st.caption('Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice.')
st.caption('Buffett-, Cathie Wood- and Burry-inspired educational interpretations. Code computes the shared facts and checks; each saved AI memo supplies its own judgment.')


@st.cache_data(ttl=21600, max_entries=32, show_spinner=False)
def cached_history_report(ticker):
    return load_report(ticker, ROOT / 'lab18/cache')


with st.sidebar:
    st.header('Company')
    st.caption('Project 2 fund: SMH. Largest holding for this run: NVDA (November 4, 2026).')
    st.markdown('[VanEck holdings](https://www.vaneck.com/us/en/investments/semiconductor-etf-smh/holdings/)')
    if st.button('Load COST known-answer check'):
        st.session_state['active_ticker'] = 'COST'
        st.session_state['company_ticker'] = 'COST'
    if st.button('Load SMH company: NVDA'):
        st.session_state['active_ticker'] = 'NVDA'
        st.session_state['company_ticker'] = 'NVDA'
    st.session_state.setdefault('company_ticker', 'COST')
    with st.form('company'):
        requested = st.text_input('Company ticker (or SMH)', max_chars=15, key='company_ticker')
        submitted = st.form_submit_button('Load company')
    if submitted:
        st.session_state['active_ticker'] = 'NVDA' if requested.strip().upper() == 'SMH' else requested.strip().upper()
    ticker = st.session_state.get('active_ticker', 'COST')
    refresh = st.button('Refresh SEC downloads')
    st.caption('10-K only. Latest five fiscal years. Dollar amounts are in USD millions.')
    st.markdown('[SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)')
    st.markdown('[How Codex skills work](https://developers.openai.com/codex/skills)')

try:
    with st.spinner('Loading annual SEC facts…'):
        if refresh:
            report = load_report(ticker, ROOT / 'lab18/cache', refresh=True)
            cached_history_report.clear()
        else:
            report = cached_history_report(ticker)
except (requests.RequestException, ValueError, KeyError) as exc:
    st.error(f'Cannot load {ticker}: {exc}')
    st.stop()

st.subheader(f"{report['ticker']} · {report['company']}")
if report['ticker'] == 'COST':
    st.info('Known-answer check: COST. Lab 19 asks you to open COST first. For your Project 2 company, use “Load SMH company: NVDA” in the sidebar.')
elif report['ticker'] == 'NVDA':
    st.info('Your Project 2 fund is SMH; this analysis is of its largest holding, NVDA, using the November 4, 2026 holdings snapshot. The graph shows NVDA’s owner earnings and net income, not SMH’s fund price.')
st.caption(f"Graph: {report['ticker']} company financials · owner earnings and net income · USD millions")
st.caption(f"SEC data downloaded {report['downloaded_at']}. Current restated history, not a point-in-time backtest dataset.")
st.markdown(f"[SEC company facts JSON]({report['source']}) · [SEC filings](https://www.sec.gov/edgar/browse/?CIK={report['cik']}&owner=exclude)")
if len(report['rows']) < 5:
    st.warning('Fewer than five fiscal years are available. The five-year checks are not known.')

history = report.get('history_rows', report['rows'])
try:
    st.iframe(chart_html(history), height=375,
              alt='Owner earnings and net income over all available annual SEC history, with bounded date zoom and automatic Y limits')
    st.caption(f"All available annual SEC history: {history[0]['fiscal_year_end']} to {history[-1]['fiscal_year_end']}. Scroll to zoom, drag to pan, double-click to reset. The Y ceiling adds 10% to the highest visible value, then rounds to the nearest 1,000 USD millions. The audit below uses only the latest five fiscal years.")
except ValueError as exc:
    st.info(str(exc))
missing_history = [r for r in history if r['owner_earnings']['value'] is None]
if missing_history:
    missing_years = ', '.join(r['fiscal_year_end'][:4] for r in missing_history)
    st.info(f'Owner earnings are not found for fiscal years {missing_years}: an input is missing under the lab-required tags. The line breaks at these years; missing values are not zero or estimates.')
    with st.expander('Why historical owner earnings are missing'):
        st.caption('Only the lab-permitted tags qualify. For example, a continuing-operations cash-flow tag is not substituted for the required total operating-cash-flow tag.')
        st.dataframe(pd.DataFrame([
            {'Fiscal year end': r['fiscal_year_end'],
             'Operating cash flow': display('operating_cash_flow', r['operating_cash_flow']),
             'Capital spending': display('capital_spending', r['capital_spending']),
             'Owner earnings': display('owner_earnings', r['owner_earnings'])}
            for r in missing_history
        ]), hide_index=True, alt='Historical years with missing inputs to owner earnings')

render_panel(report, ROOT)

st.divider()
st.subheader('Annual facts and computed values')
table = [{'Fiscal year end': r['fiscal_year_end'], **{label: display(metric, r[metric]) for metric, label in LABELS.items()}}
         for r in report['rows']]
st.dataframe(pd.DataFrame(table), hide_index=True, width='stretch', alt='Annual financial facts in USD millions and ROE in percent')
st.caption('ROE = net income ÷ year-end equity. Owner earnings = operating cash flow − total capital spending, the lab proxy. Missing facts are never estimated.')
st.subheader('Checks computed by code')
st.table(pd.DataFrame([{'Check': k, 'Result': v} for k, v in report['checks'].items()]),
         alt='The three Buffett checks and their computed results')
with st.expander('XBRL tags, filing dates, periods and calculation lineage'):
    lineage = []
    for row in report['rows']:
        for metric, label in LABELS.items():
            cell = row[metric]
            lineage.append({'Fiscal year end': row['fiscal_year_end'], 'Metric': label,
                            'Value': display(metric, cell), 'XBRL tag or formula': cell['tag'],
                            'Filed': cell.get('filed', 'derived or not found'),
                            'Period start': cell.get('start', 'instant or derived'),
                            'Accession': cell.get('accession', '')})
    st.dataframe(pd.DataFrame(lineage), hide_index=True, width='stretch', alt='Source tags and filing provenance for every financial value')
    st.code(transcript(report), language='text')
st.download_button('Download computed facts', transcript(report), file_name=f'{ticker}_facts.txt')

st.subheader('Saved AI memo')
memo_dir = ROOT / 'lab18/memos'
memo_dir.mkdir(parents=True, exist_ok=True)
memo_path = memo_dir / f'{ticker}.md'
meta_path = memo_dir / f'{ticker}.meta.json'
source_memo = memo_path.read_text() if memo_path.exists() else ''
if not source_memo:
    st.info(f'No AI memo saved for {ticker}. Ask Codex to use $buffett-edgar on {ticker}, then reload this page. You may also paste the memo below. The app does not replace model judgment with a coded verdict.')
if meta_path.exists() and json.loads(meta_path.read_text()).get('facts_fingerprint') != report['fingerprint']:
    st.warning('The financial facts have changed since this memo was saved. Review it against the current table.')
editor_key = 'memo_' + ticker + '_' + hashlib.sha256(source_memo.encode()).hexdigest()[:12]
memo = st.text_area('Review or edit the memo', value=source_memo, height=260, key=editor_key)
flags = unsupported_numbers(memo, report)
if flags:
    st.error(f'{len(flags)} unsupported number occurrence(s). These numbers were not printed as financial facts or fiscal-year labels.')
    st.dataframe(pd.DataFrame(flags), hide_index=True, width='stretch', alt='Unsupported memo numbers with their line numbers and context')
elif memo.strip():
    st.success('Every numeric token matches a printed value or fiscal-year label.')
st.caption('The scanner compares exact printed values, allowing comma and decimal formatting differences. Percentages are separate from dollar amounts. It checks each occurrence; matching a token does not establish that the memo used the correct metric, year or units. Review those yourself.')
if memo.strip():
    st.markdown(memo)
if st.button('Save memo', disabled=not memo.strip()):
    memo_path.write_text(memo)
    meta_path.write_text(json.dumps({'facts_fingerprint': report['fingerprint']}, indent=2))
    st.success(f'Saved lab18/memos/{ticker}.md')
st.download_button('Download memo', memo, file_name=f'{ticker}_memo.md', disabled=not memo.strip())

st.subheader('Your trust decision')
decision_path = ROOT / 'lab18' / f'{ticker}_decision.md'
decision_key = f'decision_{ticker}'


def save_trust_decision(path, key):
    text = st.session_state.get(key, '').strip()
    if text:
        temporary = path.with_suffix('.md.tmp')
        temporary.write_text(text + '\n')
        temporary.replace(path)


decision = st.text_area(
    'Do you trust this verdict, and why? Write your own one-line answer.',
    value=decision_path.read_text() if decision_path.exists() else '',
    key=decision_key, on_change=save_trust_decision, args=(decision_path, decision_key),
)
st.caption('Your decision saves automatically when you leave the field. It reloads from its file after a refresh or app restart. You can also save immediately below.')
if st.button('Save my decision', disabled=not decision.strip()):
    save_trust_decision(decision_path, decision_key)
    st.success(f'Saved lab18/{ticker}_decision.md')
if decision_path.exists():
    st.caption(f'Saved on this computer: lab18/{ticker}_decision.md')


st.divider()
render_valuation(report, ROOT)
