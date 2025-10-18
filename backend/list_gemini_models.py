#!/usr/bin/env python3
"""
Script to list available Gemini models
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_gemini_models():
    """List all available Gemini models"""
    try:
        # Import the Google Generative AI library
        logger.info("Importing Google Generative AI library...")
        import google.generativeai as genai
        
        # Get API key from environment variables
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_secret_gemini_key":
            logger.warning("GEMINI_API_KEY not found or is still the placeholder value in environment variables")
            logger.info("Please set a valid GEMINI_API_KEY in the .env file")
            return False
        
        logger.info(f"Gemini API key found (first 10 chars): {api_key[:10]}...")
        
        # Configure the API
        logger.info("Configuring Gemini API...")
        genai.configure(api_key=api_key)
        logger.info("Gemini API configured successfully!")
        
        # List available models
        logger.info("Listing available models...")
        for model in genai.list_models():
            logger.info(f"Model: {model.name}")
            logger.info(f"  Display Name: {model.display_name}")
            logger.info(f"  Description: {model.description}")
            logger.info(f"  Supported Methods: {model.supported_generation_methods}")
            logger.info("-" * 50)
        
        return True
        
    except ImportError:
        logger.error("Google Generative AI library not installed")
        logger.info("Please install the library using: pip install google-generativeai")
        return False
    except Exception as e:
        logger.error(f"Error listing Gemini models: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Gemini Models List Script ===")
    success = list_gemini_models()
    if success:
        logger.info("Model listing completed successfully!")
    else:
        logger.error("Failed to list models!")