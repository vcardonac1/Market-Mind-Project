# --------------------------------------
# IMPORTS
# --------------------------------------
import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
#import pmdarima as pm
from statsmodels.tsa.arima.model import ARIMA
from datetime import timedelta
import base64
import numpy as np
import pandas as pd
from prophet import Prophet
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------
# PAGE CONFIGURATION
# --------------------------------------
st.set_page_config(page_title="MarketMind", layout="wide")
dark_mode = st.sidebar.toggle("Toggle Dark Mode") # Functionality does not work, but we think the idea is cool
plotly_theme = "plotly_dark" if dark_mode else "plotly_white"

# --------------------------------------
# BACKGROUND OVERLAY
# --------------------------------------
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

bg_image = get_base64_image("background.png")
st.markdown(
    f"""
    <style>
        .stApp {{
            background: linear-gradient(
                rgba(255, 255, 255, 0.9), 
                rgba(255, 255, 255, 0.9)
            ),
            url("data:image/png;base64,{bg_image}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            background-repeat: no-repeat;
        }}

        .main {{
            background-color: rgba(255, 255, 255, 0.88);
            border-radius: 10px;
            padding: 2rem;
            box-shadow: 0 4px 30px rgba(0,0,0,0.1);
            backdrop-filter: blur(6px);
        }}

        .block-container {{
            padding-top: 1rem;
        }}
    </style>
    """,
    unsafe_allow_html=True)

# --------------------------------------
# LOAD DATA FROM S3
# --------------------------------------
def load_parquet_from_url(url):
    response = requests.get(url, verify=False, stream=True)
    response.raise_for_status()
    return pd.read_parquet(io.BytesIO(response.content), engine="pyarrow")

STOCKS_URL = "https://market-mind-project.s3.us-east-1.amazonaws.com/processed_data/stocks/final_stocks_data.parquet"
CRYPTO_URL = "https://market-mind-project.s3.us-east-1.amazonaws.com/processed_data/crypto/final_crypto_data.parquet"
ECONOMIC_URL = "https://market-mind-project.s3.us-east-1.amazonaws.com/processed_data/economic_indicators/final_economic_indicators.parquet"
GAINERS_URL = "https://market-mind-project.s3.us-east-1.amazonaws.com/processed_data/top_gainers/final_top_gainers.parquet"

# --------------------------------------
# CLEANING DATA
# --------------------------------------

# Stock Data Cleaning
df = load_parquet_from_url(STOCKS_URL)
df["date"] = pd.to_datetime(df["date"])
df[["close", "open", "high", "low", "volume"]] = df[["close", "open", "high", "low", "volume"]].apply(pd.to_numeric, errors="coerce")
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["year_month"] = df["date"].dt.to_period("M").dt.to_timestamp()
df = df.sort_values("date")

# Crypto Data Cleaning
crypto_df = load_parquet_from_url(CRYPTO_URL)
crypto_df["date"] = pd.to_datetime(crypto_df["date"])
crypto_df[["close", "open", "high", "low", "volume"]] = crypto_df[["close", "open", "high", "low", "volume"]].apply(pd.to_numeric, errors="coerce")
crypto_df = crypto_df.sort_values("date")

# Economic Indicator Data Cleaning
econ_df = load_parquet_from_url(ECONOMIC_URL)
econ_df["date"] = pd.to_datetime(econ_df["date"])
econ_df["year"] = econ_df["date"].dt.year
econ_df["month"] = econ_df["date"].dt.month
econ_df["month_name"] = econ_df["date"].dt.strftime("%b")
econ_df["value"] = pd.to_numeric(econ_df["value"], errors="coerce")
month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
econ_df["month_name"] = pd.Categorical(econ_df["month_name"], categories=month_order, ordered=True)

# --------------------------------------
# TITLE AND TABS
# --------------------------------------
st.title("\"MarketMind\": Finance for Everyone")
tabs = st.tabs(["STOCKS", "CRYPTOCURRENCY", "ECONOMIC INDICATORS", "TOP GAINERS", "ML-POWERED PREDICTIVE INSIGHTS"])

