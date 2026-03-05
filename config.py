"""
SRE Evaluation Agent — Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Model Configuration ---
SONNET_MODEL = "litellm/anthropic/claude-sonnet-4-5-20250929"
OPUS_MODEL = "litellm/anthropic/claude-opus-4-6"
EMBEDDING_MODEL = "textembedding-gecko@003"  # or "text-embedding-3-large"

# --- API Keys ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")

# --- RAG Configuration ---
VECTOR_INDEX_ENDPOINT = os.getenv("VECTOR_INDEX_ENDPOINT", "")
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
RAG_TOP_K = 5
RAG_MAX_TOKENS = 1500

# --- Scoring Configuration ---
SCORING_WEIGHTS = {
    "observability": 0.20,
    "slo_sli_error_budget": 0.25,
    "incident_management": 0.20,
    "resilience": 0.15,
    "deployment_change": 0.20,
}

PASS_THRESHOLD = 3.5
CONDITIONAL_THRESHOLD = 2.5

TIER_REQUIREMENTS = {
    "P1_CRITICAL": {
        "min_availability": "99.95%",
        "max_p99_latency_ms": 200,
        "requires_24x7_oncall": True,
        "requires_slos": True,
        "requires_runbooks": True,
        "domain_pass_threshold": 3.0,
    },
    "P2_IMPORTANT": {
        "min_availability": "99.9%",
        "max_p99_latency_ms": 500,
        "requires_24x7_oncall": True,
        "requires_slos": True,
        "requires_runbooks": True,
        "domain_pass_threshold": 3.0,
    },
    "P3_STANDARD": {
        "min_availability": "99.5%",
        "max_p99_latency_ms": 1000,
        "requires_24x7_oncall": False,
        "requires_slos": True,
        "requires_runbooks": False,
        "domain_pass_threshold": 2.0,
    },
    "P4_INTERNAL": {
        "min_availability": "99.0%",
        "max_p99_latency_ms": 2000,
        "requires_24x7_oncall": False,
        "requires_slos": False,
        "requires_runbooks": False,
        "domain_pass_threshold": 2.0,
    },
}

# --- Token Budget ---
PER_STEP_TOKEN_BUDGET = {
    "system_prompt": 800,
    "rag_context": 1500,
    "user_input": 1200,
    "output_reserved": 4000,
    "safety_margin": 500,
    "total": 8000,
}

VERDICT_TOKEN_BUDGET = {
    "system_prompt": 1200,
    "all_step_results": 6000,
    "rag_context": 1500,
    "output_reserved": 6000,
    "safety_margin": 500,
    "total": 15200,
}
