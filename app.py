import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

from data_generator import generate_synthetic_data
from risk_engine import compute_user_baseline, compute_risk
from llm_engine import generate_risk_report

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="AI Compliance Review System", layout="wide")

LOG_FILE = "decision_log.json"


# ---------------------------------------------------
# SAFE LOGGING SYSTEM
# ---------------------------------------------------
def load_log():
    """Load decision log safely. Returns [] on any failure."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_log(data):
    """Atomically save decision log."""
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------
# LOAD & CACHE DATA
# ---------------------------------------------------
@st.cache_data
def load_data():
    df = generate_synthetic_data()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@st.cache_data
def get_flagged_transactions(_df, _user_stats):
    """
    Compute flagged transactions once and cache.
    Underscore-prefixed args tell Streamlit not to hash them.
    """
    flagged = []
    for _, tx in _df.iterrows():
        user_history = _df[_df["user_id"] == tx["user_id"]]
        risk_context = compute_risk(tx, _user_stats, user_history)
        if risk_context["risk_score"] > 0.5:
            flagged.append({
                "tx": {
                    "transaction_id": tx["transaction_id"],
                    "user_id": int(tx["user_id"]),
                    "amount": float(tx["amount"]),
                    "country": tx["country"],
                    "device_id": tx["device_id"],
                    "timestamp": str(tx["timestamp"]),
                    "merchant_category": tx["merchant_category"],
                },
                "risk_context": risk_context,
            })
    return flagged


# ---------------------------------------------------
# INITIALIZE
# ---------------------------------------------------
df = load_data()
user_stats = compute_user_baseline(df)
flagged_transactions = get_flagged_transactions(df, user_stats)

# ---------------------------------------------------
# UI HEADER
# ---------------------------------------------------
st.title("🛡️ AI-Native Suspicious Transaction Review")

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.header("Flagged Transactions")

if not flagged_transactions:
    st.sidebar.info("No flagged transactions detected.")
    st.info("All transactions are within normal behavioral baselines.")
    st.stop()

tx_ids = [item["tx"]["transaction_id"] for item in flagged_transactions]
selected_tx_id = st.sidebar.selectbox("Select Transaction", tx_ids)

selected_item = next(
    item for item in flagged_transactions
    if item["tx"]["transaction_id"] == selected_tx_id
)

selected_tx = selected_item["tx"]
risk_context = selected_item["risk_context"]

# ---------------------------------------------------
# TRANSACTION DETAILS
# ---------------------------------------------------
st.subheader("📋 Transaction Details")
st.json(selected_tx)

# ---------------------------------------------------
# DETERMINISTIC RISK METRICS
# ---------------------------------------------------
st.subheader("📊 Deterministic Risk Metrics")
st.json(risk_context)

# ---------------------------------------------------
# LLM RISK ASSESSMENT
# ---------------------------------------------------
st.subheader("🤖 AI Risk Assessment")

# Key the report to the selected transaction so switching clears stale data
report_key = f"llm_report_{selected_tx_id}"

if st.button("Generate AI Report"):
    with st.spinner("Querying LLM..."):
        llm_report = generate_risk_report(risk_context)
    st.session_state[report_key] = llm_report

if report_key in st.session_state:
    report = st.session_state[report_key]
    st.json(report)

    ai_action = report.get("recommended_action", "escalate")

    # ---------------------------------------------------
    # HUMAN DECISION
    # ---------------------------------------------------
    st.subheader("✅ Human Decision")

    col1, col2, col3 = st.columns(3)

    decision = None

    if col1.button("Approve"):
        decision = "approved_by_human"

    if col2.button("Escalate"):
        decision = "escalated_by_human"

    if ai_action == "freeze" and col3.button("Confirm Freeze"):
        decision = "freeze_confirmed_by_human"

    if decision:
        log_entry = {
            "transaction_id": selected_tx["transaction_id"],
            "risk_score": risk_context["risk_score"],
            "ai_recommendation": ai_action,
            "human_decision": decision,
            "confidence": report.get("confidence", 0.0),
            "timestamp": datetime.now().isoformat(),
        }

        data = load_log()
        data.append(log_entry)
        save_log(data)

        st.success(f"Decision logged: **{decision}**")