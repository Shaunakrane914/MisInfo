#!/usr/bin/env python3
"""
Comprehensive test script for both ML models and Gemini API
Loads environment variables and tests all components
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ml_models():
    """Test loading and using the ML models"""
    try:
        import joblib
        
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
        return True, vectorizer, classifier
        
    except FileNotFoundError as e:
        logger.error(f"Model file not found: {e}")
        return False, None, None
    except Exception as e:
        logger.error(f"Error testing ML models: {e}")
        return False, None, None

def test_gemini_api():
    """Test the Gemini API connection and functionality"""
    try:
        # Try to import the Google Generative AI library
        logger.info("Importing Google Generative AI library...")
        import google.generativeai as genai
        logger.info("Google Generative AI library imported successfully!")
        
        # Get API key from environment variables
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_secret_gemini_key":
            logger.warning("GEMINI_API_KEY not found or is still the placeholder value in environment variables")
            logger.info("Please set a valid GEMINI_API_KEY in the .env file")
            return False, None
        
        logger.info(f"Gemini API key found (first 10 chars): {api_key[:10]}...")
        
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
        logger.info(f"API response: {response.text[:100]}...")
        
        # Test with a JSON response format
        logger.info("Testing API with JSON response format...")
        json_prompt = """Please respond in JSON format with the following structure:
{
    "answer": "The answer to the question",
    "confidence": 0.95
}

Question: What is the capital of France?"""
        
        response = model.generate_content(json_prompt)
        logger.info(f"JSON API response: {response.text[:100]}...")
        
        # Try to parse as JSON
        try:
            json_response = json.loads(response.text)
            logger.info(f"Parsed JSON response: {json_response}")
        except json.JSONDecodeError:
            logger.warning("Could not parse response as JSON")
        
        logger.info("Gemini API test completed successfully!")
        return True, model
        
    except ImportError:
        logger.error("Google Generative AI library not installed")
        logger.info("Please install the library using: pip install google-generativeai")
        return False, None
    except Exception as e:
        logger.error(f"Error testing Gemini API: {e}")
        return False, None

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

def test_analyst_agent():
    """Test the AnalystAgent directly"""
    try:
        from agents.analyst_agent import AnalystAgent
        from agents.base_agent import AgentTask, TaskPriority
        from datetime import datetime
        import asyncio
        
        logger.info("Testing AnalystAgent...")
        
        # Create the analyst agent
        analyst_agent = AnalystAgent(model_path=".")
        
        # Check if models were loaded
        if analyst_agent.vectorizer is None or analyst_agent.classifier is None:
            logger.warning("AnalystAgent models not loaded properly")
            return False
        
        logger.info("AnalystAgent models loaded successfully!")
        
        # Create a sample task
        task = AgentTask(
            task_id="test_analysis_task_001",
            agent_type="AnalystAgent",
            priority=TaskPriority.NORMAL,
            payload={
                "claim_text": "This is a test claim to analyze for misinformation"
            },
            created_at=datetime.now()
        )
        
        # Process the task (AnalystAgent.process_task is not async, but we'll handle it properly)
        result = analyst_agent.process_task(task)
        logger.info(f"AnalystAgent result: {result}")
        
        logger.info("AnalystAgent test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing AnalystAgent: {e}")
        return False

def test_investigator_agent():
    """Test the InvestigatorAgent directly"""
    try:
        from agents.investigator_agent import InvestigatorAgent
        from agents.base_agent import AgentTask, TaskPriority
        from datetime import datetime
        
        logger.info("Testing InvestigatorAgent...")
        
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Create the investigator agent
        investigator_agent = InvestigatorAgent(gemini_api_key=api_key)
        
        # Check if Gemini is being used
        if investigator_agent.use_gemini:
            logger.info("InvestigatorAgent is configured to use Gemini API")
        else:
            logger.info("InvestigatorAgent is using mock implementation")
        
        # Create a sample case file
        sample_case_file = {
            "claim_text": "The Earth is flat",
            "text_suspicion_score": 0.95,
            "source_credibility_score": 0.1,
            "research_dossier": {
                "wikipedia_summary": "Earth is the third planet from the Sun and the only astronomical object known to harbor life.",
                "web_snippets": [
                    "NASA evidence for spherical Earth",
                    "Ships disappearing hull-first over horizon proves Earth is round"
                ]
            }
        }
        
        # Create a sample task
        task = AgentTask(
            task_id="test_investigation_task_001",
            agent_type="InvestigatorAgent",
            priority=TaskPriority.HIGH,
            payload={
                "case_file_json": json.dumps(sample_case_file)
            },
            created_at=datetime.now()
        )
        
        # Process the task
        import asyncio
        result = asyncio.run(investigator_agent.process_task(task))
        logger.info(f"InvestigatorAgent result: {result}")
        
        logger.info("InvestigatorAgent test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing InvestigatorAgent: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Comprehensive Component Test Script ===")
    
    # Load environment variables
    logger.info("Loading environment variables from .env file...")
    
    # Test all components
    logger.info("\n1. Testing ML Models...")
    ml_success, vectorizer, classifier = test_ml_models()
    
    logger.info("\n2. Testing Mock Analysis...")
    mock_success = test_mock_analysis()
    
    logger.info("\n3. Testing Analyst Agent...")
    analyst_success = test_analyst_agent()
    
    logger.info("\n4. Testing Investigator Agent...")
    investigator_success = test_investigator_agent()
    
    logger.info("\n5. Testing Gemini API...")
    gemini_success, model = test_gemini_api()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"ML Models: {'PASS' if ml_success else 'FAIL'}")
    logger.info(f"Mock Analysis: {'PASS' if mock_success else 'FAIL'}")
    logger.info(f"Analyst Agent: {'PASS' if analyst_success else 'FAIL'}")
    logger.info(f"Investigator Agent: {'PASS' if investigator_success else 'FAIL'}")
    logger.info(f"Gemini API: {'PASS' if gemini_success else 'FAIL (Using Mock)'}")
    
    if all([ml_success, mock_success, analyst_success, investigator_success]):
        logger.info("\nAll core tests passed! The system is ready to use.")
    else:
        logger.warning("\nSome tests failed. Please check the logs above for details.")