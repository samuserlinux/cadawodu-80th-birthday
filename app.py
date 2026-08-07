import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from bank_api import BankAccountAPI

load_dotenv()
CURRENCY = os.getenv("CURRENCY_SYMBOL", "₦")
TARGET_BUDGET = float(os.getenv("TARGET_BUDGET", 10000000))

st.set_page_config(
    page_title="C. A. Dawodu 80th Birthday Party",
    page_icon="🎂",
    layout="wide"
)

# Load Colorful CSS
if os.path.exists("assets/style.css"):
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

bank = BankAccountAPI()

# Session State for Initial Data
if 'contributions' not in st.session_state:
    st.session_state.contributions = [
        {"Sibling": "Tunde (UK)", "Amount": 2500000, "Date": "2026-07-10"},
        {"Sibling": "Bisi (USA)", "Amount": 3000000, "Date": "2026-07-12"},
        {"Sibling": "Kemi (Nigeria)", "Amount": 2000000, "Date": "2026-07-15"},
    ]

if 'expenses' not in st.session_state:
    st.session_state.expenses = [
        {"Category": "Venue & Decor", "Description": "Hall Deposit", "Amount": 2000000, "Paid By": "Shared Account"},
        {"Category": "Catering", "Description": "Food & Drinks Deposit", "Amount": 2500000, "Paid By": "Shared Account"},
        {"Category": "Entertainment", "Description": "Band Deposit", "Amount": 800000, "Paid By": "Shared Account"},
    ]

# --- HEADER BANNER ---
st.markdown(
    """
    <div class="main-header">
        <h1>🎉 C. A. Dawodu 80th Birthday Party 🎂</h1>
        <p>Real-Time Bank Balance, Family Contributions & Transparent Expense Tracker</p>
    </div>
    """, 
    unsafe_allow_html=True
)

bank_info = bank.fetch_realtime_balance(st.session_state.contributions, st.session_state.expenses)

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)

total_raised = sum(c["Amount"] for c in st.session_state.contributions)
total_spent = sum(e["Amount"] for e in st.session_state.expenses)
current_balance = bank_info["available_balance"]
remaining_budget = TARGET_BUDGET - total_spent

with col1:
    st.metric("🏦 Live Bank Balance", f"{CURRENCY}{current_balance:,.2f}")
with col2:
    st.metric("💰 Total Contributions", f"{CURRENCY}{total_raised:,.2f}")
with col3:
    st.metric("💸 Total Expenses Paid", f"{CURRENCY}{total_spent:,.2f}")
with col4:
    st.metric("🎯 Remaining Target", f"{CURRENCY}{remaining_budget:,.2f}")

st.divider()

# --- CHARTS SECTION ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📊 Financial Breakdown")
    df_chart = pd.DataFrame([
        {"Type": "Target Budget", "Amount": TARGET_BUDGET},
        {"Type": "Contributed", "Amount": total_raised},
        {"Type": "Spent", "Amount": total_spent},
        {"Type": "Live Balance", "Amount": current_balance}
    ])
    
    fig = px.bar(
        df_chart, x="Type", y="Amount", color="Type",
        color_discrete_map={
            "Target Budget": "#8B5CF6",
            "Contributed": "#10B981",
            "Spent": "#EF4444",
            "Live Balance": "#3B82F6"
        },
        text_auto=',.0f'
    )
    fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("🎯 Contribution Progress")
    progress_pct = min((total_raised / TARGET_BUDGET) * 100, 100)
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = progress_pct,
        number = {'suffix': "%"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#FF4B2B"},
            'steps': [
                {'range': [0, 50], 'color': "#FFE4E6"},
                {'range': [50, 80], 'color': "#FEF3C7"},
                {'range': [80, 100], 'color': "#D1FAE5"}
            ]
        }
    ))
    fig_gauge.update_layout(height=350)
    st.plotly_chart(fig_gauge, use_container_width=True)

st.divider()

# --- LEDGERS AND INPUT FORMS ---
tab1, tab2 = st.tabs(["💵 Sibling Contributions", "🧾 Party Expenses"])

with tab1:
    st.subheader("Log New Contribution")
    with st.form("contrib_form", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns(3)
        name = fc1.text_input("Contributor Name & Location")
        amt = fc2.number_input(f"Amount ({CURRENCY})", min_value=0.0, step=50000.0)
        dt = fc3.date_input("Date Paid")
        sub = st.form_submit_button("Save Contribution")
        
        if sub and name and amt > 0:
            st.session_state.contributions.append({"Sibling": name, "Amount": amt, "Date": str(dt)})
            st.success(f"Recorded contribution of {CURRENCY}{amt:,.2f} from {name}!")
            st.rerun()

    st.subheader("Contributions History")
    st.dataframe(pd.DataFrame(st.session_state.contributions), use_container_width=True)

with tab2:
    st.subheader("Log New Expense")
    with st.form("exp_form", clear_on_submit=True):
        ec1, ec2, ec3, ec4 = st.columns(4)
        cat = ec1.selectbox("Category", ["Venue & Decor", "Catering", "Entertainment", "Gifts & Souvenirs", "Logistics", "Other"])
        desc = ec2.text_input("Description")
        e_amt = ec3.number_input(f"Amount ({CURRENCY})", min_value=0.0, step=10000.0)
        p_by = ec4.text_input("Paid By", value="Shared Bank Account")
        e_sub = st.form_submit_button("Save Expense")
        
        if e_sub and desc and e_amt > 0:
            st.session_state.expenses.append({"Category": cat, "Description": desc, "Amount": e_amt, "Paid By": p_by})
            st.success(f"Logged expense: {desc} ({CURRENCY}{e_amt:,.2f})")
            st.rerun()

    st.subheader("Expense Ledger")
    st.dataframe(pd.DataFrame(st.session_state.expenses), use_container_width=True)
