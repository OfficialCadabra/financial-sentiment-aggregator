import requests
from bs4 import BeautifulSoup
import logging
import time
from datetime import datetime
from newspaper import Article
import random

logger = logging.getLogger(__name__)

class YahooScraper:
    def __init__(self):
        self.name = "Yahoo Finance"
        self.base_url = "https://finance.yahoo.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    
    def scrape(self, start_date, end_date):
        """
        Scrape Yahoo Finance news articles.
        
        Args:
            start_date: Start date for news articles
            end_date: End date for news articles
            
        Returns:
            List of dictionaries containing article data
        """
        articles = []
        
        # Yahoo Finance doesn't have an easy way to fetch news by date,
        # so we'll scrape from different sections and filter by date later
        sections = [
            '/news',
            '/topic/stock-market-news',
            '/topic/economic-news',
            '/topic/earnings'
        ]
        
        for section in sections:
            url = f"{self.base_url}{section}"
            logger.info(f"Scraping {url}")
            
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract news links
                news_items = soup.select('div.Cf li.js-stream-content')
                
                for item in news_items:
                    try:
                        # Find headline link
                        headline_elem = item.select_one('h3 a, h4 a')
                        
                        if not headline_elem:
                            continue
                            
                        title = headline_elem.text.strip()
                        news_url = headline_elem['href']
                        
                        # Convert relative URLs to absolute
                        if news_url.startswith('/'):
                            news_url = f"{self.base_url}{news_url}"
                        
                        # Skip if URL is not from Yahoo domain (external links)
                        if "finance.yahoo.com" not in news_url:
                            continue
                        
                        # Extract timestamp element
                        time_elem = item.select_one('div.C(#959595) span')
                        timestamp = None
                        if time_elem:
                            pub_time = time_elem.text.strip()
                            # Parse the timestamp
                            if "ago" in pub_time:  # E.g., "5 hours ago"
                                timestamp = datetime.now()  # Approximation
                            else:
                                try:
                                    timestamp = datetime.strptime(pub_time, '%B %d, %Y')
                                except ValueError:
                                    logger.warning(f"Could not parse timestamp: {pub_time}")
                                    timestamp = None
                        
                        # Skip if article is outside of date range
                        if timestamp and (timestamp < start_date or timestamp > end_date):
                            continue
                        
                        # Extract full article content using newspaper3k
                        logger.debug(f"Extracting content from {news_url}")
                        article_data = self.extract_article_content(news_url)
                        
                        if not article_data:
                            continue
                        
                        article_dict = {
                            'title': title,
                            'url': news_url,
                            'timestamp': timestamp,
                            'content': article_data.get('text', ''),
                            'snippet': article_data.get('summary', ''),
                            'source': self.name
                        }
                        
                        articles.append(article_dict)
                        
                        # Sleep to avoid rate limiting
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        logger.error(f"Error processing article: {e}")
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
        
        logger.info(f"Scraped {len(articles)} articles from {self.name}")
        return articles
    
    def extract_article_content(self, url):
        """
        Extract article content using newspaper3k.
        
        Args:
            url: URL of the article
            
        Returns:
            Dictionary with article text and summary
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()
            
            return {
                'text': article.text,
                'summary': article.summary
            }
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None