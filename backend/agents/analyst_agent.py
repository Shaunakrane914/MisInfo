"""
Project Aegis - Analyst Agent
Analyzes claim text using ML models to predict probability of being fake
"""

import logging
from typing import Dict, Any
import joblib
import os

from .base_agent import BaseAgent, AgentTask, AgentStatus, TaskPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Agent responsible for analyzing claim text using ML models"""
    
    def __init__(self, agent_id: str = "analyst_agent_001", model_path: str = "."):
        super().__init__(agent_id, "AnalystAgent")
        self.model_path = model_path
        self.vectorizer = None
        self.classifier = None
        self.load_models()
        
    def load_models(self):
        """Load the ML models from disk"""
        try:
            self.vectorizer = joblib.load(os.path.join(self.model_path, "vectorizer.pkl"))
            self.classifier = joblib.load(os.path.join(self.model_path, "classifier.pkl"))
            logger.info(f"[{self.agent_name}] ML models loaded successfully")
        except FileNotFoundError:
            logger.warning(f"[{self.agent_name}] Warning: vectorizer.pkl or classifier.pkl not found")
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error loading ML models: {e}")
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process a task to analyze claim text.
        
        Args:
            task (AgentTask): The task containing the claim text to analyze
            
        Returns:
            Dict[str, Any]: The analysis results including suspicion score
        """
        logger.info(f"[{self.agent_name}] Processing analysis task {task.task_id}")
        
        # Extract claim text from payload
        claim_text = task.payload.get("claim_text", "")
        
        if not claim_text:
            raise ValueError("No claim text provided in task payload")
        
        logger.info(f"[{self.agent_name}] Analyzing claim: {claim_text[:50]}...")
        
        # Return neutral score if models not available
        if self.vectorizer is None or self.classifier is None:
            logger.warning(f"[{self.agent_name}] Warning: ML models not loaded, returning neutral score")
            return {
                "claim_text": claim_text,
                "text_suspicion_score": 0.5,
                "analysis_timestamp": task.created_at.isoformat()
            }
        
        try:
            # Vectorize the claim text
            claim_vector = self.vectorizer.transform([claim_text])
            logger.debug(f"[{self.agent_name}] Claim vectorized successfully")
            
            # Predict probability for class 0 (fake)
            fake_probability = self.classifier.predict_proba(claim_vector)[0][0]
            logger.info(f"[{self.agent_name}] Text suspicion score: {fake_probability:.4f}")
            
            return {
                "claim_text": claim_text,
                "text_suspicion_score": float(fake_probability),
                "analysis_timestamp": task.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error during analysis: {e}")
            # Return neutral score on error
            return {
                "claim_text": claim_text,
                "text_suspicion_score": 0.5,
                "error": str(e),
                "analysis_timestamp": task.created_at.isoformat()
            }


# Example usage
if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    
    async def main():
        # Create the analyst agent
        analyst_agent = AnalystAgent()
        
        # Create a sample task
        task = AgentTask(
            task_id="analysis_task_001",
            agent_type="AnalystAgent",
            priority=TaskPriority.NORMAL,
            payload={
                "claim_text": "This is a test claim to analyze for misinformation"
            },
            created_at=datetime.now()
        )
        
        # Process the task
        result = await analyst_agent.process_task(task)
        print("Analyst Agent Result:")
        print(result)
    
    # Run the example
    asyncio.run(main())