"""RetenSight — concise, visual CRM decision support."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import altair as alt
import pandas as pd
import streamlit as st

from retensight.dashboard_data import (
    DashboardDataError,
    filter_crm_policies,
    get_segment_strategy_summary,
    load_crm_policy_comparison,
    load_data_quality_audit,
    load_model_config,
    load_model_metrics,
    load_rfm_summary,
    load_segment_decision_table,
    validate_reports_directory,
)

# Keep paths stable when Streamlit Cloud launches from a different working directory.
ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"

NAVY = "#193A63"
BLUE = "#4E79A7"
SLATE = "#8A9AAF"
INK = "#172B4D"
MUTED = "#667085"
GRID = "#E7EBF0"
PALE = "#F4F7FA"

st.set_page_config(
    page_title="RetenSight | Customer Intelligence",
    page_icon="▦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700&display=swap');
    html, body, [class*="css"] {
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #172B4D;
    }
    .stApp { background: #FFFFFF; }
    .block-container {
        max-width: 1320px;
        padding-top: 1.45rem;
        padding-bottom: 2.25rem;
    }
    .brand-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 1rem;
        padding-bottom: 1rem;
        margin-bottom: 1.1rem;
        border-bottom: 1px solid #E7EBF0;
    }
    .brand-name {
        color: #193A63;
        font-size: 1.7rem;
        letter-spacing: -0.045em;
        font-weight: 700;
        line-height: 1.2;
    }
    .brand-subtitle {
        margin-top: 0.25rem;
        color: #667085;
        font-size: 0.92rem;
        font-weight: 400;
    }
    .brand-scope {
        color: #667085;
        font-size: 0.78rem;
        white-space: nowrap;
    }
    .view-title {
        color: #172B4D;
        font-size: 1.24rem;
        font-weight: 650;
        letter-spacing: -0.025em;
        margin: 0.35rem 0 0.2rem 0;
    }
    .view-subtitle {
        color: #667085;
        font-size: 0.88rem;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    .chart-title {
        color: #172B4D;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: -0.015em;
        margin-bottom: 0.15rem;
    }
    .chart-caption {
        color: #667085;
        font-size: 0.8rem;
        margin-bottom: 0.45rem;
        line-height: 1.4;
    }
    .takeaway {
        padding: 0.85rem 1rem;
        border-left: 3px solid #4E79A7;
        background: #F4F7FA;
        color: #344054;
        font-size: 0.9rem;
        line-height: 1.5;
        margin: 0.6rem 0 0.6rem 0;
    }
    div[data-testid="stMetric"] {
        padding: 0.85rem 0.95rem;
        background: #F7F9FC;
        border: 1px solid #E7EBF0;
        border-radius: 8px;
    }
    div[data-testid="stMetricLabel"] {
        color: #667085;
        font-size: 0.8rem;
    }
    div[data-testid="stMetricValue"] {
        color: #193A63;
        font-size: 1.75rem;
        font-weight: 650;
    }
    div[data-testid="stTabs"] button {
        font-weight: 550;
    }
    .footer-note {
        border-top: 1px solid #E7EBF0;
        padding-top: 0.9rem;
        margin-top: 2rem;
        color: #7A8494;
        font-size: 0.76rem;
    }
    @media (max-width: 760px) {
        .brand-row { align-items: flex-start; flex-direction: column; gap: 0.2rem; }
        .brand-scope { white-space: normal; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_dashboard_data() -> tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Load the existing verified report artifacts and enforce their schemas."""
    validate_reports_directory(REPORTS_DIR)
    return (
        load_data_quality_audit(REPORTS_DIR),
        load_rfm_summary(REPORTS_DIR),
        load_segment_decision_table(REPORTS_DIR),
        load_model_metrics(REPORTS_DIR),
        load_crm_policy_comparison(REPORTS_DIR),
        load_model_config(REPORTS_DIR),
    )


try:
    AUDIT, RFM, SEGMENT_RULES, MODEL_METRICS, POLICY_RESULTS, MODEL_CONFIG = load_dashboard_data()
except DashboardDataError as exc:
    st.error(f"Dashboard data could not be loaded: {exc}")
    st.info("Check that the verified report artifacts in the reports folder are present.")
    st.stop()


