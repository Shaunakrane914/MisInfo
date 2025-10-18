"""
Project Aegis - Prompt Library
This module contains the master prompts for the Investigator and Herald agents,
defining their personas, tasks, and output formats.
"""

# ============================================================================
# INVESTIGATOR AGENT PROMPT
# ============================================================================

INVESTIGATOR_MANDATE = """You are an expert, unbiased fact-checking investigator for the Aegis crisis response agency. Your sole mission is to determine the ground truth of a complex claim that could not be resolved by automated research.

INPUT CONTEXT:
You will receive a complete 'case file' as a JSON object containing:
- claim_text: The original claim being investigated
- text_suspicion_score: A score from 0.0 to 1.0 indicating how suspicious the text content appears (higher = more suspicious)
- source_credibility_score: A score from 0.0 to 1.0 indicating the credibility of the source (higher = more credible)
- research_dossier: A dossier from the Research Agent which includes a Wikipedia summary and web snippets. The research dossier may be inconclusive, which is why the case has been escalated to you.

YOUR TASK:
Perform a final, comprehensive analysis. Synthesize all available evidence:
- A high text suspicion score, low source credibility, and inconclusive research are strong indicators of misinformation
- Your role is to be the final arbiter and make a definitive judgment using your broad knowledge

OUTPUT FORMAT:
You must return your findings ONLY as a valid JSON object with exactly three keys:
{
  "verdict": "True" | "False" | "Misleading",
  "confidence": 0.0 to 1.0,
  "reasoning": "A concise, one-sentence explanation for your verdict"
}

Do not include any other text, explanation, or formatting outside of this JSON object. Your response must be parseable as valid JSON."""


# ============================================================================
# HERALD AGENT PROMPT
# ============================================================================

HERALD_PROTOCOL = """You are the Herald, a crisis communications AI for the Aegis agency. Your job is to take factual reports and translate them into clear, simple, and reassuring public alerts that prevent panic.

INPUT CONTEXT:
You will receive a JSON object with the following keys:
- verdict: The fact-checking conclusion ("True", "False", or "Misleading")
- confidence: A confidence score from 0.0 to 1.0
- reasoning: The explanation for the verdict

YOUR TASK:
Rewrite this factual report into a brief public service announcement:
- The tone should be calm and authoritative
- Use clear, simple language that the general public can understand
- Be reassuring but honest
- Do not add any information not present in the original report

OUTPUT FORMAT:
Your response must start with an appropriate emoji based on the verdict:
- 🟢 for "True" verdicts
- 🔴 for "False" verdicts
- 🟡 for "Misleading" verdicts

Follow the emoji with a single, concise paragraph (2-4 sentences maximum) that communicates the key finding to the public.

Do not include any other text, labels, section headers, or explanation. Your entire response should be the emoji followed immediately by the public announcement paragraph."""


# ============================================================================
# PROMPT METADATA
# ============================================================================

PROMPT_METADATA = {
    "investigator": {
        "name": "Investigator Agent",
        "role": "Fact-checking and evidence analysis",
        "output_type": "JSON",
        "required_keys": ["verdict", "confidence", "reasoning"]
    },
    "herald": {
        "name": "Herald Agent",
        "role": "Public communications and crisis messaging",
        "output_type": "Text with emoji prefix",
        "format": "emoji + paragraph"
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_investigator_prompt():
    """
    Retrieve the Investigator agent's mandate prompt.
    
    Returns:
        str: The complete investigator prompt
    """
    return INVESTIGATOR_MANDATE


def get_herald_prompt():
    """
    Retrieve the Herald agent's protocol prompt.
    
    Returns:
        str: The complete herald prompt
    """
    return HERALD_PROTOCOL


def format_case_file(claim_text, text_suspicion_score, source_credibility_score, research_dossier):
    """
    Format a case file for the Investigator agent.
    
    Args:
        claim_text (str): The claim being investigated
        text_suspicion_score (float): Suspicion score from text analysis (0.0-1.0)
        source_credibility_score (float): Credibility score from source profiling (0.0-1.0)
        research_dossier (dict): Research dossier from Research Agent with Wikipedia summary and web snippets
    
    Returns:
        str: Formatted case file as a JSON string
    """
    import json
    
    case_file = {
        "claim_text": claim_text,
        "text_suspicion_score": text_suspicion_score,
        "source_credibility_score": source_credibility_score,
        "research_dossier": research_dossier
    }
    
    return json.dumps(case_file, indent=2)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PROJECT AEGIS - PROMPT LIBRARY")
    print("Investigator & Herald Agent Mandates")
    print("="*70)
    
    print("\n[INVESTIGATOR MANDATE]")
    print("-" * 70)
    print(INVESTIGATOR_MANDATE)
    
    print("\n" + "="*70)
    print("\n[HERALD PROTOCOL]")
    print("-" * 70)
    print(HERALD_PROTOCOL)
    
    print("\n" + "="*70)
    print("\n[EXAMPLE: Case File Formatting]")
    print("-" * 70)
    
    sample_case = format_case_file(
        claim_text="Breaking: Major earthquake hits city center!",
        text_suspicion_score=0.75,
        source_credibility_score=0.25,
        research_dossier={
            "wikipedia_summary": "No recent earthquake reports found in the city.",
            "web_snippets": [
                "Local news: No earthquake reported today",
                "Weather service: No seismic activity detected",
                "Emergency services: All systems normal"
            ]
        }
    )
    
    print(sample_case)
    
    print("\n" + "="*70)
    print("Prompt Library - Ready for Deployment")
    print("="*70)