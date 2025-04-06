import requests
import logging
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime
from newspaper import Article
import json

logger = logging.getLogger(__name__)

class CNBCScraper:
    def __init__(self):
        self.name = "CNBC"
        self.base_url = "https://www.cnbc.com"
        self.endpoints = [
            "/markets",
            "/business-news",
            "/investing",
            "/finance"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    
    def scrape(self, start_date, end_date):
        """
        Scrape CNBC news articles.
        
        Args:
            start_date: Start date for news articles
            end_date: End date for news articles
            
        Returns:
            List of dictionaries containing article data
        """
        articles = []
        
        for endpoint in self.endpoints:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"Scraping {url}")
            
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all article links
                article_elements = soup.select('div.Card-standardBreakerCard, div.Card-marketsBreakerCard, div.Card-categoryCard')
                
                for element in article_elements:
                    try:
                        # Find headline link
                        headline_elem = element.select_one('a.Card-title')
                        
                        if not headline_elem:
                            continue
                            
                        title = headline_elem.text.strip()
                        news_url = headline_elem['href']
                        
                        # Convert relative URLs to absolute
                        if news_url.startswith('/'):
                            news_url = f"{self.base_url}{news_url}"
                        
                        # Skip if URL is not from CNBC domain
                        if "cnbc.com" not in news_url:
                            continue
                        
                        # Try to find timestamp
                        time_elem = element.select_one('span.Card-time')
                        timestamp = None
                        
                        if time_elem:
                            pub_time = time_elem.text.strip()
                            # Parse the timestamp
                            if "ago" in pub_time:  # E.g., "5 hours ago"
                                timestamp = datetime.now()  # Approximation
                            else:
                                try:
                                    timestamp = datetime.strptime(pub_time, '%b %d %Y')
                                except ValueError:
                                    logger.warning(f"Could not parse timestamp: {pub_time}")
                                    timestamp = None
                        
                        # If no timestamp found, extract it from the article itself
                        if not timestamp:
                            timestamp = self.extract_timestamp_from_article(news_url)
                        
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
    
    def extract_timestamp_from_article(self, url):
        """
        Extract publication timestamp from article page.
        
        Args:
            url: URL of the article
            
        Returns:
            Timestamp as datetime object or None
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for timestamp in meta tags
            meta_time = soup.select_one('meta[property="article:published_time"]')
            if meta_time and meta_time.get('content'):
                try:
                    return datetime.fromisoformat(meta_time['content'].replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            # Try to find timestamp in page content
            time_elem = soup.select_one('time.ArticleHeader-time')
            if time_elem:
                pub_time = time_elem.text.strip()
                try:
                    # Various format patterns
                    for fmt in ['%a, %b %d %Y', '%b %d %Y', '%a %b %d %Y']:
                        try:
                            return datetime.strptime(pub_time, fmt)
                        except ValueError:
                            continue
                except Exception:
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting timestamp from {url}: {e}")
            return None
    
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