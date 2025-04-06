import pandas as pd
import re
import spacy
import logging
import os

logger = logging.getLogger(__name__)

class TickerExtractor:
    def __init__(self, tickers_file):
        """
        Initialize the ticker extractor with a CSV file containing ticker symbols.
        
        Args:
            tickers_file: Path to CSV file with ticker symbols and company names
        """
        self.tickers_file = tickers_file
        self.load_tickers()
        self.load_spacy_model()
    
    def load_tickers(self):
        """
        Load ticker symbols and company names from CSV file.
        Expected CSV format: ticker,company_name
        """
        try:
            # Check if file exists, if not create a sample one
            if not os.path.exists(self.tickers_file):
                os.makedirs(os.path.dirname(self.tickers_file), exist_ok=True)
                sample_tickers = pd.DataFrame({
                    'ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'FB', 'TSLA', 'JPM', 'V', 'PG', 'WMT'],
                    'company_name': ['Apple Inc.', 'Microsoft Corporation', 'Alphabet Inc.', 'Amazon.com Inc.', 
                                    'Meta Platforms Inc.', 'Tesla Inc.', 'JPMorgan Chase & Co.', 
                                    'Visa Inc.', 'Procter & Gamble Co.', 'Walmart Inc.']
                })
                sample_tickers.to_csv(self.tickers_file, index=False)
                logger.info(f"Created sample tickers file at {self.tickers_file}")
            
            # Load tickers from CSV
            self.tickers_df = pd.read_csv(self.tickers_file)
            
            # Create ticker to company name mapping
            self.ticker_to_company = dict(zip(self.tickers_df['ticker'], self.tickers_df['company_name']))
            
            # Create company name to ticker mapping (for detecting company names in text)
            self.company_to_ticker = dict(zip(self.tickers_df['company_name'], self.tickers_df['ticker']))
            
            # Create variations of company names to improve matching
            self.company_variations = {}
            for company, ticker in self.company_to_ticker.items():
                # Add full name
                self.company_variations[company.lower()] = ticker
                
                # Add without 'Inc.', 'Corp.', etc.
                simplified = re.sub(r'\s+(Inc|Corp|Co|Ltd|LLC|Corporation|Company|Limited)\.?$', '', company)
                self.company_variations[simplified.lower()] = ticker
                
                # Add short name (first word only, if it's more than 4 characters)
                first_word = company.split()[0]
                if len(first_word) > 4 and first_word.lower() not in ['the']:
                    self.company_variations[first_word.lower()] = ticker
            
            logger.info(f"Loaded {len(self.ticker_to_company)} tickers from {self.tickers_file}")
            
        except Exception as e:
            logger.error(f"Error loading tickers: {e}")
            # Create empty dictionaries if loading fails
            self.ticker_to_company = {}
            self.company_to_ticker = {}
            self.company_variations = {}
    
    def load_spacy_model(self):
        """
        Load spaCy NLP model for named entity recognition.
        """
        try:
            # Try to load the model, download if not available
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.info("Downloading spaCy model...")
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            
            logger.info("Loaded spaCy model for named entity recognition")
        except Exception as e:
            logger.error(f"Error loading spaCy model: {e}")
            self.nlp = None
    
    def extract_tickers(self, text):
        """
        Extract ticker symbols and company names from text.
        
        Args:
            text: The text to extract tickers from
            
        Returns:
            List of ticker symbols found in the text
        """
        if not text:
            return []
        
        found_tickers = set()
        
        # Direct ticker matching with word boundaries
        for ticker in self.ticker_to_company.keys():
            pattern = r'\b' + re.escape(ticker) + r'\b'
            if re.search(pattern, text):
                found_tickers.add(ticker)
        
        # Named entity recognition for organizations
        if self.nlp:
            doc = self.nlp(text)
            organizations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            
            for org in organizations:
                # Check direct match
                org_lower = org.lower()
                if org_lower in self.company_variations:
                    found_tickers.add(self.company_variations[org_lower])
                    continue
                
                # Check partial match (company name contains this organization)
                for company, ticker in self.company_to_ticker.items():
                    if org_lower in company.lower():
                        found_tickers.add(ticker)
                        break
        
        return list(found_tickers)