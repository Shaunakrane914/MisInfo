"""
Project Aegis - Investigator Agent
Expert fact-checking agent that analyzes evidence and makes final determinations
"""

import logging
from typing import Dict, Any
import json
import os

from .base_agent import BaseAgent, AgentTask, AgentStatus, TaskPriority
from backend.prompts import INVESTIGATOR_MANDATE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvestigatorAgent(BaseAgent):
    """Agent responsible for expert fact-checking analysis"""
    
    def __init__(self, agent_id: str = "investigator_agent_001", gemini_api_key: str = None):
        super().__init__(agent_id, "InvestigatorAgent")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.use_gemini = self.gemini_api_key is not None
        
        if self.use_gemini:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                # Use a more stable model name
                self.model = genai.GenerativeModel('gemini-2.5-pro')
                logger.info(f"[{self.agent_name}] Gemini API configured successfully")
            except ImportError:
                logger.warning(f"[{self.agent_name}] Google Generative AI library not installed, using mock implementation")
                self.use_gemini = False
            except Exception as e:
                logger.error(f"[{self.agent_name}] Error configuring Gemini API: {e}")
                self.use_gemini = False
        else:
            logger.info(f"[{self.agent_name}] No Gemini API key found, using mock implementation")
    
    async def analyze_with_gemini(self, case_file: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a case file using the Gemini API.
        
        Args:
            case_file (Dict[str, Any]): The case file containing claim and evidence
            
        Returns:
            Dict[str, Any]: The analysis results from Gemini
        """
        if not self.use_gemini:
            raise RuntimeError("Gemini API not configured")
        
        try:
            # Format the case file as JSON for the prompt
            case_file_json = json.dumps(case_file, indent=2)
            
            # Create the full prompt
            prompt = f"{INVESTIGATOR_MANDATE}\n\nCASE FILE:\n{case_file_json}"
            
            logger.info(f"[{self.agent_name}] Sending case to Gemini for analysis")
            
            # Call the Gemini API
            response = await self.model.generate_content_async(prompt)
            
            # Parse the JSON response
            result = json.loads(response.text)
            
            logger.info(f"[{self.agent_name}] Gemini analysis completed successfully")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"[{self.agent_name}] Error parsing Gemini response as JSON: {e}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error during Gemini analysis: {e}")
            raise RuntimeError(f"Gemini analysis failed: {e}")
    
    def analyze_with_mock(self, case_file: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock analysis implementation for demonstration purposes.
        
        Args:
            case_file (Dict[str, Any]): The case file containing claim and evidence
            
        Returns:
            Dict[str, Any]: The mock analysis results
        """
        logger.info(f"[{self.agent_name}] Using mock analysis implementation")
        
        # Extract key information from case file
        claim_text = case_file.get("claim_text", "")
        text_suspicion_score = case_file.get("text_suspicion_score", 0.5)
        source_credibility_score = case_file.get("source_credibility_score", 0.5)
        research_dossier = case_file.get("research_dossier", {})
        
        logger.info(f"[{self.agent_name}] Scores - Text: {text_suspicion_score:.4f}, Source: {source_credibility_score:.4f}")
        
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
        
        logger.info(f"[{self.agent_name}] Verdict: {verdict}, Confidence: {confidence:.2f}")
        return result
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process a task to investigate a claim.
        
        Args:
            task (AgentTask): The task containing the case file to investigate
            
        Returns:
            Dict[str, Any]: The investigation results
        """
        logger.info(f"[{self.agent_name}] Processing investigation task {task.task_id}")
        
        # Extract case file from payload
        case_file_json = task.payload.get("case_file_json", "{}")
        
        try:
            case_file = json.loads(case_file_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in case_file_json: {e}")
        
        # Perform analysis using either Gemini or mock implementation
        if self.use_gemini:
            try:
                result = await self.analyze_with_gemini(case_file)
            except Exception as e:
                logger.warning(f"[{self.agent_name}] Gemini analysis failed, falling back to mock: {e}")
                result = self.analyze_with_mock(case_file)
        else:
            result = self.analyze_with_mock(case_file)
        
        return {
            "case_file": case_file,
            "investigation_result": result,
            "investigation_timestamp": task.created_at.isoformat()
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    
    async def main():
        # Create the investigator agent
        investigator_agent = InvestigatorAgent()
        
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
            task_id="investigation_task_001",
            agent_type="InvestigatorAgent",
            priority=TaskPriority.HIGH,
            payload={
                "case_file_json": json.dumps(sample_case_file)
            },
            created_at=datetime.now()
        )
        
        # Process the task
        result = await investigator_agent.process_task(task)
        print("Investigator Agent Result:")
        print(json.dumps(result, indent=2))
    
    # Run the example
    asyncio.run(main())