def base_chart(chart: alt.Chart, height: int = 280) -> alt.Chart:
    """Apply a consistent, quiet visual style to all charts."""
    return (
        chart.properties(height=height)
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor=MUTED,
            titleColor=MUTED,
            labelFontSize=11,
            titleFontSize=11,
            titleFontWeight="normal",
            gridColor=GRID,
            domain=False,
            tickColor="#D7DDE5",
        )
        .configure_legend(
            labelColor=MUTED,
            titleColor=MUTED,
            labelFontSize=11,
            titleFontSize=11,
            symbolType="circle",
        )
    )


def horizontal_bar(
    data: pd.DataFrame,
    category: str,
    value: str,
    *,
    color: str = NAVY,
    height: int = 280,
    value_title: str = "Count",
    label_field: str | None = None,
    domain_max: float | None = None,
    tooltip_fields: list[str] | None = None,
) -> alt.Chart:
    """Create a consistent horizontal bar chart with readable labels and tooltips."""
    max_value = float(data[value].max()) if len(data) else 1.0
    max_value = max_value if domain_max is None else domain_max
    x_scale = alt.Scale(domain=[0, max_value * 1.17])
    y_encoding = alt.Y(
        f"{category}:N",
        sort="-x",
        title=None,
        axis=alt.Axis(labelLimit=230, labelPadding=8, ticks=False),
    )
    x_encoding = alt.X(
        f"{value}:Q",
        title=value_title,
        scale=x_scale,
        axis=alt.Axis(format=",.0f", tickCount=5),
    )
    tooltips = [
        alt.Tooltip(f"{category}:N", title=category),
        alt.Tooltip(f"{value}:Q", title=value_title, format=",.2f"),
    ]
    for field in tooltip_fields or []:
        if field in data.columns and field not in {category, value}:
            tooltips.append(alt.Tooltip(f"{field}:Q", title=field, format=",.2f"))

    bars = alt.Chart(data).mark_bar(
        color=color,
        cornerRadiusEnd=4,
        size=22,
    ).encode(
        y=y_encoding,
        x=x_encoding,
        tooltip=tooltips,
    )
    if label_field and label_field in data.columns:
        labels = alt.Chart(data).mark_text(
            align="left",
            baseline="middle",
            dx=5,
            fontSize=11,
            color=INK,
        ).encode(
            y=alt.Y(f"{category}:N", sort="-x"),
            x=alt.X(f"{value}:Q", scale=x_scale),
            text=alt.Text(f"{label_field}:N"),
        )
        return base_chart(bars + labels, height=height)
    return base_chart(bars, height=height)


def policy_rows(capacity: str) -> pd.DataFrame:
    """Return comparable policy results for the chosen capacity, using the validation cohort and RFM default."""
    result = filter_crm_policies(
        POLICY_RESULTS,
        evaluation_split="Validation",
        model_name="RFM Baseline",
        outreach_capacity=capacity,
    ).copy()

    labels = {
        "Risk-first": "Risk-first",
        "Hybrid": "Hybrid",
        "Value-aware": "Value-aware",
        "Random baseline (analytical)": "Random benchmark",
    }
    result["Strategy"] = result["policy"].map(labels).fillna(result["policy"])
    ordering = ["Risk-first", "Hybrid", "Value-aware", "Random benchmark"]
    result["Strategy"] = pd.Categorical(result["Strategy"], categories=ordering, ordered=True)
    result["Non-repeat precision (%)"] = result["selected_non_repeat_rate"] * 100
    result["Spend represented (%)"] = result["share_of_cohort_commercial_value"] * 100
    result["Non-repeaters captured (%)"] = result["share_of_all_non_repeaters_captured"] * 100
    return result.sort_values("Strategy").reset_index(drop=True)