# --------------------------------------
# STOCKS TAB
# --------------------------------------
with tabs[0]:
    with st.container():
        st.markdown("""
        <div style='background-color: #e3f2fd; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); border: 1px solid #90caf9;'>
            <h3 style='margin-bottom: 10px;'>Stocks Tab Overview</h3>
            <p style='font-size: 16px;'>
                The stock market is a key reflection of investor sentiment and economic trends. Monitoring the movement of top stocks across various time periods provides valuable insight into sectors driving growth, market volatility, and price momentum.
            </p>
            <p style='font-size: 16px;'>
                This tab highlights the top 10 most actively traded stocks today. It shows associated price changes, daily percentage movement, and 7-day sparkline trends. You can also explore historical charts and compare open and close trends over customizable time ranges. 
                Happy exploring!
            </p>
        </div>
        <br />
        <div style='background-color: #fce4ec; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); border: 1px solid #f48fb1;'>
            <h3 style='margin-bottom: 10px;'>Overview of the Top 10 Stocks Shown</h3>
            <p style='font-size: 16px;'>
                The top 10 stocks displayed in this tab are the 10 largest publicly traded companies in the world and have the highest current trading volume. They include:
            </p>
            <ul style='font-size: 16px;'>
                <li><b>Tech Giants:</b> Apple (AAPL), Microsoft (MSFT), Alphabet (GOOGL), Meta Platforms (META), and NVIDIA (NVDA) — leaders in AI, cloud computing, and digital platforms.</li>
                <li><b>Consumer Leaders:</b> Amazon (AMZN) and Tesla (TSLA), dominating sectors like e-commerce and electric vehicles.</li>
                <li><b>Finance & Conglomerates:</b> JPMorgan Chase (JPM), Visa (V), and Berkshire Hathaway (BRK.B), representing major players in finance, payments, and diversified holdings.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.header("Top Stocks Snapshot")
    latest_date = df["date"].max()
    prev_date = df[df["date"] < latest_date]["date"].max()
    latest_snapshot = df[df["date"] == latest_date]
    top_stocks = latest_snapshot["stock"].value_counts().nlargest(10).index.tolist()

    prev_snapshot = df[df["date"] == prev_date]
    snapshot_top = latest_snapshot[latest_snapshot["stock"].isin(top_stocks)]
    prev_snapshot_top = prev_snapshot[prev_snapshot["stock"].isin(top_stocks)]

    change_df = pd.merge(snapshot_top, prev_snapshot_top, on="stock", suffixes=("_curr", "_prev"))
    change_df["pct_change"] = ((change_df["close_curr"] - change_df["close_prev"]) / change_df["close_prev"]) * 100
    change_df["arrow"] = change_df["pct_change"].apply(lambda x: "▲" if x > 0 else "▼")
    change_df["color"] = change_df["pct_change"].apply(lambda x: "green" if x > 0 else "red")

    col_labels = st.columns([1.6, 1.2, 1.2, 1.3, 1.3, 1.5])
    col_labels[0].markdown("**Stock**")
    col_labels[1].markdown("**Symbol**")
    #col_labels[2].markdown("**Latest Closing Price**")
    col_labels[2].markdown("**Today's Open Price**")  
    col_labels[3].markdown("**% Change**")            
    col_labels[4].markdown("**7-Day Trend**")

    for _, row in change_df.iterrows():
        spark_data = df[(df["stock"] == row["stock"]) & (df["date"] >= latest_date - pd.Timedelta(days=7))]
        spark_fig = go.Figure()
        spark_fig.add_trace(go.Scatter(
            x=spark_data["date"],
            y=spark_data["close"],
            mode="lines",
            line=dict(color=row["color"], width=2),
            hoverinfo="skip",
            showlegend=False))

        spark_fig.update_layout(
            height=50,
            width=250,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)")

        cols = st.columns([1.6, 1.2, 1.2, 1.3, 1.3, 1.5])
        cols[0].markdown(f"**{row['stock']}**")
        cols[1].markdown(f"`{row['symbol_curr']}`")
        cols[2].markdown(f"**${row['open_curr']:.2f}**")
        cols[3].markdown(
            f"<span style='color:{row['color']}; font-weight:bold;'>{row['arrow']} {row['pct_change']:.2f}%</span>",
            unsafe_allow_html=True)
        
        #cols[2].markdown(f"**${row['close_curr']:.2f}**")
        #cols[3].markdown(f"**${row['open_curr']:.2f}**")
        #cols[4].markdown(
        #    f"<span style='color:{row['color']}; font-weight:bold;'>{row['arrow']} {row['pct_change']:.2f}%</span>",
        #    unsafe_allow_html=True)
        
        with cols[4]:
            st.plotly_chart(spark_fig, use_container_width=True)

    # Historical Trends Viewer
    st.header("Top Stocks Historical Trends Viewer")
    selected_stock = st.selectbox("Choose a stock to visualize:", top_stocks)
    time_range_map = {"5D": 5, "1M": 30, "6M": 182, "YTD": 90, "1Y": 365, "5Y": 1825}
    selected_range_label = st.radio("Select Time Range:", list(time_range_map.keys()), horizontal=True)
    selected_days = time_range_map[selected_range_label]

    stock_df = df[df["stock"] == selected_stock]
    filtered_stock = stock_df[stock_df["date"] > latest_date - pd.Timedelta(days=selected_days)]
    color = "green" if len(filtered_stock) > 1 and filtered_stock["close"].iloc[-1] >= filtered_stock["close"].iloc[0] else "gray"

    fig_yahoo = go.Figure()
    fig_yahoo.add_trace(go.Scatter(
        x=filtered_stock["date"],
        y=filtered_stock["close"],
        mode="lines",
        line=dict(color=color, width=2),
        customdata=filtered_stock[["open", "high", "low", "volume"]],
        hovertemplate="<b>Date</b>: %{x|%Y-%m-%d %I:%M %p}<br>" +
                      "<b>Close</b>: %{y:.2f}<br>" +
                      "<b>Open</b>: %{customdata[0]:.2f}<br>" +
                      "<b>High</b>: %{customdata[1]:.2f}<br>" +
                      "<b>Low</b>: %{customdata[2]:.2f}<br>" +
                      "<b>Volume</b>: %{customdata[3]:,.0f}<extra></extra>"))
    fig_yahoo.update_layout(
        title=f"{selected_stock} Price Chart ({selected_range_label})",
        xaxis_title="Date",
        yaxis_title="Close Price",
        template="plotly_white",
        hovermode="x unified",
        height=400)
    st.plotly_chart(fig_yahoo, use_container_width=True)

    # Open & Close Trends Visual
    st.header("Open & Close Price Trends for Top Stocks")
    filter_days = st.radio("Select Time Range:", [7, 30], horizontal=True)
    filtered_df = df[df["date"] > latest_date - pd.Timedelta(days=filter_days)]
    filtered_df = filtered_df[filtered_df["stock"].isin(top_stocks)]

    selected_stocks = st.multiselect(
        "Select up to 3 Stocks to Compare:",
        sorted(top_stocks),
        default=[sorted(top_stocks)[0]],
        key="stock_compare_daily")

    if len(selected_stocks) == 0:
        st.warning("Please select at least one stock.")
    elif len(selected_stocks) > 3:
        st.warning("You can compare up to 3 stocks only.")
    else:
        fig = go.Figure()
        for stock in selected_stocks:
            stock_data = filtered_df[filtered_df["stock"] == stock]

            fig.add_trace(go.Scatter(
                x=stock_data["date"],
                y=stock_data["open"],
                mode="lines+markers",
                name=f"{stock} - Open",
                line=dict(dash="solid"),
                hovertemplate=(
                    f"<b>Stock:</b> {stock}<br>" +
                    "<b>Type:</b> Open<br>" +
                    "<b>Date:</b> %{x|%b %d, %Y}<br>" +
                    "<b>Open Price:</b> $%{y:.2f}<extra></extra>")))

            fig.add_trace(go.Scatter(
                x=stock_data["date"],
                y=stock_data["close"],
                mode="lines+markers",
                name=f"{stock} - Close",
                line=dict(dash="dash"),
                hovertemplate=(
                    f"<b>Stock:</b> {stock}<br>" +
                    "<b>Type:</b> Close<br>" +
                    "<b>Date:</b> %{x|%b %d, %Y}<br>" +
                    "<b>Close Price:</b> $%{y:.2f}<extra></extra>")))

        fig.update_layout(
            template="plotly_white",
            title=f"Open vs Close Prices (Last {filter_days} Days)",
            xaxis_title="Date",
            yaxis_title="Price",
            legend_title="Stock - Price Type")
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------
# CRYPTO TAB
# --------------------------------------
with tabs[1]:
    with st.container():
        st.markdown("""
        <div style='background-color: #e0f7fa; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); border: 1px solid #4fc3f7;'>
            <h3 style='margin-bottom: 10px;'>What is Cryptocurrency and Why Does it Matter?</h3>
            <p style='font-size: 16px;'>
                Cryptocurrencies are decentralized digital assets that operate on blockchain technology. They allow peer-to-peer transactions without intermediaries like banks and have become a major part of the global financial ecosystem.
            </p>
            <p style='font-size: 16px;'>
                This tab highlights the top 10 most actively moving cryptocurrencies by showing daily changes, short-term trends, and historical patterns. Understanding cryptocurrency price behavior can be useful for both investors and analysts interested in market momentum. Happy exploring!
            </p>
        </div>
        <br />
        <div style='background-color: #f3e5f5; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); border: 1px solid #ce93d8;'>
            <h3 style='margin-bottom: 10px;'>Overview of the Top 10 Cryptocurrencies Shown</h3>
            <p style='font-size: 16px;'>
                The top 10 cryptocurrencies displayed in this tab are the 10 most active cryptocurrencies based on recent volume and closing activity. They include:
            </p>
            <ul style='font-size: 16px;'>
                <li><b>Bitcoin (BTC):</b> The first and most well-known cryptocurrency, seen as digital gold.</li>
                <li><b>Ethereum (ETH):</b> A smart contract platform that powers decentralized apps.</li>
                <li><b>Stablecoins & Payment Tokens:</b> Includes Tether (USDT), widely used for trading and liquidity, and XRP, focused on cross-border payments.</li>
                <li><b>Altcoin Leaders:</b> Solana (SOL), Cardano (ADA), and Polkadot (DOT) offer fast, scalable blockchain infrastructure with strong developer activity.</li>
                <li><b>Legacy & Meme Coins:</b> Litecoin (LTC) as one of the earliest Bitcoin forks, and Dogecoin (DOGE) as a popular meme coin with community backing.</li>
                <li><b>Bitcoin Forks:</b> Bitcoin Cash (BCH), offering a different approach to peer-to-peer digital cash with larger block sizes.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.header("Today's Top Cryptocurrencies Snapshot")
    latest_crypto_date = crypto_df["date"].max()
    prev_crypto_date = crypto_df[crypto_df["date"] < latest_crypto_date]["date"].max()
    latest_crypto_snapshot = crypto_df[crypto_df["date"] == latest_crypto_date]
    prev_crypto_snapshot = crypto_df[crypto_df["date"] == prev_crypto_date]
    top_cryptos_df = latest_crypto_snapshot["symbol"].value_counts().nlargest(10).reset_index()
    top_cryptos_df.columns = ["symbol", "count"]
    top_cryptos_info = pd.merge(top_cryptos_df, latest_crypto_snapshot[["symbol", "crypto"]].drop_duplicates(), on="symbol")
    top_cryptos = top_cryptos_info["crypto"].tolist()

    prev_snapshot_top = prev_crypto_snapshot[prev_crypto_snapshot["symbol"].isin(top_cryptos_info["symbol"])]
    snapshot_top = latest_crypto_snapshot[latest_crypto_snapshot["symbol"].isin(top_cryptos_info["symbol"])]

    change_df = pd.merge(snapshot_top, prev_snapshot_top, on="symbol", suffixes=('_curr', '_prev'))
    change_df["pct_change"] = ((change_df["close_curr"] - change_df["close_prev"]) / change_df["close_prev"]) * 100
    change_df["arrow"] = change_df["pct_change"].apply(lambda x: "▲" if x > 0 else "▼")
    change_df["color"] = change_df["pct_change"].apply(lambda x: "green" if x > 0 else "red")

    col_labels = st.columns([1.6, 1.2, 1.2, 1.3, 1.3, 1.5])
    col_labels[0].markdown("**Cryptocurrency**")
    col_labels[1].markdown("**Symbol**")
    #col_labels[2].markdown("**Latest Closing Price**")
    col_labels[2].markdown("**Today's Open Price**")  
    col_labels[3].markdown("**% Change**")         
    col_labels[4].markdown("**7-Day Trend**")

    for _, row in change_df.iterrows():
        spark_data = crypto_df[(crypto_df["symbol"] == row["symbol"]) & (crypto_df["date"] >= latest_crypto_date - pd.Timedelta(days=7))]

        spark_fig = go.Figure()
        spark_fig.add_trace(go.Scatter(
            x=spark_data["date"],
            y=spark_data["close"],
            mode="lines",
            line=dict(color=row["color"], width=2),
            hoverinfo="skip",
            showlegend=False))

        spark_fig.update_layout(
            height=50,
            width=250,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)")

        cols = st.columns([1.6, 1.2, 1.2, 1.3, 1.3, 1.5])
        cols[0].markdown(f"**{row['crypto_curr']}**")
        cols[1].markdown(f"`{row['symbol']}`")
        #cols[2].markdown(f"**${row['close_curr']:.2f}**")
        cols[2].markdown(f"**${row['open_curr']:.2f}**") 
        cols[3].markdown(
            f"<span style='color:{row['color']}; font-weight:bold;'>{row['arrow']} {row['pct_change']:.2f}%</span>",
            unsafe_allow_html=True)                     
        with cols[4]:
            st.plotly_chart(spark_fig, use_container_width=True)

    st.header("Top Cryptocurrencies Historical Trends Viewer")
    crypto_name_to_symbol = dict(zip(latest_crypto_snapshot["crypto"], latest_crypto_snapshot["symbol"]))
    selected_crypto_name = st.selectbox("Choose a cryptocurrency to visualize:", top_cryptos, key="crypto_select")
    selected_crypto = crypto_name_to_symbol[selected_crypto_name]
    time_range_map_crypto = {"5D": 5, "1M": 30, "6M": 182, "YTD": 90, "1Y": 365, "5Y": 1825}
    selected_range_label_crypto = st.radio("Select Time Range:", list(time_range_map_crypto.keys()), horizontal=True, key="crypto_range")
    selected_days_crypto = time_range_map_crypto[selected_range_label_crypto]
    crypto_selected_df = crypto_df[crypto_df["symbol"] == selected_crypto]
    filtered_crypto = crypto_selected_df[crypto_selected_df["date"] > latest_crypto_date - pd.Timedelta(days=selected_days_crypto)]
    color_crypto = "green" if len(filtered_crypto) > 1 and filtered_crypto["close"].iloc[-1] >= filtered_crypto["close"].iloc[0] else "gray"

    fig_crypto = go.Figure()
    fig_crypto.add_trace(go.Scatter(
        x=filtered_crypto["date"],
        y=filtered_crypto["close"],
        mode="lines",
        line=dict(color=color_crypto, width=2),
        customdata=filtered_crypto[["open", "high", "low", "volume"]],
        hovertemplate="<b>Date</b>: %{x|%Y-%m-%d %I:%M %p}<br>" +
                      "<b>Close</b>: %{y:.2f}<br>" +
                      "<b>Open</b>: %{customdata[0]:.2f}<br>" +
                      "<b>High</b>: %{customdata[1]:.2f}<br>" +
                      "<b>Low</b>: %{customdata[2]:.2f}<br>" +
                      "<b>Volume</b>: %{customdata[3]:,.0f}<extra></extra>"))
    fig_crypto.update_layout(
        title=f"{selected_crypto_name} Price Chart ({selected_range_label_crypto})",
        xaxis_title="Date",
        yaxis_title="Close Price",
        template=plotly_theme,
        hovermode="x unified",
        height=400)
    st.plotly_chart(fig_crypto, use_container_width=True)

    st.header("Open & Close Price Trends for Top Cryptocurrencies")
    filter_crypto_days = st.radio("Select Time Range:", [7, 30], horizontal=True, key="crypto_trend_range")
    filtered_crypto_df = crypto_df[crypto_df["date"] > latest_crypto_date - pd.Timedelta(days=filter_crypto_days)]
    filtered_crypto_df = filtered_crypto_df[filtered_crypto_df["symbol"].isin(top_cryptos_info["symbol"])]

    crypto_names_sorted = sorted(top_cryptos)
    selected_cryptos = st.multiselect("Select up to 3 Cryptos to Compare:", crypto_names_sorted, default=[crypto_names_sorted[0]], key="crypto_multi")

    if len(selected_cryptos) == 0:
        st.warning("Please select at least one crypto.")
    elif len(selected_cryptos) > 3:
        st.warning("You can compare up to 3 cryptos only.")
    else:
        fig_crypto_trends = go.Figure()
        for crypto_name in selected_cryptos:
            symbol = crypto_name_to_symbol[crypto_name]
            crypto_data = filtered_crypto_df[filtered_crypto_df["symbol"] == symbol]

            fig_crypto_trends.add_trace(go.Scatter(
                x=crypto_data["date"],
                y=crypto_data["open"],
                mode="lines+markers",
                name=f"{crypto_name} - Open",
                line=dict(dash="solid"),
                hovertemplate=(
                    f"<b>Crypto:</b> {crypto_name}<br>" +
                    "<b>Type:</b> Open<br>" +
                    "<b>Date:</b> %{x|%b %d, %Y}<br>" +
                    "<b>Open Price:</b> $%{y:.2f}<extra></extra>")))

            fig_crypto_trends.add_trace(go.Scatter(
                x=crypto_data["date"],
                y=crypto_data["close"],
                mode="lines+markers",
                name=f"{crypto_name} - Close",
                line=dict(dash="dash"),
                hovertemplate=(
                    f"<b>Crypto:</b> {crypto_name}<br>" +
                    "<b>Type:</b> Close<br>" +
                    "<b>Date:</b> %{x|%b %d, %Y}<br>" +
                    "<b>Close Price:</b> $%{y:.2f}<extra></extra>")))

        fig_crypto_trends.update_layout(
            template=plotly_theme,
            title=f"Open vs Close Prices (Last {filter_crypto_days} Days)",
            xaxis_title="Date",
            yaxis_title="Price",
            legend_title="Crypto - Price Type")
        st.plotly_chart(fig_crypto_trends, use_container_width=True)

# --------------------------------------
# ECONOMIC INDICATORS TAB
# --------------------------------------
with tabs[2]:
    with st.container():
        st.markdown("""
        <div style='background-color: #e1f5fe; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); border: 1px solid #81d4fa;'>
            <h3 style='margin-bottom: 10px;'>Understanding Economic Indicators</h3>
            <p style='font-size: 16px;'>
                Economic indicators are key statistics that are used to evaluate the health and direction of an economy. The indicators available for viewing in this tab include:
            </p>
            <ul style='font-size: 16px;'>
                <li><b>Consumer Price Index (CPI):</b> Measures changes in the price level of a basket of goods and services. CPI is a key gauge of inflation.</li>
                <li><b>Treasury Yield:</b> Reflects the return on government bonds and is typically used as a benchmark for interest rates and investor confidence.</li>
                <li><b>Federal Funds Rate:</b> The interest rate at which banks lend to each other. This indicator influences borrowing costs, investment, and inflation control.</li>
            </ul>
            <p style='font-size: 16px;'>
                This tab offers you two visualizations to explore:
                <ul>
                    <li><b>Year-over-Year Comparison Viewer:</b> See how a selected indicator changes across months in different years.</li>
                    <li><b>Rolling Averages Viewer:</b> Track smoothed trends over time using a moving average.</li>
                </ul>
        </div>
        """, unsafe_allow_html=True)

    # Visual 1 - YoY Indicator Comparison
    st.subheader("Year-over-Year Economic Indicator Comparison Viewer")
    selected_indicator_yoy = st.selectbox("Select Indicator:", sorted(econ_df["indicator"].unique()))
    years_yoy = st.multiselect("Select Years:", sorted(econ_df["year"].unique()), default=[2023, 2024])

    if years_yoy and selected_indicator_yoy:
        df_yoy = econ_df[
            (econ_df["indicator"] == selected_indicator_yoy) &
            (econ_df["year"].isin(years_yoy))].copy()
        df_yoy["legend"] = df_yoy["year"].astype(str)

        fig_yoy = px.line(
            df_yoy,
            x="month_name",
            y="value",
            color="legend",
            markers=True,
            title=f"Year-over-Year Monthly Comparison: {selected_indicator_yoy}",
            template=plotly_theme)
        fig_yoy.update_layout(
            xaxis_title="Month",
            yaxis_title="Value",
            legend_title_text="Year")
        fig_yoy.update_traces(
            hovertemplate="<b>Month:</b> %{x}<br><b>Value:</b> %{y:.2f}<extra></extra>")
        st.plotly_chart(fig_yoy, use_container_width=True)

    # Visual 2 - Rolling Indicator Averages
    st.subheader("Year-over-Year Rolling Averages for Indicators")
    selected_rolling_indicators = st.multiselect("Select indicators:", econ_df["indicator"].unique(), default=["Federal Funds Rate"])

    if selected_rolling_indicators:
        roll_df = econ_df[econ_df["indicator"].isin(selected_rolling_indicators)].sort_values("date")
        roll_df["rolling_avg"] = roll_df.groupby("indicator")["value"].transform(lambda x: x.rolling(window=3).mean())
        fig_roll = px.line(
            roll_df,
            x="date",
            y="rolling_avg",
            color="indicator",
            title="Rolling Averages by Indicator",
            template=plotly_theme)
        
        fig_roll.update_traces(hovertemplate="<b>Date</b>: %{x|%Y-%m-%d}<br><b>Value</b>: %{y:.2f}<extra></extra>")
        fig_roll.update_layout(
            xaxis_title="Year",
            yaxis_title="Monthly Average Value",
            legend_title_text="Indicator")
        st.plotly_chart(fig_roll, use_container_width=True)

# --------------------------------------
# TOP GAINERS TAB
# --------------------------------------
with tabs[3]:
    with st.container():
        st.markdown("""
        <div style='background-color: #f3e5f5; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #90caf9;'>
            <h3 style='margin-bottom: 10px;'>Wondering About Top Gainers?</h3>
            <p style='font-size: 16px;'>
                Top Gainers refers to stocks or assets that have demonstrated the highest positive change in price within a given time frame; in our case, the last trading day. These are often indicators of momentum, investor interest, or recent news/events impacting valuation.
            </p>
            <p style='font-size: 16px;'>
                In this tab, you can explore the top 10 gainers based on change in dollar amount and percentage from the previous day. The snapshot includes the price, absolute change, and percentage gain, along with a visual summary of performance trends. Happy exploring!
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.header("Top Gainers Snapshot")
    gainers_df = load_parquet_from_url(GAINERS_URL)

    numeric_cols = ["price", "change_amount", "change_percentage", "volume"]
    if gainers_df["change_percentage"].dtype == object:
        gainers_df["change_percentage"] = gainers_df["change_percentage"].str.replace('%', '', regex=False)
    gainers_df[numeric_cols] = gainers_df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    gainers_df.dropna(subset=numeric_cols, inplace=True)

    if gainers_df.empty:
        st.error("No valid data found for Top Gainers.")
    else:
        gainers_df["change_percentage_display"] = gainers_df["change_percentage"].map(lambda x: f"{x:.2f}%")
        top10 = gainers_df.sort_values("change_amount", ascending=False).head(10)

        col_labels = st.columns([2, 1.5, 1.8, 2])
        col_labels[0].markdown("**Name**")
        col_labels[1].markdown("**Price**")
        col_labels[2].markdown("**Change Amount**")
        col_labels[3].markdown("**Change Percentage**")

        for _, row in top10.iterrows():
            cols = st.columns([2, 1.5, 1.8, 2])
            cols[0].markdown(f"**{row['ticker']}**")
            cols[1].markdown(f"${row['price']:.2f}")
            cols[2].markdown(f":green[+{row['change_amount']:.2f}]")
            cols[3].markdown(f"{row['change_percentage_display']}")

        st.header("Top Gainers by % Change")
        fig_bar = px.bar(
            top10,
            x="ticker",
            y="change_percentage",
            text="change_percentage_display",
            color="change_percentage",
            color_continuous_scale="Blues",
            template=plotly_theme,
            labels={"change_percentage": "Change Percentage"})
        fig_bar.update_traces(
            customdata=top10[["price", "change_amount", "change_percentage"]],
            hovertemplate="<b>Ticker:</b> %{x}<br>Price: $%{customdata[0]:.2f}<br>Change: +%{customdata[1]:.2f}<br>Change %: %{customdata[2]:.2f}%<extra></extra>")
        fig_bar.update_layout(xaxis_title="Name", yaxis_title="% Change")
        st.plotly_chart(fig_bar, use_container_width=True)

# --------------------------------------
# ML PREDICTIVE INSIGHTS TAB
# --------------------------------------
with tabs[4]:
    with st.container():
        st.markdown("""
        <div style='background-color: #fdecea; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #f5c6cb;'>
            <h3 style='margin-bottom: 10px;'>What is Prophet and Why Use Machine Learning for Asset Forecasting?</h3>
            <p style='font-size: 16px;'>
                Prophet is an open-source forecasting tool developed by Facebook designed to handle time series data that has clear trends and seasonality. It works especially well with daily financial data and allows easy customization.
            </p>
            <p style='font-size: 16px;'>
                In this tab, we harness the power of machine learning to predict short-term stock price trends based on historical data. 
                Note that while no model guarantees future returns, using ML-powered tools like Prophet can offer unique data-driven guidance that can provide useful insights to boost your trading and investment strategies. Happy forecasting!
            </p>
        </div>
        <br />
        <div style='background-color: #e0f7fa; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #81d4fa;'>
            <h3 style='margin-bottom: 10px;'>Nervous About Interpreting the Forecast Plot?</h3>
            <p style='font-size: 16px;'>
                Don't be! The forecast visual shows past stock prices and predicted future trends based on your preferences. We have described each component of the visual to help you get your head around it!
            </p>
            <ul style='font-size: 16px;'>
                <li><b>Actual (blue solid line):</b> Real historical stock prices based on your selected window.</li>
                <li><b>Fitted (red dotted line):</b> Prophet's in-sample prediction over the training period.</li>
                <li><b>Forecast (green dashed line):</b> Predicted prices for the upcoming days.</li>
                <li><b>Shaded area:</b> Confidence interval, showing the range where the price is most likely to fall.</li>
            </ul>
            <p style='font-size: 16px;'>
                Use our newly-added price forecasting tool below to identify expected trends for any of the top 10 stocks!
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.header("Stock Price Forecasting with Prophet")
    st.markdown("Forecast future stock prices using Prophet with historical data.")

    symbol_list = df["stock"].value_counts().nlargest(20).index.tolist()
    selected_symbol = st.selectbox("Choose stock to forecast:", symbol_list)
    forecast_days = st.slider("Select number of days to forecast:", min_value=5, max_value=30, value=15)
    history_window = st.slider("Days of historical data to show:", 30, 50, value=30)

    ts_df = df[df["stock"] == selected_symbol][["date", "close"]].dropna().sort_values("date")
    ts_df = ts_df.groupby("date")["close"].mean().reset_index()

    if len(ts_df) < 30:
        st.warning("Not enough historical data to make a reliable prediction.")
    else:
        ts_df["date"] = pd.to_datetime(ts_df["date"])
        ts_df.rename(columns={"date": "ds", "close": "y"}, inplace=True)
        ts_df["y"] = np.log(ts_df["y"])
        train_df = ts_df.tail(120)

        with st.spinner("Training Prophet model..."):
            model = Prophet(
                daily_seasonality=False,
                yearly_seasonality=False,
                weekly_seasonality=True,
                changepoint_prior_scale=0.5
            )
            model.fit(train_df)
            future = model.make_future_dataframe(periods=forecast_days)
            forecast = model.predict(future)

            forecast_df = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
            forecast_df.columns = ["date", "forecast", "lower_ci", "upper_ci"]
            forecast_df[["forecast", "lower_ci", "upper_ci"]] = np.exp(forecast_df[["forecast", "lower_ci", "upper_ci"]])
            forecast_df["Type"] = ["Forecast" if d > train_df["ds"].max() else "Fitted" for d in forecast_df["date"]]

            actual_df = train_df.copy()
            actual_df["y"] = np.exp(actual_df["y"])
            actual_df.rename(columns={"ds": "date", "y": "Actual"}, inplace=True)
            actual_df = actual_df.tail(history_window)
            actual_df["Type"] = "Actual"

            combined_df = pd.concat([
                actual_df[["date", "Actual", "Type"]].rename(columns={"Actual": "value"}),
                forecast_df[["date", "forecast", "Type"]].rename(columns={"forecast": "value"})
            ])

            fig_pred = px.line(
                combined_df,
                x="date",
                y="value",
                color="Type",
                line_dash="Type",
                title=f"{selected_symbol} Price Forecast ({forecast_days} Days)",
                template=plotly_theme)

            future_conf = forecast_df[forecast_df["Type"] == "Forecast"]
            fig_pred.add_traces([
                go.Scatter(
                    name="Upper Confidence",
                    x=future_conf["date"],
                    y=future_conf["upper_ci"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False),
                go.Scatter(
                    name="Lower Confidence",
                    x=future_conf["date"],
                    y=future_conf["lower_ci"],
                    mode="lines",
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor='rgba(0, 100, 80, 0.2)',
                    showlegend=True)])

            fig_pred.update_layout(xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig_pred, use_container_width=True)
