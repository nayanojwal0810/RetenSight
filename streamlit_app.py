"""RetenSight — E-Commerce CRM Analytics & Decision-Support System.

Professional executive dashboard for customer segmentation, repeat-purchase propensity,
and capacity-constrained CRM outreach queue planning.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import altair as alt
import numpy as np
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

# -----------------------------------------------------------------------------
# Page Configuration & Styling
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="RetenSight | CRM Decision Support",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom formal CSS styling: deep navy, white, cool grey, clean typography
CUSTOM_CSS = """
<style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0f172a;
    }
    
    /* Subtle main container padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Executive App Header */
    .app-header {
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
    }
    .app-title {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.025em;
        margin-bottom: 0.2rem;
    }
    .app-subtitle {
        font-size: 0.95rem;
        color: #64748b;
        font-weight: 400;
    }
    .app-badge-row {
        margin-top: 0.6rem;
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
    }
    .meta-tag {
        display: inline-block;
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
        padding: 0.2rem 0.55rem;
        font-size: 0.75rem;
        font-weight: 500;
        border-radius: 3px;
        letter-spacing: 0.01em;
    }
    
    /* Formal Metric Cards */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 1.1rem 1.2rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    .metric-subtext {
        font-size: 0.78rem;
        color: #475569;
        margin-top: 0.45rem;
    }

    /* Section Subheadings */
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #0f172a;
        letter-spacing: -0.015em;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    .section-desc {
        font-size: 0.88rem;
        color: #475569;
        margin-bottom: 1rem;
        line-height: 1.45;
    }

    /* Policy Highlight Banner */
    .policy-banner {
        background-color: #f8fafc;
        border-left: 3px solid #1e3a8a;
        padding: 0.9rem 1.1rem;
        margin-bottom: 1.2rem;
        font-size: 0.88rem;
        color: #1e293b;
    }
    
    /* Footer Disclaimer */
    .footer-box {
        margin-top: 3.5rem;
        border-top: 1px solid #e2e8f0;
        padding-top: 1.2rem;
        font-size: 0.78rem;
        color: #64748b;
        line-height: 1.5;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loading & Caching
# -----------------------------------------------------------------------------

REPORTS_DIR = Path("reports")


@st.cache_data(show_spinner=False)
def get_cached_dashboard_data() -> Tuple[
    Dict[str, Any],
    Dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    Dict[str, Any],
]:
    """Loads and validates all dashboard report artifacts with deterministic caching."""
    validate_reports_directory(REPORTS_DIR)
    audit = load_data_quality_audit(REPORTS_DIR)
    rfm = load_rfm_summary(REPORTS_DIR)
    decision = load_segment_decision_table(REPORTS_DIR)
    metrics = load_model_metrics(REPORTS_DIR)
    policies = load_crm_policy_comparison(REPORTS_DIR)
    config = load_model_config(REPORTS_DIR)
    return audit, rfm, decision, metrics, policies, config


try:
    AUDIT_DATA, RFM_DATA, DECISION_TABLE, MODEL_METRICS, POLICY_COMPARISON, MODEL_CONFIG = get_cached_dashboard_data()
except DashboardDataError as err:
    st.error(f"Configuration or data loading error: {err}")
    st.info("Ensure all verified report artifacts in `reports/` are present and properly structured.")
    st.stop()


# -----------------------------------------------------------------------------
# Header Presentation
# -----------------------------------------------------------------------------

def render_header() -> None:
    """Renders the top executive brand header and archival scope metadata."""
    st.markdown(
        """
        <div class="app-header">
            <div class="app-title">RetenSight</div>
            <div class="app-subtitle">Customer Analytics & Capacity-Constrained CRM Decision Support</div>
            <div class="app-badge-row">
                <span class="meta-tag">UCI Online Retail II Archive (2009–2011)</span>
                <span class="meta-tag">Walk-Forward Temporal Evaluation</span>
                <span class="meta-tag">Zero Look-Ahead Feature Design</span>
                <span class="meta-tag">Deterministic Preprocessing</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_header()

# -----------------------------------------------------------------------------
# Top-Level Navigation Tabs
# -----------------------------------------------------------------------------

tabs = st.tabs(["Executive Overview", "Customer Segmentation", "CRM Queue Planner"])

# =============================================================================
# View 1: Executive Overview
# =============================================================================

with tabs[0]:
    st.markdown('<div class="section-title">Executive Performance Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Key verified commercial totals and forward 90-day repeat purchase benchmarks '
        'across the walk-forward evaluation protocol. All figures reflect historical observations through December 2011.</div>',
        unsafe_allow_html=True,
    )

    # 4 Main KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    # Total Valid Customers
    total_valid_customers = AUDIT_DATA["invoice_breakdown"]["distinct_valid_customers"]
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Valid Customers</div>
                <div class="metric-value">{total_valid_customers:,}</div>
                <div class="metric-subtext">Attributed unique accounts in full archive (2009–2011)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Net Commercial Value
    net_commercial_val = AUDIT_DATA["financial_reconciliation"]["net_commercial_value_gbp"]
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Net Commercial Spend</div>
                <div class="metric-value">£{net_commercial_val:,.0f}</div>
                <div class="metric-subtext">Merchandise sales minus cancellations & discounts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Validation Cohort Repeat Rate
    val_cutoff = RFM_DATA["cutoffs"]["2011-06-10"]
    val_rate = val_cutoff["repeat_purchase_rate_pct"]
    val_rep = val_cutoff["repeat_purchasers_90d"]
    val_total = val_cutoff["eligible_customers"]
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Validation Repeat Rate</div>
                <div class="metric-value">{val_rate:.2f}%</div>
                <div class="metric-subtext">{val_rep:,} of {val_total:,} customers (Cutoff: 2011-06-10)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Retrospective Temporal Repeat Rate
    eval_cutoff = RFM_DATA["cutoffs"]["2011-09-09"]
    eval_rate = eval_cutoff["repeat_purchase_rate_pct"]
    eval_rep = eval_cutoff["repeat_purchasers_90d"]
    eval_total = eval_cutoff["eligible_customers"]
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Temporal Cohort Repeat Rate</div>
                <div class="metric-value">{eval_rate:.2f}%</div>
                <div class="metric-subtext">{eval_rep:,} of {eval_total:,} customers (Cutoff: 2011-09-09)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    # Two Primary Visualizations
    vcol1, vcol2 = st.columns([6, 5])

    with vcol1:
        st.markdown('<div class="section-title">Chronological Evaluation Cohorts (Forward 90-Day Repeat Activity)</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-desc">Comparison of eligible active customer volume versus customers making at least '
            'one qualifying purchase in the forward 90 days. Final cutoff forward window is unobserved.</div>',
            unsafe_allow_html=True,
        )

        cohort_data = [
            {
                "Cutoff": "2010-12-09\n(Benchmark)",
                "Eligible Customers": RFM_DATA["cutoffs"]["2010-12-09"]["eligible_customers"],
                "Observed Repeaters": RFM_DATA["cutoffs"]["2010-12-09"]["repeat_purchasers_90d"],
                "Repeat Rate": "30.73%",
            },
            {
                "Cutoff": "2011-06-10\n(Validation)",
                "Eligible Customers": RFM_DATA["cutoffs"]["2011-06-10"]["eligible_customers"],
                "Observed Repeaters": RFM_DATA["cutoffs"]["2011-06-10"]["repeat_purchasers_90d"],
                "Repeat Rate": "32.03%",
            },
            {
                "Cutoff": "2011-09-09\n(Evaluation)",
                "Eligible Customers": RFM_DATA["cutoffs"]["2011-09-09"]["eligible_customers"],
                "Observed Repeaters": RFM_DATA["cutoffs"]["2011-09-09"]["repeat_purchasers_90d"],
                "Repeat Rate": "43.50%",
            },
            {
                "Cutoff": "2011-12-09\n(Production)",
                "Eligible Customers": RFM_DATA["cutoffs"]["2011-12-09"]["eligible_customers"],
                "Observed Repeaters": 0,
                "Repeat Rate": "Unobserved",
            },
        ]
        cohort_df = pd.DataFrame(cohort_data)
        melted_cohort = pd.melt(
            cohort_df,
            id_vars=["Cutoff", "Repeat Rate"],
            value_vars=["Eligible Customers", "Observed Repeaters"],
            var_name="Customer Category",
            value_name="Count",
        )

        cohort_chart = (
            alt.Chart(melted_cohort)
            .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
            .encode(
                x=alt.X("Cutoff:N", title="Scoring Cutoff Date", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Count:Q", title="Customer Volume", scale=alt.Scale(domain=[0, 6500])),
                xOffset=alt.XOffset("Customer Category:N"),
                color=alt.Color(
                    "Customer Category:N",
                    scale=alt.Scale(domain=["Eligible Customers", "Observed Repeaters"], range=["#1e3a8a", "#64748b"]),
                    legend=alt.Legend(title="Cohort Grain", orient="top", direction="horizontal"),
                ),
                tooltip=[
                    alt.Tooltip("Cutoff:N", title="Cutoff"),
                    alt.Tooltip("Customer Category:N", title="Type"),
                    alt.Tooltip("Count:Q", title="Customers", format=","),
                    alt.Tooltip("Repeat Rate:N", title="Observed 90d Repeat Rate"),
                ],
            )
            .properties(height=320)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(cohort_chart, use_container_width=True)

    with vcol2:
        st.markdown('<div class="section-title">Ledger Financial Reconciliation (Archive Totals)</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-desc">Exact audit trail from gross merchandise billing to net commercial value '
            'and final audited invoice revenue (£0.00 discrepancy).</div>',
            unsafe_allow_html=True,
        )

        fin = AUDIT_DATA["financial_reconciliation"]
        fin_rows = [
            {"Component": "Gross Merchandise Sales", "Amount": fin["gross_product_sales_gbp"], "Type": "Positive"},
            {"Component": "Special Commercial Charges", "Amount": fin["special_commercial_charges_gbp"], "Type": "Positive"},
            {"Component": "Gross Billed Sales", "Amount": fin["gross_sales_gbp"], "Type": "Subtotal"},
            {"Component": "Merchandise Cancellations & Returns", "Amount": fin["cancellations_value_gbp"], "Type": "Deduction"},
            {"Component": "Net Commercial Ledger Value", "Amount": fin["net_commercial_value_gbp"], "Type": "Subtotal"},
            {"Component": "Bad-Debt Ledger Write-offs", "Amount": fin["bad_debt_adjustments_gbp"], "Type": "Deduction"},
            {"Component": "Final Net Invoice Revenue", "Amount": fin["invoice_net_revenue_sum_gbp"], "Type": "Final"},
        ]
        fin_df = pd.DataFrame(fin_rows)

        # Clean bar chart of financial structure
        fin_chart = (
            alt.Chart(fin_df)
            .mark_bar(cornerRadiusTopRight=2, cornerRadiusBottomRight=2)
            .encode(
                y=alt.Y("Component:N", sort=None, title="", axis=alt.Axis(labelLimit=250)),
                x=alt.X("Amount:Q", title="Pounds Sterling (£)", axis=alt.Axis(format="£~s")),
                color=alt.Color(
                    "Type:N",
                    scale=alt.Scale(
                        domain=["Positive", "Deduction", "Subtotal", "Final"],
                        range=["#1e3a8a", "#b91c1c", "#475569", "#0f172a"],
                    ),
                    legend=alt.Legend(title="Ledger Type", orient="top", direction="horizontal"),
                ),
                tooltip=[
                    alt.Tooltip("Component:N", title="Component"),
                    alt.Tooltip("Amount:Q", title="Amount (£)", format="£,.2f"),
                    alt.Tooltip("Type:N", title="Category"),
                ],
            )
            .properties(height=320)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(fin_chart, use_container_width=True)


# =============================================================================
# View 2: Customer Segmentation
# =============================================================================

with tabs[1]:
    st.markdown('<div class="section-title">Customer RFM Segmentation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Distribution of active accounts across 11 mutually exclusive, monetary-aware '
        'CRM segments. Evaluated deterministically using quintile score boundaries as of each cutoff date.</div>',
        unsafe_allow_html=True,
    )

    # Snapshot and Filter Controls
    scol1, scol2, scol3 = st.columns([3, 4, 3])
    with scol1:
        cutoff_options = {
            "2011-06-10": "2011-06-10 (Validation Snapshot)",
            "2011-09-09": "2011-09-09 (Retrospective Evaluation)",
            "2011-12-09": "2011-12-09 (Final Production Snapshot)",
            "2010-12-09": "2010-12-09 (Initial Benchmark)",
        }
        selected_cutoff_key = st.selectbox(
            "Select Snapshot Date",
            options=list(cutoff_options.keys()),
            format_func=lambda k: cutoff_options[k],
            index=0,
        )

    # Extract chosen cutoff summary
    cutoff_meta = RFM_DATA["cutoffs"][selected_cutoff_key]
    segment_counts_dict = cutoff_meta["segment_counts"]
    total_eligible = cutoff_meta["eligible_customers"]

    with scol2:
        segment_list = ["All Segments"] + list(segment_counts_dict.keys())
        selected_segment = st.selectbox("Filter Segment View", options=segment_list, index=0)

    with scol3:
        st.markdown(
            f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 0.6rem 0.8rem; border-radius: 4px; margin-top: 0.8rem;">
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Snapshot Eligible Base</div>
                <div style="font-size: 1.15rem; font-weight: 700; color: #0f172a;">{total_eligible:,} customers</div>
                <div style="font-size: 0.72rem; color: #475569;">Mean Spend: £{cutoff_meta['mean_net_commercial_spend_gbp']:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    # Prepare DataFrame for Segment Visualization and Table
    strategy_df = get_segment_strategy_summary(DECISION_TABLE)
    seg_records = []
    for seg, cnt in segment_counts_dict.items():
        pct = (cnt / total_eligible) * 100.0
        strat = strategy_df[strategy_df["segment"] == seg]
        rationale = strat["business_rationale"].values[0] if len(strat) > 0 else "—"
        action = strat["core_crm_action"].values[0] if len(strat) > 0 else "—"
        seg_records.append({
            "Segment": seg,
            "Customer Count": cnt,
            "Share (%)": round(pct, 2),
            "Business Rationale": rationale,
            "Recommended CRM Action": action,
        })
    seg_df = pd.DataFrame(seg_records).sort_values("Customer Count", ascending=False).reset_index(drop=True)

    # Filter if single segment selected
    if selected_segment != "All Segments":
        display_seg_df = seg_df[seg_df["Segment"] == selected_segment]
    else:
        display_seg_df = seg_df

    # Segment Distribution Chart
    seg_chart = (
        alt.Chart(display_seg_df)
        .mark_bar(cornerRadiusTopRight=2, cornerRadiusBottomRight=2)
        .encode(
            y=alt.Y("Segment:N", sort="-x", title="", axis=alt.Axis(labelLimit=200)),
            x=alt.X("Customer Count:Q", title="Number of Active Customers"),
            color=alt.value("#1e3a8a"),
            tooltip=[
                alt.Tooltip("Segment:N", title="Segment"),
                alt.Tooltip("Customer Count:Q", title="Customers", format=","),
                alt.Tooltip("Share (%):Q", title="Share of Base", format=".2f"),
                alt.Tooltip("Recommended CRM Action:N", title="Action"),
            ],
        )
        .properties(height=340)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(seg_chart, use_container_width=True)

    # Strategy and Action Matrix
    st.markdown('<div class="section-title">Segment Strategic Rationale & CRM Action Matrix</div>', unsafe_allow_html=True)
    st.dataframe(
        display_seg_df[["Segment", "Customer Count", "Share (%)", "Business Rationale", "Recommended CRM Action"]],
        use_container_width=True,
        hide_index=True,
    )


# =============================================================================
# View 3: CRM Queue Planner
# =============================================================================

with tabs[2]:
    st.markdown('<div class="section-title">CRM Outreach Queue Planner & Policy Comparison</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Interactive decision-support simulator for capacity-constrained customer contact queues. '
        'Compare Risk-First, Value-Aware, and Hybrid sorting policies against an analytical random baseline. '
        'All queue comparisons reflect verified aggregate simulation outputs.</div>',
        unsafe_allow_html=True,
    )

    # Functional Decision Controls
    ccol1, ccol2, ccol3, ccol4 = st.columns(4)

    with ccol1:
        split_options = ["Validation", "Retrospective Temporal Evaluation"]
        selected_split = st.selectbox(
            "Evaluation Cohort",
            options=split_options,
            index=0,
            help="Validation cohort (2011-06-10) is the strict governor for all model and policy selection.",
        )

    with ccol2:
        model_options = ["RFM Baseline", "Expanded Model"]
        selected_model = st.selectbox(
            "Propensity Model",
            options=model_options,
            index=0,
            help="RFM Baseline (3 features) is the recommended operational default; Expanded Model (16 features) is the challenger.",
        )

    with ccol3:
        capacity_options = ["1%", "5%", "10%", "20%"]
        selected_capacity = st.selectbox(
            "Outreach Capacity Budget",
            options=capacity_options,
            index=2,  # Default 10%
            help="Fixed proportion of active cohort that sales/retention teams can contact within available outreach capacity.",
        )

    with ccol4:
        policy_filter_options = ["All Policies", "Risk-first", "Hybrid", "Value-aware", "Random baseline (analytical)"]
        selected_policy_focus = st.selectbox(
            "Focus Policy View",
            options=policy_filter_options,
            index=0,
        )

    # Filter CRM Policy Table for Selection
    active_policies_df = filter_crm_policies(
        POLICY_COMPARISON,
        evaluation_split=selected_split,
        model_name=selected_model,
        outreach_capacity=selected_capacity,
    )

    if active_policies_df.empty:
        st.warning("No simulation records found for the selected control combination.")
        st.stop()

    # Model Context & Operational Default Note
    if selected_model == "RFM Baseline":
        st.markdown(
            '<div class="policy-banner"><strong>Recommended Default Model (RFM Baseline):</strong> '
            'Formulated strictly from Recency, Frequency, and net commercial spend (3 features). '
            'Validation evidence confirms that the RFM Baseline matches the Expanded Model\'s practical queue targeting efficiency '
            'while capturing £768.8k more historical commercial spend under Value-Aware prioritization at 10% capacity.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="policy-banner"><strong>Analytical Challenger (Expanded Model):</strong> '
            'Extends baseline with 13 additional features (16 total). While it yields minor statistical improvements in validation '
            'ROC-AUC (0.8079 vs 0.8026), its practical queue gain is negligible (+3 non-repeaters under Risk-first at 10% capacity). '
            'Retained as an analytical benchmark.</div>',
            unsafe_allow_html=True,
        )

    # Extract Key Metrics for Display
    # Default to Risk-first or selected policy for top cards
    card_policy_name = selected_policy_focus if selected_policy_focus != "All Policies" else "Risk-first"
    focus_row = active_policies_df[active_policies_df["policy"] == card_policy_name]
    if focus_row.empty:
        focus_row = active_policies_df.iloc[0:1]

    k_selected = int(focus_row["selected_count"].values[0])
    precision_val = focus_row["selected_non_repeat_rate"].values[0] * 100.0
    capture_share_val = focus_row["share_of_all_non_repeaters_captured"].values[0] * 100.0
    spend_val = focus_row["historical_commercial_value_gbp"].values[0]
    spend_share_val = focus_row["share_of_cohort_commercial_value"].values[0] * 100.0

    pcol1, pcol2, pcol3, pcol4, pcol5 = st.columns(5)
    with pcol1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Target Contacts ({card_policy_name})</div>
                <div class="metric-value">{k_selected:,}</div>
                <div class="metric-subtext">{selected_capacity} of active cohort</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with pcol2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Non-Repeat Precision</div>
                <div class="metric-value">{precision_val:.1f}%</div>
                <div class="metric-subtext">True non-repeaters among selected</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with pcol3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Cohort Capture Share</div>
                <div class="metric-value">{capture_share_val:.1f}%</div>
                <div class="metric-subtext">Share of total cohort non-repeaters</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with pcol4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Historical Spend</div>
                <div class="metric-value">£{spend_val:,.0f}</div>
                <div class="metric-subtext">Historical spend of selected queue</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with pcol5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Cohort Spend Share</div>
                <div class="metric-value">{spend_share_val:.1f}%</div>
                <div class="metric-subtext">Share of total cohort spend</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    # Comparative Visualizations
    pvcol1, pvcol2 = st.columns(2)

    with pvcol1:
        st.markdown('<div class="section-title">Non-Repeat Capture Precision by Policy</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-desc">Proportion of outreach capacity successfully targeted to non-repeating accounts. '
            'Higher precision minimizes wasted contacts on self-retaining accounts.</div>',
            unsafe_allow_html=True,
        )

        chart_df = active_policies_df.copy()
        chart_df["Precision_Pct"] = chart_df["selected_non_repeat_rate"] * 100.0

        prec_chart = (
            alt.Chart(chart_df)
            .mark_bar(cornerRadiusTopRight=2, cornerRadiusBottomRight=2)
            .encode(
                y=alt.Y("policy:N", sort="-x", title="", axis=alt.Axis(labelLimit=180)),
                x=alt.X("Precision_Pct:Q", title="Non-Repeat Precision (%)", scale=alt.Scale(domain=[0, 100])),
                color=alt.condition(
                    alt.datum.policy == card_policy_name,
                    alt.value("#1e3a8a"),
                    alt.value("#94a3b8"),
                ),
                tooltip=[
                    alt.Tooltip("policy:N", title="Policy"),
                    alt.Tooltip("Precision_Pct:Q", title="Precision", format=".2f"),
                    alt.Tooltip("selected_non_repeaters:Q", title="Non-Repeaters Captured", format=",.0f"),
                ],
            )
            .properties(height=260)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(prec_chart, use_container_width=True)

    with pvcol2:
        st.markdown('<div class="section-title">Cohort Historical Spend Represented by Policy</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-desc">Share of total cohort historical commercial spend associated with the targeted queue. '
            'Value-aware targets high-value accounts; Risk-first targets low-spend accounts.</div>',
            unsafe_allow_html=True,
        )

        chart_df["Spend_Share_Pct"] = chart_df["share_of_cohort_commercial_value"] * 100.0

        spend_chart = (
            alt.Chart(chart_df)
            .mark_bar(cornerRadiusTopRight=2, cornerRadiusBottomRight=2)
            .encode(
                y=alt.Y("policy:N", sort="-x", title="", axis=alt.Axis(labelLimit=180)),
                x=alt.X("Spend_Share_Pct:Q", title="Share of Cohort Spend (%)", scale=alt.Scale(domain=[0, 65])),
                color=alt.condition(
                    alt.datum.policy == card_policy_name,
                    alt.value("#1e3a8a"),
                    alt.value("#94a3b8"),
                ),
                tooltip=[
                    alt.Tooltip("policy:N", title="Policy"),
                    alt.Tooltip("Spend_Share_Pct:Q", title="Spend Share", format=".2f"),
                    alt.Tooltip("historical_commercial_value_gbp:Q", title="Historical Spend (£)", format="£,.2f"),
                ],
            )
            .properties(height=260)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(spend_chart, use_container_width=True)

    # Detailed Policy Decision Comparison Table
    st.markdown('<div class="section-title">Verified Policy Comparison Table</div>', unsafe_allow_html=True)

    table_display = active_policies_df.copy()
    table_display["Non-Repeat Precision"] = (table_display["selected_non_repeat_rate"] * 100).round(2).astype(str) + "%"
    table_display["Capture Share"] = (table_display["share_of_all_non_repeaters_captured"] * 100).round(2).astype(str) + "%"
    table_display["Historical Spend"] = table_display["historical_commercial_value_gbp"].apply(lambda v: f"£{v:,.2f}")
    table_display["Spend Share"] = (table_display["share_of_cohort_commercial_value"] * 100).round(2).astype(str) + "%"
    table_display["Non-Repeaters"] = table_display["selected_non_repeaters"].round(1)

    st.dataframe(
        table_display[[
            "policy",
            "selected_count",
            "Non-Repeaters",
            "Non-Repeat Precision",
            "Capture Share",
            "Historical Spend",
            "Spend Share",
        ]].rename(columns={
            "policy": "CRM Policy",
            "selected_count": "Queue Size (k)",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Strategic Guidance on Policy Trade-offs
    st.markdown('<div class="section-title">Operational Policy Guidance</div>', unsafe_allow_html=True)
    st.markdown(
        """
        - **Risk-First Policy (Maximizing Churn Interception):** Targets accounts with lowest repeat probability. 
          Achieves peak non-repeat precision (~95% in validation, ~91% in retrospective evaluation), but represents 
          minimal historical spend (<1%). Ideal for low-cost automated re-engagement (email/app notifications).
        - **Value-Aware Policy (Commercial Protection):** Prioritizes highest historical commercial spend at risk. 
          Represents 35%–41% of cohort commercial spend at 10% capacity. Because high spenders repeat more frequently, 
          non-repeat precision is lower (37%–51%). Ideal for high-touch, expensive interventions (account executive calls).
        - **Hybrid Policy (Balanced Resource Allocation):** Equal-weight combination of risk rank and spend rank 
          ($0.5 \\times \\text{Risk} + 0.5 \\times \\text{Spend}$). Achieves 74%–82% non-repeat precision while representing 
          ~7.5% of cohort historical spend. Recommended for budget-constrained marketing campaigns.
        - **Policy Selection Depends on Operating Context:** No single policy is universally superior across all business goals. 
          Policy choice must be dictated by outreach unit cost, intervention bandwidth, and customer account value.
        """
    )


# =============================================================================
# Methodology & Analytical Safeguards (Secondary Expander)
# =============================================================================

st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
with st.expander("Methodological Governance, Analytical Safeguards & Scope Disclosures"):
    st.markdown(
        """
        ### Analytical Safeguards & Data Lineage
        1. **Chronological Walk-Forward Protocol:** All modeling features are constructed point-in-time strictly prior to 
           each cutoff date. Labels are evaluated over a non-overlapping forward 90-day window to eliminate look-ahead bias.
        2. **Validation-Governed Model Recommendation:** Model selection is governed exclusively by the `2011-06-10` validation cohort. 
           The **3-feature RFM Baseline is recommended as the operational default** due to parsimony, maintainability, and practical parity 
           with the 16-feature Expanded Model.
        3. **Retrospective Status of Later Evaluation Cohort:** The `2011-09-09` cohort was inspected during development and serves 
           strictly as a retrospective temporal benchmark, rather than a prospective holdout.
        4. **Probability Underprediction & Calibration Scope:** Decile calibration was evaluated for the Expanded Model on the 
           `2011-09-09` cohort, where it exhibits systematic probability underprediction. An observed shift in cohort repeat rate 
           (from 32.03% to 43.50%) coincides with that underprediction, while the underlying cause of this shift remains unknown from 
           observational transaction data. Raw probabilities must not be interpreted as absolute calibrated frequencies.
        5. **Observational Data Boundaries:** Historical commercial spend associated with selected queues represents past transaction volume. 
           It does **not** measure incremental retention, campaign uplift, causal impact, profit, or customer lifetime value (CLV).
        6. **Archival Scope:** All data terminates in December 2011. The final `2011-12-09` snapshot has strictly unobserved forward labels.
        """
    )

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.markdown(
    """
    <div class="footer-box">
        RetenSight Decision Support System · Verified Walk-Forward Analytics · Built with Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
