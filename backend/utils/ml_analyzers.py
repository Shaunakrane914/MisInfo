"""
Project Aegis - Local ML Analyzers
NER, Sentiment Analysis, and Topic Classification without external APIs
"""

import logging
from typing import Dict, Any, List
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NERAnalyzer:
    """Named Entity Recognition using spaCy (runs locally)"""
    
    def __init__(self):
        self.nlp = None
        self.available = False
        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.available = True
                logger.info("[NER] spaCy model loaded successfully")
            except OSError:
                logger.warning("[NER] spaCy model not found. Run: python -m spacy download en_core_web_sm")
                self.available = False
        except ImportError:
            logger.warning("[NER] spaCy not installed. Install with: pip install spacy")
            self.available = False
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        if not self.available or not self.nlp:
            return self._fallback_extraction(text)
        
        try:
            doc = self.nlp(text)
            
            entities = {
                "people": list(set([ent.text for ent in doc.ents if ent.label_ == "PERSON"])),
                "places": list(set([ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]])),
                "organizations": list(set([ent.text for ent in doc.ents if ent.label_ == "ORG"])),
                "dates": list(set([ent.text for ent in doc.ents if ent.label_ == "DATE"])),
                "numbers": list(set([ent.text for ent in doc.ents if ent.label_ in ["CARDINAL", "QUANTITY"]]))
            }
            
            logger.debug(f"[NER] Extracted entities: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"[NER] Error extracting entities: {e}")
            return self._fallback_extraction(text)
    
    def _fallback_extraction(self, text: str) -> Dict[str, List[str]]:
        """Simple fallback extraction using regex"""
        return {
            "people": [],
            "places": [],
            "organizations": [],
            "dates": re.findall(r'\b\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b', text),
            "numbers": re.findall(r'\b\d+\b', text)
        }


class SentimentAnalyzer:
    """Sentiment Analysis using transformers (runs locally)"""
    
    def __init__(self):
        self.pipeline = None
        self.available = False
        try:
            from transformers import pipeline
            self.pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
            self.available = True
            logger.info("[Sentiment] Transformer model loaded successfully")
        except ImportError:
            logger.warning("[Sentiment] Transformers not installed. Install with: pip install transformers torch")
            self.available = False
        except Exception as e:
            logger.warning(f"[Sentiment] Could not load model: {e}")
            self.available = False
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        if not self.available or not self.pipeline:
            return self._fallback_sentiment(text)
        
        try:
            # Truncate text if too long
            text_sample = text[:512]
            result = self.pipeline(text_sample)[0]
            
            sentiment_data = {
                "label": result['label'],
                "score": result['score'],
                "manipulation_risk": "HIGH" if result['label'] == 'NEGATIVE' and result['score'] > 0.9 else "LOW",
                "emotional_tone": self._interpret_sentiment(result)
            }
            
            logger.debug(f"[Sentiment] Analysis: {sentiment_data}")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"[Sentiment] Error analyzing sentiment: {e}")
            return self._fallback_sentiment(text)
    
    def _interpret_sentiment(self, result: Dict) -> str:
        """Interpret sentiment result"""
        if result['label'] == 'NEGATIVE' and result['score'] > 0.9:
            return "fear/anger"
        elif result['label'] == 'POSITIVE' and result['score'] > 0.9:
            return "enthusiasm/excitement"
        else:
            return "neutral"
    
    def _fallback_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple fallback sentiment analysis"""
        text_lower = text.lower()
        
        # Count negative and positive words
        negative_words = ['false', 'fake', 'lie', 'hoax', 'scam', 'danger', 'threat', 'crisis']
        positive_words = ['true', 'real', 'fact', 'proven', 'verified', 'confirmed']
        
        neg_count = sum(1 for word in negative_words if word in text_lower)
        pos_count = sum(1 for word in positive_words if word in text_lower)
        
        if neg_count > pos_count:
            return {
                "label": "NEGATIVE",
                "score": 0.6,
                "manipulation_risk": "MEDIUM",
                "emotional_tone": "negative"
            }
        elif pos_count > neg_count:
            return {
                "label": "POSITIVE",
                "score": 0.6,
                "manipulation_risk": "LOW",
                "emotional_tone": "positive"
            }
        else:
            return {
                "label": "NEUTRAL",
                "score": 0.5,
                "manipulation_risk": "LOW",
                "emotional_tone": "neutral"
            }


class TopicClassifier:
    """Topic Classification using zero-shot classification"""
    
    def __init__(self):
        self.pipeline = None
        self.available = False
        self.topics = ["health", "politics", "science", "technology", "entertainment", 
                      "sports", "business", "environment", "education", "crime"]
        
        try:
            from transformers import pipeline
            self.pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            self.available = True
            logger.info("[TopicClassifier] Model loaded successfully")
        except ImportError:
            logger.warning("[TopicClassifier] Transformers not installed")
            self.available = False
        except Exception as e:
            logger.warning(f"[TopicClassifier] Could not load model: {e}")
            self.available = False
    
    def classify(self, text: str) -> Dict[str, Any]:
        """Classify text into topics"""
        if not self.available or not self.pipeline:
            return self._fallback_classification(text)
        
        try:
            # Truncate text if too long
            text_sample = text[:512]
            result = self.pipeline(text_sample, self.topics)
            
            classification = {
                "primary_topic": result['labels'][0],
                "confidence": result['scores'][0],
                "all_topics": dict(zip(result['labels'][:3], result['scores'][:3]))
            }
            
            logger.debug(f"[TopicClassifier] Classification: {classification}")
            return classification
            
        except Exception as e:
            logger.error(f"[TopicClassifier] Error classifying: {e}")
            return self._fallback_classification(text)
    
    def _fallback_classification(self, text: str) -> Dict[str, Any]:
        """Simple keyword-based classification"""
        text_lower = text.lower()
        
        topic_keywords = {
            "health": ["health", "medical", "disease", "vaccine", "doctor", "hospital", "cure"],
            "politics": ["government", "election", "president", "policy", "vote", "congress"],
            "science": ["research", "study", "scientist", "discovery", "experiment"],
            "technology": ["tech", "computer", "software", "ai", "digital", "internet"],
            "sports": ["game", "team", "player", "championship", "score", "match"],
            "business": ["company", "market", "economy", "stock", "business", "trade"],
            "crime": ["police", "arrest", "crime", "investigation", "suspect", "law"]
        }
        
        scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[topic] = score
        
        if max(scores.values()) > 0:
            primary_topic = max(scores, key=scores.get)
            return {
                "primary_topic": primary_topic,
                "confidence": 0.6,
                "all_topics": {k: v/10 for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]}
            }
        else:
            return {
                "primary_topic": "general",
                "confidence": 0.3,
                "all_topics": {}
            }


# Global instances
ner_analyzer = NERAnalyzer()
sentiment_analyzer = SentimentAnalyzer()
topic_classifier = TopicClassifier()


# Example usage
if __name__ == "__main__":
    test_text = "Breaking: Scientists discover new vaccine that could cure cancer in 2024!"
    
    print("=== NER Analysis ===")
    entities = ner_analyzer.extract_entities(test_text)
    print(entities)
    
    print("\n=== Sentiment Analysis ===")
    sentiment = sentiment_analyzer.analyze(test_text)
    print(sentiment)
    
    print("\n=== Topic Classification ===")
    topic = topic_classifier.classify(test_text)
    print(topic)
