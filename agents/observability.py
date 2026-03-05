"""Step 2: Observability & Monitoring Evaluation Agent"""

from google.adk.agents import LlmAgent
from config import SONNET_MODEL
from tools.rag_retriever import retrieve_sre_context

STEP_2_PROMPT = open("prompts/step2_observability.md").read().split("## System Prompt")[1].split("```")[1]

observability_agent = LlmAgent(
    name="ObservabilityAgent",
    model=SONNET_MODEL,
    instruction=STEP_2_PROMPT,
    tools=[retrieve_sre_context],
    output_key="observability_result",
    description="Evaluates application observability posture across metrics, logging, tracing, alerting.",
)
