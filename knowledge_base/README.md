# Knowledge Base — Setup Instructions

## Documents to Ingest

Populate this directory with the following documents before building
the vector index:

### Required
1. **Google SRE Handbook** (public) — key chapters:
   - Monitoring Distributed Systems
   - Service Level Objectives
   - Practical Alerting
   - Incident Response
   - Postmortem Culture

2. **Organization SRE Standards** — your internal docs:
   - Minimum SRE requirements per service tier
   - Approved tooling list
   - On-call policies
   - Change management procedures

### Recommended
3. **Production Readiness Checklist** templates
4. **Runbook templates** with examples
5. **Historical evaluation reports** (for calibration)
6. **Compliance controls** (SOC2, ISO 27001 SRE sections)
7. **DORA metrics** benchmarks and targets

## Chunking Configuration

- **Chunk size:** 512 tokens
- **Overlap:** 64 tokens
- **Metadata per chunk:**
  - `domain`: observability | slo | incident | resilience | deployment | governance
  - `source`: document name/URL
  - `date`: when the document was last updated
  - `tier_relevance`: P1_CRITICAL | P2_IMPORTANT | P3_STANDARD | P4_INTERNAL | ALL

## Building the Index
```bash
# Example using Vertex AI
python scripts/build_knowledge_base.py \
    --input_dir knowledge_base/ \
    --chunk_size 512 \
    --overlap 64 \
    --embedding_model textembedding-gecko@003 \
    --index_name sre-knowledge-base
```
