#!/usr/bin/env python3
"""
Debug script to test all components of Project Aegis
"""

import os
import json
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if all required environment variables are set"""
    logger.info("=== Testing Environment Variables ===")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if supabase_url:
        logger.info("✅ SUPABASE_URL is set")
        logger.info(f"   URL: {supabase_url}")
    else:
        logger.error("❌ SUPABASE_URL is not set")
    
    if supabase_key:
        logger.info("✅ SUPABASE_SERVICE_ROLE_KEY is set")
        logger.info(f"   Key (first 10 chars): {supabase_key[:10]}...")
    else:
        logger.error("❌ SUPABASE_SERVICE_ROLE_KEY is not set")
    
    if gemini_key:
        logger.info("✅ GEMINI_API_KEY is set")
        logger.info(f"   Key (first 10 chars): {gemini_key[:10]}...")
    else:
        logger.warning("⚠️  GEMINI_API_KEY is not set (optional for current implementation)")
    
    return supabase_url, supabase_key

def test_supabase_connection(supabase_url, supabase_key):
    """Test Supabase connection"""
    logger.info("=== Testing Supabase Connection ===")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ Cannot test Supabase connection - missing credentials")
        return None
    
    try:
        supabase_client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client created successfully")
        
        # Test query
        response = supabase_client.table("events").select("event_id, event_name").limit(1).execute()
        logger.info("✅ Supabase query successful")
        logger.info(f"   Sample data: {response.data}")
        
        return supabase_client
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        return None

def test_ml_models():
    """Test ML models loading"""
    logger.info("=== Testing ML Models ===")
    
    try:
        vectorizer = joblib.load("vectorizer.pkl")
        logger.info("✅ Vectorizer loaded successfully")
        logger.info(f"   Vectorizer type: {type(vectorizer)}")
    except FileNotFoundError:
        logger.error("❌ vectorizer.pkl not found")
        vectorizer = None
    except Exception as e:
        logger.error(f"❌ Error loading vectorizer: {e}")
        vectorizer = None
    
    try:
        classifier = joblib.load("classifier.pkl")
        logger.info("✅ Classifier loaded successfully")
        logger.info(f"   Classifier type: {type(classifier)}")
        logger.info(f"   Classifier classes: {getattr(classifier, 'classes_', 'Unknown')}")
    except FileNotFoundError:
        logger.error("❌ classifier.pkl not found")
        classifier = None
    except Exception as e:
        logger.error(f"❌ Error loading classifier: {e}")
        classifier = None
    
    return vectorizer, classifier

def test_agents():
    """Test agent functions"""
    logger.info("=== Testing Agent Functions ===")
    
    # Test source profiler
    try:
        from source_profiler import calculate_source_score
        
        test_metadata = {
            'account_age_days': 1825,
            'followers': 2500000,
            'following': 150,
            'is_verified': True
        }
        
        score = calculate_source_score(test_metadata)
        logger.info("✅ Source Profiler Agent working")
        logger.info(f"   Test score: {score:.4f}")
    except Exception as e:
        logger.error(f"❌ Source Profiler Agent failed: {e}")
    
    # Test research agent
    try:
        from research_agent import gather_evidence
        
        test_claim = "The Earth is flat"
        evidence = gather_evidence(test_claim)
        logger.info("✅ Research Agent working")
        logger.info(f"   Evidence keys: {list(evidence.keys())}")
        logger.info(f"   Wikipedia summary present: {'Yes' if evidence.get('wikipedia_summary') else 'No'}")
        logger.info(f"   Web snippets count: {len(evidence.get('web_snippets', []))}")
    except Exception as e:
        logger.error(f"❌ Research Agent failed: {e}")

def test_analyst_agent(vectorizer, classifier):
    """Test analyst agent function"""
    logger.info("=== Testing Analyst Agent ===")
    
    if not vectorizer or not classifier:
        logger.warning("⚠️  Skipping Analyst Agent test - ML models not loaded")
        return
    
    try:
        # Import the analyst_agent function
        import app
        test_claim = "This is a test claim to analyze"
        score = app.analyst_agent(test_claim)
        logger.info("✅ Analyst Agent working")
        logger.info(f"   Test score: {score:.4f}")
    except Exception as e:
        logger.error(f"❌ Analyst Agent failed: {e}")

def main():
    """Main debug function"""
    logger.info("Project Aegis - Component Debug Script")
    logger.info("=" * 50)
    
    # Test environment variables
    supabase_url, supabase_key = test_environment_variables()
    
    # Test Supabase connection
    supabase_client = test_supabase_connection(supabase_url, supabase_key)
    
    # Test ML models
    vectorizer, classifier = test_ml_models()
    
    # Test agents
    test_agents()
    
    # Test analyst agent
    test_analyst_agent(vectorizer, classifier)
    
    logger.info("=" * 50)
    logger.info("Debug script completed")

if __name__ == "__main__":
    main()