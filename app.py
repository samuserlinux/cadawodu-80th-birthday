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

DEFAULT_FILE_PATH = "Event_Budget_Breakdown.xlsx"

# -----------------------------------------------------------------------------
# 1. PERMANENT FILE SAVING & CACHE CLEARING
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Data Source & Controls")

uploaded_file = st.sidebar.file_uploader(
    "Upload New Budget Excel File", 
    type=["xlsx", "xls"],
    help="Uploading a new file will replace the current default budget for everyone!"
)

# If a user uploads a new file, save it locally to the server to make it permanent!
if uploaded_file is not None:
    try:
        # 1. Overwrite the default file on disk
        with open(DEFAULT_FILE_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 2. Clear Streamlit's data cache so all connected devices see the new file
        st.cache_data.clear()
        
        st.sidebar.success("✅ New file pinned as the current default for all users!")
    except Exception as e:
        st.sidebar.error(f"Error saving uploaded file: {e}")

# Function to read and clean the active budget file
@st.cache_data(ttl=1)  # Minimal cache TTL so changes refresh instantly
def load_and_clean_data(file_path):
    if not os.path.exists(file_path):
        return None, None

    excel_file = pd.ExcelFile(file_path)
    sheet_to_load = excel_file.sheet_names[0]
    data = pd.read_excel(file_path, sheet_name=sheet_to_load)
    
    # Clean column headers
    data.columns = [str(col).strip() for col in data.columns]
    
    # Remove Description / Notes columns
    cols_to_drop = [
        col for col in data.columns 
        if col.lower() in ['description', 'desc', 'notes', 'details', 'comment', 'comments']
    ]
    if cols_to_drop:
        data = data.drop(columns=cols_to_drop)
    
    # Clean rows
    data = data.dropna(how='all')
    data = data.drop_duplicates()
    
    # Filter out pre-existing total rows from Excel to avoid double counting
    text_cols = data.select_dtypes(include=['object', 'category']).columns
    filter_mask = pd.Series(True, index=data.index)
    keywords = ['TOTAL', 'SUBTOTAL', 'SUB-TOTAL', 'GRAND TOTAL', 'SUMMARY', 'OVERALL']
    
    for col in text_cols:
        for kw in keywords:
            filter_mask &= ~data[col].astype(str).str.upper().str.contains(kw, na=False)
            
    clean_df = data[filter_mask].copy()
    return clean_df, sheet_to_load

# Load the file from disk
df, sheet_used = load_and_clean_data(DEFAULT_FILE_PATH)

# Add a manual force-refresh button in sidebar just in case
if st.sidebar.button("🔄 Force Refresh Live Balance"):
    st.cache_data.clear()
    st.rerun()

# -----------------------------------------------------------------------------
# 2. MAIN APP DISPLAY
# -----------------------------------------------------------------------------
if df is not None and not df.empty:
    st.success(f"✅ Active Data: **'{sheet_used}'** ({len(df)} line items)")

    # Find numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

    if not numeric_cols:
        st.error("⚠️ No numeric cost/amount columns found in this Excel sheet.")
    else:
        selected_amount_col = st.sidebar.selectbox(
            "Select Amount Column to Total:",
            options=numeric_cols,
            index=0
        )

        # Calculate Overall Total
        total_amount = df[selected_amount_col].sum()

        # Display Top Summary Metric
        st.metric(
            label=f"Total Budget ({selected_amount_col})", 
            value=f"₦{total_amount:,.2f}"
        )
        st.markdown("---")

        # ---------------------------------------------------------------------
        # CALCULATION: ADD PERCENTAGE OF TOTAL COLUMN
        # ---------------------------------------------------------------------
        df_calc = df.copy()
        
        # Compute percentage for each row
        if total_amount > 0:
            df_calc['% of Total'] = (df_calc[selected_amount_col] / total_amount) * 100
        else:
            df_calc['% of Total'] = 0.0

        # Position '% of Total' right after the selected Amount column
        amount_idx = df_calc.columns.get_loc(selected_amount_col)
        cols = list(df_calc.columns)
        cols.insert(amount_idx + 1, cols.pop(cols.index('% of Total')))
        df_calc = df_calc[cols]

        # ---------------------------------------------------------------------
        # BUILD TABLE WITH FORMATTING & BOTTOM TOTAL ROW
        # ---------------------------------------------------------------------
        df_display = df_calc.copy()

        # Create Total Row
        total_row = {}
        for col in df_display.columns:
            if col == selected_amount_col:
                total_row[col] = f"₦{total_amount:,.2f}"
            elif col == '% of Total':
                total_row[col] = "100.00%"
            elif col in numeric_cols:
                col_sum = df_display[col].sum()
                total_row[col] = f"{col_sum:,.2f}"
            else:
                total_row[col] = "TOTAL"

        # Format rows for display in data table
        df_formatted = df_display.copy()
        df_formatted[selected_amount_col] = df_formatted[selected_amount_col].apply(lambda x: f"₦{x:,.2f}")
        df_formatted['% of Total'] = df_formatted['% of Total'].apply(lambda x: f"{x:.2f}%")

        # Append bottom row
        df_with_total = pd.concat([df_formatted, pd.DataFrame([total_row])], ignore_index=True)

        # Tabs Layout
        tab1, tab2, tab3 = st.tabs(["📋 Data Table", "📊 Visualizations", "🏦 Bank API Status"])

        # --- TAB 1: DATA TABLE ---
        with tab1:
            st.subheader("Raw Budget Data View")
            st.caption("Includes calculated **% of Total** and a bottom **TOTAL** row.")
            st.dataframe(df_with_total, use_container_width=True)

        # --- TAB 2: VISUALIZATIONS ---
        with tab2:
            st.subheader("Budget Analytics")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            x_col = cat_cols[0] if cat_cols else df.columns[0]

            col1, col2 = st.columns(2)
            
            with col1:
                fig_bar = px.bar(
                    df_calc, 
                    x=x_col, 
                    y=selected_amount_col, 
                    title=f"{selected_amount_col} by {x_col}",
                    color_discrete_sequence=["#1f77b4"]
                )
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                fig_pie = px.pie(
                    df_calc, 
                    names=x_col, 
                    values=selected_amount_col, 
                    title=f"{selected_amount_col} Breakdown (%)",
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
    st.info("💡 No budget file found. Please upload an Excel sheet using the sidebar.")