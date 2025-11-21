import streamlit as st
import yfinance as yf
from textblob import TextBlob
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# Page Config
st.set_page_config(page_title="Stock Sentiment Agent", page_icon="📈", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .sentiment-positive { color: #00ff00; font-weight: bold; }
    .sentiment-negative { color: #ff0000; font-weight: bold; }
    .sentiment-neutral { color: #ffff00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def get_sentiment_color(score):
    if score > 0.1: return "green"
    elif score < -0.1: return "red"
    else: return "orange"

def get_sentiment_label(score):
    if score > 0.1: return "BULLISH 🚀"
    elif score < -0.1: return "BEARISH 📉"
    else: return "NEUTRAL 😐"

# Sidebar
with st.sidebar:
    st.title("🤖 Stock Agent")
    ticker_input = st.text_input("Enter Stock Ticker", value="TSLA").upper()
    st.markdown("---")
    st.markdown("This agent fetches real-time data and analyzes news sentiment using NLP.")

if ticker_input:
    # Fetch Data
    stock = yf.Ticker(ticker_input)
    
    try:
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        previous_close = info.get('previousClose', current_price)
        delta = current_price - previous_close
        delta_percent = (delta / previous_close) * 100 if previous_close else 0
        long_name = info.get('longName', ticker_input)
        summary = info.get('longBusinessSummary', 'No summary available.')
    except Exception as e:
        st.error(f"Error fetching data for {ticker_input}. Please check the ticker.")
        st.stop()

    # --- Header Section ---
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title(f"{long_name} ({ticker_input})")
        st.markdown(f"**{summary[:200]}...**")
    
    with col2:
        st.metric(label="Current Price", value=f"${current_price:.2f}", delta=f"{delta:.2f} ({delta_percent:.2f}%)")

    # --- Sentiment Analysis ---
    news = stock.news
    total_polarity = 0
    analyzed_news = []
    
    if news:
        for item in news:
            title = item.get('title', '')
            if not title and 'content' in item:
                 title = item['content'].get('title', '')
            
            link = item.get('link', '')
            publisher = item.get('publisher', 'Unknown')
            
            blob = TextBlob(title)
            polarity = blob.sentiment.polarity
            total_polarity += polarity
            
            analyzed_news.append({
                'title': title,
                'link': link,
                'publisher': publisher,
                'polarity': polarity
            })
        
        avg_polarity = total_polarity / len(news)
    else:
        avg_polarity = 0

    sentiment_label = get_sentiment_label(avg_polarity)
    sentiment_color = get_sentiment_color(avg_polarity)

    with col3:
        st.markdown(f"### Sentiment")
        st.markdown(f"<h2 style='color: {sentiment_color};'>{sentiment_label}</h2>", unsafe_allow_html=True)
        st.write(f"Score: {avg_polarity:.2f}")

    st.markdown("---")

    # --- Charts & News ---
    tab1, tab2 = st.tabs(["📈 Price Chart", "📰 News Analysis"])

    with tab1:
        # Fetch history for chart
        history = stock.history(period="1mo")
        if not history.empty:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=history.index,
                open=history['Open'],
                high=history['High'],
                low=history['Low'],
                close=history['Close'],
                name='Price'))
            
            fig.update_layout(title=f"{ticker_input} - 1 Month Price History", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No price history available.")

    with tab2:
        st.subheader("Recent News & Sentiment")
        for item in analyzed_news:
            p_score = item['polarity']
            p_color = get_sentiment_color(p_score)
            p_emoji = "🟢" if p_score > 0.1 else "🔴" if p_score < -0.1 else "🟡"
            
            with st.expander(f"{p_emoji} {item['title']}"):
                st.write(f"**Publisher:** {item['publisher']}")
                st.write(f"**Sentiment Score:** {p_score:.2f}")
                st.markdown(f"[Read Full Story]({item['link']})")

else:
    st.info("Enter a ticker symbol in the sidebar to start.")
