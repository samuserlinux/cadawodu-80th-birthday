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
# 1. SIDEBAR / FILE UPLOADER WIDGET
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Data Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload Budget Excel File", 
    type=["xlsx", "xls"],
    help="Upload your own Excel sheet or use the default uploaded file."
)

@st.cache_data(ttl=60)
def load_data(file_source):
    """Loads and cleans data from an Excel spreadsheet."""
    # Load first sheet of Excel file
    data = pd.read_excel(file_source, sheet_name=0)
    
    # Clean column headers
    data.columns = [str(col).strip() for col in data.columns]
    
    # 1. Remove exact duplicate rows
    data = data.drop_duplicates()
    
    # 2. Exclude summary/total rows to prevent double counting
    for col in data.columns:
        if data[col].dtype == 'object':
            data = data[~data[col].astype(str).str.upper().str.contains('TOTAL|SUBTOTAL|GRAND TOTAL', na=False)]
            
    return data

df = None
file_loaded_from = None

# Priority 1: Web App Uploader
if uploaded_file is not None:
    try:
        df = load_data(uploaded_file)
        file_loaded_from = f"Uploaded File ({uploaded_file.name})"
    except Exception as e:
        st.error(f"Error reading uploaded Excel file: {e}")

# Priority 2: Fallback to GitHub repository Excel file
else:
    default_files = ["Event_Budget_Breakdown.xlsx", "Event_Budget_Breakdown.xls"]
    for file_name in default_files:
        if os.path.exists(file_name):
            try:
                df = load_data(file_name)
                file_loaded_from = f"Default Repo File ({file_name})"
                break
            except Exception as e:
                st.warning(f"Found {file_name} but couldn't read it: {e}")

# -----------------------------------------------------------------------------
# 2. MAIN APP DISPLAY
# -----------------------------------------------------------------------------
if df is not None and not df.empty:
    st.success(f"✅ Data loaded successfully from **{file_loaded_from}**")
    
    # Identify numeric columns for metrics & charts
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

    # Metrics Bar (Naira Formatted)
    if numeric_cols:
        cols = st.columns(min(len(numeric_cols), 4))
        for idx, col_name in enumerate(numeric_cols[:4]):
            total_val = df[col_name].sum()
            cols[idx].metric(
                label=col_name.title(), 
                value=f"₦{total_val:,.2f}"
            )
        st.markdown("---")

    # Layout Tabs - DATA TABLE IS NOW TAB 1 (FIRST)
    tab1, tab2, tab3 = st.tabs(["📋 Data Table", "📊 Visualizations", "🏦 Bank API Status"])

    # --- TAB 1: DATA TABLE (NOW SHOWS FIRST) ---
    with tab1:
        st.subheader("Raw Budget Data View")
        st.caption("Double-counting protection applied (Total/Subtotal summary rows filtered out).")
        st.dataframe(df, use_container_width=True)

    # --- TAB 2: VISUALIZATIONS ---
    with tab2:
        st.subheader("Budget Analytics")
        if numeric_cols:
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            x_col = cat_cols[0] if cat_cols else df.columns[0]
            y_col = numeric_cols[0]

            col1, col2 = st.columns(2)
            
            with col1:
                fig_bar = px.bar(
                    df, 
                    x=x_col, 
                    y=y_col, 
                    title=f"{y_col} by {x_col}",
                    color_discrete_sequence=["#1f77b4"]
                )
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                fig_pie = px.pie(
                    df, 
                    names=x_col, 
                    values=y_col, 
                    title=f"{y_col} Distribution",
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No numeric data columns found in the spreadsheet to plot charts.")

    # --- TAB 3: BANK API ---
    with tab3:
        st.subheader("Bank API Integration")
        try:
            from bank_api import BankAccountAPI
            st.success("`bank_api` module imported successfully!")
        except ImportError:
            st.warning("`bank_api.py` not found or `BankAccountAPI` class missing in root directory.")
        except Exception as e:
            st.error(f"Error initializing Bank API: {e}")

else:
    st.info("💡 **No budget data found.** Use the sidebar on the left to upload your Excel spreadsheet, or verify that `Event_Budget_Breakdown.xlsx` exists in your GitHub repository.")