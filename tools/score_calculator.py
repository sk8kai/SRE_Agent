"""
Score Calculator Utility

Provides helper functions for calculating weighted composite scores
and determining verdicts. Can be used as a validation layer after
the LLM-generated scores.
"""

from config import SCORING_WEIGHTS, PASS_THRESHOLD, CONDITIONAL_THRESHOLD


def calculate_weighted_score(domain_scores: dict) -> float:
    """
    Calculate weighted composite score from domain scores.

    Args:
        domain_scores: Dict mapping domain name to score (0-5).
            Expected keys: observability, slo_sli_error_budget,
            incident_management, resilience, deployment_change

    Returns:
        Weighted composite score (0.0 - 5.0)
    """
    total = 0.0
    for domain, weight in SCORING_WEIGHTS.items():
        score = domain_scores.get(domain, 0)
        total += score * weight
    return round(total, 1)


def determine_verdict(
    weighted_score: float,
    blocking_gaps: list,
) -> str:
    """
    Determine the evaluation verdict based on score and blocking gaps.

    Args:
        weighted_score: The weighted composite score (0-5).
        blocking_gaps: List of blocking gap descriptions.

    Returns:
        "PASS", "CONDITIONAL_PASS", or "REJECT"
    """
    has_blocking = len(blocking_gaps) > 0

    if weighted_score >= PASS_THRESHOLD and not has_blocking:
        return "PASS"
    elif weighted_score >= CONDITIONAL_THRESHOLD:
        return "CONDITIONAL_PASS"
    else:
        return "REJECT"


def validate_scores(step_result: dict) -> list:
    """
    Validate that LLM-generated scores are consistent and within bounds.

    Returns list of validation warnings (empty if all valid).
    """
    warnings = []

    if "scores" not in step_result:
        warnings.append("Missing 'scores' field in step result")
        return warnings

    for subdomain, data in step_result["scores"].items():
        score = data.get("score", -1)
        if not (0 <= score <= 5):
            warnings.append(f"{subdomain}: score {score} out of range [0-5]")

        if score == 0 and not data.get("gaps"):
            warnings.append(f"{subdomain}: score is 0 but no gaps listed")

        if score >= 4 and data.get("gaps"):
            warnings.append(f"{subdomain}: score is {score} but gaps exist")

    return warnings
