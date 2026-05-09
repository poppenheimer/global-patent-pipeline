import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DB_PATH = "patent_intelligence.db"

st.set_page_config(
    page_title="Global Patent Intelligence",
    page_icon="💡",
    layout="wide"
)

# ── Custom CSS ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
    }
    .main { background-color: #0e1117; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #2a3a5c;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }
    [data-testid="metric-container"] label {
        color: #7b8db0 !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #e8f0ff !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 2rem !important;
    }

    /* Divider */
    hr { border-color: #1e2a40 !important; margin: 2rem 0 !important; }

    /* Search box */
    .stTextInput input {
        background: #1a1f2e !important;
        border: 1px solid #2a3a5c !important;
        color: #e8f0ff !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Colour palette used across all charts
PALETTE = [
    "#4f7cff", "#ff6b6b", "#ffd166", "#06d6a0",
    "#a29bfe", "#fd79a8", "#00cec9", "#e17055",
    "#74b9ff", "#55efc4", "#fdcb6e", "#b2bec3",
    "#6c5ce7", "#00b894", "#e84393"
]

conn = sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def get_summary():
    total     = pd.read_sql("SELECT COUNT(*) AS n FROM patents", conn).iloc[0]["n"]
    inv_total = pd.read_sql("SELECT COUNT(DISTINCT inventor_id) AS n FROM inventors", conn).iloc[0]["n"]
    co_total  = pd.read_sql("SELECT COUNT(DISTINCT assignee_id) AS n FROM companies", conn).iloc[0]["n"]
    return int(total), int(inv_total), int(co_total)

@st.cache_data
def get_yearly():
    return pd.read_sql("""
        SELECT year, COUNT(*) AS patents
        FROM patents
        WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """, conn)

@st.cache_data
def get_top_inventors(n=30):
    return pd.read_sql(f"""
        SELECT name, COUNT(DISTINCT patent_id) AS patents
        FROM inventors
        GROUP BY inventor_id
        ORDER BY patents DESC
        LIMIT {n}
    """, conn)

@st.cache_data
def get_top_companies(n=30):
    return pd.read_sql(f"""
        SELECT name, COUNT(DISTINCT patent_id) AS patents
        FROM companies
        GROUP BY assignee_id
        ORDER BY patents DESC
        LIMIT {n}
    """, conn)

@st.cache_data
def get_countries():
    return pd.read_sql("""
        SELECT l.country, COUNT(DISTINCT i.patent_id) AS patents
        FROM inventors i
        JOIN locations l ON i.location_id = l.location_id
        GROUP BY l.country
        ORDER BY patents DESC
        LIMIT 15
    """, conn)


# ── Header ──
st.markdown("<h1 style='font-size:2.6rem; color:#e8f0ff; margin-bottom:0'>💡 Global Patent Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#7b8db0; font-size:0.95rem; margin-top:4px'>Real U.S. patent data · USPTO PatentsView · 1976–2025</p>", unsafe_allow_html=True)

st.divider()

# ── Metrics ──
total, inv_total, co_total = get_summary()
col1, col2, col3 = st.columns(3)
col1.metric("TOTAL PATENTS",   f"{total:,}")
col2.metric("TOTAL INVENTORS", f"{inv_total:,}")
col3.metric("TOTAL COMPANIES", f"{co_total:,}")

st.divider()

# ── Yearly Trends ──
st.subheader("📈 Patents Granted Per Year")
yearly = get_yearly()

fig_yearly = go.Figure()
fig_yearly.add_trace(go.Scatter(
    x=yearly["year"],
    y=yearly["patents"],
    mode="lines",
    fill="tozeroy",
    line=dict(color="#4f7cff", width=2.5),
    fillcolor="rgba(79,124,255,0.15)",
    hovertemplate="<b>%{x}</b><br>%{y:,} patents<extra></extra>"
))
fig_yearly.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(26,31,46,0.6)",
    font=dict(color="#7b8db0", family="DM Sans"),
    xaxis=dict(showgrid=False, color="#4a5568"),
    yaxis=dict(gridcolor="#1e2a40", color="#4a5568"),
    margin=dict(l=0, r=0, t=10, b=0),
    height=320,
)
st.plotly_chart(fig_yearly, use_container_width=True)

st.divider()

# ── Inventors & Companies side by side ──
col_inv, col_co = st.columns(2)

with col_inv:
    st.subheader("🏆 Top Inventors")
    n_inv = st.slider("Show top N inventors", 5, 30, 10, key="inv_slider")
    top_inv = get_top_inventors(30).head(n_inv).iloc[::-1]

    fig_inv = go.Figure(go.Bar(
        x=top_inv["patents"],
        y=top_inv["name"],
        orientation="h",
        marker=dict(
            color=top_inv["patents"],
            colorscale=[[0, "#1a2a6c"], [0.5, "#4f7cff"], [1, "#00d4ff"]],
            showscale=False,
        ),
        hovertemplate="<b>%{y}</b><br>%{x:,} patents<extra></extra>"
    ))
    fig_inv.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,31,46,0.6)",
        font=dict(color="#7b8db0", family="DM Sans"),
        xaxis=dict(gridcolor="#1e2a40", color="#4a5568"),
        yaxis=dict(showgrid=False, color="#c8d8ff", tickfont=dict(size=11)),
        margin=dict(l=0, r=0, t=10, b=0),
        height=420,
    )
    st.plotly_chart(fig_inv, use_container_width=True)

