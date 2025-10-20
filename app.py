import os
import json
import asyncio
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import joblib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Import agent logic functions and variables
from source_profiler import calculate_source_score
from research_agent import gather_evidence
from prompts import INVESTIGATOR_MANDATE, HERALD_PROTOCOL
from websocket_manager import ConnectionManager

# Define Pydantic Response Models
class UpdateResponse(BaseModel):
    verification_id: int
    raw_claim_id: int
    verification_status: str
    explanation: str
    dossier: Optional[dict]
    timestamp_verified: datetime


class LogResponse(BaseModel):
    log_id: int
    timestamp: datetime
    log_message: str


# Initialize FastAPI app
app = FastAPI(
    title="Project Aegis Backend",
    description="Backend API for Project Aegis OSINT and threat analysis system",
    version="1.0.0"
)

# Configure CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for Supabase client and ML models
supabase_client: Client = None
vectorizer = None
classifier = None
# Initialize the WebSocket connection manager
websocket_manager = ConnectionManager()

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def analyst_agent(claim_text: str) -> float:
    """
    Analyze claim text and predict probability of being "fake" (class 0).
    
    Args:
        claim_text (str): The text claim to analyze
        
    Returns:
        float: Probability of the text being fake (0.0-1.0)
    """
    global vectorizer, classifier
    
    logger.info(f"[Analyst Agent] Analyzing claim: {claim_text[:50]}...")
    
    if vectorizer is None or classifier is None:
        logger.warning("Warning: ML models not loaded")
        return 0.5  # Return neutral score if models not available
    
    try:
        # Vectorize the claim text
        claim_vector = vectorizer.transform([claim_text])
        logger.debug(f"[Analyst Agent] Claim vectorized successfully")
        
        # Predict probability for class 0 (fake)
        fake_probability = classifier.predict_proba(claim_vector)[0][0]
        logger.info(f"[Analyst Agent] Text suspicion score: {fake_probability:.4f}")
        
        return float(fake_probability)
    except Exception as e:
        logger.error(f"[Analyst Agent] Error: {e}")
        return 0.5  # Return neutral score on error


# The old scout_agent function has been removed to prevent hardcoded claims
# The new ScoutAgent class is now used instead


def investigator_agent(case_file: dict) -> dict:
    """
    Investigate a case file using the Investigator agent logic.
    
    Args:
        case_file (dict): The case file containing claim and evidence
        
    Returns:
        dict: The investigation results as a dictionary
    """
    logger.info("[Investigator Agent] Analyzing case file...")
    logger.debug(f"[Investigator Agent] Case file: {json.dumps(case_file, indent=2)[:200]}...")
    
    # In a real implementation, this would call the Gemini API
    # For now, we'll return a mock response based on the case file
    
    # Mock implementation based on case file content
    claim_text = case_file.get("claim_text", "")
    text_suspicion_score = case_file.get("text_suspicion_score", 0.5)
    source_credibility_score = case_file.get("source_credibility_score", 0.5)
    research_dossier = case_file.get("research_dossier", {})
    
    logger.info(f"[Investigator Agent] Scores - Text: {text_suspicion_score:.4f}, Source: {source_credibility_score:.4f}")
    
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
    
    logger.info(f"[Investigator Agent] Verdict: {verdict}, Confidence: {confidence:.2f}")
    return result


def herald_agent(investigator_report: dict) -> str:
    """
    Generate a public alert based on the investigator's report.
    
    Args:
        investigator_report (dict): The report from the investigator agent
        
    Returns:
        str: Formatted public alert string
    """
    logger.info("[Herald Agent] Generating public alert...")
    logger.debug(f"[Herald Agent] Report: {json.dumps(investigator_report, indent=2)}")
    
    verdict = investigator_report.get("verdict", "Misleading")
    confidence = investigator_report.get("confidence", 0.5)
    reasoning = investigator_report.get("reasoning", "No reasoning provided")
    
    # Select appropriate emoji based on verdict
    if verdict == "True":
        emoji = "🟢"
    elif verdict == "False":
        emoji = "🔴"
    else:  # Misleading
        emoji = "🟡"
    
    # Generate public alert message
    if verdict == "True":
        message = f"This information has been verified as accurate. {reasoning} Our confidence level is {confidence*100:.0f}%."
    elif verdict == "False":
        message = f"This information has been confirmed as false. {reasoning} Our confidence level is {confidence*100:.0f}%."
    else:  # Misleading
        message = f"This information may be misleading. {reasoning} Our confidence level is {confidence*100:.0f}%."
    
    alert = f"{emoji} {message}"
    logger.info(f"[Herald Agent] Alert generated: {alert[:50]}...")
    return alert


# The old coordinator_loop function has been removed
# The new CoordinatorAgent class is now used instead


