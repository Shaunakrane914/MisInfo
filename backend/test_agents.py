"""
Project Aegis - Agent Testing Script
Simple test to demonstrate the new agentic framework
"""

import asyncio
import json
from datetime import datetime
from agents.base_agent import AgentTask, TaskPriority
from agents.scout_agent import ScoutAgent
from agents.analyst_agent import AnalystAgent
from agents.research_agent import ResearchAgent


async def main():
    print("Project Aegis - Agentic Framework Demo")
    print("=" * 40)
    
    # Initialize agents
    scout_agent = ScoutAgent()
    analyst_agent = AnalystAgent()
    research_agent = ResearchAgent()
    
    print("\n1. Testing Scout Agent...")
    # Create a discovery task
    scout_task = AgentTask(
        task_id="demo_discovery_001",
        agent_type="ScoutAgent",
        priority=TaskPriority.NORMAL,
        payload={},
        created_at=datetime.now()
    )
    
    # Process the task
    scout_result = await scout_agent.process_task(scout_task)
    claims = scout_result.get("claims", [])
    print(f"   Found {len(claims)} claims")
    
    if claims:
        # Take the first claim for further processing
        claim = claims[0]
        claim_text = claim["claim_text"]
        print(f"   Processing claim: {claim_text[:50]}...")
        
        print("\n2. Testing Analyst Agent...")
        # Analyze the claim
        analyst_task = AgentTask(
            task_id="demo_analysis_001",
            agent_type="AnalystAgent",
            priority=TaskPriority.NORMAL,
            payload={"claim_text": claim_text},
            created_at=datetime.now()
        )
        
        analyst_result = await analyst_agent.process_task(analyst_task)
        suspicion_score = analyst_result["text_suspicion_score"]
        print(f"   Suspicion score: {suspicion_score:.4f}")
        
        print("\n3. Testing Research Agent...")
        # Gather evidence
        research_task = AgentTask(
            task_id="demo_research_001",
            agent_type="ResearchAgent",
            priority=TaskPriority.NORMAL,
            payload={"claim_text": claim_text},
            created_at=datetime.now()
        )
        
        research_result = await research_agent.process_task(research_task)
        dossier = research_result["research_dossier"]
        print(f"   Wikipedia summary: {'Found' if dossier.get('wikipedia_summary') else 'Not found'}")
        print(f"   Web results: {len(dossier.get('web_snippets', []))} links")
        
        print("\n4. Sample Results Summary:")
        print(f"   Claim: {claim_text}")
        print(f"   Suspicion Score: {suspicion_score:.4f}")
        print(f"   Evidence: {len(dossier.get('web_snippets', []))} sources")
    
    print("\n" + "=" * 40)
    print("Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())