import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from fredapi import Fred
from dotenv import load_dotenv
import kaleido
import plotly.io as pio
import os
import time
from economic_chatbot import render_chatbot

from fred_utils import search_series, fetch_series, fetch_state_series_data, load_csv
from plotly.subplots import make_subplots

# --- Streamlit Theme Config & Custom CSS for Dark Blue Theme ---
st.set_page_config(
    page_title="US Economic Analysis",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)
st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #0A1224 !important; /* dark navy */
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #1E90FF !important; /* primary blue */
        color: #EAEAEA !important;
        border-radius: 8px;
        border: none;
        padding: 0.5em 1.5em;
        font-weight: 600;
        font-size: 1.1rem;
        transition: background 0.2s;
        box-shadow: 0 0 8px #00BFFF55;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #00BFFF !important; /* neon blue accent */
        color: #EAEAEA !important;
        box-shadow: 0 0 16px #00BFFF99;
    }
    section[data-testid="stSidebar"] {
        background-color: #101A33 !important;
    }
    section[data-testid="stSidebar"] .css-10trblm, 
    section[data-testid="stSidebar"] .css-1v3fvcr,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #EAEAEA !important;
    }
    .stMarkdown, .stText, .stHeader, .stSubheader, .stDataFrame, .stMetric, .stCaption, .stExpander, .stRadio, .stSelectbox, .stFileUploader {
        color: #EAEAEA !important;
    }
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        color: #1E90FF;
        letter-spacing: 1px;
        text-shadow: 0 0 12px #00BFFF88;
    }
    .hero-subtitle {
        font-size: 1.6rem;
        font-weight: 400;
        text-align: center;
        margin-bottom: 2.5rem;
        color: #00BFFF;
        text-shadow: 0 0 8px #1E90FF55;
    }
    .stDataFrame, .stTable, .stMetric {
        background-color: #101A33 !important;
        color: #EAEAEA !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Matplotlib Dark Blue Style ---
plt.style.use('dark_background')
plt.rcParams['axes.facecolor'] = '#0A1224'
plt.rcParams['figure.facecolor'] = '#0A1224'
plt.rcParams['axes.edgecolor'] = '#EAEAEA'
plt.rcParams['axes.labelcolor'] = '#EAEAEA'
plt.rcParams['xtick.color'] = '#EAEAEA'
plt.rcParams['ytick.color'] = '#EAEAEA'
plt.rcParams['text.color'] = '#EAEAEA'
plt.rcParams['axes.titlecolor'] = '#1E90FF'
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=[
    '#00BFFF', '#1E90FF', "#0C3D3E", "#B724D1", "#BA515A", '#4682B4', "#E04040", "#EFFB07", "#50E723", "#646718"
])

# --- Plotly Dark Blue Template ---
PLOTLY_TEMPLATE = "plotly_dark"
COLOR_PALETTE = [
    "#1abc9c",  # teal
    "#e67e22",  # orange
    "#2980b9",  # blue
    "#9b59b6",  # purple
    "#e74c3c",  # red
    "#f1c40f",  # yellow
    "#2ecc71",  # green
    "#34495e",  # dark blue-gray
]


# --- Load API key safely from environment variable or Streamlit secrets ---
load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY") or st.secrets.get("FRED_API_KEY", None)
if not FRED_API_KEY:
    st.error("FRED API key not found. Please set it in your environment variables or Streamlit secrets.")
    st.stop()
fred = Fred(api_key=FRED_API_KEY)

# --- Pandas display options ---
pd.set_option('display.float_format', '{:.2f}'.format)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 1000)

# --- Hero Title and Subtitle ---
st.markdown(
    """
    <div class="hero-title">📊 US Economic Dashboard</div>
    <div class="hero-subtitle">Real-time economic insights powered by FRED API</div>
    """,
    unsafe_allow_html=True
)


# --- Use utility functions from fred_utils.py ---
def get_fred_search(query, filter=None):
    return search_series(fred, query, filter=filter)



# --- Caching FRED API calls for performance ---
@st.cache_data(show_spinner="Searching FRED...")
def cached_get_fred_search(query, filter=None):
    return fred.search(query, filter=filter)




# --- fetch_state_series_data is now in fred_utils.py ---

# --- Prepare state mappings BEFORE using them in sidebar ---

unemp_df = get_fred_search('unemployment rate state', filter=('frequency', 'Monthly'))
unemp_df = unemp_df.query('seasonal_adjustment == "Seasonally Adjusted" and units == "Percent"')
unemp_df = unemp_df.loc[unemp_df['title'].str.contains('Unemployment Rate')]

part_df = get_fred_search('participation rate state', filter=('frequency', 'Monthly'))
part_df = part_df.query('seasonal_adjustment == "Seasonally Adjusted" and units == "Percent"')
part_df = part_df.loc[part_df['title'].str.contains('Labor Force Participation Rate')]

# For state selection, just use unique state names from titles
def extract_state_names(df, pattern, replace_str):
    import re
    pat = re.compile(pattern)
    return sorted({pat.match(title).group(1) for title in df['title'] if pat.match(title)})

unemp_states_list = extract_state_names(unemp_df, r'^Unemployment Rate in ([A-Za-z .\-]+)$', 'Unemployment Rate in ')
part_states_list = extract_state_names(part_df, r'^Labor Force Participation Rate for ([A-Za-z .\-]+)$', 'Labor Force Participation Rate for ')
common_states = sorted(set(unemp_states_list) & set(part_states_list))
all_states = sorted(set(unemp_states_list) | set(part_states_list))
state_options = ["All States"] + all_states

# --- Sidebar for View and Filters ---
st.sidebar.title("Dashboard Controls")

tabs = [
    "S&P 500", "Unemployment", "Participation", "Unemployment by State",
    "Participation by State", "State Comparison", "📂 Upload Your CSV", "🤖 Economic Chatbot"
]

# Use session state to remember last selected view for user experience and avoid undefined 'view'
if 'view' not in st.session_state:
    st.session_state['view'] = tabs[0]
view = st.sidebar.radio(
    "Select View",
    tabs,
    index=tabs.index(st.session_state['view']) if st.session_state['view'] in tabs else 0,
    key='view'
)

year_options = list(range(2010, pd.Timestamp.today().year + 1))
start_year = st.sidebar.selectbox("Start Year", year_options, index=year_options.index(2020))
end_year = st.sidebar.selectbox("End Year", year_options, index=year_options.index(pd.Timestamp.today().year))

selected_state = st.sidebar.selectbox("Select State", state_options)

# --- Validate Year Selection ---
if start_year > end_year:
    st.sidebar.error("Start Year must be less than or equal to End Year.")
    st.stop()

