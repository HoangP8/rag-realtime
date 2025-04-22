"""
Response validation for the LLM service
"""
import re
from typing import Dict, List, Optional, Any


def validate_medical_response(response: str) -> Dict[str, Any]:
    """
    Validate a medical response for quality and safety
    
    Returns:
        Dict with validation results:
        - valid: Boolean indicating if the response is valid
        - issues: List of issues found
        - score: Quality score (0-100)
    """
    issues = []
    score = 100
    
    # Check for absolute medical advice
    absolute_advice_patterns = [
        r"you should definitely",
        r"you must",
        r"always",
        r"never",
        r"guaranteed to",
        r"100% effective"
    ]
    
    for pattern in absolute_advice_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            issues.append(f"Contains absolute medical advice: '{pattern}'")
            score -= 10
    
    # Check for diagnostic language
    diagnostic_patterns = [
        r"you have",
        r"you are suffering from",
        r"you are experiencing",
        r"I diagnose",
        r"your condition is"
    ]
    
    for pattern in diagnostic_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            issues.append(f"Contains diagnostic language: '{pattern}'")
            score -= 10
    
    # Check for treatment recommendations
    treatment_patterns = [
        r"you should take",
        r"I recommend taking",
        r"you need to take",
        r"the best treatment is",
        r"you should stop taking"
    ]
    
    for pattern in treatment_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            issues.append(f"Contains specific treatment recommendation: '{pattern}'")
            score -= 10
    
    # Check for disclaimer about consulting healthcare professional
    if not re.search(r"(consult|speak|talk|discuss with) (a|your) (healthcare|medical|health) (professional|provider|doctor|physician)", response, re.IGNORECASE):
        issues.append("Missing disclaimer about consulting healthcare professional")
        score -= 15
    
    # Ensure score is within bounds
    score = max(0, min(100, score))
    
    return {
        "valid": score >= 70,
        "issues": issues,
        "score": score
    }
