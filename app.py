"""Veridi Logistics — Last-Mile Delivery Auditor  ·  Streamlit dashboard.

Reads small pre-computed aggregates from ./app_data/ (committed) plus the Brazil GeoJSON
(downloaded at runtime), so it runs on Streamlit Community Cloud without the raw Olist dataset.

Run locally:  MLprojs/bin/streamlit run app.py
"""
import json
import os
import urllib.request

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

GEO_URL = ("https://raw.githubusercontent.com/codeforgermany/click_that_hood/"
           "main/public/data/brazil-states.geojson")
GEO_LOCAL = "brazil_states.geojson"

# palette (AMALITECH accent + clean neutrals)
ACCENT, INK, MUTED = "#F26A21", "#101828", "#667085"
GREEN, AMBER, RED, BLUE = "#12B76A", "#F79009", "#F04438", "#2E90FA"
STATUS_COLOR = {"On Time": GREEN, "Late": AMBER, "Super Late": RED}
TIER = {"Healthy": GREEN, "Watch": AMBER, "Critical": RED}

st.set_page_config(page_title="Veridi · Delivery Auditor", page_icon="🚚",
                   layout="wide", initial_sidebar_state="expanded")


@st.cache_data
def load():
    state = pd.read_csv("app_data/state_perf.csv")
    status = pd.read_csv("app_data/status_summary.csv")
    score = pd.read_csv("app_data/score_by_status.csv")
    cat = pd.read_csv("app_data/category_perf.csv")
    monthly = pd.read_csv("app_data/monthly.csv")
    bott = pd.read_csv("app_data/bottleneck.csv")
    with open("app_data/kpis.json") as f:
        kpis = json.load(f)
    if not os.path.exists(GEO_LOCAL):
        urllib.request.urlretrieve(GEO_URL, GEO_LOCAL)
    with open(GEO_LOCAL, encoding="utf-8") as f:
        geo = json.load(f)
    return state, status, score, cat, monthly, bott, kpis, geo


state, status, score, cat, monthly, bott, kpis, geo = load()