@app.on_event("startup")
async def startup_event():
    """Initialize Supabase client and load ML models on startup"""
    global supabase_client, vectorizer, classifier
    
    logger.info("=== PROJECT AEGIS STARTUP ===")
    
    # Initialize Supabase client
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        try:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            logger.info("Supabase client initialized successfully")
            logger.info(f"Supabase URL: {SUPABASE_URL}")
            
            # Test Supabase connection
            try:
                response = supabase_client.table("events").select("event_id").limit(1).execute()
                logger.info("Supabase connection test successful")
            except Exception as e:
                logger.error(f"Supabase connection test failed: {e}")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
    else:
        logger.warning("Warning: Supabase credentials not found in environment variables")
    
    # Load ML models
    try:
        vectorizer = joblib.load("vectorizer.pkl")
        classifier = joblib.load("classifier.pkl")
        logger.info("ML models loaded successfully")
    except FileNotFoundError:
        logger.warning("Warning: vectorizer.pkl or classifier.pkl not found")
    except Exception as e:
        logger.error(f"Error loading ML models: {e}")
    
    # Check Gemini API key
    if GEMINI_API_KEY:
        logger.info("Gemini API key found in environment variables")
        logger.info(f"Gemini API key (first 10 chars): {GEMINI_API_KEY[:10]}...")
    else:
        logger.warning("Warning: Gemini API key not found in environment variables")
    
    # The new agentic framework will be started by the backend app


@app.get("/")
async def health_check():
    """Health check endpoint to verify server is running"""
    logger.info("Health check endpoint called")
    return {"status": "Project Aegis backend is running"}


@app.get("/updates", response_model=List[UpdateResponse])
async def get_updates():
    """Get the 20 most recent verified claims for the public dashboard"""
    global supabase_client
    
    logger.info("Get updates endpoint called")
    
    if supabase_client is None:
        logger.error("Supabase client not initialized")
        return {"error": "Supabase client not initialized"}
    
    try:
        # Query the verified_claims table
        response = (supabase_client.table("verified_claims")
                   .select("verification_id, raw_claim_id, verification_status, explanation, dossier, timestamp_verified")
                   .order("timestamp_verified", desc=True)
                   .limit(20)
                   .execute())
        
        # Transform the data to match the UpdateResponse model
        updates = []
        for item in response.data:
            update = UpdateResponse(
                verification_id=item.get("verification_id", 0),
                raw_claim_id=item.get("raw_claim_id", 0),
                verification_status=item.get("verification_status", "Unknown"),
                explanation=item.get("explanation", ""),
                dossier=item.get("dossier", None),
                timestamp_verified=item.get("timestamp_verified", datetime.now())
            )
            updates.append(update)
        
        logger.info(f"Returning {len(updates)} verified claims")
        return updates
    except Exception as e:
        logger.error(f"Error fetching updates: {e}")
        return {"error": "Failed to fetch updates"}


@app.get("/agent-status", response_model=List[LogResponse])
async def get_agent_status():
    """Get the 10 most recent agent status logs for the public dashboard"""
    global supabase_client
    
    logger.info("Get agent status endpoint called")
    
    if supabase_client is None:
        logger.error("Supabase client not initialized")
        return {"error": "Supabase client not initialized"}
    
    try:
        # Query the system_logs table
        response = (supabase_client.table("system_logs")
                   .select("log_id, timestamp, log_message")
                   .order("timestamp", desc=True)
                   .limit(10)
                   .execute())
        
        # Transform the data to match the LogResponse model
        logs = []
        for item in response.data:
            log = LogResponse(
                log_id=item.get("log_id", 0),
                timestamp=item.get("timestamp", datetime.now()),
                log_message=item.get("log_message", "")
            )
            logs.append(log)
        
        logger.info(f"Returning {len(logs)} agent status logs")
        return logs
    except Exception as e:
        logger.error(f"Error fetching agent status: {e}")
        return {"error": "Failed to fetch agent status"}


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    logger.info("New WebSocket connection request")
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Keep the connection alive
            data = await websocket.receive_text()
            # Echo the message back (optional)
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        logger.info(f"WebSocket connection closed: {e}")
    finally:
        websocket_manager.disconnect(websocket)
        logger.info("WebSocket connection removed")


# Example endpoint to demonstrate Supabase integration
@app.get("/test-db")
async def test_database():
    """Test endpoint to verify Supabase connection"""
    if supabase_client is None:
        return {"error": "Supabase client not initialized"}
    
    try:
        # Test query on events table
        response = supabase_client.table("events").select("event_id, event_name").limit(1).execute()
        return {"status": "Database connection successful", "data": response.data}
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}


# Demo Injection Endpoint
class DemoClaim(BaseModel):
    claim_text: str
    source_metadata_json: str


@app.post("/seed-demo-claim")
async def seed_demo_claim(claim: DemoClaim):
    """Insert a demo claim directly into the raw_claims table to trigger agent processing"""
    global supabase_client
    
    if supabase_client is None:
        return {"error": "Supabase client not initialized"}
    
    try:
        # Get the default event ID (assuming there's at least one event)
        event_response = supabase_client.table("events").select("event_id").limit(1).execute()
        if not event_response.data:
            return {"error": "No events found in database"}
        
        default_event_id = event_response.data[0]["event_id"]
        
        # Insert the demo claim into raw_claims table with status='pending_initial_analysis'
        claim_data = {
            "event_id": default_event_id,
            "claim_text": claim.claim_text,
            "source_metadata_json": claim.source_metadata_json,
            "status": "pending_initial_analysis"
        }
        
        response = supabase_client.table("raw_claims").insert(claim_data).execute()
        
        # Log this action
        log_entry = {
            "log_message": f"Demo claim injected: {claim.claim_text[:50]}..."
        }
        supabase_client.table("system_logs").insert(log_entry).execute()
        
        return {
            "status": "success",
            "message": "Demo claim inserted successfully",
            "claim_id": response.data[0]["claim_id"] if response.data else None
        }
    except Exception as e:
        print(f"Error inserting demo claim: {e}")
        return {"error": f"Failed to insert demo claim: {str(e)}"}

