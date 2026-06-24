"""
OWLSNATION ENGINE — Streamlit Frontend UI
========================================
"""

import streamlit as st
from owlsnation_engine import TeamStats, run_engine

st.set_page_config(page_title="OWLSNATION Engine", page_icon="🦉", layout="wide")

st.title("🦉 OWLSNATION Analytical Engine v2.0")
st.caption("Score Power Baseline Shift Grid + Dominance Stress System Matrix Modulators")
st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Home — Team A")
    name_a = st.text_input("Team name", value="Team A", key="name_a")
    ga = st.number_input("Avg Goals Scored", min_value=0.0, value=2.0, step=0.01, key="ga")
    ca = st.number_input("Avg Goals Conceded", min_value=0.0, value=4.0, step=0.01, key="ca")
    sota = st.number_input("Shots on Target For", min_value=0.0, value=5.0, step=0.01, key="sota")
    sotaga = st.number_input("Shots on Target Against", min_value=0.0, value=3.0, step=0.01, key="sotaga")
    bca = st.number_input("Avg Big Chances", min_value=0.0, value=0.58, step=0.01, key="bca")
    xga = st.number_input("Avg Expected Goals (xG)", min_value=0.0, value=0.77, step=0.01, key="xga")

with col_b:
    st.subheader("Away — Team B")
    name_b = st.text_input("Team name", value="Team B", key="name_b")
    gb = st.number_input("Avg Goals Scored", min_value=0.0, value=3.0, step=0.01, key="gb")
    cb = st.number_input("Avg Goals Conceded", min_value=0.0, value=5.0, step=0.01, key="cb")
    sotb = st.number_input("Shots on Target For", min_value=0.0, value=2.0, step=0.01, key="sotb")
    sotbga = st.number_input("Shots on Target Against", min_value=0.0, value=8.0, step=0.01, key="sotbga")
    bcb = st.number_input("Avg Big Chances", min_value=0.0, value=0.50, step=0.01, key="bcb")
    xgb = st.number_input("Avg Expected Goals (xG)", min_value=0.0, value=0.89, step=0.01, key="xgb")

st.divider()
st.subheader("Bookmaker Decimal Odds")
bk_col1, bk_col2, bk_col3 = st.columns(3)
with bk_col1: bk_home = st.number_input(f"{name_a} Win Odd", min_value=1.01, value=3.40, step=0.01, key="bk_home")
with bk_col2: bk_draw = st.number_input("Draw Odd", min_value=1.01, value=3.40, step=0.01, key="bk_draw")
with bk_col3: bk_away = st.number_input(f"{name_b} Win Odd", min_value=1.01, value=2.10, step=0.01, key="bk_away")

st.divider()
if st.button("RUN ENGINE ANALYSIS", type="primary", use_container_width=True):
    team_a = TeamStats(name=name_a or "Team A", goals_scored=ga, goals_conceded=ca, shots_on_target_for=sota, shots_on_target_against=sotaga, big_chances=bca, expected_goals=xga)
    team_b = TeamStats(name=name_b or "Team B", goals_scored=gb, goals_conceded=cb, shots_on_target_for=sotb, shots_on_target_against=sotbga, big_chances=bcb, expected_goals=xgb)

    result = run_engine(team_a, team_b, bk_home, bk_draw, bk_away)
    st.success("Analysis Matrix successfully compiled.")

    # Core Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{team_a.name} Score Power", result.sp_home)
    m2.metric(f"{team_b.name} Score Power", result.sp_away)
    m3.metric(f"{team_a.name} Dominance", result.dominance_home)
    m4.metric(f"{team_b.name} Dominance", result.dominance_away)

    st.subheader("Calculated Matrix vs Bookmaker Probabilities")
    st.table({
        "Outcome Window": [f"{team_a.name} Win", "Draw Option", f"{team_b.name} Win"],
        "Baseline Price": [result.baseline_odds["oh"], result.baseline_odds["od"], result.baseline_odds["oa"]],
        "Master Ensemble Odd": [result.master_odds["oh"], result.master_odds["od"], result.master_odds["oa"]],
        "Bookmaker Market Input": [bk_home, bk_draw, bk_away],
        "Value Advantage Edge %": [result.value_margin["h"], result.value_margin["d"], result.value_margin["a"]]
    })

    st.subheader("3-Way Draw Comparison Shift")
    st.write(f"Baseline Draw% = **{result.baseline_pct['d']}%** | Master Draw% = **{result.master_pct['d']}%** | Consensus Target = **{result.model_consensus_draw_pct}%** | Bookmaker Draw% = **{result.bookmaker_pct['d']}%**")
    st.info(f"Draw Drift Margin Adjustment Factor: **{result.draw_diff_pct} points**")

    # Final Outputs
    st.subheader("Phase 7: Core Score Predictions")
    sc1, sc2, sc3 = st.columns(3)
    for idx, (col, (h, a, p)) in enumerate(zip((sc1, sc2, sc3), result.top_scores), 1):
        col.metric(f"Rank Selection {idx}", f"{h} - {a}", f"{round(p * 100, 2)}% Probability")

    st.subheader("Derivative Market Selections")
    for idx, m in enumerate(result.top_markets, 1):
        st.write(f"**{idx}. Optimal Target:** `{m.name}` — Confidence Level: **{m.prob}%**")