# Minimal brand header: no development-stage badges.
st.markdown(
    """
    <div class="brand-row">
      <div>
        <div class="brand-name">RetenSight</div>
        <div class="brand-subtitle">Customer intelligence for smarter CRM prioritization</div>
      </div>
      <div class="brand-scope">Historical data · 2009–2011</div>
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs(["Overview", "Customer segments", "Contact strategy"])

# ---------------------------------------------------------------------------
# 1. OVERVIEW — what the customer data says and why prioritization matters
# ---------------------------------------------------------------------------
with tabs[0]:
    validation = RFM["cutoffs"]["2011-06-10"]
    cohort_size = int(validation["eligible_customers"])
    repeaters = int(validation["repeat_purchasers_90d"])
    non_repeaters = cohort_size - repeaters
    repeat_rate = float(validation["repeat_purchase_rate_pct"])
    ten_pct = policy_rows("10%")
    risk = ten_pct.loc[ten_pct["policy"] == "Risk-first"].iloc[0]
    random = ten_pct.loc[ten_pct["policy"] == "Random baseline (analytical)"].iloc[0]

    st.markdown('<div class="view-title">Understand the customer opportunity</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="view-subtitle">A clear view of repeat purchasing and how prioritization changes a limited contact queue.</div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Customers in observed cohort", f"{cohort_size:,}")
    m2.metric("Repeat purchase rate", f"{repeat_rate:.2f}%", f"{repeaters:,} customers")
    m3.metric("Risk-first precision", f"{risk['Non-repeat precision (%)']:.2f}%", "At 10% contact capacity")

    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown('<div class="chart-title">What happened over the next 90 days?</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-caption">Observed purchasing behaviour for the selected customer cohort.</div>',
            unsafe_allow_html=True,
        )
        outcome_data = pd.DataFrame([
            {
                "Outcome": "No repeat purchase",
                "Customers": non_repeaters,
                "Share": non_repeaters / cohort_size * 100,
                "Label": f"{non_repeaters:,} · {non_repeaters / cohort_size * 100:.1f}%",
            },
            {
                "Outcome": "Repeat purchase",
                "Customers": repeaters,
                "Share": repeaters / cohort_size * 100,
                "Label": f"{repeaters:,} · {repeaters / cohort_size * 100:.1f}%",
            },
        ])
        outcome_bars = alt.Chart(outcome_data).mark_bar(
            cornerRadiusEnd=4,
            size=30,
        ).encode(
            y=alt.Y("Outcome:N", sort="-x", title=None, axis=alt.Axis(labelLimit=180, ticks=False)),
            x=alt.X("Customers:Q", title="Customers", scale=alt.Scale(domain=[0, 4100]), axis=alt.Axis(format=",.0f")),
            color=alt.Color(
                "Outcome:N",
                scale=alt.Scale(
                    domain=["No repeat purchase", "Repeat purchase"],
                    range=[NAVY, BLUE],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Outcome:N"),
                alt.Tooltip("Customers:Q", format=","),
                alt.Tooltip("Share:Q", title="Cohort share (%)", format=".2f"),
            ],
        )
        outcome_labels = alt.Chart(outcome_data).mark_text(
            align="left", baseline="middle", dx=5, color=INK, fontSize=11
        ).encode(
            y=alt.Y("Outcome:N", sort="-x"),
            x=alt.X("Customers:Q", scale=alt.Scale(domain=[0, 4100])),
            text=alt.Text("Label:N"),
        )
        st.altair_chart(base_chart(outcome_bars + outcome_labels, height=210), use_container_width=True)

    with right:
        st.markdown('<div class="chart-title">Does prioritization beat random selection?</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-caption">Share of selected contacts who did not repeat-purchase, at the same 10% capacity.</div>',
            unsafe_allow_html=True,
        )
        compare = pd.DataFrame([
            {"Strategy": "RFM Risk-first", "Precision": float(risk["Non-repeat precision (%)"]), "Label": f"{risk['Non-repeat precision (%)']:.2f}%"},
            {"Strategy": "Random benchmark", "Precision": float(random["Non-repeat precision (%)"]), "Label": f"{random['Non-repeat precision (%)']:.2f}%"},
        ])
        comp_bars = alt.Chart(compare).mark_bar(cornerRadiusEnd=4, size=30).encode(
            y=alt.Y("Strategy:N", sort="-x", title=None, axis=alt.Axis(ticks=False)),
            x=alt.X("Precision:Q", title="Non-repeat precision", scale=alt.Scale(domain=[0, 112]), axis=alt.Axis(format=".0f", tickCount=5, grid=True)),
            color=alt.Color(
                "Strategy:N",
                scale=alt.Scale(domain=["RFM Risk-first", "Random benchmark"], range=[NAVY, SLATE]),
                legend=None,
            ),
            tooltip=[alt.Tooltip("Strategy:N"), alt.Tooltip("Precision:Q", title="Precision (%)", format=".2f")],
        )
        comp_labels = alt.Chart(compare).mark_text(align="left", baseline="middle", dx=5, color=INK, fontSize=11).encode(
            y=alt.Y("Strategy:N", sort="-x"),
            x=alt.X("Precision:Q", scale=alt.Scale(domain=[0, 112])),
            text=alt.Text("Label:N"),
        )
        st.altair_chart(base_chart(comp_bars + comp_labels, height=210), use_container_width=True)

    st.markdown(
        '<div class="takeaway"><strong>Key finding:</strong> At 10% contact capacity, the RFM Risk-first queue identifies historical non-repeaters more often than random selection. This is a prioritization result, not proof that contacting them changes their behaviour.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# 2. CUSTOMER SEGMENTS — where customers sit today in the archive
# ---------------------------------------------------------------------------
with tabs[1]:
    # Latest complete segmentation snapshot is suitable for describing segments.
    # Its future 90-day outcomes are not observed and are never plotted as zero.
    snapshot = RFM["cutoffs"]["2011-12-09"]
    segment_counts = snapshot["segment_counts"]
    eligible = int(snapshot["eligible_customers"])
    summary = get_segment_strategy_summary(SEGMENT_RULES).set_index("segment")

    records = []
    for segment, count in segment_counts.items():
        count = int(count)
        strategy = summary.loc[segment] if segment in summary.index else None
        full_action = str(strategy["core_crm_action"]) if strategy is not None else "Review segment definition"
        # Use one concise action from the project's documented decision table.
        concise_action = full_action.split(";")[0].split(",")[0].strip().rstrip(".")
        records.append({
            "Segment": segment,
            "Customers": count,
            "Share (%)": count / eligible * 100,
            "Label": f"{count:,}",
            "CRM focus": concise_action,
        })
    segments = pd.DataFrame(records).sort_values("Customers", ascending=False).reset_index(drop=True)

    st.markdown('<div class="view-title">Know your customer mix</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="view-subtitle">Customer segments based on purchase history through December 2011 · {eligible:,} customers. The future 90-day purchase outcome for this final snapshot is unobserved.</div>',
        unsafe_allow_html=True,
    )

    segment_chart = horizontal_bar(
        segments,
        "Segment",
        "Customers",
        height=390,
        value_title="Customers",
        label_field="Label",
        tooltip_fields=["Share (%)"],
    )
    st.altair_chart(segment_chart, use_container_width=True)

    with st.expander("Suggested CRM focus by segment"):
        action_view = segments[["Segment", "Customers", "Share (%)", "CRM focus"]].copy()
        action_view["Share of customers"] = action_view["Share (%)"].map(lambda value: f"{value:.1f}%")
        st.dataframe(
            action_view[["Segment", "Customers", "Share of customers", "CRM focus"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Customers": st.column_config.NumberColumn(format="%d"),
                "CRM focus": st.column_config.TextColumn(width="large"),
            },
        )


# ---------------------------------------------------------------------------
# 3. CONTACT STRATEGY — a fair, visible comparison at equal capacity
# ---------------------------------------------------------------------------
with tabs[2]:
    st.markdown('<div class="view-title">Choose how to prioritize contacts</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="view-subtitle">Compare identification precision with the share of historical customer spend represented by each queue.</div>',
        unsafe_allow_html=True,
    )

    ctrl, note = st.columns([1, 3])
    with ctrl:
        capacity = st.selectbox(
            "Contact capacity",
            options=["1%", "5%", "10%", "20%"],
            index=2,
            help="The percentage of the observed validation cohort selected for contact.",
        )
    with note:
        row_count = int(policy_rows(capacity)["selected_count"].iloc[0])
        st.caption(
            f"Same customer population across strategies · {row_count:,} contacts at {capacity} capacity · Recommended default: RFM"
        )

    active = policy_rows(capacity)
    precision_data = active[["Strategy", "Non-repeat precision (%)"]].copy()
    precision_data["Precision label"] = precision_data["Non-repeat precision (%)"].map(lambda value: f"{value:.1f}%")
    precision_chart_bars = alt.Chart(precision_data).mark_bar(cornerRadiusEnd=4, size=26).encode(
        y=alt.Y("Strategy:N", sort="-x", title=None, axis=alt.Axis(labelLimit=180, ticks=False)),
        x=alt.X("Non-repeat precision (%):Q", title="Selected contacts who did not repeat (%)", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(format=".0f")),
        color=alt.condition(
            alt.datum.Strategy == "Risk-first",
            alt.value(NAVY),
            alt.value(SLATE),
        ),
        tooltip=[
            alt.Tooltip("Strategy:N"),
            alt.Tooltip("Non-repeat precision (%):Q", format=".2f"),
        ],
    )
    precision_chart_labels = alt.Chart(precision_data).mark_text(align="left", baseline="middle", dx=5, fontSize=11, color=INK).encode(
        y=alt.Y("Strategy:N", sort="-x"),
        x=alt.X("Non-repeat precision (%):Q", scale=alt.Scale(domain=[0, 100])),
        text=alt.Text("Precision label:N"),
    )

    spend_data = active[["Strategy", "Spend represented (%)"]].copy()
    spend_data["Spend label"] = spend_data["Spend represented (%)"].map(lambda value: f"{value:.1f}%")
    spend_max = max(15.0, float(spend_data["Spend represented (%)"].max()) * 1.18)
    spend_scale = alt.Scale(domain=[0, spend_max])
    spend_bars = alt.Chart(spend_data).mark_bar(cornerRadiusEnd=4, size=26).encode(
        y=alt.Y("Strategy:N", sort="-x", title=None, axis=alt.Axis(labelLimit=180, ticks=False)),
        x=alt.X("Spend represented (%):Q", title="Share of cohort historical spend (%)", scale=spend_scale, axis=alt.Axis(format=".0f")),
        color=alt.condition(
            alt.datum.Strategy == "Value-aware",
            alt.value(NAVY),
            alt.value(SLATE),
        ),
        tooltip=[
            alt.Tooltip("Strategy:N"),
            alt.Tooltip("Spend represented (%):Q", format=".2f"),
            alt.Tooltip("historical_commercial_value_gbp:Q", title="Historical spend (£)", format="£,.0f"),
        ],
    )
    spend_labels = alt.Chart(spend_data).mark_text(align="left", baseline="middle", dx=5, fontSize=11, color=INK).encode(
        y=alt.Y("Strategy:N", sort="-x"),
        x=alt.X("Spend represented (%):Q", scale=spend_scale),
        text=alt.Text("Spend label:N"),
    )

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="chart-title">Who is less likely to repeat-purchase?</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-caption">Higher precision means fewer selected customers would have repeated on their own in the observed period.</div>', unsafe_allow_html=True)
        st.altair_chart(base_chart(precision_chart_bars + precision_chart_labels, height=270), use_container_width=True)
    with right:
        st.markdown('<div class="chart-title">How much historical spend is represented?</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-caption">Past spend associated with selected customers; not campaign uplift or protected revenue.</div>', unsafe_allow_html=True)
        st.altair_chart(base_chart(spend_bars + spend_labels, height=270), use_container_width=True)

    table = active.copy()
    table["Non-repeat precision"] = table["Non-repeat precision (%)"].map(lambda value: f"{value:.1f}%")
    table["All non-repeaters captured"] = table["Non-repeaters captured (%)"].map(lambda value: f"{value:.1f}%")
    table["Historical spend"] = table["historical_commercial_value_gbp"].map(lambda value: f"£{value:,.0f}")
    table["Spend represented"] = table["Spend represented (%)"].map(lambda value: f"{value:.1f}%")
    table["Contacts"] = table["selected_count"].astype(int)
    st.dataframe(
        table[["Strategy", "Contacts", "Non-repeat precision", "All non-repeaters captured", "Historical spend", "Spend represented"]],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Risk-first prioritizes non-repeat precision. Value-aware represents more historical spend. Hybrid balances the two. Random is the benchmark."
    )


# Technical detail stays available without dominating the main experience.
with st.expander("Methodology and limitations"):
    st.markdown(
        """
        - **Source:** UCI Online Retail II, December 2009–December 2011.
        - **Outcome:** At least one qualifying merchandise purchase in the following 90 days.
        - **Recommended default:** The 3-feature RFM Baseline logistic regression. The 16-feature Expanded Model remains a challenger because improvements on the observed validation results are small relative to its added complexity.
        - **Evaluation integrity:** The June 2011 cohort governs the recommendation. The September 2011 cohort was inspected during development and is a retrospective temporal evaluation, not a prospective holdout.
        - **Probability underprediction:** The Expanded Model shows systematic probability underprediction on the retrospective temporal cohort; the cause is unknown from the available transaction data.
        - **Unobserved outcomes:** The December 2011 segmentation snapshot has no observed forward 90-day target. Its segment counts are descriptive only; no repeat outcome is imputed.
        - **Financial interpretation:** Queue spend is historical customer-attributed commercial spend associated with selected customers. It is not profit, customer lifetime value, or evidence of campaign impact.
        - **Causal limitation:** There is no campaign exposure or treatment data to establish that contacting a selected customer changes their behaviour.
        """
    )

st.markdown(
    '<div class="footer-note">RetenSight · Historical customer analysis, 2009–2011 · Results describe past behaviour, not proven campaign impact.</div>',
    unsafe_allow_html=True,
)
