import re

PROHIBITED_PATTERNS = [
    r"\bdiagnos(?:e|ed|is|ing)\b",
    r"\bprescri(?:be|bed|ption|bing)\b",
    r"\bstop (?:taking|your)\b",
    r"\bchange (?:your )?(?:dose|dosage|medication)\b",
    r"\b(?:increase|decrease) (?:your )?(?:dose|dosage)\b",
    r"\b(?:cure|reverse|heal) (?:diabetes|pcos|anemia|cholesterol|blood pressure)\b",
    r"\b(?:starve|fast for|skip all meals|extreme restriction)\b",
    r"\byou (?:have|are suffering from)\b",
]


def validate_ai_output(text: str) -> tuple[bool, list[str]]:
    violations = [pattern for pattern in PROHIBITED_PATTERNS if re.search(pattern, text, re.IGNORECASE)]
    return not violations, violations


def safe_fallback() -> dict:
    return {
        "message": "I do not have enough approved health information in the HealthMate knowledge base to answer that condition-specific question reliably. I do not want to guess or provide potentially misleading medical information. Try an available verified topic, or consult a qualified healthcare professional for condition-specific advice.",
        "needs_professional_guidance": True,
    }
