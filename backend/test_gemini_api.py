#!/usr/bin/env python3
"""
Test script for Gemini API
"""

import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini_api():
    """Test the Gemini API connection and functionality"""
    try:
        # Try to import the Google Generative AI library
        logger.info("Importing Google Generative AI library...")
        import google.generativeai as genai
        logger.info("Google Generative AI library imported successfully!")
        
        # Get API key from environment variables
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            logger.info("Please set the GEMINI_API_KEY environment variable to test the API")
            return False
        
        # Configure the API
        logger.info("Configuring Gemini API...")
        genai.configure(api_key=api_key)
        logger.info("Gemini API configured successfully!")
        
        # Create a model instance
        logger.info("Creating model instance...")
        model = genai.GenerativeModel('gemini-2.5-pro')
        logger.info("Model instance created successfully!")
        
        # Test with a simple prompt
        logger.info("Testing API with a simple prompt...")
        prompt = "What is the capital of France?"
        response = model.generate_content(prompt)
        logger.info(f"API response: {response.text}")
        
        # Test with a JSON response format
        logger.info("Testing API with JSON response format...")
        json_prompt = """Please respond in JSON format with the following structure:
{
    "answer": "The answer to the question",
    "confidence": 0.95
}

Question: What is the capital of France?"""
        
        response = model.generate_content(json_prompt)
        logger.info(f"JSON API response: {response.text}")
        
        # Try to parse as JSON
        try:
            json_response = json.loads(response.text)
            logger.info(f"Parsed JSON response: {json_response}")
        except json.JSONDecodeError:
            logger.warning("Could not parse response as JSON")
        
        logger.info("Gemini API test completed successfully!")
        return True
        
    except ImportError:
        logger.error("Google Generative AI library not installed")
        logger.info("Please install the library using: pip install google-generativeai")
        return False
    except Exception as e:
        logger.error(f"Error testing Gemini API: {e}")
        return False

def test_mock_analysis():
    """Test the mock analysis implementation"""
    logger.info("Testing mock analysis implementation...")
    
    # Sample case file
    case_file = {
        "claim_text": "Scientists confirm that drinking water cures all forms of cancer",
        "text_suspicion_score": 0.95,
        "source_credibility_score": 0.1,
        "research_dossier": {
            "wikipedia_summary": "Water is a chemical compound made of hydrogen and oxygen.",
            "web_snippets": [
                "No scientific evidence supports the claim that water alone can cure cancer",
                "Medical experts warn against relying on unproven cancer treatments"
            ]
        }
    }
    
    # Mock analysis logic
    claim_text = case_file.get("claim_text", "")
    text_suspicion_score = case_file.get("text_suspicion_score", 0.5)
    source_credibility_score = case_file.get("source_credibility_score", 0.5)
    
    logger.info(f"Claim: {claim_text}")
    logger.info(f"Text suspicion score: {text_suspicion_score:.4f}")
    logger.info(f"Source credibility score: {source_credibility_score:.4f}")
    
    # Simple mock logic based on scores
    if text_suspicion_score > 0.8 and source_credibility_score < 0.3:
        verdict = "False"
        confidence = 0.9
        reasoning = "High suspicion score and low source credibility indicate misinformation."
    elif text_suspicion_score < 0.3 and source_credibility_score > 0.7:
        verdict = "True"
        confidence = 0.8
        reasoning = "Low suspicion score and high source credibility suggest authentic information."
    else:
        verdict = "Misleading"
        confidence = 0.6
        reasoning = "Mixed indicators require further investigation for complete accuracy."
    
    result = {
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": reasoning
    }
    
    logger.info(f"Mock analysis result: {result}")
    logger.info("Mock analysis test completed successfully!")
    return True

if __name__ == "__main__":
    logger.info("=== Gemini API Test Script ===")
    
    # Test mock analysis first
    mock_success = test_mock_analysis()
    
    # Test actual Gemini API if possible
    gemini_success = test_gemini_api()
    
    if mock_success:
        logger.info("Mock analysis test passed!")
    
    if gemini_success:
        logger.info("Gemini API test passed!")
    else:
        logger.warning("Gemini API test failed. Using mock analysis as fallback.")