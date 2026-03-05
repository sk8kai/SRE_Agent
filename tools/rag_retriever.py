"""
RAG Retriever Tool

Retrieves relevant SRE standards, policies, and best practices from the
vector knowledge base. Used by Steps 2-7 to inject organization-specific
context into evaluations.
"""

from typing import Optional
from config import RAG_TOP_K, RAG_MAX_TOKENS, VECTOR_INDEX_ENDPOINT


def retrieve_sre_context(
    domain: str,
    query: str,
    tier: Optional[str] = None,
) -> str:
    """
    Retrieve relevant SRE standards for a specific evaluation domain.

    Args:
        domain: The evaluation domain (observability, slo, incident,
                resilience, deployment, governance).
        query: A natural language query describing what context is needed.
        tier: Optional app tier (P1_CRITICAL, P2_IMPORTANT, etc.) to
              filter results by relevance.

    Returns:
        A string containing the concatenated relevant context chunks,
        separated by '---'. Maximum ~1500 tokens.
    """

    # --- PLACEHOLDER IMPLEMENTATION ---
    # Replace this with your actual vector search implementation.
    # Options:
    #   1. Vertex AI Vector Search (Matching Engine)
    #   2. Pinecone
    #   3. Weaviate
    #   4. ChromaDB (for local development)

    # Example with Vertex AI:
    #
    # from google.cloud import aiplatform
    #
    # index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
    #     VECTOR_INDEX_ENDPOINT
    # )
    #
    # query_embedding = embed(query)  # Use your embedding model
    #
    # response = index_endpoint.find_neighbors(
    #     queries=[query_embedding],
    #     num_neighbors=RAG_TOP_K,
    #     filter=[
    #         {"name": "domain", "allow_tokens": [domain]},
    #         {"name": "tier_relevance", "allow_tokens": [tier or "ALL", "ALL"]},
    #     ],
    # )
    #
    # chunks = [neighbor.text for neighbor in response[0]]
    # context = "\n---\n".join(chunks)
    # return truncate_to_tokens(context, RAG_MAX_TOKENS)

    return f"[RAG context for domain='{domain}', query='{query}' — connect your vector store]"


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Approximate token truncation (4 chars per token heuristic)."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[...truncated to fit token budget]"