# --- Main Content ---
if view == "S&P 500":
    st.header("📈 S&P 500 Index")
    st.info("This chart shows the historical S&P 500 index values. Data is sourced from FRED and updated daily. Use the controls below to filter by year, chart type, and add moving averages.")

    # --- Fetch and filter S&P 500 data by year range ---
    sp500 = fetch_series(fred, 'SP500')
    if sp500.empty:
        st.warning("No data available for the selected state and year range.")
    else:
        # Filter by selected year range
        start_date = f"{start_year}-01-01"
        end_date = f"{end_year}-12-31"
        sp500 = sp500[(sp500.index >= start_date) & (sp500.index <= end_date)]
        sp500 = sp500.dropna()

        if sp500.empty:
            st.warning("No S&P 500 data available for the selected year range.")
        else:
            # --- Controls ---
            col1, col2, col3 = st.columns([1,1,2])
            chart_type = col1.selectbox("Chart Type", ["Line Chart", "Bar Chart"], index=0)
            change_mode = col2.radio("Display Mode", ["Absolute", "% Change"], horizontal=True)
            export_fmt = col3.selectbox("Export Format", ["CSV", "Excel"], index=0)

            # --- Comparison Dropdown (example: add CPI or other index) ---
            compare_options = {
                "None": None,
                "CPI (Consumer Price Index)": "CPIAUCSL",
                "Unemployment Rate": "UNRATE"
            }
            compare_label = st.selectbox("Comparison Series (optional)", list(compare_options.keys()), index=0)
            compare_series_id = compare_options[compare_label]



            # --- Prepare DataFrame (advanced optimization) ---
            # Use @st.cache_data to cache the entire S&P 500 DataFrame preparation for the selected range and comparison
            @st.cache_data(show_spinner="Preparing S&P 500 data...", max_entries=10)
            def prepare_sp500_df(sp500, compare_series_id, compare_label, start_date, end_date, change_mode):
                # Use numpy for fast rolling means
                import numpy as np
                df = sp500.reset_index()
                df.rename(columns={df.columns[0]: 'Date', df.columns[1]: 'S&P 500'}, inplace=True)
                arr = df['S&P 500'].to_numpy()
                # Fast rolling means with numpy (valid for large data)
                def fast_rolling(arr, window):
                    if len(arr) < window:
                        return np.convolve(arr, np.ones(len(arr))/len(arr), mode='same')
                    return np.convolve(arr, np.ones(window)/window, mode='same')
                df['30D MA'] = fast_rolling(arr, 30)
                df['90D MA'] = fast_rolling(arr, 90)
                # Fetch and merge comparison series only if needed
                if compare_series_id:
                    compare_series = fetch_series(fred, compare_series_id, df['Date'].min(), df['Date'].max())
                    if not compare_series.empty:
                        compare_df = compare_series.reset_index()
                        compare_df.rename(columns={compare_df.columns[0]: 'Date', compare_df.columns[1]: compare_label}, inplace=True)
                        df = pd.merge(df, compare_df, on='Date', how='left')
                # % Change if selected (vectorized, in-place)
                if change_mode == "% Change":
                    for col in ['S&P 500', '30D MA', '90D MA']:
                        df[col] = df[col].pct_change() * 100
                    if compare_series_id and compare_label in df.columns:
                        df[compare_label] = df[compare_label].pct_change() * 100
                return df

            sp500_df = prepare_sp500_df(sp500, compare_series_id, compare_label, start_date, end_date, change_mode)

            # --- Metrics ---
            min_val = sp500_df["S&P 500"].min()
            max_val = sp500_df["S&P 500"].max()
            mean_val = sp500_df["S&P 500"].mean()
            latest_val = sp500_df["S&P 500"].iloc[-1]
            prev_val = sp500_df["S&P 500"].iloc[-2] if len(sp500_df) > 1 else latest_val
            change_val = latest_val - prev_val

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Latest", f"{latest_val:,.2f}", f"{change_val:+.2f}")
            m2.metric("Min", f"{min_val:,.2f}")
            m3.metric("Max", f"{max_val:,.2f}")
            m4.metric("Mean", f"{mean_val:,.2f}")

            # --- Plotly Chart ---
            import plotly.graph_objects as go
            fig = go.Figure()
            hovertemplate = '<b>Date</b>: %{x|%Y-%m-%d}<br><b>S&P 500</b>: %{y:,.2f}<extra></extra>'
            # S&P 500 main line/bar
            if chart_type == "Line Chart":
                fig.add_trace(go.Scatter(
                    x=sp500_df['Date'], y=sp500_df['S&P 500'],
                    mode='lines', name='S&P 500',
                    line=dict(color=COLOR_PALETTE[0], width=2, shape='spline', smoothing=1.3),
                    hovertemplate=hovertemplate,
                    yaxis='y1',
                ))
                # 30D MA
                fig.add_trace(go.Scatter(
                    x=sp500_df['Date'], y=sp500_df['30D MA'],
                    mode='lines', name='30-Day MA',
                    line=dict(color=COLOR_PALETTE[1], width=2, dash='dot', shape='spline', smoothing=1.3),
                    hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>30D MA</b>: %{y:,.2f}<extra></extra>',
                    yaxis='y1',
                    visible=True
                ))
                # 90D MA
                fig.add_trace(go.Scatter(
                    x=sp500_df['Date'], y=sp500_df['90D MA'],
                    mode='lines', name='90-Day MA',
                    line=dict(color=COLOR_PALETTE[2], width=2, dash='dash', shape='spline', smoothing=1.3),
                    hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>90D MA</b>: %{y:,.2f}<extra></extra>',
                    yaxis='y1',
                    visible=True
                ))
            else:
                fig.add_trace(go.Bar(
                    x=sp500_df['Date'], y=sp500_df['S&P 500'],
                    name='S&P 500', marker_color=COLOR_PALETTE[0],
                    hovertemplate=hovertemplate,
                    yaxis='y1',
                ))

            # Add comparison series on secondary y-axis if selected
            if compare_series_id and compare_label in sp500_df.columns:
                fig.add_trace(go.Scatter(
                    x=sp500_df['Date'], y=sp500_df[compare_label],
                    mode='lines', name=compare_label,
                    line=dict(color='#FFA500', width=2, shape='spline', smoothing=1.3),
                    hovertemplate=f'<b>Date</b>: %{{x|%Y-%m-%d}}<br><b>{compare_label}</b>: %{{y:,.2f}}<extra></extra>',
                    yaxis='y2',
                    visible=True
                ))

            # Layout for dual y-axis
            yaxis2_title = compare_label if compare_series_id else None
            fig.update_layout(
                title=f"S&P 500 Index ({start_year}–{end_year})" + (f" vs {compare_label}" if compare_series_id else ""),
                xaxis=dict(title="Date", showgrid=True, gridcolor="#222A44", zeroline=False),
                yaxis=dict(title="S&P 500" + (" (% Change)" if change_mode == "% Change" else ""), showgrid=True, gridcolor="#222A44", zeroline=False, color="#EAEAEA"),
                yaxis2=dict(
                    title=yaxis2_title,
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    zeroline=False,
                    color="#FFA500"
                ) if compare_series_id else {},
                legend=dict(
                    title="Legend",
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor="#101A33",
                    bordercolor="#1E90FF",
                    borderwidth=1,
                    font=dict(color="#EAEAEA", size=14)
                ),
                hovermode="x unified",
                margin=dict(l=20, r=20, t=60, b=40),
                plot_bgcolor="#0A1224",
                paper_bgcolor="#0A1224",
                font=dict(color="#EAEAEA"),
            )
            fig.update_xaxes(rangeslider_visible=True, showline=True, linewidth=1, linecolor="#EAEAEA")
            fig.update_yaxes(showline=True, linewidth=1, linecolor="#EAEAEA")
            st.plotly_chart(fig, use_container_width=True)

            # --- Facet-style subplot grid ---
            st.markdown("---")
            st.subheader("Facet Grid: S&P 500 vs Comparison Series by Year")
            facet_enabled = compare_series_id is not None and compare_label in sp500_df.columns
            # Compute 'Year' column only once, before facet logic
            if 'Year' not in sp500_df.columns:
                sp500_df['Year'] = pd.to_datetime(sp500_df['Date']).dt.year
            facet_col = 'Year'
            facet_values = sorted(sp500_df[facet_col].unique())
            ncols = 4
            nrows = (len(facet_values) + ncols - 1) // ncols
            subplot_titles = [f"{v}" for v in facet_values]
            # Precompute facet DataFrames for each year to avoid repeated filtering
            # Use groupby for faster slicing
            facet_dfs = {year: df for year, df in sp500_df.groupby(facet_col)}
            if facet_enabled:
                # Only apply this improved layout for S&P 500 vs CPI
                if compare_label == "CPI (Consumer Price Index)":
                    # Flexible facet grid: no fixed width/height, improved axis visibility, controlled spacing
                    fig_grid = make_subplots(
                        rows=nrows, cols=ncols,
                        subplot_titles=subplot_titles,
                        shared_xaxes=True, shared_yaxes=True,
                        vertical_spacing=0.1, horizontal_spacing=0.05
                    )
                    y_min = sp500_df['S&P 500'].min()
                    y_max = sp500_df['S&P 500'].max()
                    for idx, val in enumerate(facet_values):
                        row = idx // ncols + 1
                        col = idx % ncols + 1
                        df_facet = facet_dfs[val]
                        # S&P 500 line (only if data exists)
                        if not df_facet['S&P 500'].isnull().all():
                            fig_grid.add_trace(
                                go.Scatter(
                                    x=df_facet['Date'], y=df_facet['S&P 500'],
                                    mode='lines', name='S&P 500',
                                    line=dict(color='#1abc9c', width=2),
                                    legendgroup='sp500',
                                    showlegend=(idx==0),
                                    hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>S&P 500</b>: %{y:,.2f}<extra></extra>',
                                ), row=row, col=col
                            )
                        # CPI line (only if valid data exists)
                        if compare_label in df_facet.columns and df_facet[compare_label].notnull().sum() > 0:
                            fig_grid.add_trace(
                                go.Scatter(
                                    x=df_facet['Date'], y=df_facet[compare_label],
                                    mode='lines', name='CPI',
                                    line=dict(color='#f39c12', width=2),
                                    legendgroup='cpi',
                                    showlegend=(idx==0),
                                    hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>CPI</b>: %{y:,.2f}<extra></extra>',
                                ), row=row, col=col
                            )
                        # Only show y-axis label on first column
                        if col == 1:
                            fig_grid.update_yaxes(title_text="S&P 500", row=row, col=col)
                        else:
                            fig_grid.update_yaxes(title_text=None, row=row, col=col)
                        # Only show x-axis label on bottom row
                        if row == nrows:
                            fig_grid.update_xaxes(title_text="Date", row=row, col=col)
                        else:
                            fig_grid.update_xaxes(title_text=None, row=row, col=col)
                    # Hide x-tick labels except for bottom row, y-tick labels except for leftmost
                    for i in range(1, nrows+1):
                        for j in range(1, ncols+1):
                            if i != nrows:
                                fig_grid.update_xaxes(showticklabels=False, row=i, col=j)
                            if j != 1:
                                fig_grid.update_yaxes(showticklabels=False, row=i, col=j)
                            fig_grid.update_yaxes(range=[y_min, y_max], row=i, col=j)
                    # Enhance subplot titles
                    for i, title in enumerate(fig_grid['layout']['annotations']):
                        title['font'] = dict(size=15, color="#EAEAEA", family="Arial Black")
                    fig_grid.update_yaxes(showline=True, linewidth=1, linecolor="#EAEAEA", zeroline=False, gridcolor="#222A44")
                    fig_grid.update_xaxes(showline=True, linewidth=1, linecolor="#EAEAEA", zeroline=False, gridcolor="#222A44")
                    fig_grid.update_layout(
                        template="plotly_dark",
                        # No fixed height/width for flexible sizing
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            x=0.5, y=-0.2,
                            xanchor="center", yanchor="top",
                            bgcolor="#101A33",
                            bordercolor="#1E90FF",
                            borderwidth=1,
                            font=dict(color="#EAEAEA", size=14)
                        ),
                        plot_bgcolor="#0A1224",
                        paper_bgcolor="#0A1224",
                        font=dict(color="#EAEAEA"),
                        margin=dict(l=30, r=30, t=70, b=90),
                        title_text=f"S&P 500 vs CPI by Year",
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig_grid, use_container_width=True)
                else:
                    # fallback to previous layout for other comparisons
                    fig_grid = make_subplots(
                        rows=nrows, cols=ncols, subplot_titles=subplot_titles,
                        shared_xaxes=True, shared_yaxes=True,
                        vertical_spacing=0.1, horizontal_spacing=0.07
                    )
                    y_min = sp500_df['S&P 500'].min()
                    y_max = sp500_df['S&P 500'].max()
                    for idx, val in enumerate(facet_values):
                        row = idx // ncols + 1
                        col = idx % ncols + 1
                        df_facet = facet_dfs[val]
                        fig_grid.add_trace(
                            go.Scatter(
                                x=df_facet['Date'], y=df_facet['S&P 500'],
                                mode='lines', name='S&P 500',
                                line=dict(color=COLOR_PALETTE[0], width=2, shape='spline', smoothing=1.2),
                                showlegend=(idx==0),
                                hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>S&P 500</b>: %{y:,.2f}<extra></extra>',
                            ), row=row, col=col
                        )
                        fig_grid.add_trace(
                            go.Scatter(
                                x=df_facet['Date'], y=df_facet[compare_label],
                                mode='lines', name=compare_label,
                                line=dict(color='#FFA500', width=2, shape='spline', smoothing=1.2),
                                showlegend=(idx==0),
                                hovertemplate=f'<b>Date</b>: %{{x|%Y-%m-%d}}<br><b>{compare_label}</b>: %{{y:,.2f}}<extra></extra>',
                            ), row=row, col=col
                        )
                        if col == 1:
                            fig_grid.update_yaxes(title_text="S&P 500", row=row, col=col)
                        if row == nrows:
                            fig_grid.update_xaxes(title_text="Date", row=row, col=col)
                    for i in range(1, nrows+1):
                        for j in range(1, ncols+1):
                            if i != nrows:
                                fig_grid.update_xaxes(showticklabels=False, row=i, col=j)
                            if j != 1:
                                fig_grid.update_yaxes(showticklabels=False, row=i, col=j)
                            fig_grid.update_yaxes(range=[y_min, y_max], row=i, col=j)
                    for i, title in enumerate(fig_grid['layout']['annotations']):
                        title['font'] = dict(size=15, color="#EAEAEA", family="Arial Black")
                    fig_grid.update_yaxes(showline=True, linewidth=1, linecolor="#EAEAEA", zeroline=False, gridcolor="#222A44")
                    fig_grid.update_xaxes(showline=True, linewidth=1, linecolor="#EAEAEA", zeroline=False, gridcolor="#222A44")
                    fig_grid.update_layout(
                        template="plotly_dark",
                        height=320*nrows,
                        width=340*ncols,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            x=0.5, y=-0.2,
                            xanchor="center", yanchor="top",
                            bgcolor="#101A33",
                            bordercolor="#1E90FF",
                            borderwidth=1,
                            font=dict(color="#EAEAEA", size=14)
                        ),
                        plot_bgcolor="#0A1224",
                        paper_bgcolor="#0A1224",
                        font=dict(color="#EAEAEA"),
                        margin=dict(l=30, r=30, t=70, b=90),
                        title_text=f"S&P 500 vs {compare_label} by Year",
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig_grid, use_container_width=True)
            else:
                st.info("Select a comparison series to enable facet grid.")

            # --- Export Buttons ---
            with st.expander("Show raw data & export"):
                # --- Show raw data & export (dynamically include comparison) ---
                display_cols = ['Date', 'S&P 500', '30D MA', '90D MA']
                if compare_label in sp500_df.columns:
                    display_cols.append(compare_label)
                st.dataframe(sp500_df[display_cols])

                if export_fmt == "CSV":
                    csv = sp500_df[display_cols].to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f'sp500_{start_year}_{end_year}.csv',
                        mime='text/csv'
                    )
                elif export_fmt == "Excel":
                    try:
                        import openpyxl
                        import io
                        excel_buffer = io.BytesIO()
                        sp500_df[display_cols].to_excel(excel_buffer, index=False)
                        st.download_button(
                            label="Download Excel",
                            data=excel_buffer.getvalue(),
                            file_name=f'sp500_{start_year}_{end_year}.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
                    except ImportError:
                        st.warning("Excel export requires openpyxl. Install it with: pip install openpyxl")
                        if st.button("Show Installation Command"):
                            st.code("pip install openpyxl")
                elif export_fmt == "PNG":
                    try:
                        import kaleido
                        import plotly.io as pio
                        png_bytes = fig.to_image(format="png", engine="kaleido")
                        st.download_button(
                            label="Download Chart as PNG",
                            data=png_bytes,
                            file_name=f'sp500_{start_year}_{end_year}.png',
                            mime='image/png'
                        )
                    except Exception as e:
                        st.warning(f"PNG export failed: {e}. Please ensure 'kaleido' is installed.")

elif view == "Unemployment":
    st.header("📉 Unemployment Rate by State")
    st.info("Monthly unemployment rates by US state. Hover for details. Data is seasonally adjusted.")


    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    import re
    state_pattern = r'^Unemployment Rate in ([A-Za-z .\-]+)$'
    unemp_df = cached_get_fred_search('unemployment rate state', filter=('frequency', 'Monthly'))
    unemp_df = unemp_df.query('seasonal_adjustment == "Seasonally Adjusted" and units == "Percent"')

    # --- Advanced optimization: cache all DataFrame prep and trendlines ---
    @st.cache_data(show_spinner="Preparing unemployment data...", max_entries=10)
    def prepare_unemployment_states(unemp_df, state_pattern, start_date, end_date, _fred, selected_state):
        import numpy as np
        uemp_states = fetch_state_series_data(
            unemp_df,
            state_pattern,
            start_date,
            end_date,
            fred
        )
        show_states = uemp_states.copy()
        show_us_avg = False
        if selected_state != "All States" and not uemp_states.empty:
            if selected_state in uemp_states.columns:
                show_states = uemp_states[[selected_state]]
            else:
                show_states = pd.DataFrame()  # No data for this state
        elif selected_state == "All States" and not uemp_states.empty:
            show_states["US Average"] = show_states.mean(axis=1)
            show_us_avg = True
        # Fast rolling mean with numpy for trendlines
        def fast_rolling(arr, window):
            if len(arr) < window:
                return np.convolve(arr, np.ones(len(arr))/len(arr), mode='same')
            return np.convolve(arr, np.ones(window)/window, mode='same')
        trendlines = {}
        for col in show_states.columns:
            arr = show_states[col].to_numpy()
            trend = fast_rolling(arr, 12)
            # Pad to match index length if needed
            if len(trend) < len(show_states):
                pad = np.full(len(show_states)-len(trend), np.nan)
                trend = np.concatenate([trend, pad])
            trendlines[col] = trend
        # Annual averages for tooltips
        annual_avg = show_states.resample('Y').mean()
        annual_avg.index = annual_avg.index.year
        return show_states, show_us_avg, trendlines, annual_avg

    show_states, show_us_avg, trendlines, annual_avg = prepare_unemployment_states(
        unemp_df, state_pattern, start_date, end_date, fred, selected_state
    )

    # --- Chart type toggle ---
    chart_type = st.radio("Chart Type", ["Line Chart", "Smoothed Area Chart"], horizontal=True)

    if show_states.empty:
        st.warning("No data available for the selected state and year range.")
    else:
        latest_month = show_states.index.max()
        if pd.notnull(latest_month) and latest_month in show_states.index:
            if show_us_avg:
                avg_unemp = show_states.loc[latest_month, "US Average"]
                col1, col2 = st.columns(2)
                col1.metric("US Average Unemployment Rate", f"{avg_unemp:.2f}%", help="Average unemployment rate across all states for the latest month.")
                # Optionally, show highest/lowest state as well
                max_state = show_states.loc[latest_month].drop("US Average", errors="ignore").idxmax()
                min_state = show_states.loc[latest_month].drop("US Average", errors="ignore").idxmin()
                max_val = show_states.loc[latest_month].drop("US Average", errors="ignore").max()
                min_val = show_states.loc[latest_month].drop("US Average", errors="ignore").min()
                col2.metric(f"Highest: {max_state} / Lowest: {min_state}", f"{max_val:.2f}% / {min_val:.2f}%")
            else:
                avg_unemp = show_states.loc[latest_month].mean()
                max_state = show_states.loc[latest_month].idxmax()
                min_state = show_states.loc[latest_month].idxmin()
                max_val = show_states.loc[latest_month].max()
                min_val = show_states.loc[latest_month].min()
                col1, col2, col3 = st.columns(3)
                col1.metric("US State Avg Unemployment Rate", f"{avg_unemp:.2f}%", help="Average unemployment rate across all states for the latest month.")
                col2.metric(f"Highest: {max_state}", f"{max_val:.2f}%", help="State with the highest unemployment rate.")
                col3.metric(f"Lowest: {min_state}", f"{min_val:.2f}%", help="State with the lowest unemployment rate.")
        else:
            st.warning("No valid unemployment data found for the selected year/state.")

    st.subheader("State Unemployment Rates (Interactive Plotly Chart)")
    st.caption("Tip: Use the legend to show/hide states. Toggle chart type above.")
    import plotly.graph_objects as go
    fig = go.Figure()
    color_cycle = COLOR_PALETTE
    for i, col in enumerate(show_states.columns):
        color = color_cycle[i % len(color_cycle)]
        # Main line/area
        if chart_type == "Line Chart":
            fig.add_trace(go.Scatter(
                x=show_states.index, y=show_states[col],
                mode='lines',
                name=col,
                line=dict(color=color, width=2, shape='spline', smoothing=1.2),
                hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>'+col+'</b>: %{y:.1f}%<br>Annual Avg: %{customdata:.1f}%<extra></extra>',
                customdata=[annual_avg.loc[d.year, col] if d.year in annual_avg.index and col in annual_avg.columns else None for d in show_states.index],
                yaxis='y1',
            ))
        else:
            fig.add_trace(go.Scatter(
                x=show_states.index, y=show_states[col],
                mode='lines',
                name=col,
                line=dict(color=color, width=0, shape='spline', smoothing=1.2),
                fill='tozeroy',
                hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>'+col+'</b>: %{y:.1f}%<br>Annual Avg: %{customdata:.1f}%<extra></extra>',
                customdata=[annual_avg.loc[d.year, col] if d.year in annual_avg.index and col in annual_avg.columns else None for d in show_states.index],
                yaxis='y1',
                showlegend=True
            ))
        # Trendline (rolling mean)
        fig.add_trace(go.Scatter(
            x=show_states.index, y=trendlines[col],
            mode='lines',
            name=f"{col} Trend (12M MA)",
            line=dict(color=color, width=2, dash='dash'),
            hoverinfo='skip',
            yaxis='y1',
            showlegend=True,
            visible=True
        ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        plot_bgcolor="#0A1224",
        paper_bgcolor="#0A1224",
        font=dict(color="#EAEAEA"),
        legend=dict(
            bgcolor="#101A33",
            bordercolor="#1E90FF",
            borderwidth=1,
            font=dict(color="#EAEAEA", size=14),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=40),
        xaxis=dict(title="Date", showgrid=True, gridcolor="#222A44", zeroline=False),
        yaxis=dict(title="Unemployment Rate (%)", showgrid=True, gridcolor="#222A44", zeroline=False, color="#EAEAEA", tickformat=".1f"),
    )
    fig.update_xaxes(showline=True, linewidth=1, linecolor="#EAEAEA")
    fig.update_yaxes(showline=True, linewidth=1, linecolor="#EAEAEA")
    if not show_states.empty and show_states.shape[0] > 0 and show_states.shape[1] > 0:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No unemployment data available for the selected year/state.")

    with st.expander("Show raw data"):
        if show_states.columns.duplicated().any():
            st.warning("Duplicate columns detected, cannot display table. Please check your data source.")
        else:
            st.dataframe(show_states)
            csv = show_states.to_csv().encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f'unemployment_by_state_{start_year}_{end_year}.csv',
                mime='text/csv'
            )

elif view == "Participation":
    st.header("👷 Labor Force Participation Rate")
    st.info("Labor force participation rates by state. Higher rates indicate a larger share of the population is working or seeking work.")

    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    import re
    part_df = get_fred_search('participation rate state', filter=('frequency', 'Monthly'))
    part_df = part_df.query('seasonal_adjustment == "Seasonally Adjusted" and units == "Percent"')
    part_df = part_df.loc[part_df['title'].str.contains('Labor Force Participation Rate')]
    state_pattern = r'^Labor Force Participation Rate for ([A-Za-z .\-]+)$'
    part_states = fetch_state_series_data(
        part_df,
        state_pattern,
        start_date,
        end_date,
        fred
    )

    # --- Filter for selected state(s) and add US Average if 'All States' ---
    show_states = part_states.copy()
    show_us_avg = False
    if selected_state != "All States" and not part_states.empty:
        if selected_state in part_states.columns:
            show_states = part_states[[selected_state]]
        else:
            show_states = pd.DataFrame()  # No data for this state
    elif selected_state == "All States" and not part_states.empty:
        show_states["US Average"] = show_states.mean(axis=1)
        show_us_avg = True


    # --- Advanced optimization: cache all DataFrame prep and trendlines ---
    @st.cache_data(show_spinner="Preparing participation data...", max_entries=10)
    def prepare_participation_states(part_states, selected_state):
        import numpy as np
        show_states = part_states.copy()
        show_us_avg = False
        if selected_state != "All States" and not part_states.empty:
            if selected_state in part_states.columns:
                show_states = part_states[[selected_state]]
            else:
                show_states = pd.DataFrame()  # No data for this state
        elif selected_state == "All States" and not part_states.empty:
            show_states["US Average"] = show_states.mean(axis=1)
            show_us_avg = True
        # Fast rolling mean with numpy for trendlines
        def fast_rolling(arr, window):
            if len(arr) < window:
                return np.convolve(arr, np.ones(len(arr))/len(arr), mode='same')
            return np.convolve(arr, np.ones(window)/window, mode='same')
        trendlines = {}
        for col in show_states.columns:
            arr = show_states[col].to_numpy()
            trend = fast_rolling(arr, 12)
            if len(trend) < len(show_states):
                pad = np.full(len(show_states)-len(trend), np.nan)
                trend = np.concatenate([trend, pad])
            trendlines[col] = trend
        # Year-over-year change for tooltips
        yoy_change = show_states.pct_change(periods=12) * 100
        return show_states, show_us_avg, trendlines, yoy_change

    show_states, show_us_avg, trendlines, yoy_change = prepare_participation_states(part_states, selected_state)

    # --- Chart colors: use light blue/green for lines, highlight US Average ---
    palette = [ 
    "#1abc9c",  # teal
    "#e67e22",  # orange
    "#2980b9",  # blue
    "#9b59b6",  # purple
    "#e74c3c",  # red
    "#f1c40f",  # yellow
    "#2ecc71",  # green
    "#34495e",  # dark blue-gray
    ]
    us_avg_color = "#FFA500"  # orange highlight for US Average

    st.subheader("Participation Rate by State (Interactive Plotly Chart)")
    st.caption("Tip: Use the legend to show/hide states. US Average is highlighted if available.")
    import plotly.graph_objects as go
    fig = go.Figure()
    for i, col in enumerate(show_states.columns):
        color = us_avg_color if col == "US Average" else palette[i % len(palette)]
        # Main line
        fig.add_trace(go.Scatter(
            x=show_states.index, y=show_states[col],
            mode='lines',
            name=col,
            line=dict(color=color, width=3 if col == "US Average" else 2, shape='spline', smoothing=1.2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>'+col+'</b>: %{y:.1f}%<br>YoY Change: %{customdata:.1f}%<extra></extra>',
            customdata=[yoy_change.loc[d, col] if d in yoy_change.index and col in yoy_change.columns and pd.notnull(yoy_change.loc[d, col]) else 0 for d in show_states.index],
            yaxis='y1',
        ))
        # Trendline (rolling mean)
        fig.add_trace(go.Scatter(
            x=show_states.index, y=trendlines[col],
            mode='lines',
            name=f"{col} Trend (12M MA)",
            line=dict(color=color, width=2, dash='dash'),
            hoverinfo='skip',
            yaxis='y1',
            showlegend=True,
            visible=True
        ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        plot_bgcolor="#0A1224",
        paper_bgcolor="#0A1224",
        font=dict(color="#EAEAEA"),
        legend=dict(
            bgcolor="#101A33",
            bordercolor="#1E90FF",
            borderwidth=1,
            font=dict(color="#EAEAEA", size=14),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=40),
        xaxis=dict(title="Date", showgrid=True, gridcolor="#222A44", zeroline=False),
        yaxis=dict(title="Participation Rate (%)", showgrid=True, gridcolor="#222A44", zeroline=False, color="#EAEAEA", tickformat=".1f"),
    )
    fig.update_xaxes(showline=True, linewidth=1, linecolor="#EAEAEA")
    fig.update_yaxes(showline=True, linewidth=1, linecolor="#EAEAEA")
    if not show_states.empty and show_states.shape[0] > 0 and show_states.shape[1] > 0:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected state and year range.")

    with st.expander("Show raw data"):
        st.dataframe(show_states)
        csv = show_states.to_csv().encode('utf-8')
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'participation_by_state_plotly_{start_year}_{end_year}.csv',
            mime='text/csv'
        )

elif view == "Unemployment by State":
    st.header("🗺️ Unemployment Rate by State (Plotly)")
    st.info("This tab shows the monthly, seasonally adjusted unemployment rate for each US state using FRED data.")

    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    import re
    unemp_df = cached_get_fred_search('unemployment rate state', filter=('frequency', 'Monthly'))
    unemp_df = unemp_df.query('seasonal_adjustment == "Seasonally Adjusted" and units == "Percent"')
    unemp_df = unemp_df.loc[unemp_df['title'].str.contains('Unemployment Rate')]
    state_pattern = re.compile(r'^Unemployment Rate in ([A-Za-z .\-]+)$')
    state_rows = unemp_df['title'].apply(lambda t: bool(state_pattern.match(t)))
    unemp_df = unemp_df[state_rows]
    id_to_state = unemp_df['title'].str.replace('Unemployment Rate in ', '', regex=False).to_dict()

    # Use unified utility for state series data

    uemp_states = fetch_state_series_data(
        unemp_df,
        r'^Unemployment Rate in ([A-Za-z .\-]+)$',
        start_date,
        end_date,
        fred
    )

    # --- Advanced optimization: cache all DataFrame prep and trendlines ---
    @st.cache_data(show_spinner="Preparing unemployment by state data...", max_entries=10)
    def prepare_unemployment_by_state(uemp_states, show_mode, highlight_states):
        import numpy as np
        state_options_multi = sorted(uemp_states.columns)
        if show_mode == "All States":
            filtered_states = uemp_states.copy()
            highlight_states = []
        else:
            filtered_states = uemp_states[highlight_states] if highlight_states else pd.DataFrame()
        # Fast rolling mean with numpy for trendlines
        def fast_rolling(arr, window):
            if len(arr) < window:
                return np.convolve(arr, np.ones(len(arr))/len(arr), mode='same')
            return np.convolve(arr, np.ones(window)/window, mode='same')
        trendlines = {}
        for col in filtered_states.columns:
            arr = filtered_states[col].to_numpy()
            trend = fast_rolling(arr, 12)
            if len(trend) < len(filtered_states):
                pad = np.full(len(filtered_states)-len(trend), np.nan)
                trend = np.concatenate([trend, pad])
            trendlines[col] = trend
        return filtered_states, highlight_states, trendlines

    state_options_multi = sorted(uemp_states.columns)
    show_mode = st.radio("Show", ["All States", "Select State(s)"])
    if show_mode == "All States":
        highlight_states = []
    else:
        highlight_states = st.multiselect("Select State(s) to Highlight", state_options_multi, default=[state_options_multi[0]] if state_options_multi else [])

    filtered_states, highlight_states, trendlines = prepare_unemployment_by_state(uemp_states, show_mode, highlight_states)

    # --- Plotly line chart ---
    if filtered_states.empty:
        st.warning("No data available for the selected state(s) and year range.")
    else:
        import plotly.graph_objects as go
        fig = go.Figure()
        palette = COLOR_PALETTE
        show_trend = filtered_states.shape[1] <= 5
        for i, col in enumerate(filtered_states.columns):
            color = palette[i % len(palette)]
            width = 4 if col in highlight_states else 2
            fig.add_trace(go.Scatter(
                x=filtered_states.index, y=filtered_states[col],
                mode='lines',
                name=col,
                line=dict(color=color, width=width, shape='spline', smoothing=1.2),
                hovertemplate=f"<b>{col}</b><br>Date: %{{x|%Y-%m-%d}}<br>Unemployment: %{{y:.1f}}%<extra></extra>",
            ))
            # Add trendline if ≤ 5 states
            if show_trend:
                trend = filtered_states[col].rolling(window=12, min_periods=1).mean()
                fig.add_trace(go.Scatter(
                    x=filtered_states.index, y=trend,
                    mode='lines',
                    name=f"{col} Trend (12M MA)",
                    line=dict(color=color, width=2, dash='dash'),
                    hoverinfo='skip',
                    showlegend=True,
                    visible=True
                ))
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            plot_bgcolor="#0A1224",
            paper_bgcolor="#0A1224",
            font=dict(color="#EAEAEA"),
            legend=dict(
                bgcolor="#101A33",
                bordercolor="#1E90FF",
                borderwidth=1,
                font=dict(color="#EAEAEA", size=14),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            hovermode="x unified",
            margin=dict(l=20, r=20, t=60, b=40),
            xaxis=dict(title="Date", showgrid=True, gridcolor="#222A44", zeroline=False, showline=True, linewidth=1, linecolor="#EAEAEA", rangeslider=dict(visible=True)),
            yaxis=dict(title="Unemployment Rate (%)", showgrid=True, gridcolor="#222A44", zeroline=False, color="#EAEAEA", tickformat=".1f", showline=True, linewidth=1, linecolor="#EAEAEA"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Export to PNG ---
        export_fmt = st.selectbox("Export Format", ["CSV"], index=0)
        if export_fmt == "PNG":
            try:
                import kaleido
                import plotly.io as pio
                png_bytes = fig.to_image(format="png", engine="kaleido")
                st.download_button(
                    label="Download Chart as PNG",
                    data=png_bytes,
                    file_name=f'unemployment_by_state_{start_year}_{end_year}.png',
                    mime='image/png'
                )
            except Exception as e:
                st.warning(f"PNG export failed: {e}. Please ensure 'kaleido' is installed.")

    with st.expander("Show raw data"):
        if filtered_states.columns.duplicated().any():
            st.warning("Duplicate columns detected, cannot display table. Please check your data source.")
        else:
            st.dataframe(filtered_states)
            csv = filtered_states.to_csv().encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f'unemployment_by_state_plotly_{start_year}_{end_year}.csv',
                mime='text/csv'
            )

elif view == "Participation by State":
    st.header("👷 Participation Rate by State (Plotly)")
    st.info("Monthly, seasonally adjusted labor force participation rates for each US state from FRED.")

    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    import re
    part_df = fred.search('participation rate state', filter=('frequency', 'Monthly'))
    part_df = part_df.query('seasonal_adjustment == "Seasonally Adjusted" and units == "Percent"')
    part_df = part_df.loc[part_df['title'].str.contains('Labor Force Participation Rate')]
    state_pattern = r'^Labor Force Participation Rate for ([A-Za-z .\-]+)$'

    part_states = fetch_state_series_data(
        part_df,
        state_pattern,
        start_date,
        end_date,
        fred
    )

    # --- Advanced optimization: cache all DataFrame prep and trendlines ---
    @st.cache_data(show_spinner="Preparing participation by state data...", max_entries=10)
    def prepare_participation_by_state(part_states, show_mode, highlight_states):
        import numpy as np
        state_options_multi = sorted(part_states.columns)
        if show_mode == "All States":
            filtered_states = part_states.copy()
            highlight_states = []
        else:
            filtered_states = part_states[highlight_states] if highlight_states else pd.DataFrame()
        # National average overlay
        show_us_avg = False
        us_avg_col = None
        if not part_states.empty:
            us_state_names = [c for c in part_states.columns if c.lower() in ["us", "united states"]]
            if us_state_names:
                us_avg_col = us_state_names[0]
            else:
                us_avg_col = "US Average"
                part_states[us_avg_col] = part_states.mean(axis=1)
        if us_avg_col:
            show_us_avg = True if show_mode=="All States" else False
        # Fast rolling mean with numpy for trendlines
        def fast_rolling(arr, window):
            if len(arr) < window:
                return np.convolve(arr, np.ones(len(arr))/len(arr), mode='same')
            return np.convolve(arr, np.ones(window)/window, mode='same')
        trendlines = {}
        for col in filtered_states.columns:
            arr = filtered_states[col].to_numpy()
            trend = fast_rolling(arr, 12)
            if len(trend) < len(filtered_states):
                pad = np.full(len(filtered_states)-len(trend), np.nan)
                trend = np.concatenate([trend, pad])
            trendlines[col] = trend
        return filtered_states, highlight_states, show_us_avg, us_avg_col, trendlines

    state_options_multi = sorted(part_states.columns)
    show_mode = st.radio("Show", ["All States", "Select State(s)"])
    if show_mode == "All States":
        highlight_states = []
    else:
        highlight_states = st.multiselect("Select State(s) to Highlight", state_options_multi, default=[state_options_multi[0]] if state_options_multi else [])

    filtered_states, highlight_states, show_us_avg, us_avg_col, trendlines = prepare_participation_by_state(part_states, show_mode, highlight_states)

    # --- Plotly line chart ---
    st.subheader("Participation Rate by State (Interactive Plotly Chart)")
    st.caption("Tip: Use the legend to show/hide states. US Average is highlighted if available.")
    if filtered_states.empty or filtered_states.shape[1] == 0:
        st.warning("No data available for the selected state(s) and year range.")
    else:
        import plotly.graph_objects as go
        fig = go.Figure()
        # Light blue/green palette for contrast
        palette = [ 
            "#1abc9c",  # teal
            "#e67e22",  # orange
            "#2980b9",  # blue
            "#9b59b6",  # purple
            "#e74c3c",  # red
            "#f1c40f",  # yellow
            "#2ecc71",  # green
            "#34495e",  # dark blue-gray
        ]
        us_avg_color = "#FFA500"  # orange highlight for US Average
        show_trend = filtered_states.shape[1] <= 5
        for i, col in enumerate(filtered_states.columns):
            color = us_avg_color if col == us_avg_col and show_us_avg else palette[i % len(palette)]
            width = 3 if (col == us_avg_col and show_us_avg) or (col in highlight_states) else (1 if show_mode == "All States" else 2)
            opacity = 0.5 if show_mode == "All States" and (col != us_avg_col or not show_us_avg) else 1.0
            fig.add_trace(go.Scatter(
                x=filtered_states.index, y=filtered_states[col],
                mode='lines',
                name=col,
                line=dict(color=color, width=width, shape='spline', smoothing=1.2),
                opacity=opacity,
                hovertemplate=f"<b>{col}</b><br>Date: %{{x|%Y-%m-%d}}<br>Participation: %{{y:.1f}}%<extra></extra>",
            ))
            # Add trendline if ≤ 5 states
            if show_trend:
                trend = filtered_states[col].rolling(window=12, min_periods=1).mean()
                fig.add_trace(go.Scatter(
                    x=filtered_states.index, y=trend,
                    mode='lines',
                    name=f"{col} Trend (12M MA)",
                    line=dict(color=color, width=2, dash='dash'),
                    hoverinfo='skip',
                    showlegend=True,
                    visible=True
                ))
        # Overlay US average if checked and not already in filtered_states
        if show_us_avg and us_avg_col and us_avg_col not in filtered_states.columns and us_avg_col in part_states.columns:
            fig.add_trace(go.Scatter(
                x=part_states.index, y=part_states[us_avg_col],
                mode='lines',
                name=us_avg_col,
                line=dict(color=us_avg_color, width=3, dash='dot', shape='spline', smoothing=1.2),
                opacity=1.0,
                hovertemplate=f"<b>{us_avg_col}</b><br>Date: %{{x|%Y-%m-%d}}<br>Participation: %{{y:.1f}}%<extra></extra>",
            ))
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            plot_bgcolor="#0A1224",
            paper_bgcolor="#0A1224",
            font=dict(color="#EAEAEA"),
            legend=dict(
                bgcolor="#101A33",
                bordercolor="#1E90FF",
                borderwidth=1,
                font=dict(color="#EAEAEA", size=14),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            hovermode="x unified",
            margin=dict(l=20, r=20, t=60, b=40),
            xaxis=dict(title="Date", showgrid=True, gridcolor="#222A44", zeroline=False),
            yaxis=dict(title="Participation Rate (%)", showgrid=True, gridcolor="#222A44", zeroline=False, color="#EAEAEA", tickformat=".1f"),
        )
        st.plotly_chart(fig, use_container_width=True)
        # --- Export to PNG (no selectbox, always show button) ---
        try:
            import kaleido
            import plotly.io as pio
            png_bytes = fig.to_image(format="png", engine="kaleido")
            st.download_button(
                label="Download Chart as PNG",
                data=png_bytes,
                file_name=f'participation_by_state_{start_year}_{end_year}.png',
                mime='image/png'
            )
        except Exception as e:
            st.warning(f"PNG export failed: {e}. Please ensure 'kaleido' is installed.")

    with st.expander("Show raw data"):
        st.dataframe(filtered_states)  # Changed from show_states to filtered_states
        csv = filtered_states.to_csv().encode('utf-8')  # Changed from show_states to filtered_states
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'participation_by_state_plotly_{start_year}_{end_year}.csv',
            mime='text/csv'
        )

elif view == "Unemployment by State":
    st.header("🗺️ Unemployment Rate by State (Plotly)")
    st.info("This tab shows the monthly, seasonally adjusted unemployment rate for each US state using FRED data.")

    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    import re
    unemp_df = cached_get_fred_search('unemployment rate state', filter=('frequency', 'Monthly'))
    unemp_df = unemp_df.query('seasonal_adjustment == "Seasonally Adjusted" and units == "Percent"')
    unemp_df = unemp_df.loc[unemp_df['title'].str.contains('Unemployment Rate')]
    state_pattern = re.compile(r'^Unemployment Rate in ([A-Za-z .\-]+)$')
    state_rows = unemp_df['title'].apply(lambda t: bool(state_pattern.match(t)))
    unemp_df = unemp_df[state_rows]
    id_to_state = unemp_df['title'].str.replace('Unemployment Rate in ', '', regex=False).to_dict()

    # Use unified utility for state series data

    uemp_states = fetch_state_series_data(
        unemp_df,
        r'^Unemployment Rate in ([A-Za-z .\-]+)$',
        start_date,
        end_date,
        fred
    )

    # --- Advanced optimization: cache all DataFrame prep and trendlines ---
    @st.cache_data(show_spinner="Preparing unemployment by state data...", max_entries=10)
    def prepare_unemployment_by_state(uemp_states, show_mode, highlight_states):
        import numpy as np
        state_options_multi = sorted(uemp_states.columns)
        if show_mode == "All States":
            filtered_states = uemp_states.copy()
            highlight_states = []
        else:
            filtered_states = uemp_states[highlight_states] if highlight_states else pd.DataFrame()
        # Fast rolling mean with numpy for trendlines
        def fast_rolling(arr, window):
            if len(arr) < window:
                return np.convolve(arr, np.ones(len(arr))/len(arr), mode='same')
            return np.convolve(arr, np.ones(window)/window, mode='same')
        trendlines = {}
        for col in filtered_states.columns:
            arr = filtered_states[col].to_numpy()
            trend = fast_rolling(arr, 12)
            if len(trend) < len(filtered_states):
                pad = np.full(len(filtered_states)-len(trend), np.nan)
                trend = np.concatenate([trend, pad])
            trendlines[col] = trend
        return filtered_states, highlight_states, trendlines

    state_options_multi = sorted(uemp_states.columns)
    show_mode = st.radio("Show", ["All States", "Select State(s)"])
    if show_mode == "All States":
        highlight_states = []
    else:
        highlight_states = st.multiselect("Select State(s) to Highlight", state_options_multi, default=[state_options_multi[0]] if state_options_multi else [])

    filtered_states, highlight_states, trendlines = prepare_unemployment_by_state(uemp_states, show_mode, highlight_states)

    # --- Plotly line chart ---
    if filtered_states.empty:
        st.warning("No data available for the selected state(s) and year range.")
    else:
        import plotly.graph_objects as go
        fig = go.Figure()
        palette = COLOR_PALETTE
        show_trend = filtered_states.shape[1] <= 5
        for i, col in enumerate(filtered_states.columns):
            color = palette[i % len(palette)]
            width = 4 if col in highlight_states else 2
            fig.add_trace(go.Scatter(
                x=filtered_states.index, y=filtered_states[col],
                mode='lines',
                name=col,
                line=dict(color=color, width=width, shape='spline', smoothing=1.2),
                hovertemplate=f"<b>{col}</b><br>Date: %{{x|%Y-%m-%d}}<br>Unemployment: %{{y:.1f}}%<extra></extra>",
            ))
            # Add trendline if ≤ 5 states
            if show_trend:
                trend = filtered_states[col].rolling(window=12, min_periods=1).mean()
                fig.add_trace(go.Scatter(
                    x=filtered_states.index, y=trend,
                    mode='lines',
                    name=f"{col} Trend (12M MA)",
                    line=dict(color=color, width=2, dash='dash'),
                    hoverinfo='skip',
                    showlegend=True,
                    visible=True
                ))
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            plot_bgcolor="#0A1224",
            paper_bgcolor="#0A1224",
            font=dict(color="#EAEAEA"),
            legend=dict(
                bgcolor="#101A33",
                bordercolor="#1E90FF",
                borderwidth=1,
                font=dict(color="#EAEAEA", size=14),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            hovermode="x unified",
            margin=dict(l=20, r=20, t=60, b=40),
            xaxis=dict(title="Date", showgrid=True, gridcolor="#222A44", zeroline=False, showline=True, linewidth=1, linecolor="#EAEAEA", rangeslider=dict(visible=True)),
            yaxis=dict(title="Unemployment Rate (%)", showgrid=True, gridcolor="#222A44", zeroline=False, color="#EAEAEA", tickformat=".1f", showline=True, linewidth=1, linecolor="#EAEAEA"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Export to PNG ---
        export_fmt = st.selectbox("Export Format", ["CSV"], index=0)
        if export_fmt == "PNG":
            try:
                import kaleido
                import plotly.io as pio
                png_bytes = fig.to_image(format="png", engine="kaleido")
                st.download_button(
                    label="Download Chart as PNG",
                    data=png_bytes,
                    file_name=f'unemployment_by_state_{start_year}_{end_year}.png',
                    mime='image/png'
                )
            except Exception as e:
                st.warning(f"PNG export failed: {e}. Please ensure 'kaleido' is installed.")

    with st.expander("Show raw data"):
        if filtered_states.columns.duplicated().any():
            st.warning("Duplicate columns detected, cannot display table. Please check your data source.")
        else:
            st.dataframe(filtered_states)
            csv = filtered_states.to_csv().encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f'unemployment_by_state_plotly_{start_year}_{end_year}.csv',
                mime='text/csv'
            )

elif view == "Participation by State":
    st.header("👷 Participation Rate by State (Plotly)")
    st.info("Monthly, seasonally adjusted labor force participation rates for each US state from FRED.")

    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    import re
    part_df = fred.search('participation rate state', filter=('frequency', 'Monthly'))
    part_df = part_df.query('seasonal_adjustment == "Seasonally Adjusted" and units == "Percent"')
    part_df = part_df.loc[part_df['title'].str.contains('Labor Force Participation Rate')]
    state_pattern = r'^Labor Force Participation Rate for ([A-Za-z .\-]+)$'

    part_states = fetch_state_series_data(
        part_df,
        state_pattern,
        start_date,
        end_date,
        fred
    )

    # --- Advanced optimization: cache all DataFrame prep and trendlines ---
    @st.cache_data(show_spinner="Preparing participation by state data...", max_entries=10)
    def prepare_participation_by_state(part_states, show_mode, highlight_states):
        import numpy as np
        state_options_multi = sorted(part_states.columns)
        if show_mode == "All States":
            filtered_states = part_states.copy()
            highlight_states = []
        else:
            filtered_states = part_states[highlight_states] if highlight_states else pd.DataFrame()
        # National average overlay
        show_us_avg = False
        us_avg_col = None
        if not part_states.empty:
            us_state_names = [c for c in part_states.columns if c.lower() in ["us", "united states"]]
            if us_state_names:
                us_avg_col = us_state_names[0]
            else:
                us_avg_col = "US Average"
                part_states[us_avg_col] = part_states.mean(axis=1)
        if us_avg_col:
            show_us_avg = True if show_mode=="All States" else False
        # Fast rolling mean with numpy for trendlines
        def fast_rolling(arr, window):
            if len(arr) < window:
                return np.convolve(arr, np.ones(len(arr))/len(arr), mode='same')
            return np.convolve(arr, np.ones(window)/window, mode='same')
        trendlines = {}
        for col in filtered_states.columns:
            arr = filtered_states[col].to_numpy()
            trend = fast_rolling(arr, 12)
            if len(trend) < len(filtered_states):
                pad = np.full(len(filtered_states)-len(trend), np.nan)
                trend = np.concatenate([trend, pad])
            trendlines[col] = trend
        return filtered_states, highlight_states, show_us_avg, us_avg_col, trendlines

    state_options_multi = sorted(part_states.columns)
    show_mode = st.radio("Show", ["All States", "Select State(s)"])
    if show_mode == "All States":
        highlight_states = []
    else:
        highlight_states = st.multiselect("Select State(s) to Highlight", state_options_multi, default=[state_options_multi[0]] if state_options_multi else [])

    filtered_states, highlight_states, show_us_avg, us_avg_col, trendlines = prepare_participation_by_state(part_states, show_mode, highlight_states)

    # --- Plotly line chart ---
    st.subheader("Participation Rate by State (Interactive Plotly Chart)")
    st.caption("Tip: Use the legend to show/hide states. US Average is highlighted if available.")
    if filtered_states.empty or filtered_states.shape[1] == 0:
        st.warning("No data available for the selected state(s) and year range.")
    else:
        import plotly.graph_objects as go
        fig = go.Figure()
        # Light blue/green palette for contrast
        palette = [ 
            "#1abc9c",  # teal
            "#e67e22",  # orange
            "#2980b9",  # blue
            "#9b59b6",  # purple
            "#e74c3c",  # red
            "#f1c40f",  # yellow
            "#2ecc71",  # green
            "#34495e",  # dark blue-gray
        ]
        us_avg_color = "#FFA500"  # orange highlight for US Average
        show_trend = filtered_states.shape[1] <= 5
        for i, col in enumerate(filtered_states.columns):
            color = us_avg_color if col == us_avg_col and show_us_avg else palette[i % len(palette)]
            width = 3 if (col == us_avg_col and show_us_avg) or (col in highlight_states) else (1 if show_mode == "All States" else 2)
            opacity = 0.5 if show_mode == "All States" and (col != us_avg_col or not show_us_avg) else 1.0
            fig.add_trace(go.Scatter(
                x=filtered_states.index, y=filtered_states[col],
                mode='lines',
                name=col,
                line=dict(color=color, width=width, shape='spline', smoothing=1.2),
                opacity=opacity,
                hovertemplate=f"<b>{col}</b><br>Date: %{{x|%Y-%m-%d}}<br>Participation: %{{y:.1f}}%<extra></extra>",
            ))
            # Add trendline if ≤ 5 states
            if show_trend:
                trend = filtered_states[col].rolling(window=12, min_periods=1).mean()
                fig.add_trace(go.Scatter(
                    x=filtered_states.index, y=trend,
                    mode='lines',
                    name=f"{col} Trend (12M MA)",
                    line=dict(color=color, width=2, dash='dash'),
                    hoverinfo='skip',
                    showlegend=True,
                    visible=True
                ))
        # Overlay US average if checked and not already in filtered_states
        if show_us_avg and us_avg_col and us_avg_col not in filtered_states.columns and us_avg_col in part_states.columns:
            fig.add_trace(go.Scatter(
                x=part_states.index, y=part_states[us_avg_col],
                mode='lines',
                name=us_avg_col,
                line=dict(color=us_avg_color, width=3, dash='dot', shape='spline', smoothing=1.2),
                opacity=1.0,
                hovertemplate=f"<b>{us_avg_col}</b><br>Date: %{{x|%Y-%m-%d}}<br>Participation: %{{y:.1f}}%<extra></extra>",
            ))
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            plot_bgcolor="#0A1224",
            paper_bgcolor="#0A1224",
            font=dict(color="#EAEAEA"),
            legend=dict(
                bgcolor="#101A33",
                bordercolor="#1E90FF",
                borderwidth=1,
                font=dict(color="#EAEAEA", size=14),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            hovermode="x unified",
            margin=dict(l=20, r=20, t=60, b=40),
            xaxis=dict(title="Date", showgrid=True, gridcolor="#222A44", zeroline=False),
            yaxis=dict(title="Participation Rate (%)", showgrid=True, gridcolor="#222A44", zeroline=False, color="#EAEAEA", tickformat=".1f"),
        )
        st.plotly_chart(fig, use_container_width=True)
        # --- Export to PNG (no selectbox, always show button) ---
        try:
            import kaleido
            import plotly.io as pio
            png_bytes = fig.to_image(format="png", engine="kaleido")
            st.download_button(
                label="Download Chart as PNG",
                data=png_bytes,
                file_name=f'participation_by_state_{start_year}_{end_year}.png',
                mime='image/png'
            )
        except Exception as e:
            st.warning(f"PNG export failed: {e}. Please ensure 'kaleido' is installed.")

    with st.expander("Show raw data"):
        st.dataframe(filtered_states)  # Changed from show_states to filtered_states
        csv = filtered_states.to_csv().encode('utf-8')  # Changed from show_states to filtered_states
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'participation_by_state_plotly_{start_year}_{end_year}.csv',
            mime='text/csv'
        )

elif view == "State Comparison":
    st.header(f"📊 State Unemployment vs Participation Rate ({start_year}–{end_year})")
    st.info(f"Compare unemployment and labor force participation rates for selected states between {start_year} and {end_year}.")

    # --- Multi-state selection ---
    state_options_multi = sorted(common_states)
    selected_states = st.multiselect("Select State(s)", state_options_multi, default=["Texas", "California", "New York"])
    sort_metric = st.radio("Sort bars by", ["Unemployment Rate", "Participation Rate"], horizontal=True)

    # --- Fetch data for selected states ---
    import re
    unemp_pat = re.compile(r'^Unemployment Rate in ([A-Za-z .\-]+)$')
    part_pat = re.compile(r'^Labor Force Participation Rate for ([A-Za-z .\-]+)$')
    state_data = []
    for state in selected_states:
        # Unemployment
        unemp_mask = unemp_df['title'].dropna().apply(lambda t: bool(unemp_pat.match(t) and unemp_pat.match(t).group(1) == state))
        unemp_row = unemp_df.loc[unemp_df['title'].dropna().index[unemp_mask]]
        # Participation
        part_mask = part_df['title'].dropna().apply(lambda t: bool(part_pat.match(t) and part_pat.match(t).group(1) == state))
        part_row = part_df.loc[part_df['title'].dropna().index[part_mask]]
        if not unemp_row.empty and not part_row.empty:
            unemp_series_id = unemp_row.index[0]
            part_series_id = part_row.index[0]
            start = f"{start_year}-01-01"
            end = f"{end_year}-12-31"
            unemp_series = fetch_series(fred, unemp_series_id, observation_start=start, observation_end=end)
            part_series = fetch_series(fred, part_series_id, observation_start=start, observation_end=end)
            # Use last available value in range
            if not unemp_series.empty and not part_series.empty:
                state_data.append({
                    "State": state,
                    "Unemployment Rate": unemp_series.dropna().iloc[-1],
                    "Participation Rate": part_series.dropna().iloc[-1]
                })
    df = pd.DataFrame(state_data)

    # --- National averages for annotation ---
    us_unemp = us_part = None
    if "United States" in common_states:
        us_unemp_mask = unemp_df['title'].dropna().apply(lambda t: bool(unemp_pat.match(t) and unemp_pat.match(t).group(1) == "United States"))
        us_unemp_row = unemp_df.loc[unemp_df['title'].dropna().index[us_unemp_mask]]
        us_part_mask = part_df['title'].dropna().apply(lambda t: bool(part_pat.match(t) and part_pat.match(t).group(1) == "United States"))
        us_part_row = part_df.loc[part_df['title'].dropna().index[us_part_mask]]
        if not us_unemp_row.empty and not us_part_row.empty:
            us_unemp_series = fetch_series(fred, us_unemp_row.index[0], observation_start=start, observation_end=end)
            us_part_series = fetch_series(fred, us_part_row.index[0], observation_start=start, observation_end=end)
            if not us_unemp_series.empty:
                us_unemp = us_unemp_series.dropna().iloc[-1]
            if not us_part_series.empty:
                us_part = us_part_series.dropna().iloc[-1]

    # --- Sorting ---
    if not df.empty:
        if sort_metric == "Unemployment Rate":
            df = df.sort_values("Unemployment Rate", ascending=False)
        else:
            df = df.sort_values("Participation Rate", ascending=False)

    # --- Plotly grouped horizontal bar chart ---
    import plotly.graph_objects as go
    palette = ["#20B2AA", "#FFA500"]  # teal for participation, orange for unemployment
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["State"] if not df.empty else [],
        x=df["Unemployment Rate"] if not df.empty else [],
        name="Unemployment Rate",
        orientation="h",
        marker_color=palette[1],
        text=[f"{v:.2f}%" for v in df["Unemployment Rate"]] if not df.empty else [],
        textposition="auto",
        hovertemplate="<b>%{y}</b><br>Unemployment: %{x:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df["State"] if not df.empty else [],
        x=df["Participation Rate"] if not df.empty else [],
        name="Participation Rate",
        orientation="h",
        marker_color=palette[0],
        text=[f"{v:.2f}%" for v in df["Participation Rate"]] if not df.empty else [],
        textposition="auto",
        hovertemplate="<b>%{y}</b><br>Participation: %{x:.2f}%<extra></extra>",
    ))

    # --- Delta from national average as annotation ---
    if us_unemp is not None and us_part is not None and not df.empty:
        for i, row in df.iterrows():
            delta_unemp = row["Unemployment Rate"] - us_unemp
            delta_part = row["Participation Rate"] - us_part
            fig.add_annotation(
                x=row["Unemployment Rate"] + 0.5,
                y=row["State"],
                text=f"Δ {delta_unemp:+.2f}% vs US",
                showarrow=False,
                font=dict(color=palette[1], size=12),
                xanchor="left",
                yshift=10
            )
            fig.add_annotation(
                x=row["Participation Rate"] + 0.5,
                y=row["State"],
                text=f"Δ {delta_part:+.2f}% vs US",
                showarrow=False,
                font=dict(color=palette[0], size=12),
                xanchor="left",
                yshift=-10
            )

    # --- Average line overlay if >1 state ---
    if not df.empty and len(df) > 1:
        avg_unemp = df["Unemployment Rate"].mean()
        avg_part = df["Participation Rate"].mean()
        fig.add_shape(type="line",
            x0=avg_unemp, x1=avg_unemp,
            y0=-0.5, y1=len(df)-0.5,
            line=dict(color=palette[1], width=2, dash="dot"),
            xref="x", yref="y"
        )
        fig.add_shape(type="line",
            x0=avg_part, x1=avg_part,
            y0=-0.5, y1=len(df)-0.5,
            line=dict(color=palette[0], width=2, dash="dot"),
            xref="x", yref="y"
        )

    fig.update_layout(
        barmode="group",
        template=PLOTLY_TEMPLATE,
        plot_bgcolor="#0A1224",
        paper_bgcolor="#0A1224",
        font=dict(color="#EAEAEA"),
        legend=dict(
            bgcolor="#101A33",
            bordercolor="#1E90FF",
            borderwidth=1,
            font=dict(color="#EAEAEA", size=14),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(title="%", showgrid=True, gridcolor="#222A44", zeroline=False, showline=True, linewidth=1, linecolor="#EAEAEA"),
        yaxis=dict(title="State", showgrid=False, showline=False),
        hovermode="y unified",
        title=f"State Unemployment vs Participation Rate ({start_year}–{end_year})"
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show raw data"):
        st.dataframe(df)
        csv = df.to_csv().encode('utf-8')
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f"state_comparison_{start_year}_{end_year}.csv",
            mime='text/csv'
        )

elif view == "📂 Upload Your CSV":
    st.subheader("📂 Upload and Visualize Your CSV Data")
    st.markdown("Upload a CSV file, preview the first 5 rows, and plot selected columns as a line or bar chart.")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        try:
            df = load_csv(uploaded_file)
            if df.empty:
                st.warning("No data available for the selected state and year range.")
            else:
                st.success("File uploaded successfully!")

                st.subheader("Preview: First 5 Rows")
                st.dataframe(df.head())

                st.subheader("Plot Columns")
                columns = df.columns.tolist()
                x_col = st.selectbox("Select X-axis column", columns)
                y_cols = st.multiselect("Select Y-axis column(s)", columns, default=[col for col in columns if col != x_col])

                chart_type = st.radio("Chart Type", ("Line Chart", "Bar Chart"), horizontal=True)
                export_fmt = st.selectbox("Export Format", ["CSV"], index=0)

                if x_col and y_cols:
                    # --- X-axis datetime validation ---
                    x_is_datetime = pd.api.types.is_datetime64_any_dtype(df[x_col])
                    if not x_is_datetime:
                        try:
                            df[x_col] = pd.to_datetime(df[x_col], errors='coerce')
                            x_is_datetime = pd.api.types.is_datetime64_any_dtype(df[x_col])
                        except Exception:
                            x_is_datetime = False
                    if not x_is_datetime:
                        st.warning(f"X-axis column '{x_col}' could not be parsed as datetime. Plotting may not work as expected.")

                    non_numeric = [col for col in y_cols if not pd.api.types.is_numeric_dtype(df[col])]
                    if non_numeric:
                        st.warning(f"Selected Y-axis columns must be numeric. Non-numeric columns: {', '.join(non_numeric)}")
                    if len(y_cols) == 0 or len(non_numeric) == len(y_cols):
                        st.info("Please select at least one numeric Y-axis column to plot.")
                    else:
                        # --- Color scheme ---
                        palette = ["#00FBFF", "#12716C", "#F20F0F", "#CFE31D", "#0DD02A", "#004452", "#006AFF", "#C109E6", "#FFA500", "#FF69B4"]
                        import plotly.graph_objects as go
                        fig = go.Figure()
                        for i, col in enumerate([c for c in y_cols if c not in non_numeric]):
                            color = palette[i % len(palette)]
                            if chart_type == "Line Chart":
                                fig.add_trace(go.Scatter(
                                    x=df[x_col], y=df[col],
                                    mode='lines+markers',
                                    name=col,
                                    line=dict(color=color, width=2, shape='spline', smoothing=1.2),
                                    marker=dict(color=color),
                                    hovertemplate=f"<b>{col}</b>: %{{y:.2f}}<br><b>{x_col}</b>: %{{x}}<extra></extra>",
                                ))
                            else:
                                fig.add_trace(go.Bar(
                                    x=df[x_col], y=df[col],
                                    name=col,
                                    marker_color=color,
                                    hovertemplate=f"<b>{col}</b>: %{{y:.2f}}<br><b>{x_col}</b>: %{{x}}<extra></extra>",
                                ))
                        fig.update_layout(
                            template=PLOTLY_TEMPLATE,
                            plot_bgcolor="#0A1224",
                            paper_bgcolor="#0A1224",
                            font=dict(color="#EAEAEA"),
                            legend=dict(
                                bgcolor="#101A33",
                                bordercolor="#1E90FF",
                                borderwidth=1,
                                font=dict(color="#EAEAEA", size=14),
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                            ),
                            hovermode="x unified",
                            margin=dict(l=20, r=20, t=60, b=40),
                            xaxis=dict(
                                title=x_col,
                                showgrid=True,
                                gridcolor="#222A44",
                                zeroline=False,
                                showline=True,
                                linewidth=1,
                                linecolor="#EAEAEA",
                                tickformat="%b %Y" if x_is_datetime else None,
                                ticklabelmode="period" if x_is_datetime else None,
                                rangeslider=dict(visible=x_is_datetime)
                            ),
                            yaxis=dict(
                                title=", ".join([c for c in y_cols if c not in non_numeric]),
                                showgrid=True,
                                gridcolor="#222A44",
                                zeroline=False,
                                showline=True,
                                linewidth=1,
                                linecolor="#EAEAEA",
                            ),
                        )
                        if x_is_datetime:
                            fig.update_xaxes(tickformat="%b %Y")
                        st.plotly_chart(fig, use_container_width=True)
                        # --- Export to PNG (always show button) ---
                        try:
                            import kaleido
                            import plotly.io as pio
                            png_bytes = fig.to_image(format="png", engine="kaleido")
                            st.download_button(
                                label="Download Chart as PNG",
                                data=png_bytes,
                                file_name=f'user_uploaded_chart.png',
                                mime='image/png'
                            )
                        except Exception as e:
                            st.warning(f"PNG export failed: {e}. Please ensure 'kaleido' is installed.")
                else:
                    st.info("Please select both X-axis and at least one Y-axis column to plot.")

        except Exception as e:
            st.warning(f"Could not read the uploaded CSV file: {e}")
    else:
        st.info("Please upload a CSV file to preview its contents.")
elif view == "🤖 Economic Chatbot":
    render_chatbot()

