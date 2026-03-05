"""Step 3: SLO / SLI / Error Budget Evaluation Agent"""

from google.adk.agents import LlmAgent
from config import SONNET_MODEL
from tools.rag_retriever import retrieve_sre_context

STEP_3_PROMPT = open("prompts/step3_slo.md").read().split("## System Prompt")[1].split("```")[1]

slo_agent = LlmAgent(
    name="SLOAgent",
    model=SONNET_MODEL,
    instruction=STEP_3_PROMPT,
    tools=[retrieve_sre_context],
    output_key="slo_result",
    description="Evaluates SLO/SLI definitions, error budget policies, and operationalization.",
)
