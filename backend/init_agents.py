"""
Project Aegis - Agent Initialization Script
Initialize and test all agents in the agentic framework
"""

import asyncio
import json
import logging
from datetime import datetime

from agents.scout_agent import ScoutAgent
from agents.analyst_agent import AnalystAgent
from agents.research_agent import ResearchAgent
from agents.source_profiler_agent import SourceProfilerAgent
from agents.investigator_agent import InvestigatorAgent
from agents.herald_agent import HeraldAgent
from agents.coordinator_agent import CoordinatorAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scout_agent():
    """Test the Scout Agent"""
    logger.info("=== Testing Scout Agent ===")
    scout_agent = ScoutAgent()
    
    # Create a sample task
    from agents.base_agent import AgentTask, TaskPriority
    task = AgentTask(
        task_id="test_discovery_001",
        agent_type="ScoutAgent",
        priority=TaskPriority.NORMAL,
        payload={},
        created_at=datetime.now()
    )
    
    try:
        result = await scout_agent.process_task(task)
        logger.info("✅ Scout Agent test passed")
        logger.info(f"   Found {len(result.get('claims', []))} claims")
        return result
    except Exception as e:
        logger.error(f"❌ Scout Agent test failed: {e}")
        return None


async def test_analyst_agent():
    """Test the Analyst Agent"""
    logger.info("=== Testing Analyst Agent ===")
    analyst_agent = AnalystAgent()
    
    # Create a sample task
    from agents.base_agent import AgentTask, TaskPriority
    task = AgentTask(
        task_id="test_analysis_001",
        agent_type="AnalystAgent",
        priority=TaskPriority.NORMAL,
        payload={
            "claim_text": "This is a test claim to analyze for misinformation"
        },
        created_at=datetime.now()
    )
    
    try:
        result = await analyst_agent.process_task(task)
        logger.info("✅ Analyst Agent test passed")
        logger.info(f"   Suspicion score: {result.get('text_suspicion_score', 0.5):.4f}")
        return result
    except Exception as e:
        logger.error(f"❌ Analyst Agent test failed: {e}")
        return None


async def test_research_agent():
    """Test the Research Agent"""
    logger.info("=== Testing Research Agent ===")
    research_agent = ResearchAgent()
    
    # Create a sample task
    from agents.base_agent import AgentTask, TaskPriority
    task = AgentTask(
        task_id="test_research_001",
        agent_type="ResearchAgent",
        priority=TaskPriority.NORMAL,
        payload={
            "claim_text": "The Earth is flat"
        },
        created_at=datetime.now()
    )
    
    try:
        result = await research_agent.process_task(task)
        logger.info("✅ Research Agent test passed")
        dossier = result.get('research_dossier', {})
        logger.info(f"   Wikipedia summary: {'Yes' if dossier.get('wikipedia_summary') else 'No'}")
        logger.info(f"   Web snippets: {len(dossier.get('web_snippets', []))}")
        return result
    except Exception as e:
        logger.error(f"❌ Research Agent test failed: {e}")
        return None


async def test_source_profiler_agent():
    """Test the Source Profiler Agent"""
    logger.info("=== Testing Source Profiler Agent ===")
    source_profiler_agent = SourceProfilerAgent()
    
    # Create sample metadata
    credible_metadata = {
        'account_age_days': 1825,      # 5 years old
        'followers': 2_500_000,         # 2.5M followers
        'following': 150,               # Following only 150
        'is_verified': True             # Verified account
    }
    
    # Create a sample task
    from agents.base_agent import AgentTask, TaskPriority
    task = AgentTask(
        task_id="test_profiling_001",
        agent_type="SourceProfilerAgent",
        priority=TaskPriority.NORMAL,
        payload={
            "source_metadata_json": json.dumps(credible_metadata)
        },
        created_at=datetime.now()
    )
    
    try:
        result = await source_profiler_agent.process_task(task)
        logger.info("✅ Source Profiler Agent test passed")
        logger.info(f"   Credibility score: {result.get('source_credibility_score', 0.5):.4f}")
        return result
    except Exception as e:
        logger.error(f"❌ Source Profiler Agent test failed: {e}")
        return None


async def test_investigator_agent():
    """Test the Investigator Agent"""
    logger.info("=== Testing Investigator Agent ===")
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
    from agents.base_agent import AgentTask, TaskPriority
    task = AgentTask(
        task_id="test_investigation_001",
        agent_type="InvestigatorAgent",
        priority=TaskPriority.HIGH,
        payload={
            "case_file_json": json.dumps(sample_case_file)
        },
        created_at=datetime.now()
    )
    
    try:
        result = await investigator_agent.process_task(task)
        logger.info("✅ Investigator Agent test passed")
        investigation_result = result.get('investigation_result', {})
        logger.info(f"   Verdict: {investigation_result.get('verdict', 'Unknown')}")
        logger.info(f"   Confidence: {investigation_result.get('confidence', 0.0):.2f}")
        return result
    except Exception as e:
        logger.error(f"❌ Investigator Agent test failed: {e}")
        return None


async def test_herald_agent():
    """Test the Herald Agent"""
    logger.info("=== Testing Herald Agent ===")
    herald_agent = HeraldAgent()
    
    # Create a sample investigator report
    sample_report = {
        "verdict": "False",
        "confidence": 0.95,
        "reasoning": "Multiple credible sources contradict this claim, and scientific consensus confirms the opposite."
    }
    
    # Create a sample task
    from agents.base_agent import AgentTask, TaskPriority
    task = AgentTask(
        task_id="test_alert_001",
        agent_type="HeraldAgent",
        priority=TaskPriority.NORMAL,
        payload={
            "investigator_report_json": json.dumps(sample_report)
        },
        created_at=datetime.now()
    )
    
    try:
        result = await herald_agent.process_task(task)
        logger.info("✅ Herald Agent test passed")
        logger.info(f"   Alert: {result.get('public_alert', '')[:50]}...")
        return result
    except Exception as e:
        logger.error(f"❌ Herald Agent test failed: {e}")
        return None


async def test_coordinator_agent():
    """Test the Coordinator Agent"""
    logger.info("=== Testing Coordinator Agent ===")
    coordinator_agent = CoordinatorAgent()
    
    try:
        results = await coordinator_agent.run_cycle()
        logger.info("✅ Coordinator Agent test passed")
        logger.info(f"   Processed {len(results)} claims")
        return results
    except Exception as e:
        logger.error(f"❌ Coordinator Agent test failed: {e}")
        return None


async def main():
    """Main function to test all agents"""
    logger.info("Project Aegis - Agent Initialization and Testing")
    logger.info("=" * 50)
    
    # Test individual agents
    await test_scout_agent()
    await test_analyst_agent()
    await test_research_agent()
    await test_source_profiler_agent()
    await test_investigator_agent()
    await test_herald_agent()
    
    # Test coordinator agent
    await test_coordinator_agent()
    
    logger.info("=" * 50)
    logger.info("All agent tests completed")


if __name__ == "__main__":
    asyncio.run(main())