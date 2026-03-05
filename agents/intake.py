"""Step 1: Intake & Metadata Extraction Agent"""

from google.adk.agents import LlmAgent
from config import SONNET_MODEL

STEP_1_PROMPT = open("prompts/step1_intake.md").read().split("## System Prompt")[1].split("```")[1]

intake_agent = LlmAgent(
    name="IntakeAgent",
    model=SONNET_MODEL,
    instruction=STEP_1_PROMPT,
    output_key="intake_result",
    description="Extracts and normalizes structured metadata from application submissions.",
)
