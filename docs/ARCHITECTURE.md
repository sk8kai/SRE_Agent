# SRE Evaluation Agent — Architecture & Deployment Guide

## System Architecture

### Agent Topology

The SRE Evaluation Agent uses a Sequential Multi-Agent architecture with 7 specialist
sub-agents, each responsible for one evaluation domain. The pipeline follows a
SequentialAgent pattern in Google ADK, where each step's output feeds into the next
via shared session state (`output_key`).
```
┌──────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (Root)                        │
│                    Google ADK SequentialAgent                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────┐                                          │
│  │  Step 1: Intake │ ─── output_key: "intake_result" ───┐   │
│  │  (Sonnet 4.5)  │                                     │   │
│  └────────────────┘                                     ▼   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          PARALLEL EVALUATION BLOCK (optional)         │   │
│  │          Google ADK ParallelAgent                     │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │ Step 2:      │  │ Step 3:      │  │ Step 4:    │ │   │
│  │  │ Observability│  │ SLO/SLI/EB   │  │ Incident   │ │   │
│  │  │ (Sonnet)     │  │ (Sonnet)     │  │ (Sonnet)   │ │   │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐                  │   │
│  │  │ Step 5:      │  │ Step 6:      │                  │   │
│  │  │ Resilience   │  │ Deployment   │                  │   │
│  │  │ (Sonnet)     │  │ (Sonnet)     │                  │   │
│  │  └──────────────┘  └──────────────┘                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Step 7: Final Verdict & Report Generation            │   │
│  │  (Opus 4.6 — complex reasoning & synthesis)           │   │
│  │  output_key: "final_verdict"                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Model Strategy

- **Orchestrator + Step 7 (Final Verdict):** Claude Opus 4.6
  - Complex multi-factor reasoning
  - Synthesis across all 6 domain evaluations
  - Nuanced judgment for borderline cases
  - High-quality narrative report generation

- **Steps 1–6 (Domain Evaluations):** Claude Sonnet 4.5
  - Fast structured extraction (~3-5s per step)
  - Cost-effective (~70% cheaper than Opus)
  - Reliable JSON output formatting
  - Consistent scoring against rubrics

- **RAG Retrieval:** Vertex AI textembedding-gecko@003
  - Or OpenAI text-embedding-3-large via LiteLLM
  - 768-dimensional vectors
  - Cosine similarity matching

### RAG Knowledge Base

The vector store should be populated with:

1. **Google SRE Handbook** — Chapters on monitoring, alerting, SLOs, incident response
2. **Organization SRE Standards** — Internal policies, minimum requirements per tier
3. **Production Readiness Checklists** — Templates for PRR reviews
4. **Runbook Templates** — Standard runbook format and examples
5. **Compliance Frameworks** — SOC2, ISO 27001 SRE-relevant controls
6. **Historical Evaluations** — Past reports for consistency calibration
7. **Industry Benchmarks** — DORA metrics, SRE maturity models

**Chunking strategy:**
- Chunk size: 512 tokens with 64-token overlap
- Metadata tags per chunk: `{domain, source, date, tier_relevance}`
- Pre-filter by domain before semantic search

### Data Flow Between Steps

Each step writes its result to ADK's shared session state via `output_key`.
Downstream steps read from `context.state["key_name"]`.
```
Step 1 writes: context.state["intake_result"]         → JSON metadata
Step 2 writes: context.state["observability_result"]   → JSON scores + findings
Step 3 writes: context.state["slo_result"]             → JSON scores + findings
Step 4 writes: context.state["incident_result"]        → JSON scores + findings
Step 5 writes: context.state["resilience_result"]      → JSON scores + findings
Step 6 writes: context.state["deployment_result"]      → JSON scores + findings
Step 7 reads:  ALL of the above → produces final_verdict
```

---

## Deployment Phases

### Phase 1: Copilot Testing (Weeks 1–2)

Test each prompt individually in Claude.ai or API Workbench.

1. **Create test fixtures** for each step:
   - Sample "good" application (should PASS)
   - Sample "mediocre" application (should CONDITIONAL_PASS)
   - Sample "poor" application (should REJECT)

2. **Test each step in isolation:**
   - Feed test data → verify JSON output is valid and parseable
   - Check scoring consistency across 3+ runs
   - Verify token usage stays within budget per step

3. **Test the full chain manually:**
   - Run Step 1 → copy output → feed to Step 2 → ... → Step 7
   - Verify the final verdict matches expectations
   - Time each step for latency benchmarking

4. **Iterate on prompts:**
   - Adjust scoring rubrics if too strict or lenient
   - Refine output JSON format if downstream parsing fails
   - Add edge case handling to system prompts

### Phase 2: RAG Setup (Weeks 3–4)

1. **Document Collection & Chunking:**
```
   ├── Google SRE Handbook      → chunk by section (512 tokens)
   ├── Internal SRE policies    → chunk by policy (512 tokens)
   ├── Runbook templates        → chunk per template
   ├── Past evaluations         → chunk per domain score
   └── Compliance frameworks    → chunk per control
```

2. **Vector Store Setup (Vertex AI Vector Search):**
```python
   from google.cloud import aiplatform

   index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
       display_name="sre-knowledge-base",
       dimensions=768,
       approximate_neighbors_count=10,
       distance_measure_type="DOT_PRODUCT_DISTANCE"
   )
```

3. **Embedding Pipeline:**
   - Use textembedding-gecko@003 or text-embedding-3-large
   - Batch embed all documents
   - Store with metadata tags: `{domain, source, date, tier}`

### Phase 3: Google ADK Agent Build (Weeks 5–7)

- Wire up all agents in `agents/orchestrator.py`
- Connect RAG retriever as a tool via `tools/rag_retriever.py`
- Configure LiteLLM for Anthropic model routing
- Test with ADK dev UI: `adk web sre-evaluation-agent`

### Phase 4: Evaluation & Deployment (Weeks 8–10)

1. **ADK Built-in Evaluation:**
```bash
   adk eval sre-evaluation-agent evals/sre_eval_set.evalset.json
```

2. **Deploy to Vertex AI Agent Engine:**
```python
   from vertexai.agent_engines import AdkApp

   app = AdkApp(agent=sre_pipeline)
   remote_app = agent_engines.create(
       agent_engine=app,
       display_name="sre-evaluation-agent",
       requirements=["anthropic", "litellm"]
   )
```

3. **Production Monitoring:**
   - Track per-step latency and token usage
   - Alert on verdict distribution anomalies
   - Log all evaluations for audit trail
   - Dashboard: pass rate, avg score by domain, top gaps
