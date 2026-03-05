"""
SRE Evaluation Agent — Entry Point

Run locally:
    python main.py

Or use ADK CLI:
    adk web .
    adk run . --user_id=test --message="<submission data>"
"""

import asyncio
import json
from agents.orchestrator import root_agent


async def run_evaluation(submission_data: str, user_id: str = "evaluator-1"):
    """Run a full SRE evaluation pipeline."""

    # In production, this would be handled by ADK's runtime.
    # This is a simplified local runner for testing.

    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()

    runner = Runner(
        agent=root_agent,
        app_name="sre-evaluation-agent",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="sre-evaluation-agent",
        user_id=user_id,
    )

    from google.genai import types

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(submission_data)],
    )

    print("Starting SRE Evaluation Pipeline...")
    print("=" * 60)

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=content,
    ):
        author = event.get("author", "unknown")
        content_parts = event.get("content", {}).get("parts", [])

        for part in content_parts:
            if "text" in part:
                print(f"\n[{author}]")
                print(part["text"][:500])  # Truncate for console

    # Retrieve final state
    final_session = await session_service.get_session(
        app_name="sre-evaluation-agent",
        user_id=user_id,
        session_id=session.id,
    )

    verdict = final_session.state.get("final_verdict")
    if verdict:
        print("\n" + "=" * 60)
        print("FINAL VERDICT:")
        print(json.dumps(json.loads(verdict), indent=2))


if __name__ == "__main__":
    # Example: load test fixture
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            submission = f.read()
    else:
        submission = """
        Application: Example Service
        Tier: P2_IMPORTANT
        Architecture: Microservices on Kubernetes (GKE)
        Team: Platform Engineering
        [Provide your full submission data here]
        """

    asyncio.run(run_evaluation(submission))
