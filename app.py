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


def scout_agent() -> list:
    """
    Placeholder function for discovering new claims.
    
    Returns:
        list: Hardcoded list of sample claims for demo purposes
    """
    logger.info("[Scout Agent] Discovering new claims...")
    
    sample_claims = [
        {
            "claim_text": "Breaking: Major earthquake hits city center!",
            "source_metadata_json": json.dumps({
                "account_age_days": 15,
                "followers": 50,
                "following": 800,
                "is_verified": False
            })
        },
        {
            "claim_text": "Scientists confirm that drinking water cures all forms of cancer",
            "source_metadata_json": json.dumps({
                "account_age_days": 1825,
                "followers": 2500000,
                "following": 150,
                "is_verified": True
            })
        },
        {
            "claim_text": "New government policy will eliminate all taxes starting next month",
            "source_metadata_json": json.dumps({
                "account_age_days": 180,
                "followers": 5000,
                "following": 800,
                "is_verified": False
            })
        }
    ]
    
    logger.info(f"[Scout Agent] Found {len(sample_claims)} sample claims")
    return sample_claims


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


async def coordinator_loop():
    """
    The autonomous Coordinator loop that manages the entire fact-checking process.
    """
    global supabase_client
    
    if supabase_client is None:
        logger.error("Error: Supabase client not initialized. Coordinator loop cannot start.")
        return
    
    logger.info("Coordinator loop started...")
    
    # Get the default event ID (assuming there's at least one event)
    default_event_id = 2  # Default to the existing event
    try:
        event_response = supabase_client.table("events").select("event_id").limit(1).execute()
        if event_response.data:
            default_event_id = event_response.data[0]["event_id"]
        logger.info(f"Using event_id: {default_event_id}")
    except Exception as e:
        logger.error(f"Error getting event, using default: {e}")
    
    while True:
        try:
            # Wait for 30 seconds before next cycle
            await asyncio.sleep(30)
            logger.info("Coordinator loop running...")
            
            # === DISCOVERY ===
            # Get new claims from scout agent
            logger.info("=== DISCOVERY PHASE ===")
            new_claims = scout_agent()
            
            # Insert new claims into raw_claims table
            for claim in new_claims:
                try:
                    # Insert claim into raw_claims table
                    claim_data = {
                        "event_id": default_event_id,
                        "claim_text": claim["claim_text"],
                        "source_metadata_json": claim["source_metadata_json"],
                        "status": "pending_initial_analysis"
                    }
                    
                    response = supabase_client.table("raw_claims").insert(claim_data).execute()
                    claim_id = response.data[0]["claim_id"] if response.data else None
                    
                    # Log this action
                    if claim_id:
                        log_entry = {
                            "log_message": f"New claim discovered and inserted: {claim['claim_text'][:50]}..."
                        }
                        supabase_client.table("system_logs").insert(log_entry).execute()
                        logger.info(f"[Coordinator] Claim {claim_id} inserted into database")
                        
                except Exception as e:
                    logger.error(f"[Coordinator] Error inserting claim: {e}")
            
            # === INITIAL ANALYSIS ===
            # Find all cases with status='pending_initial_analysis'
            logger.info("=== INITIAL ANALYSIS PHASE ===")
            try:
                response = supabase_client.table("raw_claims").select("*").eq("status", "pending_initial_analysis").execute()
                pending_claims = response.data
                logger.info(f"[Coordinator] Found {len(pending_claims)} claims for initial analysis")
                
                for claim in pending_claims:
                    claim_id = claim["claim_id"]
                    claim_text = claim["claim_text"]
                    source_metadata_json = claim["source_metadata_json"]
                    
                    logger.info(f"[Coordinator] Analyzing claim {claim_id}: {claim_text[:50]}...")
                    
                    # Run analyst_agent on the claim
                    text_suspicion_score = analyst_agent(claim_text)
                    
                    # Calculate source credibility score
                    try:
                        source_metadata = json.loads(source_metadata_json)
                        source_credibility_score = calculate_source_score(source_metadata)
                        logger.info(f"[Coordinator] Source credibility score for claim {claim_id}: {source_credibility_score:.4f}")
                    except Exception as e:
                        logger.error(f"[Coordinator] Error calculating source score: {e}")
                        source_credibility_score = 0.5  # Default neutral score
                    
                    # Update the claim with scores and change status
                    update_data = {
                        "text_suspicion_score": text_suspicion_score,
                        "source_credibility_score": source_credibility_score,
                        "status": "pending_fusion_decision"
                    }
                    
                    supabase_client.table("raw_claims").update(update_data).eq("claim_id", claim_id).execute()
                    logger.info(f"[Coordinator] Claim {claim_id} updated with scores and moved to fusion decision")
                    
            except Exception as e:
                logger.error(f"[Coordinator] Error in initial analysis: {e}")
            
            # === FIRST DECISION POINT (FUSION AGENT) ===
            # Find all cases with status='pending_fusion_decision'
            logger.info("=== FUSION DECISION PHASE ===")
            try:
                response = supabase_client.table("raw_claims").select("*").eq("status", "pending_fusion_decision").execute()
                fusion_claims = response.data
                logger.info(f"[Coordinator] Found {len(fusion_claims)} claims for fusion decision")
                
                for claim in fusion_claims:
                    claim_id = claim["claim_id"]
                    text_suspicion_score = claim.get("text_suspicion_score", 0.5)
                    source_credibility_score = claim.get("source_credibility_score", 0.5)
                    
                    logger.info(f"[Coordinator] Fusion decision for claim {claim_id} - Text: {text_suspicion_score:.4f}, Source: {source_credibility_score:.4f}")
                    
                    # If scores are very low, archive the claim
                    if text_suspicion_score < 0.2 and source_credibility_score > 0.8:
                        update_data = {
                            "status": "archived"
                        }
                        supabase_client.table("raw_claims").update(update_data).eq("claim_id", claim_id).execute()
                        
                        # Log this action
                        log_entry = {
                            "log_message": f"Claim {claim_id} archived due to low suspicion and high credibility scores"
                        }
                        supabase_client.table("system_logs").insert(log_entry).execute()
                        logger.info(f"[Coordinator] Claim {claim_id} archived")
                    else:
                        # Escalate by gathering evidence
                        claim_text = claim["claim_text"]
                        logger.info(f"[Coordinator] Gathering evidence for claim {claim_id}")
                        research_dossier = gather_evidence(claim_text)
                        logger.info(f"[Coordinator] Evidence gathered for claim {claim_id}: {len(research_dossier.get('web_snippets', []))} web results")
                        
                        # Update claim with research dossier and change status
                        update_data = {
                            "research_dossier_json": json.dumps(research_dossier),
                            "status": "pending_final_decision"
                        }
                        
                        supabase_client.table("raw_claims").update(update_data).eq("claim_id", claim_id).execute()
                        
                        # Log this escalation
                        log_entry = {
                            "log_message": f"Claim {claim_id} escalated for research gathering due to moderate/high risk scores"
                        }
                        supabase_client.table("system_logs").insert(log_entry).execute()
                        logger.info(f"[Coordinator] Claim {claim_id} escalated to final decision")
                        
            except Exception as e:
                logger.error(f"[Coordinator] Error in fusion decision: {e}")
            
            # === SECOND DECISION POINT (FUSION AGENT CONTINUED) ===
            # Find all cases with status='pending_final_decision'
            logger.info("=== FINAL DECISION PHASE ===")
            try:
                response = supabase_client.table("raw_claims").select("*").eq("status", "pending_final_decision").execute()
                final_decision_claims = response.data
                logger.info(f"[Coordinator] Found {len(final_decision_claims)} claims for final decision")
                
                for claim in final_decision_claims:
                    claim_id = claim["claim_id"]
                    research_dossier_json = claim.get("research_dossier_json", "{}")
                    claim_text = claim.get("claim_text", "")
                    
                    try:
                        research_dossier = json.loads(research_dossier_json)
                    except Exception as e:
                        logger.error(f"[Coordinator] Error parsing research dossier: {e}")
                        research_dossier = {}
                    
                    # Check if evidence is conclusive
                    wikipedia_summary = research_dossier.get("wikipedia_summary", "")
                    web_snippets = research_dossier.get("web_snippets", [])
                    
                    # Simple logic to determine if evidence is conclusive
                    # In a real implementation, this would be more sophisticated
                    is_conclusive = (
                        wikipedia_summary and 
                        ("not" in wikipedia_summary.lower() or "false" in wikipedia_summary.lower()) and
                        len(web_snippets) > 0
                    )
                    
                    if is_conclusive:
                        # Resolve directly without Gemini
                        # Include the original claim text in the dossier
                        dossier_data = {
                            "claim_text": claim_text,
                            "text_suspicion_score": claim.get("text_suspicion_score", 0.0),
                            "source_credibility_score": claim.get("source_credibility_score", 0.0),
                            "research_dossier": research_dossier
                        }
                        
                        result_data = {
                            "raw_claim_id": claim_id,
                            "verification_status": "False",
                            "explanation": "Wikipedia and web search results strongly contradict the claim",
                            "dossier": dossier_data
                        }
                        
                        # Insert result into verified_claims
                        supabase_client.table("verified_claims").insert(result_data).execute()
                        
                        # Update raw_claims status
                        update_data = {
                            "status": "resolved_by_fusion"
                        }
                        supabase_client.table("raw_claims").update(update_data).eq("claim_id", claim_id).execute()
                        
                        # Log this action
                        log_entry = {
                            "log_message": f"Claim {claim_id} resolved directly by fusion agent based on conclusive evidence"
                        }
                        supabase_client.table("system_logs").insert(log_entry).execute()
                        logger.info(f"[Coordinator] Claim {claim_id} resolved by fusion agent")
                    else:
                        # Escalate to expert (investigator)
                        update_data = {
                            "status": "escalated_to_investigator"
                        }
                        supabase_client.table("raw_claims").update(update_data).eq("claim_id", claim_id).execute()
                        
                        # Log this action
                        log_entry = {
                            "log_message": f"Claim {claim_id} escalated to investigator agent for expert analysis"
                        }
                        supabase_client.table("system_logs").insert(log_entry).execute()
                        logger.info(f"[Coordinator] Claim {claim_id} escalated to investigator")
                        
            except Exception as e:
                logger.error(f"[Coordinator] Error in final decision: {e}")
            
            # === EXPERT CONSULTATION ===
            # Find all cases with status='escalated_to_investigator'
            logger.info("=== EXPERT CONSULTATION PHASE ===")
            try:
                response = supabase_client.table("raw_claims").select("*").eq("status", "escalated_to_investigator").execute()
                expert_claims = response.data
                logger.info(f"[Coordinator] Found {len(expert_claims)} claims for expert consultation")
                
                for claim in expert_claims:
                    claim_id = claim["claim_id"]
                    claim_text = claim["claim_text"]
                    text_suspicion_score = claim.get("text_suspicion_score", 0.5)
                    source_credibility_score = claim.get("source_credibility_score", 0.5)
                    research_dossier_json = claim.get("research_dossier_json", "{}")
                    
                    try:
                        research_dossier = json.loads(research_dossier_json)
                    except Exception as e:
                        logger.error(f"[Coordinator] Error parsing research dossier: {e}")
                        research_dossier = {}
                    
                    # Create case file for investigator
                    case_file = {
                        "claim_text": claim_text,
                        "text_suspicion_score": text_suspicion_score,
                        "source_credibility_score": source_credibility_score,
                        "research_dossier": research_dossier
                    }
                    
                    # Call investigator agent
                    logger.info(f"[Coordinator] Calling investigator agent for claim {claim_id}")
                    investigator_report = investigator_agent(case_file)
                    
                    # Call herald agent
                    logger.info(f"[Coordinator] Calling herald agent for claim {claim_id}")
                    alert_message = herald_agent(investigator_report)
                    
                    # Include the original claim text in the dossier
                    dossier_data = {
                        "claim_text": claim_text,
                        "text_suspicion_score": text_suspicion_score,
                        "source_credibility_score": source_credibility_score,
                        "research_dossier": research_dossier
                    }
                    
                    # Insert final result into verified_claims
                    result_data = {
                        "raw_claim_id": claim_id,
                        "verification_status": investigator_report["verdict"],
                        "explanation": investigator_report["reasoning"],
                        "dossier": dossier_data
                    }
                    
                    supabase_client.table("verified_claims").insert(result_data).execute()
                    logger.info(f"[Coordinator] Verified claim inserted for claim {claim_id}")
                    
                    # Update raw_claims status
                    update_data = {
                        "status": "resolved_by_investigator"
                    }
                    supabase_client.table("raw_claims").update(update_data).eq("claim_id", claim_id).execute()
                    logger.info(f"[Coordinator] Claim {claim_id} marked as resolved")
                    
            except Exception as e:
                logger.error(f"[Coordinator] Error in expert consultation: {e}")
                
        except Exception as e:
            logger.error(f"[Coordinator] Error in coordinator loop: {e}")
            await asyncio.sleep(5)  # Short delay before retrying


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

