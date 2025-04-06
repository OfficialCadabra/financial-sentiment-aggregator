import logging
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
import os

logger = logging.getLogger(__name__)

def load_model():
    """
    Load FinBERT model for financial sentiment analysis.
    
    Returns:
        Tuple of (model, tokenizer)
    """
    try:
        logger.info("Loading FinBERT model for sentiment analysis...")
        
        # Use FinBERT model specifically trained for financial sentiment
        model_name = "ProsusAI/finbert"
        
        # Check if model is already downloaded
        model_path = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "transformers", model_name)
        
        if os.path.exists(model_path):
            logger.info("Using cached FinBERT model")
        else:
            logger.info("Downloading FinBERT model (this may take a while)...")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        logger.info("FinBERT model loaded successfully")
        
        return {
            'model': model,
            'tokenizer': tokenizer,
            'labels': ['negative', 'neutral', 'positive']
        }
        
    except Exception as e:
        logger.error(f"Error loading FinBERT model: {e}")
        logger.warning("Falling back to simple rule-based sentiment analysis")
        return None