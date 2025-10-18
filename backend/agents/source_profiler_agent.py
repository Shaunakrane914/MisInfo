"""
Project Aegis - Source Profiler Agent
Evaluates the credibility of a source based on metadata heuristics
"""

import logging
from typing import Dict, Any
import json

from .base_agent import BaseAgent, AgentTask, AgentStatus, TaskPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SourceProfilerAgent(BaseAgent):
    """Agent responsible for evaluating source credibility based on metadata"""
    
    def __init__(self, agent_id: str = "source_profiler_agent_001"):
        super().__init__(agent_id, "SourceProfilerAgent")
        
    def calculate_source_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate a credibility score for a source based on metadata heuristics.
        
        Args:
            metadata (Dict[str, Any]): A dictionary containing source metadata
            
        Returns:
            float: A credibility score clamped between 0.0 and 1.0
        """
        logger.info(f"[{self.agent_name}] Calculating source credibility score")
        logger.debug(f"[{self.agent_name}] Metadata: {metadata}")
        
        # Start with a neutral base score
        score = 0.5
        logger.debug(f"[{self.agent_name}] Base score: {score}")
        
        # Safely extract metadata with default values
        account_age_days = metadata.get('account_age_days', 0)
        followers = metadata.get('followers', 0)
        following = metadata.get('following', 0)
        is_verified = metadata.get('is_verified', False)
        
        logger.debug(f"[{self.agent_name}] Extracted metadata - Age: {account_age_days}, Followers: {followers}, Following: {following}, Verified: {is_verified}")
        
        # === VERIFIED STATUS ===
        # Verified accounts receive a significant trust bonus
        if is_verified:
            score += 0.4
            logger.debug(f"[{self.agent_name}] Verified account bonus: +0.4, Score: {score}")
        
        # === ACCOUNT AGE ===
        # Very new accounts are suspicious
        if account_age_days < 30:
            score -= 0.25
            logger.debug(f"[{self.agent_name}] New account penalty: -0.25, Score: {score}")
        # Established accounts receive a trust bonus
        elif account_age_days > 365:
            score += 0.1
            logger.debug(f"[{self.agent_name}] Established account bonus: +0.1, Score: {score}")
        
        # === FOLLOWER RATIO ===
        # Analyze the relationship between followers and following
        if following > 0:  # Avoid division by zero
            # Healthy ratio: many more followers than following
            if followers > following * 5:
                score += 0.1
                logger.debug(f"[{self.agent_name}] Healthy follower ratio bonus: +0.1, Score: {score}")
            
            # Suspicious ratio: following many more than followers (potential bot behavior)
            if following > followers * 10 and followers < 1000:
                score -= 0.2
                logger.debug(f"[{self.agent_name}] Suspicious ratio penalty: -0.2, Score: {score}")
        
        # === FOLLOWER COUNT ===
        # Major public figures with large followings
        if followers > 1_000_000:
            score += 0.1
            logger.debug(f"[{self.agent_name}] High follower count bonus: +0.1, Score: {score}")
        
        # === FINAL CLAMPING ===
        # Ensure score stays within valid bounds [0.0, 1.0]
        original_score = score
        score = max(0.0, min(1.0, score))
        if score != original_score:
            logger.debug(f"[{self.agent_name}] Score clamped from {original_score} to {score}")
        
        logger.info(f"[{self.agent_name}] Final credibility score: {score:.4f}")
        return score
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process a task to evaluate source credibility.
        
        Args:
            task (AgentTask): The task containing source metadata to evaluate
            
        Returns:
            Dict[str, Any]: The credibility score and evaluation details
        """
        logger.info(f"[{self.agent_name}] Processing source profiling task {task.task_id}")
        
        # Extract source metadata from payload
        source_metadata_json = task.payload.get("source_metadata_json", "{}")
        
        try:
            source_metadata = json.loads(source_metadata_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in source_metadata_json: {e}")
        
        # Calculate credibility score
        credibility_score = self.calculate_source_score(source_metadata)
        
        return {
            "source_metadata": source_metadata,
            "source_credibility_score": credibility_score,
            "evaluation_timestamp": task.created_at.isoformat()
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    
    async def main():
        # Create the source profiler agent
        source_profiler_agent = SourceProfilerAgent()
        
        # Create a sample task with credible source metadata
        credible_metadata = {
            'account_age_days': 1825,      # 5 years old
            'followers': 2_500_000,         # 2.5M followers
            'following': 150,               # Following only 150
            'is_verified': True             # Verified account
        }
        
        task = AgentTask(
            task_id="profiling_task_001",
            agent_type="SourceProfilerAgent",
            priority=TaskPriority.NORMAL,
            payload={
                "source_metadata_json": json.dumps(credible_metadata)
            },
            created_at=datetime.now()
        )
        
        # Process the task
        result = await source_profiler_agent.process_task(task)
        print("Source Profiler Agent Result:")
        print(result)
    
    # Run the example
    asyncio.run(main())