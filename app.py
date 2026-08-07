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
# 1. FILE LOADING, CLEANING & COLUMN REMOVAL
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
    
    # Strip whitespace from column headers
    data.columns = [str(col).strip() for col in data.columns]
    
    # -------------------------------------------------------------------------
    # DELETE DESCRIPTION COLUMNS
    # -------------------------------------------------------------------------
    # Drop columns that match 'description', 'desc', 'notes', etc. (case-insensitive)
    cols_to_drop = [
        col for col in data.columns 
        if col.lower() in ['description', 'desc', 'notes', 'details', 'comment', 'comments']
    ]
    if cols_to_drop:
        data = data.drop(columns=cols_to_drop)
    
    # Clean empty and duplicate rows
    data = data.dropna(how='all')
    data = data.drop_duplicates()
    
    # Filter out summary/total rows to prevent double counting
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
# 2. MAIN APP DISPLAY
# -----------------------------------------------------------------------------
if df is not None and not df.empty:
    st.success(f"✅ Data loaded successfully from sheet: **'{sheet_used}'**")

    # Find numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

    if not numeric_cols:
        st.error("⚠️ No numeric cost/amount columns found in this Excel sheet.")
    else:
        # Select Primary Amount Column (defaults to first numeric column)
        selected_amount_col = st.sidebar.selectbox(
            "Select Amount Column to Total:",
            options=numeric_cols,
            index=0
        )

        # Calculate Total
        total_amount = df[selected_amount_col].sum()

        # Display Total Metric
        st.metric(
            label=f"Total Budget ({selected_amount_col})", 
            value=f"₦{total_amount:,.2f}"
        )
        st.markdown("---")

        # Tabs Layout - DATA TABLE IS FIRST
        tab1, tab2, tab3 = st.tabs(["📋 Data Table", "📊 Visualizations", "🏦 Bank API Status"])

        # --- TAB 1: DATA TABLE (FIRST) ---
        with tab1:
            st.subheader("Raw Budget Data View")
            st.caption("Note: 'Description' column has been removed automatically.")
            st.dataframe(df, use_container_width=True)

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