
import plotly.express as px
import streamlit as st
import pandas as pd
import re
import concurrent.futures


def plot_line_chart(
    df,
    title="",
    yaxis_label="",
    color_palette=None,
    template="plotly_dark",
    xaxis_label="Date",
    legend_title=None,
    **kwargs
):
    """
    Reusable Plotly line chart for economic data.
    Args:
        df: DataFrame (index as x, columns as series)
        title: Chart title
        yaxis_label: Y-axis label
        color_palette: List of colors (optional)
        template: Plotly template (default plotly_dark)
        xaxis_label: X-axis label (default 'Date')
        legend_title: Legend title (optional)
        kwargs: Passed to px.line
    Returns:
        Plotly Figure
    """
    fig = px.line(
        df,
        labels={"value": yaxis_label, "index": xaxis_label},
        title=title,
        color_discrete_sequence=color_palette,
        template=template,
        **kwargs
    )
    fig.update_layout(
        legend_title_text=legend_title or "",
        xaxis_title=xaxis_label,
        yaxis_title=yaxis_label,
        title_font_size=20,
        legend=dict(font=dict(size=12), bgcolor="#0A1224"),
        margin=dict(l=40, r=20, t=60, b=40),
        font_color="#EAEAEA",
        hoverlabel=dict(bgcolor="#101A33", font_size=12)
    )
    return fig
import streamlit as st
import pandas as pd
import re

def search_series(fred, query, filter=None):
    """
    Search FRED for series matching the query and filter.
    Returns a DataFrame of results.
    """
    return fred.search(query, filter=filter)

@st.cache_data(show_spinner="Fetching FRED series...")
def fetch_series(_fred, series_id, observation_start=None, observation_end=None):
    """
    Fetch a single FRED series as a pandas Series.
    Logs the series_id and date range for debugging.
    """
    # Logging can be handled outside for performance; only print if needed
    # print(f"[fetch_series] series_id={series_id}, start={observation_start}, end={observation_end}")
    result = _fred.get_series(series_id, observation_start=observation_start, observation_end=observation_end)
    # Fastest check for empty result
    if result is None or (hasattr(result, 'empty') and result.empty) or (hasattr(result, '__len__') and not len(result)):
        today = pd.Timestamp.today().normalize()
        fallback_start = (today - pd.Timedelta(days=730)).strftime('%Y-%m-%d')
        fallback_end = today.strftime('%Y-%m-%d')
        fallback_result = _fred.get_series(series_id, observation_start=fallback_start, observation_end=fallback_end)
        if fallback_result is None or (hasattr(fallback_result, 'empty') and fallback_result.empty) or (hasattr(fallback_result, '__len__') and not len(fallback_result)):
            return pd.Series(dtype='float64')
        return fallback_result
    return result

@st.cache_data(show_spinner="Fetching state series data...")
def fetch_state_series_data(df, title_pattern, observation_start, observation_end, _fred=None):
    """
    Given a FRED search DataFrame and a title regex pattern, fetch all matching state series.
    Returns a DataFrame with columns as state names and rows as monthly values.
    Handles duplicates, drops all-NaN columns, and shows a spinner while loading.
    """
    # Compile pattern once
    pat = re.compile(title_pattern)
    # Vectorized filter for matching titles
    state_rows = df['title'].str.match(pat)
    df = df[state_rows]
    # Extract state names efficiently
    id_to_state = dict(zip(df.index, df['title'].str.extract(pat)[0].fillna(df['title'])))

    def fetch_one(myid):
        try:
            series = _fred.get_series(myid, observation_start=observation_start, observation_end=observation_end)
            if hasattr(series, 'to_frame'):
                return series.to_frame(name=myid)
            return pd.DataFrame(series)
        except Exception:
            return None

    all_results = []
    with st.spinner("Fetching state series data (parallel)..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            futures = {executor.submit(fetch_one, myid): myid for myid in df.index}
            for fut in concurrent.futures.as_completed(futures):
                res = fut.result()
                if res is not None:
                    all_results.append(res)
    if all_results:
        result_df = pd.concat(all_results, axis=1, copy=False)
        # Rename columns to state names, ensure uniqueness
        seen = set()
        new_cols = []
        for c in result_df.columns:
            state = id_to_state.get(c, c)
            if state in seen:
                state = f"{state} ({c})"
            seen.add(state)
            new_cols.append(state)
        result_df.columns = new_cols
        # Drop all-NaN columns efficiently
        result_df = result_df.dropna(axis=1, how='all')
    else:
        result_df = pd.DataFrame()
    return result_df
@st.cache_data(show_spinner="Reading uploaded CSV", max_entries=5)
def load_csv(file):
    """
    Load a CSV file into a pandas DataFrame.
    """
    return pd.read_csv(file)
