"""Tableau de bord Direction : « Comment se porte l'activité ? ».

Lancement (base chargée) : uv run streamlit run dashboards/app.py
"""

import pandas as pd
import streamlit as st

from shoppulse.config import FULL_MONTHS, SQL_DIR
from shoppulse.db import get_engine
from shoppulse.queries import run_query


@st.cache_data(ttl=600)
def load(path: str) -> pd.DataFrame:
    return run_query(SQL_DIR / path, get_engine())


def brl(value: float) -> str:
    return f"{value:,.0f} R$".replace(",", " ")


st.set_page_config(page_title="ShopPulse · Direction", layout="wide")
st.title("ShopPulse : comment se porte l'activité ?")
st.caption("Source : base PostgreSQL alimentée par le pipeline ETL (données Olist).")

kpi = load("kpis.sql").iloc[0]
cards = st.columns(5)
cards[0].metric(
    "Chiffre d'affaires", brl(kpi.revenue), help="Articles + port, hors annulations"
)
cards[1].metric("Commandes", f"{int(kpi.orders):,}".replace(",", " "))
cards[2].metric("Panier moyen", brl(kpi.avg_basket))
cards[3].metric(
    "Livraisons en retard",
    f"{kpi.late_rate_pct} %",
    help="Livrées après la date promise au client",
)
cards[4].metric("Note client moyenne", f"{kpi.avg_review_score} / 5")

left, right = st.columns(2)
with left:
    st.subheader("Chiffre d'affaires mensuel")
    monthly = load("queries/01_monthly_revenue.sql")
    monthly = monthly[monthly["month"].astype(str).between(*FULL_MONTHS)]
    st.line_chart(monthly, x="month", y="revenue", y_label="R$", x_label="")
with right:
    st.subheader("Le retard fait chuter la note client")
    scores = load("queries/04_review_score_vs_delay.sql")
    st.bar_chart(scores, x="delay_bucket", y="avg_score", y_label="note /5", x_label="")

st.subheader("Taux de retard par État")
states = load("queries/03_late_rate_by_state.sql")
st.bar_chart(
    states,
    x="customer_state",
    y="late_rate_pct",
    y_label="% en retard",
    x_label="",
    sort="-late_rate_pct",
)
