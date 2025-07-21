"""
Multi-Agent Sentiment Watchdog Dashboard
Real-time visualization of customer sentiment data using Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import os
import json
from firebase_admin import firestore, credentials
import firebase_admin
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

# Load environment variables early
load_dotenv()

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="Customer Sentiment Watchdog",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper: Firebase Initialization ---
@st.cache_resource
def get_firestore_client():
    try:
        firebase_admin.get_app()
    except ValueError:
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                st.error("Firebase credentials not found.")
                st.stop()
    return firestore.client()

# --- Helper: Retrieve App ID ---
def get_app_id():
    with st.sidebar:
        st.title("🎯 Sentiment Watchdog")
        env_appid = os.getenv('APP_ID', 'default')
        app_id = st.text_input(
            "App ID", 
            value=env_appid,
            help="Enter your application ID (must exactly match agents and processing)"
        )
        st.caption(f"Current environment: `{env_appid}`")
    return app_id

# --- Helper: Load Ticket Data ---
@st.cache_data(ttl=30)
def load_tickets_data(app_id):
    try:
        db = get_firestore_client()
        tickets_ref = db.collection(f'artifacts/{app_id}/public/data/raw_tickets')
        docs = tickets_ref.where('status', '==', 'processed').get()
        tickets_data = []
        for doc in docs:
            data = doc.to_dict()
            # Robust timestamp conversion
            if 'timestamp' in data and data['timestamp']:
                ts = data['timestamp']
                if hasattr(ts, "seconds"):
                    data['timestamp'] = datetime.fromtimestamp(ts.seconds)
                else:
                    data['timestamp'] = pd.to_datetime(ts)
            else:
                data['timestamp'] = pd.NaT
            data['id'] = doc.id
            tickets_data.append(data)
        df = pd.DataFrame(tickets_data)
        # Defensive: fill missing columns so downstream code is robust
        for col in ['sentiment', 'source', 'sender', 'summary', 'confidence']:
            if col not in df.columns:
                df[col] = None
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# --- Helper: Get System Stats ---
@st.cache_data(ttl=60)
def get_system_stats(app_id):
    try:
        db = get_firestore_client()
        tickets_ref = db.collection(f'artifacts/{app_id}/public/data/raw_tickets')
        docs = tickets_ref.get()
        stats = dict.fromkeys(['total', 'processed', 'new', 'processing', 'error'], 0)
        for doc in docs:
            status = doc.to_dict().get('status', 'unknown')
            if status in stats:
                stats[status] += 1
            stats['total'] += 1
        return stats
    except Exception as e:
        st.error(f"Error loading system stats: {e}")
        return dict.fromkeys(['total', 'processed', 'new', 'processing', 'error'], 0)

# --- Sidebar: Controls ---
def render_sidebar():
    st.markdown("---")
    st.subheader("🔧 Controls")
    time_range = st.selectbox(
        "Time Range",
        ["Last 24 hours", "Last 3 days", "Last week", "Last month"],
        index=2
    )
    sentiment_filter = st.multiselect(
        "Filter by Sentiment",
        ["anger", "confusion", "delight", "neutral"],
        default=["anger", "confusion", "delight", "neutral"]
    )
    source_filter = st.multiselect(
        "Filter by Source",
        ["Email", "Form_Contact", "Form_Feedback", "Form_Support", "Form_Custom"],
        default=["Email", "Form_Contact", "Form_Feedback", "Form_Support", "Form_Custom"]
    )
    return time_range, sentiment_filter, source_filter

# --- Filters ---
def apply_filters(df, time_range, sentiment_filter, source_filter):
    if df.empty:
        return df

    now = datetime.now(timezone.utc)  # this line is key

    if time_range == "Last 24 hours":
        cutoff = now - timedelta(hours=24)
    elif time_range == "Last 3 days":
        cutoff = now - timedelta(days=3)
    elif time_range == "Last week":
        cutoff = now - timedelta(days=7)
    else:
        cutoff = now - timedelta(days=30)

    df = df[df['timestamp'] >= cutoff]
    df = df[df['timestamp'] >= cutoff]
    if sentiment_filter:
        df = df[df['sentiment'].isin(sentiment_filter)]
    if source_filter and 'source' in df.columns:
        df = df[df['source'].isin(source_filter)]
    return df

# --- Main Rendering Functions ---
def render_header():
    st.title("🎯 Customer Sentiment Watchdog Dashboard")
    st.markdown("Real-time monitoring of customer sentiment across support channels")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        interval = st.selectbox(
            "Auto-refresh interval",
            [30, 60, 120, 300], index=1,
            format_func=lambda x: f"{x} seconds"
        )
    with col2:
        manual_refresh = st.button("🔄 Refresh Now")
    with col3:
        auto_refresh = st.checkbox("Auto-refresh", value=True)
    if auto_refresh:
        st_autorefresh(interval=interval * 1000, key="dashboard_refresh")
    if manual_refresh:
        st.rerun()

def render_system_overview(stats):
    st.subheader("📊 System Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tickets", stats['total'])
    col2.metric("Processed", stats['processed'])
    col3.metric("Pending", stats['new'])
    col4.metric("Processing", stats['processing'])
    col5.metric("Errors", stats['error'])

def render_sentiment_overview(df):
    if df.empty:
        st.warning("No sentiment data available")
        return
    st.subheader("😊 Sentiment Analysis Overview")
    sentiment_counts = df['sentiment'].value_counts()
    col1, col2, col3, col4 = st.columns(4)
    colors = {'anger': '#ff4444', 'confusion': '#ff8800', 'delight': '#44ff44', 'neutral': '#888888'}
    for sentiment, col in zip(['anger', 'confusion', 'delight', 'neutral'], [col1, col2, col3, col4]):
        count = sentiment_counts.get(sentiment, 0)
        pct = (count / len(df) * 100) if len(df) > 0 else 0
        col.metric(sentiment.title(), count, f"{pct:.1f}%")

def render_sentiment_trends(df):
    if df.empty:
        return
    st.subheader("📈 Sentiment Trends Over Time")
    df['date'] = df['timestamp'].dt.date
    daily = df.groupby(['date', 'sentiment']).size().unstack(fill_value=0)
    fig = go.Figure()
    colors = {'anger': '#ff4444', 'confusion': '#ff8800', 'delight': '#44ff44', 'neutral': '#888888'}
    for sentiment in daily.columns:
        fig.add_trace(go.Scatter(
            x=daily.index, y=daily[sentiment],
            mode='lines+markers', name=sentiment.title(),
            line=dict(color=colors.get(sentiment, '#888888')), marker=dict(size=6)
        ))
    fig.update_layout(
        title="Daily Sentiment Counts",
        xaxis_title="Date",
        yaxis_title="Number of Tickets",
        hovermode='x unified',
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

def render_alerts_section(df):
    if df.empty:
        return
    st.subheader("🚨 Alerts & High Priority Issues")
    window = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_anger = df[(df['sentiment'] == 'anger') & (df['timestamp'] >= window)].sort_values('timestamp', ascending=False)
    recent_total = len(df[df['timestamp'] >= window])
    anger_ratio = len(recent_anger) / recent_total if recent_total > 0 else 0
    if anger_ratio >= 0.3:
        st.error(f"🚨 **HIGH ANGER ALERT!** {anger_ratio:.1%} of recent messages show anger sentiment")
    elif anger_ratio >= 0.2:
        st.warning(f"⚠️ **Elevated anger levels:** {anger_ratio:.1%} of recent messages show anger sentiment")
    else:
        st.success(f"✅ Sentiment levels are stable ({anger_ratio:.1%} anger)")
    if not recent_anger.empty:
        st.markdown("**Recent Angry Messages:**")
        for _, message in recent_anger.head(5).iterrows():
            with st.expander(f"From {message.get('sender', 'Unknown')} - {message['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(f"**Source:** {message.get('source', 'Unknown')}")
                st.write(f"**Summary:** {message.get('summary', 'No summary')}")
                st.write(f"**Confidence:** {message.get('confidence', 0):.2f}")
                if isinstance(message.get('keywords'), (list, tuple)):
                    st.write(f"**Keywords:** {', '.join(message['keywords'])}")
                st.write(f"**Message:** {message.get('message', '')[:200]}...")

def render_detailed_analysis(df):
    if df.empty:
        return
    st.subheader("🔍 Detailed Analysis")
    col1, col2 = st.columns(2)
    # Pie chart
    sentiment_counts = df['sentiment'].value_counts()
    with col1:
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="Sentiment Distribution",
            color=sentiment_counts.index,
            color_discrete_map={'anger': '#ff4444', 'confusion': '#ff8800', 'delight': '#44ff44', 'neutral': '#888888'}
        )
        st.plotly_chart(fig, use_container_width=True)
    # Bar chart by source
    with col2:
        if 'source' in df.columns:
            source_counts = df['source'].value_counts()
            fig = px.bar(
                x=source_counts.index,
                y=source_counts.values,
                title="Messages by Source",
                labels={'x': 'Source', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)

def render_recent_messages(df):
    if df.empty:
        return
    st.subheader("📝 Recent Messages")
    rec = df.sort_values('timestamp', ascending=False).head(20)
    display = rec[['timestamp', 'source', 'sender', 'sentiment', 'summary', 'confidence']].copy()
    display['timestamp'] = display['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    display['confidence'] = display['confidence'].round(2)
    st.dataframe(display, use_container_width=True)

# --- Main app ---
def main():
    app_id = get_app_id()
    # Show the app_id for quick verification
    st.info(f"**Current App ID:** `{app_id}`")
    render_header()
    time_range, sentiment_filter, source_filter = render_sidebar()
    with st.spinner("Loading data..."):
        tickets_df = load_tickets_data(app_id)
        system_stats = get_system_stats(app_id)
    # Debug print: see what is actually loaded
    st.write("Loaded tickets (raw):", tickets_df)
    filtered_df = apply_filters(tickets_df, time_range, sentiment_filter, source_filter)
    render_system_overview(system_stats)
    st.markdown("---")
    if not filtered_df.empty:
        render_sentiment_overview(filtered_df)
        st.markdown("---")
        render_sentiment_trends(filtered_df)
        st.markdown("---")
        render_alerts_section(filtered_df)
        st.markdown("---")
        render_detailed_analysis(filtered_df)
        st.markdown("---")
        render_recent_messages(filtered_df)
    else:
        st.info("No data available for the selected filters. Check your agent configuration and ensure tickets are being processed.")
    # Footer
    st.markdown("---")
    st.markdown("*Dashboard last updated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*")

if __name__ == "__main__":
    main()
