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
# 1. SIDEBAR / TOP FILE UPLOADER WIDGET
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Data Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload Budget Excel File", 
    type=["xlsx", "xls"],
    help="Upload your own Excel sheet or use the default uploaded file."
)

@st.cache_data(ttl=60)
def load_data(file_source):
    """Loads and returns data from an uploaded file or local path."""
    return pd.read_excel(file_source)

df = None
file_loaded_from = None

# Priority 1: User uploaded a file in the web app
if uploaded_file is not None:
    try:
        df = load_data(uploaded_file)
        file_loaded_from = f"Uploaded File ({uploaded_file.name})"
    except Exception as e:
        st.error(f"Error reading uploaded Excel file: {e}")

# Priority 2: Fallback to default files in the GitHub repository
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
if df is not None:
    st.success(f"✅ Data loaded successfully from **{file_loaded_from}**")
    
    # Clean column names (strip leading/trailing whitespace)
    df.columns = [str(col).strip() for col in df.columns]

    # Metrics Summary Bar (Adapts if numeric columns exist)
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if numeric_cols:
        cols = st.columns(min(len(numeric_cols), 4))
        for idx, col_name in enumerate(numeric_cols[:4]):
            total_val = df[col_name].sum()
            cols[idx].metric(
                label=col_name.title(), 
                value=f"{total_val:,.2f}"
            )
        st.markdown("---")

    # Layout Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Visualizations", "📋 Data Table", "🏦 Bank API Status"])

    with tab1:
        st.subheader("Budget Analytics")
        if len(numeric_cols) >= 1:
            # First categorical column for X-axis, first numeric for Y-axis
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
            st.info("No numeric data found in the file to plot charts.")

    with tab2:
        st.subheader("Raw Data View")
        st.dataframe(df, use_container_width=True)

    with tab3:
        st.subheader("Bank API Integration")
        # Safe import check for bank_api module
        try:
            from bank_api import BankAccountAPI
            st.success("`bank_api` module imported successfully!")
            # Call bank API methods here as needed
        except ImportError:
            st.warning("`bank_api.py` not found or `BankAccountAPI` class missing.")
        except Exception as e:
            st.error(f"Error initializing Bank API: {e}")

else:
    st.info("💡 **No budget file found.** Use the sidebar on the left to upload an Excel file, or ensure `Event_Budget_Breakdown.xlsx` is uploaded to your GitHub repository root folder.")