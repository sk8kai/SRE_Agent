# SRE Evaluation Agent — Multi-Step Implementation Guide

A multi-step AI agent pipeline that evaluates application Site Reliability Engineering (SRE) readiness. Built for deployment with **Google ADK**, **RAG**, and **Anthropic Claude** (Opus 4.6 + Sonnet 4.5).

## Architecture Overview
```
ORCHESTRATOR (Root Agent)
  │
  ├─► Step 1: Intake & Metadata Extraction       (Sonnet 4.5)
  ├─► Step 2: Observability & Monitoring          (Sonnet 4.5)
  ├─► Step 3: SLO / SLI / Error Budget            (Sonnet 4.5)
  ├─► Step 4: Incident Management & On-Call        (Sonnet 4.5)
  ├─► Step 5: Reliability & Resilience Patterns    (Sonnet 4.5)
  ├─► Step 6: Deployment & Change Management       (Sonnet 4.5)
  ├─► Step 7: Final Verdict & Report Generation    (Opus 4.6)
  │
  └─► OUTPUT: Structured SRE Readiness Report
              PASS / CONDITIONAL_PASS / REJECT
```

## Model Strategy

| Role | Model | Rationale |
|------|-------|-----------|
| Orchestrator + Step 7 | Claude Opus 4.6 | Complex reasoning, synthesis, final judgment |
| Steps 1–6 | Claude Sonnet 4.5 | Fast, cost-effective, structured extraction |
| RAG Embeddings | text-embedding-3-large or Vertex AI | Document retrieval |

## Scoring Weights

| Domain | Weight | Pass Threshold |
|--------|--------|----------------|
| Observability & Monitoring | 20% | 3.0 / 5.0 |
| SLO / SLI / Error Budget | 25% | 3.0 / 5.0 |
| Incident Management | 20% | 3.0 / 5.0 |
| Resilience Patterns | 15% | 2.5 / 5.0 |
| Deployment & Change Mgmt | 20% | 3.0 / 5.0 |

## Verdict Logic

- **PASS** — score >= 3.5 AND zero blocking gaps
- **CONDITIONAL_PASS** — score >= 2.5 AND gaps remediable within 30 days
- **REJECT** — score < 2.5 OR critical architectural gaps

## Quick Start
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_CLOUD_PROJECT="your-project"
adk web sre-evaluation-agent
```

See `docs/ARCHITECTURE.md` for full deployment details.
See `docs/TOKEN_OPTIMIZATION.md` for token budget strategies.
See `prompts/` for all evaluation step prompts.
