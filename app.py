import streamlit as st
import pandas as pd
import plotly.express as px

# App Title
st.title("Universal Data Analyzer & Campaign Tracker")

# File Upload
file = st.file_uploader("Upload your dataset (CSV or XLSX)", type=["csv", "xlsx"])

if file is not None:
    try:
        # Load file
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        st.subheader("Dataset Overview")
        st.write(df.head())

        # -----------------------------
        # 🔥 COLUMN MAPPING (UNIVERSAL)
        # -----------------------------
        st.sidebar.header("Map Your Columns")

        numeric_cols = df.select_dtypes(include='number').columns

        clicks_col = st.sidebar.selectbox("Clicks", numeric_cols)
        impressions_col = st.sidebar.selectbox("Impressions", numeric_cols)
        spend_col = st.sidebar.selectbox("Spend", numeric_cols)
        revenue_col = st.sidebar.selectbox("Revenue / ROI", numeric_cols)

        # -----------------------------
        # 🔥 METRICS CALCULATION
        # -----------------------------
        df['ctr'] = df[clicks_col] / df[impressions_col]
        df['cpc'] = df[spend_col] / df[clicks_col]
        df['roi'] = df[revenue_col]

        # -----------------------------
        # 🔥 KPI SECTION
        # -----------------------------
        st.subheader("Key Performance Indicators")

        col1, col2, col3 = st.columns(3)

        col1.metric("Avg CTR", f"{df['ctr'].mean():.2%}")
        col2.metric("Avg ROI", f"{df['roi'].mean():.2f}")
        col3.metric("Total Spend", f"{df[spend_col].sum():,.0f}")

        # -----------------------------
        # 🔥 PERFORMANCE CLASSIFICATION
        # -----------------------------
        def ctr_level(ctr):
            if ctr >= 0.03:
                return "Excellent"
            elif ctr >= 0.01:
                return "Good"
            elif ctr >= 0.005:
                return "Average"
            else:
                return "Needs Improvement"

        df['performance'] = df['ctr'].apply(ctr_level)

        # -----------------------------
        # 🔥 OPTIONAL FILTERS
        # -----------------------------
        st.sidebar.header("Filters")

        categorical_cols = df.select_dtypes(include='object').columns

        filter_col = st.sidebar.selectbox("Filter Column", categorical_cols)

        filter_value = st.sidebar.selectbox("Filter Value", df[filter_col].unique())

        filtered_df = df[df[filter_col] == filter_value]

        # -----------------------------
        # 🔥 TOP RECORDS
        # -----------------------------
        st.subheader("Top Performers")
        st.dataframe(filtered_df.sort_values('ctr', ascending=False).head(5))

        # -----------------------------
        # 🔥 CHARTS
        # -----------------------------
        fig = px.bar(
            filtered_df.sort_values('ctr', ascending=False),
            x=filtered_df.index,
            y='ctr',
            color='performance',
            title="CTR Performance"
        )

        st.plotly_chart(fig)

        fig2 = px.scatter(
            filtered_df,
            x=spend_col,
            y='roi',
            color='performance',
            title="ROI vs Spend"
        )

        st.plotly_chart(fig2)

        # -----------------------------
        # 🔥 AI INSIGHTS (VERY POWERFUL)
        # -----------------------------
        st.subheader("Insights & Recommendations")

        avg_ctr = df['ctr'].mean()

        if avg_ctr >= 0.03:
            st.success("Excellent performance! Your campaign is highly engaging.")
        elif avg_ctr >= 0.01:
            st.info("Good performance. Consider optimizing top-performing ads.")
        elif avg_ctr >= 0.005:
            st.warning("Average performance. Improve targeting and creatives.")
        else:
            st.error("Low performance. Review your strategy and audience targeting.")

        if df['roi'].mean() < 1:
            st.warning("ROI is low. You're spending more than you're earning.")
        else:
            st.success("Campaign is profitable based on ROI.")

        # -----------------------------
        # 🔥 DATA PREVIEW
        # -----------------------------
        st.subheader("Full Dataset")
        st.dataframe(filtered_df)

    except Exception as e:
        st.error(f"Error loading file: {e}")
