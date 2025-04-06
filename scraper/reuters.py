import requests
import logging
import time
import random
import xml.etree.ElementTree as ET
from datetime import datetime
from newspaper import Article

logger = logging.getLogger(__name__)

class ReutersScraper:
    def __init__(self):
        self.name = "Reuters"
        self.base_url = "https://www.reuters.com"
        self.rss_feeds = [
            "https://www.reuters.com/rssfeed/business",
            "https://www.reuters.com/rssfeed/marketsNews",
            "https://www.reuters.com/rssfeed/companyNews",
            "https://www.reuters.com/rssfeed/stocksNews"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    
    def scrape(self, start_date, end_date):
        """
        Scrape Reuters news articles from RSS feeds.
        
        Args:
            start_date: Start date for news articles
            end_date: End date for news articles
            
        Returns:
            List of dictionaries containing article data
        """
        articles = []
        
        for feed_url in self.rss_feeds:
            logger.info(f"Scraping RSS feed: {feed_url}")
            
            try:
                response = requests.get(feed_url, headers=self.headers)
                response.raise_for_status()
                
                # Parse XML
                root = ET.fromstring(response.content)
                
                # Find all items in the RSS feed
                items = root.findall('.//item')
                
                for item in items:
                    try:
                        title_elem = item.find('title')
                        title = title_elem.text if title_elem is not None else ""
                        
                        link_elem = item.find('link')
                        news_url = link_elem.text if link_elem is not None else ""
                        
                        pub_date_elem = item.find('pubDate')
                        pub_date_str = pub_date_elem.text if pub_date_elem is not None else ""
                        
                        # Parse publication date
                        if pub_date_str:
                            try:
                                # Example format: Wed, 14 Dec 2023 16:32:00 GMT
                                timestamp = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                            except ValueError:
                                try:
                                    # Alternative format
                                    timestamp = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                                except ValueError:
                                    logger.warning(f"Could not parse timestamp: {pub_date_str}")
                                    timestamp = None
                        else:
                            timestamp = None
                        
                        # Skip if article is outside of date range
                        if timestamp and (timestamp < start_date or timestamp > end_date):
                            continue
                        
                        # Extract description/snippet
                        description_elem = item.find('description')
                        snippet = description_elem.text if description_elem is not None else ""
                        
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
                            'snippet': snippet,
                            'source': self.name
                        }
                        
                        articles.append(article_dict)
                        
                        # Sleep to avoid rate limiting
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        logger.error(f"Error processing article: {e}")
                
            except Exception as e:
                logger.error(f"Error scraping RSS feed {feed_url}: {e}")
        
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