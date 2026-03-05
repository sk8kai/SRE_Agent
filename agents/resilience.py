"""Step 5: Reliability & Resilience Patterns Evaluation Agent"""

from google.adk.agents import LlmAgent
from config import SONNET_MODEL
from tools.rag_retriever import retrieve_sre_context

STEP_5_PROMPT = open("prompts/step5_resilience.md").read().split("## System Prompt")[1].split("```")[1]

resilience_agent = LlmAgent(
    name="ResilienceAgent",
    model=SONNET_MODEL,
    instruction=STEP_5_PROMPT,
    tools=[retrieve_sre_context],
    output_key="resilience_result",
    description="Evaluates fault tolerance, resilience patterns, capacity planning, and DR readiness.",
)
