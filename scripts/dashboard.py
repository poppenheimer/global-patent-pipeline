import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Syne', sans-serif !important; }
    .main { background-color: #0e1117; }
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
    .insight-box {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #2a3a5c;
        border-left: 3px solid #4f7cff;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 8px 0;
        color: #c8d8ff;
        font-size: 0.9rem;
    }
    hr { border-color: #1e2a40 !important; margin: 2rem 0 !important; }
    .stTextInput input {
        background: #1a1f2e !important;
        border: 1px solid #2a3a5c !important;
        color: #e8f0ff !important;
        border-radius: 8px !important;
    }
    .section-label {
        font-size: 0.7rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #4f7cff;
        font-weight: 600;
        margin-bottom: 2px;
    }
</style>
""", unsafe_allow_html=True)

PALETTE = [
    "#4f7cff", "#ff6b6b", "#ffd166", "#06d6a0",
    "#a29bfe", "#fd79a8", "#00cec9", "#e17055",
    "#74b9ff", "#55efc4", "#fdcb6e", "#b2bec3",
    "#6c5ce7", "#00b894", "#e84393"
]

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(26,31,46,0.6)",
    font=dict(color="#7b8db0", family="DM Sans"),
    margin=dict(l=0, r=0, t=10, b=0),
)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)


# ── Data functions ──────────────────────────────────────────────────────────

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
        FROM patents WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """, conn)

@st.cache_data
def get_top_inventors(n=30):
    return pd.read_sql(f"""
        SELECT name, COUNT(DISTINCT patent_id) AS patents
        FROM inventors
        GROUP BY inventor_id
        ORDER BY patents DESC LIMIT {n}
    """, conn)

@st.cache_data
def get_top_companies(n=30):
    return pd.read_sql(f"""
        SELECT name, COUNT(DISTINCT patent_id) AS patents
        FROM companies
        GROUP BY assignee_id
        ORDER BY patents DESC LIMIT {n}
    """, conn)

@st.cache_data
def get_countries():
    return pd.read_sql("""
        SELECT l.country, COUNT(DISTINCT i.patent_id) AS patents
        FROM inventors i
        JOIN locations l ON i.location_id = l.location_id
        GROUP BY l.country ORDER BY patents DESC LIMIT 15
    """, conn)

# ── ADVANCED ANALYTICS queries ──────────────────────────────────────────────

@st.cache_data
def get_innovation_velocity():
    """Patent growth rate per country across decades."""
    return pd.read_sql("""
        SELECT
            l.country,
            CASE
                WHEN p.year BETWEEN 1976 AND 1985 THEN '1976-1985'
                WHEN p.year BETWEEN 1986 AND 1995 THEN '1986-1995'
                WHEN p.year BETWEEN 1996 AND 2005 THEN '1996-2005'
                WHEN p.year BETWEEN 2006 AND 2015 THEN '2006-2015'
                WHEN p.year BETWEEN 2016 AND 2025 THEN '2016-2025'
            END AS decade,
            COUNT(DISTINCT p.patent_id) AS patents
        FROM patents p
        JOIN inventors i ON p.patent_id = i.patent_id
        JOIN locations l ON i.location_id = l.location_id
        WHERE l.country IN (
            SELECT l2.country
            FROM inventors i2
            JOIN locations l2 ON i2.location_id = l2.location_id
            GROUP BY l2.country
            ORDER BY COUNT(DISTINCT i2.patent_id) DESC
            LIMIT 8
        )
        AND p.year IS NOT NULL
        GROUP BY l.country, decade
        ORDER BY l.country, decade
    """, conn)

@st.cache_data
def get_inventor_career_spans():
    """Distribution of how many years inventors stay active."""
    return pd.read_sql("""
        SELECT
            career_span,
            COUNT(*) AS inventors
        FROM (
            SELECT
                inventor_id,
                MAX(p.year) - MIN(p.year) AS career_span
            FROM inventors i
            JOIN patents p ON i.patent_id = p.patent_id
            WHERE p.year IS NOT NULL
            GROUP BY inventor_id
            HAVING COUNT(DISTINCT p.patent_id) > 1
        )
        GROUP BY career_span
        ORDER BY career_span
    """, conn)

@st.cache_data
def get_corporate_vs_independent():
    """Ratio of patents with company assignees vs no assignee, per decade."""
    return pd.read_sql("""
        SELECT
            CASE
                WHEN p.year BETWEEN 1976 AND 1985 THEN '1976-85'
                WHEN p.year BETWEEN 1986 AND 1995 THEN '1986-95'
                WHEN p.year BETWEEN 1996 AND 2005 THEN '1996-05'
                WHEN p.year BETWEEN 2006 AND 2015 THEN '2006-15'
                WHEN p.year BETWEEN 2016 AND 2025 THEN '2016-25'
            END AS decade,
            SUM(CASE WHEN c.patent_id IS NOT NULL THEN 1 ELSE 0 END) AS corporate,
            SUM(CASE WHEN c.patent_id IS NULL THEN 1 ELSE 0 END) AS independent
        FROM patents p
        LEFT JOIN companies c ON p.patent_id = c.patent_id
        WHERE p.year IS NOT NULL
        GROUP BY decade
        ORDER BY decade
    """, conn)

@st.cache_data
def get_patent_type_over_time():
    """Patent type (utility/design/plant) counts per decade."""
    return pd.read_sql("""
        SELECT
            CASE
                WHEN year BETWEEN 1976 AND 1985 THEN '1976-85'
                WHEN year BETWEEN 1986 AND 1995 THEN '1986-95'
                WHEN year BETWEEN 1996 AND 2005 THEN '1996-05'
                WHEN year BETWEEN 2006 AND 2015 THEN '2006-15'
                WHEN year BETWEEN 2016 AND 2025 THEN '2016-25'
            END AS decade,
            patent_type,
            COUNT(*) AS patents
        FROM patents
        WHERE year IS NOT NULL AND patent_type IS NOT NULL
        GROUP BY decade, patent_type
        ORDER BY decade, patent_type
    """, conn)

@st.cache_data
def get_prolific_inventor_trajectories():
    """Year-by-year patent counts for top 5 inventors."""
    return pd.read_sql("""
        SELECT
            i.inventor_id,
            i.name,
            p.year,
            COUNT(DISTINCT p.patent_id) AS patents
        FROM inventors i
        JOIN patents p ON i.patent_id = p.patent_id
        WHERE i.inventor_id IN (
            SELECT inventor_id FROM inventors
            GROUP BY inventor_id
            ORDER BY COUNT(DISTINCT patent_id) DESC
            LIMIT 5
        )
        AND p.year IS NOT NULL
        GROUP BY i.inventor_id, i.name, p.year
        ORDER BY i.name, p.year
    """, conn)


# ═══════════════════════════════════════════════════════════════════════════
# LAYOUT
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("<h1 style='font-size:2.6rem; color:#e8f0ff; margin-bottom:0'>💡 Global Patent Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#7b8db0; font-size:0.95rem; margin-top:4px'>Real U.S. patent data · USPTO PatentsView · 1976–2025</p>", unsafe_allow_html=True)

st.divider()

# ── Metrics ─────────────────────────────────────────────────────────────────
total, inv_total, co_total = get_summary()
col1, col2, col3 = st.columns(3)
col1.metric("TOTAL PATENTS",   f"{total:,}")
col2.metric("TOTAL INVENTORS", f"{inv_total:,}")
col3.metric("TOTAL COMPANIES", f"{co_total:,}")

st.divider()

# ── Yearly Trends ────────────────────────────────────────────────────────────
st.subheader("📈 Patents Granted Per Year")
yearly = get_yearly()
fig_yearly = go.Figure()
fig_yearly.add_trace(go.Scatter(
    x=yearly["year"], y=yearly["patents"],
    mode="lines", fill="tozeroy",
    line=dict(color="#4f7cff", width=2.5),
    fillcolor="rgba(79,124,255,0.15)",
    hovertemplate="<b>%{x}</b><br>%{y:,} patents<extra></extra>"
))
fig_yearly.update_layout(**LAYOUT_BASE, height=300,
    xaxis=dict(showgrid=False, color="#4a5568"),
    yaxis=dict(gridcolor="#1e2a40", color="#4a5568"),
)
st.plotly_chart(fig_yearly, use_container_width=True)

st.divider()

# ── Top Inventors & Companies ─────────────────────────────────────────────
col_inv, col_co = st.columns(2)

with col_inv:
    st.subheader("🏆 Top Inventors")
    n_inv = st.slider("Top N inventors", 5, 30, 10, key="inv_slider")
    top_inv = get_top_inventors(30).head(n_inv).iloc[::-1]
    fig_inv = go.Figure(go.Bar(
        x=top_inv["patents"], y=top_inv["name"], orientation="h",
        marker=dict(color=top_inv["patents"],
                    colorscale=[[0,"#1a2a6c"],[0.5,"#4f7cff"],[1,"#00d4ff"]],
                    showscale=False),
        hovertemplate="<b>%{y}</b><br>%{x:,} patents<extra></extra>"
    ))
    fig_inv.update_layout(**LAYOUT_BASE, height=400,
        xaxis=dict(gridcolor="#1e2a40", color="#4a5568"),
        yaxis=dict(showgrid=False, color="#c8d8ff", tickfont=dict(size=11)),
    )
    st.plotly_chart(fig_inv, use_container_width=True)

with col_co:
    st.subheader("🏢 Top Companies")
    n_co = st.slider("Top N companies", 5, 30, 10, key="co_slider")
    top_co = get_top_companies(30).head(n_co).iloc[::-1]
    fig_co = go.Figure(go.Bar(
        x=top_co["patents"], y=top_co["name"], orientation="h",
        marker=dict(color=top_co["patents"],
                    colorscale=[[0,"#4a0030"],[0.5,"#ff6b6b"],[1,"#ffd166"]],
                    showscale=False),
        hovertemplate="<b>%{y}</b><br>%{x:,} patents<extra></extra>"
    ))
    fig_co.update_layout(**LAYOUT_BASE, height=400,
        xaxis=dict(gridcolor="#1e2a40", color="#4a5568"),
        yaxis=dict(showgrid=False, color="#c8d8ff", tickfont=dict(size=11)),
    )
    st.plotly_chart(fig_co, use_container_width=True)

st.divider()

# ── Countries ────────────────────────────────────────────────────────────────
st.subheader("🌍 Patents by Country")
top_countries = get_countries()
col_bar, col_pie = st.columns([3, 2])

with col_bar:
    fig_countries = go.Figure(go.Bar(
        x=top_countries["country"], y=top_countries["patents"],
        marker=dict(color=PALETTE[:len(top_countries)]),
        hovertemplate="<b>%{x}</b><br>%{y:,} patents<extra></extra>"
    ))
    fig_countries.update_layout(**LAYOUT_BASE, height=320,
        xaxis=dict(showgrid=False, color="#4a5568"),
        yaxis=dict(gridcolor="#1e2a40", color="#4a5568"),
    )
    st.plotly_chart(fig_countries, use_container_width=True)

with col_pie:
    fig_pie = go.Figure(go.Pie(
        labels=top_countries["country"], values=top_countries["patents"],
        hole=0.45,
        marker=dict(colors=PALETTE[:len(top_countries)], line=dict(color="#0e1117", width=2)),
        textfont=dict(size=11, color="#e8f0ff"),
        hovertemplate="<b>%{label}</b><br>%{value:,} patents<br>%{percent}<extra></extra>"
    ))
    fig_pie.update_layout(**LAYOUT_BASE, height=320,
        legend=dict(font=dict(color="#7b8db0", size=11)),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# ── ADVANCED ANALYTICS ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("<p class='section-label'>Advanced Analytics</p>", unsafe_allow_html=True)
st.subheader("🚀 Innovation Velocity by Country")
st.markdown("Patent output per decade for the top 8 countries — reveals who is accelerating and who has plateaued.")

velocity = get_innovation_velocity()
if not velocity.empty:
    fig_vel = px.line(
        velocity, x="decade", y="patents", color="country",
        markers=True,
        color_discrete_sequence=PALETTE,
    )
    fig_vel.update_traces(line=dict(width=2.5), marker=dict(size=8))
    fig_vel.update_layout(**LAYOUT_BASE, height=380,
        xaxis=dict(showgrid=False, color="#4a5568", title=None),
        yaxis=dict(gridcolor="#1e2a40", color="#4a5568", title="Patents granted"),
        legend=dict(font=dict(color="#c8d8ff", size=11), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_vel, use_container_width=True)

    # Auto insight
    pivot = velocity.pivot(index="decade", columns="country", values="patents").fillna(0)
    if "2006-2015" in pivot.index and "2016-2025" in pivot.index:
        growth = ((pivot.loc["2016-2025"] - pivot.loc["2006-2015"]) / pivot.loc["2006-2015"].replace(0,1) * 100)
        fastest = growth.idxmax()
        pct = growth.max()
        st.markdown(f"<div class='insight-box'>📊 <b>Insight:</b> <b style='color:#4f7cff'>{fastest}</b> had the fastest patent growth in the most recent decade (+{pct:.0f}% vs prior decade).</div>", unsafe_allow_html=True)

st.divider()

# ── Corporate vs Independent ─────────────────────────────────────────────────
st.subheader("🏭 Corporate vs Independent Inventors Over Time")
st.markdown("Has invention become more corporatised? This shows the shifting balance between company-assigned and individually-filed patents across decades.")

corp = get_corporate_vs_independent()
if not corp.empty:
    corp["total"] = corp["corporate"] + corp["independent"]
    corp["corp_pct"]  = (corp["corporate"]  / corp["total"] * 100).round(1)
    corp["indep_pct"] = (corp["independent"] / corp["total"] * 100).round(1)

    fig_corp = go.Figure()
    fig_corp.add_trace(go.Bar(
        name="Corporate", x=corp["decade"], y=corp["corp_pct"],
        marker_color="#4f7cff",
        hovertemplate="<b>%{x}</b><br>Corporate: %{y:.1f}%<extra></extra>"
    ))
    fig_corp.add_trace(go.Bar(
        name="Independent", x=corp["decade"], y=corp["indep_pct"],
        marker_color="#ffd166",
        hovertemplate="<b>%{x}</b><br>Independent: %{y:.1f}%<extra></extra>"
    ))
    fig_corp.update_layout(**LAYOUT_BASE, barmode="stack", height=320,
        xaxis=dict(showgrid=False, color="#4a5568", title=None),
        yaxis=dict(gridcolor="#1e2a40", color="#4a5568", title="% of patents", ticksuffix="%"),
        legend=dict(font=dict(color="#c8d8ff", size=11), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_corp, use_container_width=True)

    if len(corp) >= 2:
        first_corp = corp.iloc[0]["corp_pct"]
        last_corp  = corp.iloc[-1]["corp_pct"]
        direction  = "increased" if last_corp > first_corp else "decreased"
        st.markdown(f"<div class='insight-box'>📊 <b>Insight:</b> Corporate patent share has <b>{direction}</b> from <b style='color:#4f7cff'>{first_corp:.1f}%</b> in the first decade to <b style='color:#4f7cff'>{last_corp:.1f}%</b> in the most recent — reflecting how invention has {('become more institutionalised' if direction == 'increased' else 'seen a resurgence of independent inventors')}.</div>", unsafe_allow_html=True)

st.divider()

# ── Inventor Career Spans ─────────────────────────────────────────────────────
st.subheader("🧬 Inventor Career Span Distribution")
st.markdown("How long do inventors stay active in the patent system? This shows the distribution of active years between first and last patent for multi-patent inventors.")

spans = get_inventor_career_spans()
if not spans.empty:
    spans = spans[spans["career_span"] <= 40]  # cap outliers for readability

    fig_span = go.Figure(go.Bar(
        x=spans["career_span"], y=spans["inventors"],
        marker=dict(
            color=spans["inventors"],
            colorscale=[[0,"#16213e"],[0.5,"#06d6a0"],[1,"#00b894"]],
            showscale=False,
        ),
        hovertemplate="<b>%{x} year career</b><br>%{y:,} inventors<extra></extra>"
    ))
    fig_span.update_layout(**LAYOUT_BASE, height=300,
        xaxis=dict(showgrid=False, color="#4a5568", title="Active years (first to last patent)"),
        yaxis=dict(gridcolor="#1e2a40", color="#4a5568", title="Number of inventors"),
    )
    st.plotly_chart(fig_span, use_container_width=True)

    median_span = spans.loc[spans["inventors"].idxmax(), "career_span"]
    long_career = int(spans[spans["career_span"] >= 20]["inventors"].sum())
    st.markdown(f"<div class='insight-box'>📊 <b>Insight:</b> The most common active career length is <b style='color:#06d6a0'>{median_span} years</b>. <b style='color:#06d6a0'>{long_career:,}</b> inventors maintained active patent careers spanning 20+ years.</div>", unsafe_allow_html=True)

st.divider()

# ── Patent Type Over Time ────────────────────────────────────────────────────
st.subheader("🔬 Patent Type Mix Across Decades")
st.markdown("Utility, design, and plant patents each serve different purposes. This shows how the composition of U.S. patents has shifted over time.")

type_data = get_patent_type_over_time()
if not type_data.empty:
    fig_type = px.bar(
        type_data, x="decade", y="patents", color="patent_type",
        barmode="group",
        color_discrete_sequence=["#4f7cff", "#ff6b6b", "#06d6a0", "#ffd166", "#a29bfe"],
    )
    fig_type.update_layout(**LAYOUT_BASE, height=320,
        xaxis=dict(showgrid=False, color="#4a5568", title=None),
        yaxis=dict(gridcolor="#1e2a40", color="#4a5568", title="Patents granted"),
        legend=dict(font=dict(color="#c8d8ff", size=11), bgcolor="rgba(0,0,0,0)", title=None),
    )
    st.plotly_chart(fig_type, use_container_width=True)

st.divider()

# ── Top Inventor Trajectories ─────────────────────────────────────────────────
st.subheader("🌟 Top Inventor Year-by-Year Trajectories")
st.markdown("Tracking the annual patent output of the 5 most prolific inventors — shows peak years, bursts of activity, and career patterns.")

traj = get_prolific_inventor_trajectories()
if not traj.empty:
    fig_traj = px.line(
        traj, x="year", y="patents", color="name",
        markers=True,
        color_discrete_sequence=PALETTE,
    )
    fig_traj.update_traces(line=dict(width=2), marker=dict(size=6))
    fig_traj.update_layout(**LAYOUT_BASE, height=360,
        xaxis=dict(showgrid=False, color="#4a5568", title=None),
        yaxis=dict(gridcolor="#1e2a40", color="#4a5568", title="Patents per year"),
        legend=dict(font=dict(color="#c8d8ff", size=11), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_traj, use_container_width=True)

st.divider()

# ── Search ───────────────────────────────────────────────────────────────────
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
        results, use_container_width=True,
        column_config={
            "patent_id":    st.column_config.TextColumn("Patent ID"),
            "patent_title": st.column_config.TextColumn("Title", width="large"),
            "year":         st.column_config.NumberColumn("Year"),
            "patent_type":  st.column_config.TextColumn("Type"),
        }
    )
