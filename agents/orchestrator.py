"""
SRE Evaluation Pipeline — Orchestrator

Defines the SequentialAgent (or Sequential + Parallel hybrid) that
wires all 7 evaluation steps together via Google ADK.
"""

from google.adk.agents import SequentialAgent, ParallelAgent

from agents.intake import intake_agent
from agents.observability import observability_agent
from agents.slo import slo_agent
from agents.incident import incident_agent
from agents.resilience import resilience_agent
from agents.deployment import deployment_agent
from agents.verdict import verdict_agent


# ----------------------------------------------------------------
# Option A: Fully Sequential Pipeline
# Steps run one after another. Simpler, easier to debug.
# Total latency: ~60s (10s per step)
# ----------------------------------------------------------------
sequential_pipeline = SequentialAgent(
    name="SREEvaluationPipeline_Sequential",
    sub_agents=[
        intake_agent,        # Step 1: Extract metadata
        observability_agent, # Step 2: Evaluate observability
        slo_agent,           # Step 3: Evaluate SLOs
        incident_agent,      # Step 4: Evaluate incident mgmt
        resilience_agent,    # Step 5: Evaluate resilience
        deployment_agent,    # Step 6: Evaluate deployment
        verdict_agent,       # Step 7: Final verdict (Opus)
    ],
)


# ----------------------------------------------------------------
# Option B: Parallel Evaluation Pipeline (RECOMMENDED)
# Steps 2-6 run in parallel (they only depend on Step 1).
# Total latency: ~20s (Step 1: 5s + parallel: 10s + Step 7: 5s)
# ----------------------------------------------------------------
parallel_evaluations = ParallelAgent(
    name="DomainEvaluations",
    sub_agents=[
        observability_agent,
        slo_agent,
        incident_agent,
        resilience_agent,
        deployment_agent,
    ],
)

parallel_pipeline = SequentialAgent(
    name="SREEvaluationPipeline_Parallel",
    sub_agents=[
        intake_agent,          # Step 1: runs first
        parallel_evaluations,  # Steps 2-6: run in parallel
        verdict_agent,         # Step 7: runs last (Opus)
    ],
)


# Default export — use the parallel pipeline
root_agent = parallel_pipeline