with col_co:
    st.subheader("🏢 Top Companies")
    n_co = st.slider("Show top N companies", 5, 30, 10, key="co_slider")
    top_co = get_top_companies(30).head(n_co).iloc[::-1]

    fig_co = go.Figure(go.Bar(
        x=top_co["patents"],
        y=top_co["name"],
        orientation="h",
        marker=dict(
            color=top_co["patents"],
            colorscale=[[0, "#4a0030"], [0.5, "#ff6b6b"], [1, "#ffd166"]],
            showscale=False,
        ),
        hovertemplate="<b>%{y}</b><br>%{x:,} patents<extra></extra>"
    ))
    fig_co.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,31,46,0.6)",
        font=dict(color="#7b8db0", family="DM Sans"),
        xaxis=dict(gridcolor="#1e2a40", color="#4a5568"),
        yaxis=dict(showgrid=False, color="#c8d8ff", tickfont=dict(size=11)),
        margin=dict(l=0, r=0, t=10, b=0),
        height=420,
    )
    st.plotly_chart(fig_co, use_container_width=True)

st.divider()

# ── Countries ──
st.subheader("🌍 Patents by Country")
top_countries = get_countries()

col_bar, col_pie = st.columns([3, 2])

with col_bar:
    fig_countries = go.Figure(go.Bar(
        x=top_countries["country"],
        y=top_countries["patents"],
        marker=dict(color=PALETTE[:len(top_countries)]),
        hovertemplate="<b>%{x}</b><br>%{y:,} patents<extra></extra>"
    ))
    fig_countries.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,31,46,0.6)",
        font=dict(color="#7b8db0", family="DM Sans"),
        xaxis=dict(showgrid=False, color="#4a5568"),
        yaxis=dict(gridcolor="#1e2a40", color="#4a5568"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=340,
    )
    st.plotly_chart(fig_countries, use_container_width=True)

with col_pie:
    fig_pie = go.Figure(go.Pie(
        labels=top_countries["country"],
        values=top_countries["patents"],
        hole=0.45,
        marker=dict(colors=PALETTE[:len(top_countries)], line=dict(color="#0e1117", width=2)),
        textfont=dict(size=11, color="#e8f0ff"),
        hovertemplate="<b>%{label}</b><br>%{value:,} patents<br>%{percent}<extra></extra>"
    ))
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#7b8db0", family="DM Sans"),
        legend=dict(font=dict(color="#7b8db0", size=11)),
        margin=dict(l=0, r=0, t=10, b=0),
        height=340,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ── Search ──
st.subheader("🔍 Search Patents")
search = st.text_input("Search by keyword in patent title", placeholder="e.g. artificial intelligence, battery, semiconductor...")
if search:
    results = pd.read_sql("""
        SELECT patent_id, patent_title, year, patent_type
        FROM patents
        WHERE patent_title LIKE ?
        ORDER BY year DESC
        LIMIT 50
    """, conn, params=(f"%{search}%",))
    st.markdown(f"<p style='color:#7b8db0'>Found <b style='color:#4f7cff'>{len(results)}</b> results</p>", unsafe_allow_html=True)
    st.dataframe(
        results,
        use_container_width=True,
        column_config={
            "patent_id":    st.column_config.TextColumn("Patent ID"),
            "patent_title": st.column_config.TextColumn("Title", width="large"),
            "year":         st.column_config.NumberColumn("Year"),
            "patent_type":  st.column_config.TextColumn("Type"),
        }
    )
