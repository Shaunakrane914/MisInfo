"""
Project Aegis - Scout Agent
Discovers new claims for fact-checking
"""

import json
import logging
from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentTask, AgentStatus, TaskPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScoutAgent(BaseAgent):
    """Agent responsible for discovering new claims"""
    
    def __init__(self, agent_id: str = "scout_agent_001"):
        super().__init__(agent_id, "ScoutAgent")
        
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process a task to discover new claims.
        
        Args:
            task (AgentTask): The task to process
            
        Returns:
            Dict[str, Any]: The discovered claims
        """
        logger.info(f"[{self.agent_name}] Processing discovery task {task.task_id}")
        
        # For demo purposes, return sample claims
        # In a real implementation, this would connect to social media APIs, news feeds, etc.
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
        
        logger.info(f"[{self.agent_name}] Found {len(sample_claims)} sample claims")
        
        return {
            "claims": sample_claims,
            "discovery_timestamp": task.created_at.isoformat()
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    
    async def main():
        # Create the scout agent
        scout_agent = ScoutAgent()
        
        # Create a sample task
        task = AgentTask(
            task_id="discovery_task_001",
            agent_type="ScoutAgent",
            priority=TaskPriority.NORMAL,
            payload={},
            created_at=datetime.now()
        )
        
        # Process the task
        result = await scout_agent.process_task(task)
        print("Scout Agent Result:")
        print(json.dumps(result, indent=2))
    
    # Run the example
    asyncio.run(main())