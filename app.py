import os
import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="C.A. Dawodu 80th Birthday Budget",
    page_icon="🎉",
    layout="wide"
)

st.title("🎉 C.A. Dawodu 80th Birthday Dashboard")
st.markdown("---")

# -----------------------------------------------------------------------------
# 1. FILE LOADING & DE-DUPLICATION
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Data Source & Controls")
uploaded_file = st.sidebar.file_uploader(
    "Upload Budget Excel File", 
    type=["xlsx", "xls"],
    help="Upload your Excel sheet or use default repository file."
)

@st.cache_data(ttl=60)
def load_and_clean_data(file_source):
    # Load ONLY the first sheet to avoid multi-sheet double counting
    excel_file = pd.ExcelFile(file_source)
    sheet_to_load = excel_file.sheet_names[0]
    data = pd.read_excel(file_source, sheet_name=sheet_to_load)
    
    # Strip whitespace from column names
    data.columns = [str(col).strip() for col in data.columns]
    
    # Remove empty rows
    data = data.dropna(how='all')
    
    # Remove exact row duplicates
    data = data.drop_duplicates()
    
    # Rigorous filtering for subtotal/summary keywords across text columns
    text_cols = data.select_dtypes(include=['object', 'category']).columns
    filter_mask = pd.Series(True, index=data.index)
    
    keywords = ['TOTAL', 'SUBTOTAL', 'SUB-TOTAL', 'GRAND TOTAL', 'SUMMARY', 'OVERALL']
    for col in text_cols:
        for kw in keywords:
            filter_mask &= ~data[col].astype(str).str.upper().str.contains(kw, na=False)
            
    clean_df = data[filter_mask].copy()
    return clean_df, sheet_to_load

df = None
sheet_used = None

if uploaded_file is not None:
    try:
        df, sheet_used = load_and_clean_data(uploaded_file)
    except Exception as e:
        st.error(f"Error reading uploaded file: {e}")
else:
    default_files = ["Event_Budget_Breakdown.xlsx", "Event_Budget_Breakdown.xls"]
    for file_name in default_files:
        if os.path.exists(file_name):
            try:
                df, sheet_used = load_and_clean_data(file_name)
                break
            except Exception as e:
                st.warning(f"Error loading {file_name}: {e}")

# -----------------------------------------------------------------------------
# 2. APP MAIN DISPLAY
# -----------------------------------------------------------------------------
if df is not None and not df.empty:
    st.success(f"✅ Loaded Sheet: **'{sheet_used}'** ({len(df)} line items detected)")

    # Find numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

    if not numeric_cols:
        st.error("⚠️ No numeric cost/amount columns found in this Excel sheet.")
    else:
        # Sidebar control: Let user select EXACTLY which column contains the amount
        selected_amount_col = st.sidebar.selectbox(
            "Select Primary Amount Column to Total:",
            options=numeric_cols,
            index=0,
            help="If your sheet has multiple numeric columns (e.g. Budget vs Actual), pick the right one."
        )

        # Calculate isolated total
        true_total = df[selected_amount_col].sum()

        # Display Prominent Metric
        st.metric(
            label=f"Calculated Total ({selected_amount_col})", 
            value=f"₦{true_total:,.2f}"
        )
        st.markdown("---")

        # Tabs - Data Table FIRST
        tab1, tab2, tab3 = st.tabs(["📋 Data Table (Raw Items)", "📊 Visualizations", "🏦 Bank API Status"])

        # --- TAB 1: DATA TABLE ---
        with tab1:
            st.subheader("Line Items Included in Total")
            st.caption("Inspect the rows below to check if any subtotal rows are still present.")
            st.dataframe(df, use_container_width=True)
            
            # Show debug sum per column
            st.markdown("#### Column Sums Breakdown:")
            for n_col in numeric_cols:
                st.write(f"• **{n_col}** Sum: `₦{df[n_col].sum():,.2f}`")

        # --- TAB 2: VISUALIZATIONS ---
        with tab2:
            st.subheader("Budget Analytics")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            x_col = cat_cols[0] if cat_cols else df.columns[0]

            col1, col2 = st.columns(2)
            
            with col1:
                fig_bar = px.bar(
                    df, 
                    x=x_col, 
                    y=selected_amount_col, 
                    title=f"{selected_amount_col} by {x_col}",
                    color_discrete_sequence=["#1f77b4"]
                )
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                fig_pie = px.pie(
                    df, 
                    names=x_col, 
                    values=selected_amount_col, 
                    title=f"{selected_amount_col} Distribution",
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        # --- TAB 3: BANK API ---
        with tab3:
            st.subheader("Bank API Integration")
            try:
                from bank_api import BankAccountAPI
                st.success("`bank_api` module imported successfully!")
            except ImportError:
                st.warning("`bank_api.py` not found in root directory.")
            except Exception as e:
                st.error(f"Error: {e}")

else:
    st.info("💡 No budget file found. Please upload an Excel sheet.")