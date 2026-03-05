"""Step 6: Deployment & Change Management Evaluation Agent"""

from google.adk.agents import LlmAgent
from config import SONNET_MODEL
from tools.rag_retriever import retrieve_sre_context

STEP_6_PROMPT = open("prompts/step6_deployment.md").read().split("## System Prompt")[1].split("```")[1]

deployment_agent = LlmAgent(
    name="DeploymentAgent",
    model=SONNET_MODEL,
    instruction=STEP_6_PROMPT,
    tools=[retrieve_sre_context],
    output_key="deployment_result",
    description="Evaluates CI/CD, deployment strategy, rollback, change management, and DORA metrics.",
)
