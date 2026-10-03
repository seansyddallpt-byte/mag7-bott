import os
import requests
import pandas as pd
import yfinance as yf

MAG7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

def get_hated_pick():
    data = yf.download(MAG7, period="1y", interval="1d", auto_adjust=True)['Close']
    
    ret_3m = (data.iloc[-1] / data.iloc[-63] - 1) * 100
    ret_6m = (data.iloc[-1] / data.iloc[-126] - 1) * 100
    ret_12m = (data.iloc[-1] / data.iloc[0] - 1) * 100
    
    df = pd.DataFrame({
        'price': data.iloc[-1],
        'ret_3m': ret_3m,
        'ret_6m': ret_6m,
        'ret_12m': ret_12m
    })
    
    df['rank_3m'] = df['ret_3m'].rank(ascending=False)
    df['rank_6m'] = df['ret_6m'].rank(ascending=False)
    df['rank_12m'] = df['ret_12m'].rank(ascending=False)
    df['avg_rank'] = df[['rank_3m', 'rank_6m', 'rank_12m']].mean(axis=1)
    
    sorted_df = df.sort_values(by='avg_rank', ascending=False)
    target = sorted_df.iloc[0]
    return sorted_df, target

def send_discord_notification(df, target):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL environment variable is missing.")

    ticker = target.name
    price = f"${target['price']:.2f}"
    avg_rank = f"{target['avg_rank']:.2f} / 7.00"
    
    board_lines = []
    for rank, (t, row) in enumerate(df.iterrows(), 1):
        board_lines.append(
            f"`{rank}.` **{t}** — 3M: `{row['ret_3m']:+.1f}%` | 6M: `{row['ret_6m']:+.1f}%` | 12M: `{row['ret_12m']:+.1f}%`"
        )
    leaderboard_text = "\n".join(board_lines)

    embed = {
        "title": "📉 FinTwit 'Most Hated' Mag 7 Weekly DCA",
        "description": f"Today's mean-reversion DCA target is **{ticker}**.",
        "color": 0xFF4500,
        "fields": [
            {"name": "🎯 DCA Target", "value": f"**{ticker}** ({price})", "inline": True},
            {"name": "📊 Composite Rank", "value": avg_rank, "inline": True},
            {"name": "🏆 Full Performance Board (Worst to Best)", "value": leaderboard_text, "inline": False}
        ],
        "footer": {"text": "Rankings based on 3M, 6M, and 12M trailing returns."}
    }

    payload = {
        "username": "Mag 7 Sentiment Bot",
        "embeds": [embed]
    }

    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()

if __name__ == "__main__":
    df, target = get_hated_pick()
    send_discord_notification(df, target)