# ------------------------------------------------------------------ CSS
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL@20..48,400,0..1');
  html, body, [class*="css"], button, input { font-family:'Inter',sans-serif !important; }
  .stApp { background:#F6F7F9; }
  #MainMenu, footer { display:none; }
  header[data-testid="stHeader"] { background:transparent; }   /* keep the sidebar toggle visible */
  /* make the sidebar collapse/expand control obvious */
  button[data-testid="stSidebarCollapseButton"], button[data-testid="collapsedControl"],
  [data-testid="stSidebarCollapsedControl"] { color:#F26A21 !important; }
  .block-container { padding:1.4rem 2rem 2rem; max-width:1320px; }
  .material-symbols-rounded { font-family:'Material Symbols Rounded'; vertical-align:middle; }

  /* ---------- sidebar ---------- */
  section[data-testid="stSidebar"] { background:#FFFFFF; border-right:1px solid #ECEFF3; width:248px !important; }
  section[data-testid="stSidebar"] .block-container { padding-top:1.2rem; }
  .logo { font-size:23px; font-weight:800; letter-spacing:-1px; color:#101828; padding:2px 4px 0; }
  .logo .x { color:#F26A21; }
  .logo-sub { font-size:11px; color:#98A2B3; padding:1px 4px 14px; font-weight:600; letter-spacing:.04em; }
  .poweredby { text-align:center; font-size:11px; color:#98A2B3; margin-top:14px;
               border-top:1px solid #ECEFF3; padding-top:10px; }
  .poweredby b { color:#475467; } .poweredby .x { color:#F26A21; }
  .navcap { font-size:11px; font-weight:700; letter-spacing:.08em; color:#98A2B3;
            text-transform:uppercase; margin:14px 6px 4px; }
  /* nav buttons */
  section[data-testid="stSidebar"] .stButton>button {
      width:100%; justify-content:flex-start; gap:10px; border:none; background:transparent;
      color:#475467; font-weight:600; font-size:14px; padding:9px 12px; border-radius:9px; box-shadow:none; }
  section[data-testid="stSidebar"] .stButton>button:hover { background:#F4F5F7; color:#101828; }
  section[data-testid="stSidebar"] .stButton>button[kind="primary"] {
      background:#FFF3EC; color:#F26A21; }
  .getstarted { background:#101828; color:#fff; border-radius:12px; padding:14px; margin-top:16px; }
  .getstarted b { font-size:13px; } .getstarted p { font-size:11px; color:#98A2B3; margin:4px 0 0; }
  .userbox { display:flex; align-items:center; gap:10px; margin-top:14px; padding-top:12px;
             border-top:1px solid #ECEFF3; }
  .avatar { width:34px;height:34px;border-radius:50%;background:#F26A21;color:#fff;display:flex;
            align-items:center;justify-content:center;font-weight:700;font-size:13px; }
  .userbox .n { font-size:13px;font-weight:600;color:#101828; } .userbox .e { font-size:11px;color:#98A2B3; }

  /* ---------- header ---------- */
  .h-title { font-size:24px; font-weight:800; color:#101828; letter-spacing:-.5px; }
  .h-sub { font-size:13px; color:#667085; margin-top:1px; }

  /* ---------- cards (st.container border) ---------- */
  div[data-testid="stVerticalBlockBorderWrapper"] {
      background:#fff; border:1px solid #ECEFF3 !important; border-radius:16px;
      box-shadow:0 1px 2px rgba(16,24,40,.04); }
  .card-h { font-size:15px; font-weight:700; color:#101828; }

  /* ---------- KPI ---------- */
  .kpi { background:#fff; border:1px solid #ECEFF3; border-radius:14px; padding:15px 16px; height:100%; }
  .kpi .ic { width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center; }
  .kpi .ic .material-symbols-rounded { font-size:20px; }
  .kpi .lab { font-size:12.5px; color:#667085; font-weight:500; margin-top:10px; }
  .kpi .val { font-size:24px; font-weight:800; color:#101828; line-height:1.1; margin-top:2px; }
  .kpi .delta { font-size:12px; font-weight:700; margin-left:6px; }

  /* badges */
  .badge { padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600; }
  /* insight callout */
  .callout { background:#fff; border:1px solid #ECEFF3; border-left:4px solid #F26A21;
             border-radius:12px; padding:13px 16px; font-size:13.5px; color:#475467;
             box-shadow:0 1px 2px rgba(16,24,40,.04); }
  .callout b { color:#101828; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar nav
if "view" not in st.session_state:
    st.session_state.view = "Overview"
NAV = [("Overview", "dashboard", "WORK"), ("Regional", "public", None),
       ("Sentiment", "sentiment_satisfied", None),
       ("Categories", "category", "ANALYSIS"), ("Operations", "conveyor_belt", None),
       ("Revenue", "payments", None)]

with st.sidebar:
    st.markdown('<div class="logo">AMALIT<span class="x">≡</span>CH</div>'
                '<div class="logo-sub">LOGISTICS INTELLIGENCE</div>', unsafe_allow_html=True)
    for name, icon, cap in NAV:
        if cap:
            st.markdown(f'<div class="navcap">{cap}</div>', unsafe_allow_html=True)
        if st.button(name, icon=f":material/{icon}:", use_container_width=True,
                     type="primary" if st.session_state.view == name else "secondary",
                     key=f"nav_{name}"):
            st.session_state.view = name
    st.markdown('<div class="getstarted"><b>📈 Audit complete</b>'
                '<p>Veridi delivery performance · Olist dataset</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="userbox"><div class="avatar">JF</div>'
                '<div><div class="n">Joseph Forson</div><div class="e">Data Engineer</div></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="poweredby">Powered by <b>AMALIT<span class="x">≡</span>CH</b></div>',
                unsafe_allow_html=True)

view = st.session_state.view


# ------------------------------------------------------------------ helpers
def money(v):
    return f"R$ {v/1e6:.2f}M" if v >= 1e6 else f"R$ {v/1e3:.0f}k"


def kpi(col, icon, value, label, accent=ACCENT, delta=None, dcolor=MUTED):
    d = f'<span class="delta" style="color:{dcolor}">{delta}</span>' if delta else ""
    col.markdown(f"""<div class="kpi">
        <div class="ic" style="background:{accent}1a;color:{accent}">
          <span class="material-symbols-rounded">{icon}</span></div>
        <div class="lab">{label}</div>
        <div class="val">{value}{d}</div></div>""", unsafe_allow_html=True)


def callout(text, color=ACCENT):
    st.markdown(f'<div class="callout" style="border-left-color:{color}">{text}</div>',
                unsafe_allow_html=True)


PCFG = {"displayModeBar": False}            # hide the Plotly toolbar clutter


def style_fig(fig, h=300):
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=14, b=8),
                      paper_bgcolor="white", plot_bgcolor="white",
                      font=dict(family="Inter", color=INK, size=12),
                      legend=dict(orientation="h", y=1.14, x=0),
                      hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter",
                                      bordercolor="#E4E7EC"))
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False)
    fig.update_yaxes(gridcolor="#F2F4F7", zeroline=False, showline=False)
    return fig


def page_header(title, sub):
    a, b = st.columns([3, 1])
    a.markdown(f'<div class="h-title">{title}</div><div class="h-sub">{sub}</div>', unsafe_allow_html=True)
    b.selectbox("period", ["All time", "Delivered orders only"], label_visibility="collapsed")


# ================================================================== OVERVIEW
if view == "Overview":
    page_header("Delivery Performance", "Are we failing specific regions, or is this nationwide?")
    st.write("")
    left, right = st.columns([1.55, 1])

    with left:
        with st.container(border=True):
            top = st.columns([2, 1])
            top[0].markdown('<div class="card-h">Late-rate trend</div>', unsafe_allow_html=True)
            with top[1]:
                mode = st.segmented_control("m", ["% Late", "Volume"], default="% Late",
                                            label_visibility="collapsed")
            mdf = monthly.copy()
            mdf["mdate"] = pd.to_datetime(mdf["month"] + "-01")
            nat = kpis["national_late_rate"]
            if mode == "Volume":
                bars = ["#E7EAEE"] * (len(mdf) - 1) + [ACCENT]
                f = go.Figure(go.Bar(x=mdf.mdate, y=mdf.orders,
                                     marker=dict(color=bars, cornerradius=6, line_width=0),
                                     hovertemplate="%{x|%b %Y}<br><b>%{y:,}</b> orders<extra></extra>"))
                f.update_layout(yaxis_title=None, bargap=0.34)
            else:
                f = go.Figure()
                f.add_trace(go.Scatter(x=mdf.mdate, y=mdf.pct_late, mode="lines",
                    line=dict(color=ACCENT, width=3, shape="spline"),
                    fill="tozeroy", fillcolor="rgba(242,106,33,.10)",
                    hovertemplate="%{x|%b %Y}<br><b>%{y:.1f}%</b> late<extra></extra>"))
                pk = mdf.loc[mdf.pct_late.idxmax()]
                f.add_trace(go.Scatter(x=[pk["mdate"]], y=[pk["pct_late"]], mode="markers+text",
                    marker=dict(color=ACCENT, size=11, line=dict(color="white", width=2)),
                    text=[f"  {pk['pct_late']:.0f}%"], textposition="middle right",
                    textfont=dict(color=ACCENT, size=12, family="Inter"), hoverinfo="skip"))
                f.add_hline(y=nat, line_dash="dot", line_color="#98A2B3",
                    annotation_text=f"national avg {nat}%", annotation_position="bottom right",
                    annotation_font=dict(size=11, color="#98A2B3"))
                f.update_layout(yaxis_title=None, yaxis_ticksuffix="%", showlegend=False)
            f.update_xaxes(tickformat="%b %Y", dtick="M6")
            f.update_layout(xaxis_title=None)
            st.plotly_chart(style_fig(f, 300), use_container_width=True, config=PCFG)

    with right:
        g = st.columns(2)
        kpi(g[0], "local_shipping", f'{kpis["national_late_rate"]}%', "Late rate", RED,
            f'{kpis["worst_state"]} {kpis["worst_state_rate"]}%', RED)
        kpi(g[1], "warning", money(kpis["revenue_at_risk"]), "Revenue at risk", AMBER,
            f'{kpis["revenue_at_risk_pct"]}%', AMBER)
        st.write("")
        g2 = st.columns(2)
        kpi(g2[0], "check_circle", f'{kpis["ontime_pct"]}%', "On-time", GREEN)
        kpi(g2[1], "schedule", f'+{kpis["national_promise_gap"]}d', "Promise gap", BLUE)

    st.write("")
    callout(f"<b>It's regional, not nationwide.</b> The North-east (AL, MA, PI, CE, SE) runs "
            f"2–3× the national <b>{kpis['national_late_rate']}%</b> late rate, while the "
            f"high-volume south-east stays reliable.")

    st.write("")
    best = state.sort_values("pct_late").iloc[0]
    worst = state.sort_values("pct_late").iloc[-1]
    bw = st.columns(2)
    kpi(bw[0], "trophy", f'{best.customer_state} · {best.pct_late}%', "Best state — lowest late rate", GREEN)
    kpi(bw[1], "priority_high", f'{worst.customer_state} · {worst.pct_late}%', "Worst state — highest late rate", RED)

    st.write("")
    with st.container(border=True):
        h = st.columns([2, 1.5, 1, 1])
        h[0].markdown('<div class="card-h">State performance</div>', unsafe_allow_html=True)
        q = h[1].text_input("search", placeholder="Search state…", label_visibility="collapsed")
        flt = h[2].selectbox("f", ["All status", "Critical", "Watch", "Healthy"],
                             label_visibility="collapsed")
        h[3].download_button("Export", state.to_csv(index=False), "veridi_states.csv",
                             "text/csv", icon=":material/download:", use_container_width=True)
        tbl = state.copy()
        if q:
            tbl = tbl[tbl.customer_state.str.contains(q.strip().upper())]
        if flt != "All status":
            tbl = tbl[tbl.status == flt]
        show = tbl[["customer_state", "orders", "pct_late", "pct_super_late",
                    "avg_promise_gap", "avg_delivery_days", "avg_review", "status"]]
        sty = (show.style
               .format({"orders": "{:,}", "pct_late": "{:.1f}%", "pct_super_late": "{:.1f}%",
                        "avg_promise_gap": "{:+.1f}d", "avg_delivery_days": "{:.1f}d",
                        "avg_review": "{:.2f} ★"})
               .apply(lambda s: [f"background-color:{TIER[v]}1f;color:{TIER[v]};font-weight:700;"
                                 "border-radius:8px;text-align:center" for v in s], subset=["status"]))
        st.dataframe(sty, use_container_width=True, hide_index=True, height=340,
                     column_config={"customer_state": "State", "orders": "Orders",
                                    "pct_late": "% Late", "pct_super_late": "Super-late",
                                    "avg_promise_gap": "Promise gap", "avg_delivery_days": "Avg delivery",
                                    "avg_review": "Rating", "status": "Status"})
        st.caption(f"Showing {len(show)} of {len(state)} states")

# ================================================================== REGIONAL
elif view == "Regional":
    page_header("Regional analysis", "Where the broken promises concentrate — and why distance matters.")
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="card-h">Late-rate by state — % labelled on each state</div>',
                    unsafe_allow_html=True)
        f = px.choropleth(state, geojson=geo, locations="customer_state",
                          featureidkey="properties.sigla", color="pct_late",
                          color_continuous_scale=["#FEF0E6", "#FBC9A8", "#F79B63",
                                                  "#F26A21", "#B23E0C"],
                          hover_name="customer_state",
                          hover_data={"pct_late": ":.1f", "orders": ":,",
                                      "avg_promise_gap": ":+.1f", "avg_delivery_days": ":.1f"})
        f.update_traces(marker_line_color="white", marker_line_width=0.8)

        # label each state with its code + % at the polygon centroid
        rate_map = dict(zip(state.customer_state, state.pct_late))
        rows = []
        for feat in geo["features"]:
            uf = feat["properties"]["sigla"]
            if uf not in rate_map:
                continue
            pts = []

            def _walk(c):
                if isinstance(c[0], (int, float)):
                    pts.append(c)
                else:
                    for sub in c:
                        _walk(sub)
            _walk(feat["geometry"]["coordinates"])
            rows.append((uf, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)))
        lab = pd.DataFrame(rows, columns=["uf", "lon", "lat"])
        f.add_trace(go.Scattergeo(
            lon=lab.lon, lat=lab.lat, mode="text",
            text=[f"<b>{u}</b><br>{rate_map[u]:.0f}%" for u in lab.uf],
            textfont=dict(size=9, color="#1F2D3D", family="Inter"),
            hoverinfo="skip", showlegend=False))

        f.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)",
                      showframe=False, showcoastlines=False)
        f.update_layout(coloraxis_colorbar=dict(title="% late", thickness=11, len=0.8,
                                                outlinewidth=0, ticksuffix="%"),
                        dragmode=False)
        st.plotly_chart(style_fig(f, 600), use_container_width=True, config=PCFG)
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="card-h">State drill-down</div>', unsafe_allow_html=True)
        sel = st.selectbox("state", sorted(state.customer_state), label_visibility="collapsed")
        r = state[state.customer_state == sel].iloc[0]
        c = st.columns(4)
        kpi(c[0], "local_shipping", f'{r.pct_late}%', "Late rate", TIER[r.status])
        kpi(c[1], "near_me", f'{int(r.dist_km):,} km', "Distance from hub", BLUE)
        kpi(c[2], "schedule", f'{r.avg_delivery_days}d', "Avg delivery", ACCENT)
        kpi(c[3], "star", f'{r.avg_review}', "Avg rating", AMBER)
    st.write("")
    callout("<b>Remoteness drives delivery time, not the late-rate directly.</b> Distance from the "
            "São Paulo hub correlates +0.91 with delivery time but only +0.15 with the late-rate — "
            "the far north is heavily padded, so the worst <i>lateness</i> lands on the mid-distance North-east.")

# ================================================================== SENTIMENT
elif view == "Sentiment":
    page_header("Customer sentiment", "Do late deliveries actually cause bad reviews?")
    st.write("")
    c = st.columns(3)
    for i, s in enumerate(["On Time", "Late", "Super Late"]):
        row = score[score.delivery_status == s]
        kpi(c[i], "sentiment_satisfied", f'{row.avg_score.iloc[0]:.2f} ★' if len(row) else "—",
            f"Avg score — {s}", STATUS_COLOR[s])
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="card-h">Average review score by delivery status</div>', unsafe_allow_html=True)
        f = px.bar(score, x="delivery_status", y="avg_score", text="avg_score",
                   color="delivery_status", color_discrete_map=STATUS_COLOR,
                   category_orders={"delivery_status": ["On Time", "Late", "Super Late"]})
        f.update_traces(marker_cornerradius=8)
        f.update_layout(showlegend=False, yaxis_range=[0, 5], xaxis_title="", yaxis_title="avg ★")
        st.plotly_chart(style_fig(f, 320), use_container_width=True, config=PCFG)
    callout("On-time ≈ <b>4.3★</b> → Super-Late ≈ <b>1.8★</b>. The negative-review spike is a "
            "<b>logistics</b> problem, not a product one.")

# ================================================================== CATEGORIES
elif view == "Categories":
    page_header("Product categories", "Which categories ship late most? (translated to English).")
    st.write("")
    worst_c = cat.iloc[0]
    c = st.columns(3)
    kpi(c[0], "category", f'{len(cat)}', "Categories analysed", BLUE)
    kpi(c[1], "trending_up", f'{worst_c["pct_late"]}%',
        f'Worst: {worst_c["cat"].replace("_", " ").title()[:20]}', RED)
    kpi(c[2], "inventory_2", f'{int(cat["orders"].sum()):,}', "Orders covered", ACCENT)
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="card-h">Late-rate by product category (top 15)</div>', unsafe_allow_html=True)
        top = cat.head(15).sort_values("pct_late")
        top = top.assign(label=top["cat"].str.replace("_", " ").str.title())
        f = px.bar(top, x="pct_late", y="label", orientation="h", text="pct_late",
                   color="pct_late", color_continuous_scale="OrRd")
        f.update_traces(texttemplate="%{text:.1f}%", marker_cornerradius=6)
        f.update_layout(xaxis_title="% late", yaxis_title="", coloraxis_showscale=False)
        st.plotly_chart(style_fig(f, 470), use_container_width=True, config=PCFG)
    callout("Bulky / high-value categories (electronics, furniture, office) ship latest — consistent "
            "with the carrier-transit bottleneck, and they are exactly the pricier orders most at risk.")

# ================================================================== OPERATIONS
elif view == "Operations":
    page_header("Operations — where the time leaks", "Decomposing the delivery pipeline to find the bottleneck.")
    st.write("")
    total = bott.avg_days.sum()
    ic = {"Payment approval": "credit_score", "Seller handling": "inventory_2",
          "Carrier transit": "local_shipping"}
    c = st.columns(3)
    for i, row in bott.iterrows():
        kpi(c[i], ic.get(row.stage, "timelapse"), f'{row.avg_days:.1f}d', row.stage,
            RED if row.stage == "Carrier transit" else ACCENT,
            f'{row.avg_days/total*100:.0f}%', MUTED)
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="card-h">Stage duration — On-Time vs Late</div>', unsafe_allow_html=True)
        m = bott.melt(id_vars="stage", value_vars=["ontime_days", "late_days"],
                      var_name="grp", value_name="days")
        m["grp"] = m.grp.map({"ontime_days": "On Time", "late_days": "Late"})
        f = px.bar(m, x="stage", y="days", color="grp", barmode="group", text="days",
                   color_discrete_map={"On Time": GREEN, "Late": RED})
        f.update_traces(marker_cornerradius=7)
        f.update_layout(xaxis_title="", yaxis_title="avg days", legend_title="")
        st.plotly_chart(style_fig(f, 320), use_container_width=True, config=PCFG)
    callout("<b>Carrier transit ≈ 74%</b> of total time and explodes <b>8→26 days</b> on late orders "
            "→ the fix is the carrier / last-mile network, not the warehouse.")

# ================================================================== REVENUE
else:
    page_header("Revenue at risk", "What lateness costs — and where the money actually is.")
    st.write("")
    c = st.columns(3)
    kpi(c[0], "account_balance", money(kpis["total_revenue"]), "Total delivered revenue", INK)
    kpi(c[1], "warning", money(kpis["revenue_at_risk"]), "Revenue on late orders", RED,
        f'{kpis["revenue_at_risk_pct"]}%', RED)
    kpi(c[2], "trending_up", f'{kpis["revenue_at_risk_pct"]}%', "Share at risk", AMBER)
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="card-h">Late-order revenue at risk — top 10 states</div>', unsafe_allow_html=True)
        top = state.sort_values("late_revenue", ascending=False).head(10)
        f = px.bar(top, x="customer_state", y="late_revenue", text="late_revenue",
                   color="late_revenue", color_continuous_scale="OrRd")
        f.update_traces(texttemplate="R$%{text:.2s}", marker_cornerradius=7)
        f.update_layout(xaxis_title="", yaxis_title="R$ at risk", coloraxis_showscale=False)
        st.plotly_chart(style_fig(f, 340), use_container_width=True, config=PCFG)
    callout("Money concentrates in high-volume <b>SP / RJ / MG</b> — different states than the "
            "worst-<i>rate</i> North-east. Two programmes: protect revenue in SP/RJ, fix the rate in the North-east.")
