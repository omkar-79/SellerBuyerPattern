import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(layout="wide")
st.title("📈 Price Action vs Buy/Sell Pressure Analysis")

# Sidebar inputs
with st.sidebar:
    ticker = st.text_input("Enter US Stock Ticker:", "AAPL").upper()
    period = st.selectbox("Select data period:", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
    interval = st.selectbox("Select interval:", ["1d", "1h", "15m"], index=0)
    show_imbalance = st.checkbox("Show Buy/Sell Imbalance Line", value=True)
    show_cumulative = st.checkbox("Show Cumulative Pressure", value=True)

# Data Fetching and Processing
if ticker:
    data = yf.download(ticker, period=period, interval=interval)

    if data.empty:
        st.error("No data found. Check ticker or interval.")
    else:
        # Enhanced Calculations
        data['Price Change'] = data['Close'].diff()
        data['Buy Pressure'] = data['Volume'].where(data['Price Change'] > 0, 0)
        data['Sell Pressure'] = data['Volume'].where(data['Price Change'] < 0, 0)
        data['Net Pressure'] = data['Buy Pressure'] - data['Sell Pressure']
        data['Cumulative Pressure'] = data['Net Pressure'].cumsum()
        data['Imbalance'] = data['Net Pressure'] / (data['Buy Pressure'] + data['Sell Pressure'] + 1e-6)

        # Create Figure with Secondary Y-axes
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.7, 0.3],  # Adjusted ratio for better visibility
            vertical_spacing=0.05,
            subplot_titles=[f"{ticker} Price Action", "Buy/Sell Pressure Analysis"]
        )

        # Price Chart with Volume (modified for better visibility)
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price',
            increasing_line_color='green',
            decreasing_line_color='red',
            showlegend=True
        ), row=1, col=1)

        # Add volume bars to price chart
        colors = ['green' if x >= 0 else 'red' for x in data['Price Change']]
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.3,
            showlegend=True
        ), row=1, col=1)

        if show_cumulative:
            # Add cumulative pressure line to price chart
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['Cumulative Pressure']/data['Cumulative Pressure'].abs().max()*data['Close'].mean(),
                name='Cumulative Pressure',
                line=dict(color='purple', width=1, dash='dot'),
                opacity=0.7
            ), row=1, col=1)

        # Pressure Analysis
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Buy Pressure'],
            name='Buy Volume',
            marker_color='green',
            opacity=0.5
        ), row=2, col=1)

        fig.add_trace(go.Bar(
            x=data.index,
            y=-data['Sell Pressure'],  # Negative to show below axis
            name='Sell Volume',
            marker_color='red',
            opacity=0.5
        ), row=2, col=1)

        if show_imbalance:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['Imbalance'],
                name='Buy/Sell Imbalance',
                line=dict(color='orange', width=1),
                yaxis="y3"
            ), row=2, col=1)

        # Update Layout
        fig.update_layout(
            height=800,
            margin=dict(t=30, l=40, r=40, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis=dict(
                title="Price",
                type="log",  # Use log scale for better price visibility
                showgrid=True
            ),
            yaxis2=dict(
                title="Volume",
                overlaying="y",
                side="right",
                showgrid=False
            ),
            xaxis_rangeslider_visible=False,
            hovermode="x unified"
        )

        # Add range buttons
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="1w", step="day", stepmode="backward"),
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=3, label="3m", step="month", stepmode="backward"),
                        dict(step="all")
                    ])
                )
            )
        )

        # Show plot
        st.plotly_chart(fig, use_container_width=True)

        # Fix metrics calculation
        try:
            # Calculate metrics using float values
            total_volume = float(data['Volume'].sum())
            buy_volume = float(data['Buy Pressure'].sum())
            sell_volume = float(data['Sell Pressure'].sum())
            
            # Calculate ratios
            buy_ratio = (buy_volume / total_volume * 100) if total_volume > 0 else 0
            sell_ratio = (sell_volume / total_volume * 100) if total_volume > 0 else 0
            net_pressure = buy_ratio - sell_ratio

            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Buy Pressure Ratio", f"{buy_ratio:.1f}%")
            with col2:
                st.metric("Sell Pressure Ratio", f"{sell_ratio:.1f}%")
            with col3:
                st.metric("Net Pressure Bias", f"{net_pressure:.1f}%")
        except Exception as e:
            st.warning("Could not calculate metrics due to insufficient data")
