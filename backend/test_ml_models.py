#!/usr/bin/env python3
"""
Test script for ML models (vectorizer.pkl and classifier.pkl)
"""

import joblib
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ml_models():
    """Test loading and using the ML models"""
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"Script directory: {script_dir}")
        
        # Load the models
        logger.info("Loading vectorizer...")
        vectorizer = joblib.load(os.path.join(script_dir, "vectorizer.pkl"))
        logger.info("Vectorizer loaded successfully!")
        
        logger.info("Loading classifier...")
        classifier = joblib.load(os.path.join(script_dir, "classifier.pkl"))
        logger.info("Classifier loaded successfully!")
        
        # Test the models with a sample text
        sample_texts = [
            "This is a completely true and factual statement",
            "Scientists confirm that drinking water cures all forms of cancer",
            "The Earth is flat and NASA is hiding the truth",
            "Breaking: Major earthquake hits city center!"
        ]
        
        logger.info("Testing models with sample texts...")
        for i, text in enumerate(sample_texts):
            logger.info(f"Processing text {i+1}: {text[:50]}...")
            
            # Vectorize the text
            text_vector = vectorizer.transform([text])
            logger.info(f"Text vectorized successfully")
            
            # Predict probability
            fake_probability = classifier.predict_proba(text_vector)[0][0]
            prediction = classifier.predict(text_vector)[0]
            
            logger.info(f"Fake probability: {fake_probability:.4f}")
            logger.info(f"Prediction: {'Fake' if prediction == 0 else 'Real'}")
            logger.info("-" * 50)
        
        logger.info("ML models test completed successfully!")
        return True
        
    except FileNotFoundError as e:
        logger.error(f"Model file not found: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing ML models: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== ML Models Test Script ===")
    success = test_ml_models()
    if success:
        logger.info("All tests passed!")
    else:
        logger.error("Tests failed!")