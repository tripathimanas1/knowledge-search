import streamlit as st
import requests
import sqlite3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DB_PATH = Path("data/metrics/app.db")

st.set_page_config(page_title="Knowledge Search + KPI Dashboard", layout="wide")

@st.cache_data(ttl=30)
def get_db_data(query: str, params: tuple = ()):
    """Safe database query helper with caching."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# Sidebar Navigation
st.sidebar.title("🚀 Navigation")
page = st.sidebar.radio("Select View", ["Search", "KPIs", "Evaluation", "Debug Logs"])

if page == "Search":
    st.title("🔍 Knowledge Search")
    
    with st.container():
        query = st.text_input("Query", placeholder="What are you looking for?")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            alpha = st.slider("Hybrid Alpha (0=Vector, 1=BM25)", 0.0, 1.0, 0.5)
        with col2:
            top_k = st.number_input("Top K Results", 1, 50, 10)
        with col3:
            st.write(" ") # Padding for alignment
            search_btn = st.button("Search", use_container_width=True, type="primary")

    if (search_btn or query) and query:
        try:
            resp = requests.post(f"{BACKEND_URL}/search", json={
                "query": query,
                "alpha": float(alpha),
                "top_k": int(top_k)
            })
            
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"Found {len(data['results'])} results in {data['latency_ms']:.2f}ms")
                
                for res in data["results"]:
                    with st.expander(f"📄 {res['title']} (Hybrid Score: {res['hybrid_score']:.3f})"):
                        st.write(res["text_snippet"] + "...")
                        m1, m2, m3 = st.columns(3)
                        m1.caption(f"BM25 Score: {res['bm25_score']:.2f}")
                        m2.caption(f"Vector Score: {res['vector_score']:.3f}")
                        m3.caption(f"Doc ID: {res['doc_id']}")
            else:
                st.error(f"Backend Error: {resp.text}")
        except Exception as e:
            st.error(f"Could not connect to backend at {BACKEND_URL}: {e}")

elif page == "KPIs":
    st.title("📈 Performance Metrics")
    
    df = get_db_data("SELECT * FROM query_logs")
    
    if df.empty:
        st.info("No query logs found. Run some searches to see data!")
    else:
        # Metrics Cards
        p50 = df["latency_ms"].median()
        p95 = df["latency_ms"].quantile(0.95)
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Total Requests", len(df))
        m_col2.metric("P50 Latency", f"{p50:.1f}ms")
        m_col3.metric("P95 Latency", f"{p95:.1f}ms")
        
        # Volume per Hour (Last 24h)
        st.subheader("Request Volume (Last 24h)")
        df['ts'] = pd.to_datetime(df['timestamp'])
        now = datetime.now(timezone.utc)
        last_24h = df[df['ts'] > (now - timedelta(hours=24))]
        
        if not last_24h.empty:
            vol_series = last_24h.set_index('ts').resample('H').size()
            st.bar_chart(vol_series)
        else:
            st.caption("Not enough data in the last 24 hours.")
            
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Top 10 Frequent Queries")
            top_q = df['query'].value_counts().head(10).reset_index()
            top_q.columns = ['Query', 'Count']
            st.table(top_q)
            
        with col_right:
            st.subheader("Queries with No Results")
            zeros = df[df['result_count'] == 0][['timestamp', 'query']].tail(10)
            if not zeros.empty:
                st.table(zeros)
            else:
                st.success("No zero-result searches found!")

elif page == "Evaluation":
    st.title("🧪 Model Evaluation Results")
    
    eval_csv = Path("data/metrics/experiments.csv")
    if eval_csv.exists():
        df_eval = pd.read_csv(eval_csv)
        st.dataframe(df_eval, use_container_width=True)
        
        if "ndcg_10" in df_eval.columns:
            st.subheader("nDCG@10 Trend")
            st.line_chart(df_eval["ndcg_10"])
    else:
        st.warning("No evaluation history found at `data/metrics/experiments.csv`.")

elif page == "Debug Logs":
    st.title("🛠️ System Logs")
    
    col_a, col_b = st.columns(2)
    start_date = col_a.date_input("Filter by Date", datetime.now() - timedelta(days=7))
    show_errors_only = col_b.checkbox("Only show entries with errors", value=False)
    
    sql = "SELECT timestamp, query, latency_ms, result_count, error FROM query_logs WHERE 1=1"
    if show_errors_only:
        sql += " AND error IS NOT NULL"
    sql += " ORDER BY timestamp DESC"
    
    df_logs = get_db_data(sql)
    
    if not df_logs.empty:
        df_logs['date'] = pd.to_datetime(df_logs['timestamp']).dt.date
        filtered_df = df_logs[df_logs['date'] >= start_date]
        st.dataframe(filtered_df.drop(columns=['date']), use_container_width=True)
    else:
        st.info("No logs match the current filters.")
