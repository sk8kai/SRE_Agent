"""Step 7: Final Verdict & Report Generation Agent (Opus 4.6)"""

from google.adk.agents import LlmAgent
from config import OPUS_MODEL
from tools.rag_retriever import retrieve_sre_context

STEP_7_PROMPT = open("prompts/step7_verdict.md").read().split("## System Prompt")[1].split("```")[1]

verdict_agent = LlmAgent(
    name="VerdictAgent",
    model=OPUS_MODEL,
    instruction=STEP_7_PROMPT,
    tools=[retrieve_sre_context],
    output_key="final_verdict",
    description="Synthesizes all domain evaluations into a final SRE readiness verdict.",
)
