import logging
import torch
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re

logger = logging.getLogger(__name__)

def download_nltk_data():
    """
    Download required NLTK data if not already available.
    """
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        logger.info("Downloading NLTK vader_lexicon...")
        nltk.download('vader_lexicon', quiet=True)
    
    try:
        nltk.data.find('punkt')
    except LookupError:
        logger.info("Downloading NLTK punkt...")
        nltk.download('punkt', quiet=True)

def analyze_sentiment(text, model_data):
    """
    Analyze sentiment of text using FinBERT model or NLTK VADER as fallback.
    
    Args:
        text: Text to analyze
        model_data: FinBERT model data dictionary or None
    
    Returns:
        Sentiment score between -1 (very negative) and 1 (very positive)
    """
    if not text:
        return 0.0
    
    # Clean text first
    text = clean_text(text)
    
    # Split text into chunks if it's too long
    chunks = split_text(text)
    
    # If we have a FinBERT model, use it
    if model_data and model_data['model'] and model_data['tokenizer']:
        return analyze_with_finbert(chunks, model_data)
    else:
        # Fallback to NLTK VADER if FinBERT is not available
        return analyze_with_vader(chunks)

def clean_text(text):
    """
    Clean text before sentiment analysis.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    # Convert to string if needed
    if not isinstance(text, str):
        text = str(text)
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def split_text(text, max_length=512):
    """
    Split text into chunks if it's too long for the model.
    
    Args:
        text: Text to split
        max_length: Maximum chunk length in characters
    
    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    # Try to split on sentence boundaries
    try:
        sentences = nltk.sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    except:
        # Fallback to simple chunking if sentence tokenization fails
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def analyze_with_finbert(chunks, model_data):
    """
    Analyze sentiment using FinBERT model.
    
    Args:
        chunks: List of text chunks
        model_data: FinBERT model data dictionary
    
    Returns:
        Average sentiment score between -1 and 1
    """
    model = model_data['model']
    tokenizer = model_data['tokenizer']
    labels = model_data['labels']
    
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    
    # Ensure model is in evaluation mode
    model.eval()
    
    scores = []
    
    with torch.no_grad():
        for chunk in chunks:
            try:
                # Tokenize and prepare input
                inputs = tokenizer(chunk, padding=True, truncation=True, 
                                  max_length=512, return_tensors="pt")
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                # Get model output
                outputs = model(**inputs)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
                
                # Convert to numpy
                probs = probabilities.cpu().numpy()[0]
                
                # Calculate sentiment score: -1 (negative) to 1 (positive)
                # Assuming labels order: negative, neutral, positive
                neg_prob = probs[0]
                pos_prob = probs[2]
                
                score = pos_prob - neg_prob
                scores.append(score)
                
            except Exception as e:
                logger.error(f"Error analyzing sentiment with FinBERT: {e}")
    
    # Return average score across all chunks
    if scores:
        return sum(scores) / len(scores)
    else:
        return 0.0

def analyze_with_vader(chunks):
    """
    Analyze sentiment using NLTK VADER.
    
    Args:
        chunks: List of text chunks
    
    Returns:
        Average compound sentiment score between -1 and 1
    """
    # Download NLTK data if needed
    download_nltk_data()
    
    try:
        # Initialize VADER
        sid = SentimentIntensityAnalyzer()
        
        # Get compound scores for each chunk
        scores = [sid.polarity_scores(chunk)['compound'] for chunk in chunks]
        
        # Return average score
        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.0
    except Exception as e:
        logger.error(f"Error analyzing sentiment with VADER: {e}")
        return 0.0

def get_financial_keywords():
    """
    Get dictionary of financial keywords with sentiment values.
    
    Returns:
        Dictionary of financial terms and their sentiment scores
    """
    # Financial terms with positive/negative connotations
    financial_terms = {
        # Positive terms
        'profit': 0.8,
        'growth': 0.7,
        'upside': 0.6,
        'bullish': 0.9,
        'outperform': 0.8,
        'beat': 0.7,
        'strong': 0.6,
        'upgrade': 0.8,
        'opportunity': 0.6,
        'recovery': 0.6,
        'gains': 0.7,
        'positive': 0.7,
        'exceeded expectations': 0.9,
        'dividend': 0.6,
        'expansion': 0.7,
        
        # Negative terms
        'loss': -0.8,
        'decline': -0.7,
        'downside': -0.6,
        'bearish': -0.9,
        'underperform': -0.8,
        'miss': -0.7,
        'weak': -0.6,
        'downgrade': -0.8,
        'risk': -0.6,
        'warning': -0.7,
        'losses': -0.7,
        'negative': -0.7,
        'below expectations': -0.9,
        'investigation': -0.8,
        'contraction': -0.7
    }
    
    return financial_terms

def enhance_sentiment_analysis(text, base_score):
    """
    Enhance sentiment analysis with financial domain knowledge.
    
    Args:
        text: Original text
        base_score: Base sentiment score from model
    
    Returns:
        Adjusted sentiment score
    """
    text = text.lower()
    financial_terms = get_financial_keywords()
    
    # Count matches for financial terms
    matches = 0
    term_score_sum = 0
    
    for term, score in financial_terms.items():
        if term in text:
            count = text.count(term)
            matches += count
            term_score_sum += count * score
    
    # If we found financial terms, adjust the score
    if matches > 0:
        financial_score = term_score_sum / matches
        # Blend the base score with the financial score (70% base, 30% financial)
        adjusted_score = 0.7 * base_score + 0.3 * financial_score
        return adjusted_score
    
    # If no financial terms found, return the original score
    return base_score