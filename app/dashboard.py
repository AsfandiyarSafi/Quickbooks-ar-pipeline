"""Streamlit AR dashboard: reads invoices and payments from Supabase."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from payments_ar.config import ConfigurationError, supabase_service_key, supabase_url  # noqa: E402

try:
    _url = supabase_url()
    _key = supabase_service_key()
except ConfigurationError as err:
    st.set_page_config(page_title="AR Dashboard", layout="wide")
    st.error(str(err))
    st.stop()

supabase = create_client(_url, _key)

st.set_page_config(page_title="AR Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.title("Accounts receivable")
st.caption("Invoice and payment totals from Supabase.")

# Load data
invoices_resp = supabase.table("invoices").select("*").execute()
invoices = pd.DataFrame(invoices_resp.data)
if invoices.empty:
    st.warning("No invoice data found.")
    st.stop()

payments_resp = supabase.table("payments").select("*").execute()
payments = pd.DataFrame(payments_resp.data)
if payments.empty:
    payments = pd.DataFrame(
        columns=["id", "invoice_id", "customername", "totalamt", "paymentdate", "paymentmethod"]
    )

# Types (Supabase/JSON can mix str/int for ids and money)
invoices["id"] = invoices["id"].astype(str).str.strip()

invoices["txndate"] = pd.to_datetime(invoices["txndate"], errors="coerce")
invoices["totalamt"] = pd.to_numeric(invoices["totalamt"], errors="coerce").fillna(0)
invoices["balance"] = pd.to_numeric(invoices["balance"], errors="coerce").fillna(0)
invoices["status"] = (
    invoices["status"].fillna("").astype(str).str.strip().str.capitalize()
)

if not payments.empty:
    payments["invoice_id"] = payments["invoice_id"].astype(str).str.strip()
    payments["paymentdate"] = pd.to_datetime(payments["paymentdate"], errors="coerce")
    payments["totalamt"] = pd.to_numeric(payments["totalamt"], errors="coerce").fillna(0)

# AR metrics
total_invoiced = invoices["totalamt"].sum()
total_outstanding = invoices.loc[invoices["balance"] > 0, "balance"].sum()
open_invoices = int((invoices["balance"] > 0).sum())
total_payments_recorded = float(payments["totalamt"].sum()) if not payments.empty else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Invoices", f"{len(invoices):,}")
col2.metric("Total invoiced", f"${total_invoiced:,.2f}")
col3.metric("Outstanding", f"${total_outstanding:,.2f}", help="Sum of balance on open invoices")
col4.metric("Open invoices", f"{open_invoices:,}")
col5.metric("Payments received", f"${total_payments_recorded:,.2f}", help="Sum of payment rows")

st.divider()

# Portfolio: invoiced vs payments
st.subheader("Portfolio: invoiced vs payments")
portfolio = pd.DataFrame(
    {
        "Amount": [total_invoiced, total_payments_recorded],
        "Series": ["Total invoiced", "Payments received"],
    }
)
fig_portfolio = px.bar(
    portfolio,
    x="Series",
    y="Amount",
    color="Series",
    text="Amount",
    color_discrete_map={"Total invoiced": "#2563eb", "Payments received": "#059669"},
)
fig_portfolio.update_traces(texttemplate="$%{y:,.2f}", textposition="outside")
fig_portfolio.update_layout(showlegend=False, yaxis_title="USD", xaxis_title=None, height=400)
fig_portfolio.update_yaxes(tickprefix="$")
st.plotly_chart(fig_portfolio, width="stretch")

# Per invoice: invoice amount vs payments (merge uses id_inv / id_pay)
st.subheader("Per invoice: invoice amount vs payments received")
merged = invoices.merge(
    payments,
    left_on="id",
    right_on="invoice_id",
    how="left",
    suffixes=("_inv", "_pay"),
)
payment_summary = merged.groupby("id_inv", dropna=False).agg(
    invoice_amount=("totalamt_inv", "first"),
    payments_received=("totalamt_pay", "sum"),
    open_balance=("balance", "first"),
).fillna(0).reset_index()
payment_summary["remaining"] = payment_summary["invoice_amount"] - payment_summary["payments_received"]

fig_scatter = px.scatter(
    payment_summary,
    x="invoice_amount",
    y="payments_received",
    color="remaining",
    color_continuous_scale="Teal",
    hover_data={
        "id_inv": True,
        "invoice_amount": ":$,.2f",
        "payments_received": ":$,.2f",
        "remaining": ":$,.2f",
        "open_balance": ":$,.2f",
    },
    labels={
        "invoice_amount": "Invoice amount",
        "payments_received": "Payments received",
        "remaining": "Remaining (invoice − payments)",
        "open_balance": "Open balance (on invoice)",
    },
)
fig_scatter.add_shape(
    type="line",
    x0=0,
    y0=0,
    x1=max(payment_summary["invoice_amount"].max(), 1),
    y1=max(payment_summary["invoice_amount"].max(), 1),
    line=dict(color="rgba(0,0,0,0.35)", width=1, dash="dash"),
)
fig_scatter.update_layout(height=480, xaxis_tickprefix="$", yaxis_tickprefix="$")
st.plotly_chart(fig_scatter, width="stretch")

with st.expander("Per-invoice table"):
    display_tbl = payment_summary.rename(
        columns={
            "id_inv": "invoice_id",
            "invoice_amount": "Invoice amount",
            "payments_received": "Payments received",
            "remaining": "Remaining (inv − pay)",
            "open_balance": "Open balance (invoice row)",
        }
    )
    st.dataframe(
        display_tbl,
        width="stretch",
        hide_index=True,
        column_config={
            "Invoice amount": st.column_config.NumberColumn(format="$%.2f"),
            "Payments received": st.column_config.NumberColumn(format="$%.2f"),
            "Remaining (inv − pay)": st.column_config.NumberColumn(format="$%.2f"),
            "Open balance (invoice row)": st.column_config.NumberColumn(format="$%.2f"),
        },
    )
    st.caption(
        "If **Payments received** is $0, no `payments` rows matched that `invoice_id` (or none exist). "
        "Compare **Remaining** to **Open balance**: they should match when payments are recorded correctly."
    )
