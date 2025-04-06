import argparse
import logging
from datetime import datetime, timedelta
import pandas as pd
import os

from scraper.yahoo import YahooScraper
from scraper.marketwatch import MarketWatchScraper
from scraper.cnbc import CNBCScraper
from scraper.bloomberg import BloombergScraper
from scraper.reuters import ReutersScraper
from utils.extract_ticker import TickerExtractor
from sentiment.model import load_model
from sentiment.analyze import analyze_sentiment
from utils.logger import setup_logger

def parse_args():
    parser = argparse.ArgumentParser(description='Financial News Sentiment Aggregator')
    parser.add_argument('--days', type=int, default=1, help='Number of days to look back for news')
    parser.add_argument('--sources', type=str, nargs='+', default=['yahoo', 'marketwatch', 'reuters'],
                        choices=['yahoo', 'marketwatch', 'cnbc', 'bloomberg', 'reuters'],
                        help='News sources to scrape')
    parser.add_argument('--tickers-file', type=str, default='data/tickers.csv',
                        help='Path to CSV file with ticker symbols')
    parser.add_argument('--output', type=str, default='data/output/results.csv',
                        help='Path to output file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Financial News Sentiment Aggregator")
    
    # Calculate date range for news
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    logger.info(f"Fetching news from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Initialize scrapers based on selected sources
    scrapers = []
    for source in args.sources:
        if source == 'yahoo':
            scrapers.append(YahooScraper())
        elif source == 'marketwatch':
            scrapers.append(MarketWatchScraper())
        elif source == 'cnbc':
            scrapers.append(CNBCScraper())
        elif source == 'bloomberg':
            scrapers.append(BloombergScraper())
        elif source == 'reuters':
            scrapers.append(ReutersScraper())
    
    # Make sure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Load ticker extractor
    ticker_extractor = TickerExtractor(args.tickers_file)
    
    # Load sentiment model
    sentiment_model = load_model()
    
    # Collect all news
    all_articles = []
    for scraper in scrapers:
        logger.info(f"Scraping news from {scraper.name}")
        articles = scraper.scrape(start_date, end_date)
        all_articles.extend(articles)
    
    logger.info(f"Collected {len(all_articles)} articles")
    
    # Extract tickers from article texts
    for article in all_articles:
        article['tickers'] = ticker_extractor.extract_tickers(article['title'] + ' ' + article['content'])
    
    # Filter articles with no relevant tickers
    filtered_articles = [article for article in all_articles if article['tickers']]
    logger.info(f"{len(filtered_articles)} articles contain relevant tickers")
    
    # Analyze sentiment
    for article in filtered_articles:
        article['sentiment_score'] = analyze_sentiment(article['content'], sentiment_model)
    
    # Aggregate sentiment per ticker
    ticker_sentiment = {}
    for article in filtered_articles:
        for ticker in article['tickers']:
            if ticker not in ticker_sentiment:
                ticker_sentiment[ticker] = {
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'total': 0,
                    'headlines': []
                }
            
            ticker_sentiment[ticker]['total'] += 1
            sentiment = article['sentiment_score']
            
            if sentiment > 0.1:
                ticker_sentiment[ticker]['positive'] += 1
            elif sentiment < -0.1:
                ticker_sentiment[ticker]['negative'] += 1
            else:
                ticker_sentiment[ticker]['neutral'] += 1
                
            ticker_sentiment[ticker]['headlines'].append({
                'headline': article['title'],
                'sentiment': sentiment,
                'url': article['url'],
                'source': article['source']
            })
    
    # Calculate sentiment score
    for ticker, data in ticker_sentiment.items():
        if data['total'] > 0:
            data['score'] = (data['positive'] - data['negative']) / data['total']
        else:
            data['score'] = 0
    
    # Convert to DataFrame
    results = []
    for ticker, data in ticker_sentiment.items():
        results.append({
            'ticker': ticker,
            'sentiment_score': data['score'],
            'total_mentions': data['total'],
            'positive_mentions': data['positive'],
            'negative_mentions': data['negative'],
            'neutral_mentions': data['neutral'],
            'sample_headlines': '; '.join([h['headline'] for h in data['headlines'][:3]])
        })
    
    df = pd.DataFrame(results)
    
    # Sort by sentiment score
    df = df.sort_values('sentiment_score', ascending=False)
    
    # Save to CSV
    df.to_csv(args.output, index=False)
    
    # Print top bullish and bearish tickers
    print("\n=== Top 5 Bullish Tickers ===")
    if len(df) > 0:
        top_bullish = df.head(5)
        for _, row in top_bullish.iterrows():
            print(f"{row['ticker']}: {row['sentiment_score']:.2f} (Mentions: {row['total_mentions']})")
            print(f"Sample headline: {row['sample_headlines'].split(';')[0]}")
            print()
    else:
        print("No bullish tickers found")
    
    print("\n=== Top 5 Bearish Tickers ===")
    if len(df) > 0:
        top_bearish = df.tail(5).sort_values('sentiment_score')
        for _, row in top_bearish.iterrows():
            print(f"{row['ticker']}: {row['sentiment_score']:.2f} (Mentions: {row['total_mentions']})")
            print(f"Sample headline: {row['sample_headlines'].split(';')[0]}")
            print()
    else:
        print("No bearish tickers found")
    
    logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()