import typer
import yfinance as yf
from textblob import TextBlob
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from datetime import datetime

app = typer.Typer()
console = Console()

def get_sentiment_color(score):
    if score > 0.1:
        return "green"
    elif score < -0.1:
        return "red"
    else:
        return "yellow"

def get_sentiment_label(score):
    if score > 0.1:
        return "BULLISH 🚀"
    elif score < -0.1:
        return "BEARISH 📉"
    else:
        return "NEUTRAL 😐"

@app.command()
def hello():
    console.print("Hello World")

@app.command()
def analyze(symbol: str):
    """Analyze a stock ticker for price and news sentiment."""
    ticker = symbol.upper()
    
    with console.status(f"[bold green]Fetching data for {ticker}...[/bold green]"):
        stock = yf.Ticker(ticker)
        
        # Get Info (Price, etc)
        try:
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            currency = info.get('currency', 'USD')
            long_name = info.get('longName', ticker)
        except Exception as e:
            console.print(f"[red]Error fetching info for {ticker}: {e}[/red]")
            return

        # Get News
        try:
            news = stock.news
        except Exception as e:
            console.print(f"[red]Error fetching news for {ticker}: {e}[/red]")
            news = []

    # Analyze Sentiment
    total_polarity = 0
    analyzed_news = []
    
    if news:
        # Debug: Print first item to see structure
        # console.print(news[0]) 
        for item in news:
            # yfinance news structure can vary. Usually 'title', 'publisher', 'link'.
            # Sometimes it's 'content' dictionary.
            title = item.get('title', '')
            if not title and 'content' in item:
                 title = item['content'].get('title', '')
            
            publisher = item.get('publisher', 'Unknown')
            link = item.get('link', '')
            
            # Calculate sentiment
            blob = TextBlob(title)
            polarity = blob.sentiment.polarity
            total_polarity += polarity
            
            analyzed_news.append({
                'title': title,
                'publisher': publisher,
                'link': link,
                'polarity': polarity
            })
        
        avg_polarity = total_polarity / len(news)
    else:
        avg_polarity = 0

    # --- Display Dashboard ---
    
    # 1. Header Panel
    sentiment_color = get_sentiment_color(avg_polarity)
    sentiment_label = get_sentiment_label(avg_polarity)
    
    header_text = Text()
    header_text.append(f"{long_name} ({ticker})\n", style="bold white")
    header_text.append(f"Price: {current_price} {currency}\n", style="bold cyan")
    header_text.append(f"Sentiment: {sentiment_label} ({avg_polarity:.2f})", style=f"bold {sentiment_color}")
    
    console.print(Panel(header_text, title="Stock Sentiment Agent", border_style="blue"))

    # 2. News Table
    table = Table(title=f"Recent News for {ticker}")
    table.add_column("Publisher", style="cyan", no_wrap=True)
    table.add_column("Headline", style="white")
    table.add_column("Sentiment", style="bold")

    for item in analyzed_news[:5]: # Show top 5
        p_color = get_sentiment_color(item['polarity'])
        p_label = "Pos" if item['polarity'] > 0.1 else "Neg" if item['polarity'] < -0.1 else "Neu"
        
        table.add_row(
            item['publisher'],
            item['title'],
            f"[{p_color}]{p_label}[/{p_color}]"
        )

    console.print(table)
    
    if not news:
        console.print("[yellow]No recent news found to analyze.[/yellow]")

if __name__ == "__main__":
    app()
