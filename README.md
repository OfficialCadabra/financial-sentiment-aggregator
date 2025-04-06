# Financial Sentiment News Aggregator

A Python-based application that scrapes financial news from various sources, analyzes sentiment using NLP models, categorizes news by tickers/companies, and outputs a ranked list of the most bullish and bearish stocks based on news sentiment.

## Features

- Scrapes financial news from multiple sources (Yahoo Finance, MarketWatch, CNBC, Bloomberg, Reuters)
- Analyzes text sentiment using FinBERT (financial BERT model) or NLTK VADER as fallback
- Identifies company mentions and maps them to stock tickers
- Calculates aggregate sentiment scores for each ticker
- Ranks stocks by most bullish/bearish sentiment
- Exports results to CSV

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/financial-news-aggregator.git
cd financial-news-aggregator
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Download required NLTK data:
```bash
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"
```

4. Download required spaCy model:
```bash
python -m spacy download en_core_web_sm
```

## Usage

### Basic usage:

```bash
python main.py
```

This will:
- Scrape news from the default sources (Yahoo Finance, MarketWatch, Reuters)
- Look for news from the past day
- Use the default tickers list
- Output results to `data/output/results.csv`

### Advanced options:

```bash
python main.py --days 3 --sources yahoo marketwatch cnbc --tickers-file custom_tickers.csv --output custom_output.csv --verbose
```

Options:
- `--days`: Number of days to look back for news (default: 1)
- `--sources`: News sources to scrape (options: yahoo, marketwatch, cnbc, bloomberg, reuters)
- `--tickers-file`: Path to CSV file with ticker symbols
- `--output`: Path to output file
- `--verbose`: Enable verbose logging

## Ticker File Format

The ticker file should be a CSV with at least two columns:
- `ticker`: The stock ticker symbol
- `company_name`: The company name

Example:
```
ticker,company_name
AAPL,Apple Inc.
MSFT,Microsoft Corporation
GOOGL,Alphabet Inc.
```

## Output Format

The program outputs a CSV file with the following columns:
- `ticker`: Stock ticker symbol
- `sentiment_score`: Aggregate sentiment score (-1 to 1)
- `total_mentions`: Total number of mentions in articles
- `positive_mentions`: Number of positive mentions
- `negative_mentions`: Number of negative mentions
- `neutral_mentions`: Number of neutral mentions
- `sample_headlines`: Sample headlines mentioning the ticker

## Project Structure

```
financial_news_aggregator/
├── main.py                  # Main entry point
├── scraper/                 # News scrapers
│   ├── yahoo.py
│   ├── marketwatch.py
│   ├── cnbc.py
│   ├── bloomberg.py
│   └── reuters.py
├── sentiment/               # Sentiment analysis
│   ├── model.py             # FinBERT model loading
│   └── analyze.py           # Sentiment analysis functions
├── data/                    # Data files
│   ├── tickers.csv          # Default tickers list
│   └── output/              # Output directory
├── utils/                   # Utilities
│   ├── extract_ticker.py    # Ticker extraction
│   └── logger.py            # Logging setup
├── requirements.txt         # Dependencies
└── README.md                # This file
```

## Development Timeline

- Day 1: Building scrapers for financial news sources
- Day 2: Implementing ticker extraction using spaCy
- Day 3: Integrating FinBERT sentiment model
- Day 4: Aggregating and scoring tickers
- Day 5: Output to CSV, build CLI interface
- Day 6-7: Polishing code, adding features and improvements

## Success Criteria

- Scrape at least 50 financial articles from 3+ sources
- Extract ticker mentions with 90%+ accuracy
- Provide accurate sentiment scoring and ranking
- Generate daily output of bullish/bearish tickers

## License

MIT