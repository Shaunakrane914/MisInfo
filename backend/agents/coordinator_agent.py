"""
Project Aegis - Coordinator Agent
Manages the workflow between all agents in the fact-checking pipeline
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4

from .base_agent import AgentCoordinator, AgentTask, TaskPriority
from .scout_agent import ScoutAgent
from .analyst_agent import AnalystAgent
from .research_agent import ResearchAgent
from .source_profiler_agent import SourceProfilerAgent
from .investigator_agent import InvestigatorAgent
from .herald_agent import HeraldAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """Agent responsible for coordinating the entire fact-checking workflow"""
    
    def __init__(self, supabase_client=None, model_path=".", websocket_manager=None,
                 scout_agent=None, analyst_agent=None, research_agent=None, 
                 source_agent=None, investigator_agent=None, herald_agent=None):
        self.supabase_client = supabase_client
        self.model_path = model_path
        self.websocket_manager = websocket_manager
        self.coordinator = AgentCoordinator()
        
        # Initialize all agents (use provided agents or create new ones)
        self.scout_agent = scout_agent or ScoutAgent()
        self.analyst_agent = analyst_agent or AnalystAgent(model_path=model_path)
        self.research_agent = research_agent or ResearchAgent()
        self.source_profiler_agent = source_agent or SourceProfilerAgent()
        self.investigator_agent = investigator_agent or InvestigatorAgent()
        self.herald_agent = herald_agent or HeraldAgent()
        
        # Register all agents with the coordinator
        self.coordinator.register_agent(self.scout_agent)
        self.coordinator.register_agent(self.analyst_agent)
        self.coordinator.register_agent(self.research_agent)
        self.coordinator.register_agent(self.source_profiler_agent)
        self.coordinator.register_agent(self.investigator_agent)
        self.coordinator.register_agent(self.herald_agent)
        
        logger.info("CoordinatorAgent initialized with all agents registered")
    
    def generate_task_id(self) -> str:
        """Generate a unique task ID"""
        return f"task_{uuid4().hex[:8]}"
    
    async def start(self):
        """Start the coordinator loop"""
        logger.info("Coordinator loop started...")
        
        # Get or create an active event
        active_event_id = await self.get_or_create_active_event()
        
        while True:
            try:
                # Wait for 30 seconds before next cycle
                await asyncio.sleep(30)
                logger.info("Coordinator loop running...")
                
                # Run a cycle of the coordinator agent
                results = await self.run_cycle(active_event_id)
                
                # Broadcast results to WebSocket connections if manager is available
                if results and self.websocket_manager:
                    message = {
                        "type": "claim_updates",
                        "count": len(results),
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.websocket_manager.broadcast(message)
                    
            except Exception as e:
                logger.error(f"[Coordinator] Error in coordinator loop: {e}")
                await asyncio.sleep(5)  # Short delay before retrying

    async def get_or_create_active_event(self):
        """Get or create an active event for claim processing"""
        if not self.supabase_client:
            return None
            
        try:
            # Check if an active event already exists
            response = self.supabase_client.table("events").select("event_id").eq("status", "active").execute()
            
            if response.data:
                # Use existing active event
                event_id = response.data[0]["event_id"]
                logger.info(f"Using existing active event (ID: {event_id})")
                return event_id
            else:
                # Create a new default event
                event_data = {
                    "event_name": "Live Monitoring",
                    "status": "active"
                }
                response = self.supabase_client.table("events").insert(event_data).execute()
                event_id = response.data[0]["event_id"] if response.data else None
                logger.info(f"Created new active event (ID: {event_id})")
                return event_id
                
        except Exception as e:
            logger.error(f"Error getting or creating active event: {e}")
            return None

    async def discover_claims(self) -> List[Dict[str, Any]]:
        """Discover new claims using the Scout Agent"""
        logger.info("=== DISCOVERY PHASE ===")
        
        task = AgentTask(
            task_id=self.generate_task_id(),
            agent_type="ScoutAgent",
            priority=TaskPriority.NORMAL,
            payload={},
            created_at=datetime.now()
        )
        
        result = await self.scout_agent.process_task(task)
        claims = result.get("claims", [])
        logger.info(f"Discovered {len(claims)} new claims")
        
        return claims
    
    async def analyze_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Perform initial analysis on a claim"""
        logger.info("=== INITIAL ANALYSIS PHASE ===")
        
        claim_text = claim["claim_text"]
        source_metadata_json = claim["source_metadata_json"]
        
        # Analyze text with Analyst Agent
        analyst_task = AgentTask(
            task_id=self.generate_task_id(),
            agent_type="AnalystAgent",
            priority=TaskPriority.NORMAL,
            payload={"claim_text": claim_text},
            created_at=datetime.now()
        )
        
        analyst_result = await self.analyst_agent.process_task(analyst_task)
        text_suspicion_score = analyst_result["text_suspicion_score"]
        logger.info(f"Text suspicion score: {text_suspicion_score:.4f}")
        
        # Profile source with Source Profiler Agent
        profiler_task = AgentTask(
            task_id=self.generate_task_id(),
            agent_type="SourceProfilerAgent",
            priority=TaskPriority.NORMAL,
            payload={"source_metadata_json": source_metadata_json},
            created_at=datetime.now()
        )
        
        profiler_result = await self.source_profiler_agent.process_task(profiler_task)
        source_credibility_score = profiler_result["source_credibility_score"]
        logger.info(f"Source credibility score: {source_credibility_score:.4f}")
        
        return {
            "claim_text": claim_text,
            "source_metadata_json": source_metadata_json,
            "text_suspicion_score": text_suspicion_score,
            "source_credibility_score": source_credibility_score
        }
    
    async def gather_evidence(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gather evidence for a claim using the Research Agent"""
        logger.info("=== EVIDENCE GATHERING PHASE ===")
        
        claim_text = claim_data["claim_text"]
        
        research_task = AgentTask(
            task_id=self.generate_task_id(),
            agent_type="ResearchAgent",
            priority=TaskPriority.NORMAL,
            payload={"claim_text": claim_text},
            created_at=datetime.now()
        )
        
        research_result = await self.research_agent.process_task(research_task)
        research_dossier = research_result["research_dossier"]
        logger.info(f"Evidence gathered: {len(research_dossier.get('web_snippets', []))} web results")
        
        claim_data["research_dossier"] = research_dossier
        return claim_data
    
    async def investigate_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Investigate a claim using the Investigator Agent"""
        logger.info("=== INVESTIGATION PHASE ===")
        
        # Create case file for investigator
        case_file = {
            "claim_text": claim_data["claim_text"],
            "text_suspicion_score": claim_data["text_suspicion_score"],
            "source_credibility_score": claim_data["source_credibility_score"],
            "research_dossier": claim_data["research_dossier"]
        }
        
        investigator_task = AgentTask(
            task_id=self.generate_task_id(),
            agent_type="InvestigatorAgent",
            priority=TaskPriority.HIGH,
            payload={"case_file_json": json.dumps(case_file)},
            created_at=datetime.now()
        )
        
        investigator_result = await self.investigator_agent.process_task(investigator_task)
        investigation_result = investigator_result["investigation_result"]
        logger.info(f"Investigation verdict: {investigation_result['verdict']}")
        
        claim_data["investigation_result"] = investigation_result
        return claim_data
    
    async def generate_alert(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate public alert using the Herald Agent"""
        logger.info("=== ALERT GENERATION PHASE ===")
        
        investigation_result = claim_data["investigation_result"]
        
        herald_task = AgentTask(
            task_id=self.generate_task_id(),
            agent_type="HeraldAgent",
            priority=TaskPriority.NORMAL,
            payload={"investigator_report_json": json.dumps(investigation_result)},
            created_at=datetime.now()
        )
        
        herald_result = await self.herald_agent.process_task(herald_task)
        public_alert = herald_result["public_alert"]
        logger.info(f"Public alert generated: {public_alert[:50]}...")
        
        claim_data["public_alert"] = public_alert
        return claim_data
    
    async def process_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single claim through the entire pipeline"""
        logger.info(f"Processing claim: {claim['claim_text'][:50]}...")
        
        # Initial analysis
        claim_data = await self.analyze_claim(claim)
        
        # If scores indicate high risk, gather evidence
        text_suspicion_score = claim_data["text_suspicion_score"]
        source_credibility_score = claim_data["source_credibility_score"]
        
        if text_suspicion_score > 0.3 or source_credibility_score < 0.7:
            # Gather evidence
            claim_data = await self.gather_evidence(claim_data)
            
            # Investigate claim
            claim_data = await self.investigate_claim(claim_data)
            
            # Generate public alert
            claim_data = await self.generate_alert(claim_data)
        else:
            # Low risk claim, archive it
            claim_data["status"] = "archived"
            logger.info("Low risk claim archived without further investigation")
        
        return claim_data
    
    async def run_cycle(self, event_id=None):
        """Run a single cycle of the coordinator loop"""
        try:
            logger.info("Coordinator cycle started")
            
            # Discovery phase
            new_claims = await self.discover_claims()
            
            # Process each claim
            processed_claims = []
            for claim in new_claims:
                try:
                    processed_claim = await self.process_claim(claim)
                    processed_claims.append(processed_claim)
                    
                    # If using Supabase, save results to database
                    if self.supabase_client:
                        await self.save_claim_results(processed_claim, event_id)
                        
                except Exception as e:
                    logger.error(f"Error processing claim: {e}")
                    continue
            
            logger.info(f"Coordinator cycle completed. Processed {len(processed_claims)} claims")
            return processed_claims
            
        except Exception as e:
            logger.error(f"Error in coordinator cycle: {e}")
            return []

    async def save_claim_results(self, claim_data: Dict[str, Any], event_id: int = None):
        """Save claim results to Supabase database"""
        if not self.supabase_client:
            return
        
        try:
            # Save to raw_claims table with analysis results
            claim_record = {
                "event_id": event_id,
                "claim_text": claim_data["claim_text"],
                "source_metadata_json": claim_data["source_metadata_json"],
                "text_suspicion_score": claim_data["text_suspicion_score"],
                "source_credibility_score": claim_data["source_credibility_score"],
                "research_dossier_json": json.dumps(claim_data.get("research_dossier", {})),
                "status": claim_data.get("status", "processed")
            }
            
            response = self.supabase_client.table("raw_claims").insert(claim_record).execute()
            claim_id = response.data[0]["claim_id"] if response.data else None
            
            # If investigation was performed, save to verified_claims table
            if "investigation_result" in claim_data and claim_id:
                verification_record = {
                    "raw_claim_id": claim_id,
                    "verification_status": claim_data["investigation_result"]["verdict"],
                    "explanation": claim_data["investigation_result"]["reasoning"],
                    "dossier": {
                        "claim_text": claim_data["claim_text"],
                        "text_suspicion_score": claim_data["text_suspicion_score"],
                        "source_credibility_score": claim_data["source_credibility_score"],
                        "research_dossier": claim_data.get("research_dossier", {})
                    }
                }
                
                self.supabase_client.table("verified_claims").insert(verification_record).execute()
            
            # Log the action
            log_entry = {
                "log_message": f"Claim processed and saved: {claim_data['claim_text'][:50]}..."
            }
            self.supabase_client.table("system_logs").insert(log_entry).execute()
            
            logger.info(f"Claim results saved to database (ID: {claim_id})")
            
        except Exception as e:
            logger.error(f"Error saving claim results to database: {e}")


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create the coordinator agent
        coordinator_agent = CoordinatorAgent()
        
        # Run a single cycle
        results = await coordinator_agent.run_cycle()
        print(f"Processed {len(results)} claims")
        
        # Print results
        for i, result in enumerate(results):
            print(f"\n--- Claim {i+1} Results ---")
            print(f"Claim: {result['claim_text'][:50]}...")
            print(f"Text Suspicion Score: {result['text_suspicion_score']:.4f}")
            print(f"Source Credibility Score: {result['source_credibility_score']:.4f}")
            if "investigation_result" in result:
                print(f"Verdict: {result['investigation_result']['verdict']}")
                print(f"Confidence: {result['investigation_result']['confidence']:.2f}")
            if "public_alert" in result:
                print(f"Alert: {result['public_alert']}")
    
    # Run the example
    asyncio.run(main())