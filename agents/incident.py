"""Step 4: Incident Management & On-Call Evaluation Agent"""

from google.adk.agents import LlmAgent
from config import SONNET_MODEL
from tools.rag_retriever import retrieve_sre_context

STEP_4_PROMPT = open("prompts/step4_incident.md").read().split("## System Prompt")[1].split("```")[1]

incident_agent = LlmAgent(
    name="IncidentAgent",
    model=SONNET_MODEL,
    instruction=STEP_4_PROMPT,
    tools=[retrieve_sre_context],
    output_key="incident_result",
    description="Evaluates on-call structure, runbooks, incident response, and postmortem culture.",
)
