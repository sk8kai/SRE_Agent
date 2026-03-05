# Token Optimization Strategies

## Per-Step Token Budget

Each evaluation step (2–6) is designed to stay within ~8,000 total tokens:
```
┌─────────────────────────────────────┐
│ Per-Step Token Budget (Steps 2-6)   │
├─────────────────────────────────────┤
│ System prompt:        ~800 tokens   │
│ RAG context injection: ~1,500 tokens│
│ User input (app data): ~1,200 tokens│
│ Reserved for output:  ~4,000 tokens │
│ Safety margin:         ~500 tokens  │
│ TOTAL per call:       ~8,000 tokens │
└─────────────────────────────────────┘
```

Step 1 (Intake) has a smaller budget since it has no RAG context:
```
┌─────────────────────────────────────┐
│ Step 1 Token Budget                 │
├─────────────────────────────────────┤
│ System prompt:        ~600 tokens   │
│ User input (raw sub): ~3,000 tokens │
│ Reserved for output:  ~3,000 tokens │
│ Safety margin:         ~400 tokens  │
│ TOTAL:               ~7,000 tokens  │
└─────────────────────────────────────┘
```

Step 7 (Verdict) gets a larger budget since it synthesizes all results:
```
┌─────────────────────────────────────┐
│ Step 7 Token Budget (Opus 4.6)      │
├─────────────────────────────────────┤
│ System prompt:       ~1,200 tokens  │
│ All step results:    ~6,000 tokens  │
│ RAG context:         ~1,500 tokens  │
│ Reserved for output: ~6,000 tokens  │
│ Safety margin:        ~500 tokens   │
│ TOTAL:              ~15,200 tokens  │
└─────────────────────────────────────┘
```

## Strategy 1: Output Compression Between Steps

Each step outputs structured JSON via `output_key`. Only the output_key value
is written to ADK's shared session state — not the full conversation.

Keep outputs compact:
- BAD:  Long narrative paragraphs in findings arrays
- GOOD: Concise 1-sentence findings, numeric scores, gap lists only

Example of compact output (~600 tokens vs ~2,000 tokens unoptimized):
```json
{
  "domain": "observability",
  "scores": {
    "metrics": {"score": 4, "findings": ["All golden signals tracked via Prometheus"], "gaps": []},
    "logging": {"score": 2, "findings": ["Logs exist but unstructured"], "gaps": ["No correlation IDs"]},
    "tracing": {"score": 0, "findings": [], "gaps": ["No distributed tracing implemented"]},
    "alerting": {"score": 3, "findings": ["PagerDuty integrated, burn-rate alerts"], "gaps": ["No escalation policy"]},
    "dashboards": {"score": 3, "findings": ["Grafana dashboards for golden signals"], "gaps": []}
  },
  "composite_score": 2.4,
  "passed": false,
  "critical_gaps": ["No distributed tracing on P1 service"],
  "summary": "Metrics strong but tracing absent. Logging needs structuring."
}
```

## Strategy 2: RAG Context Window Management

- Retrieve max 5 chunks per domain (stays under ~1,500 tokens)
- Pre-filter by app tier metadata to reduce irrelevant results
- Use metadata filtering PLUS semantic search (hybrid approach)
- If a chunk isn't directly relevant to the current domain, drop it
```python
def retrieve_sre_context(domain: str, query: str, tier: str) -> str:
    results = vector_search.find_neighbors(
        query_embedding=embed(query),
        filter=[
            ("domain", "=", domain),
            ("tier_relevance", "in", [tier, "ALL"]),
        ],
        num_neighbors=5
    )
    # Truncate to 1500 tokens max
    context = "\n---\n".join([r.text for r in results])
    return truncate_to_tokens(context, max_tokens=1500)
```

## Strategy 3: Prompt Caching (Anthropic Feature)

System prompts are identical across all evaluations for the same step.
Enable prompt caching to reduce cost by ~90% on the system prompt portion
after the first API call.

With Anthropic's API:
```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4000,
    system=[
        {
            "type": "text",
            "text": STEP_2_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}  # Enables caching
        }
    ],
    messages=[{"role": "user", "content": user_input}]
)
```

Savings estimate for 100 evaluations/month:
- Without caching: ~$45/month (system prompts re-processed each time)
- With caching: ~$8/month (system prompts cached after first call)

## Strategy 4: Parallel Execution

Steps 2–6 only depend on Step 1 (not on each other). Use ADK's ParallelAgent:
```python
from google.adk.agents import SequentialAgent, ParallelAgent

parallel_eval = ParallelAgent(
    name="DomainEvaluations",
    sub_agents=[observability, slo_agent, incident, resilience, deployment]
)

full_pipeline = SequentialAgent(
    name="SREPipeline",
    sub_agents=[intake, parallel_eval, verdict]
)
```

Latency improvement:
- Sequential: ~60s (10s per step × 6 steps)
- Parallel: ~20s (Step 1: 5s + parallel block: 10s + Step 7: 5s)

## Strategy 5: Streaming for UX

Use ADK's built-in streaming to show progress as each step completes,
rather than blocking the UI until the full pipeline finishes.
```python
async for event in app.async_stream_query(
    user_id=user_id,
    message=submission_data
):
    # Events arrive as each sub-agent completes
    if event.get("author") == "ObservabilityAgent":
        show_progress("Observability evaluation complete ✓")
    elif event.get("author") == "VerdictAgent":
        show_result(event)
```

## Strategy 6: Input Truncation for Large Submissions

If an application submission exceeds the input budget, truncate intelligently:

1. Keep all structured data (JSON configs, YAML manifests) — highest signal
2. Summarize prose documentation to first 200 words per section
3. For architecture diagrams (images), rely on the LLM's vision capability
   rather than converting to text
4. Drop duplicate/redundant content (e.g., multiple similar runbooks)

## Total Cost Estimate

Per evaluation (7 steps):
| Component | Tokens | Cost (approx) |
|-----------|--------|----------------|
| Steps 1-6 (Sonnet) | ~48K input + ~24K output | ~$0.36 |
| Step 7 (Opus) | ~15K input + ~6K output | ~$0.75 |
| RAG embeddings | ~5 queries | ~$0.001 |
| **Total per evaluation** | | **~$1.11** |

With prompt caching enabled: **~$0.85 per evaluation**
With parallel execution: same cost, but **3x faster**
