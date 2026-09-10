import os
from .safety import validate_ai_output
SYSTEM="""You are HealthMate AI, an educational wellness assistant. Approved HealthMate knowledge is your only condition-specific source of truth. Do not diagnose, prescribe, recommend medication or dosage changes, claim cures, use unsupported certainty, give restrictive dieting advice, or use body-shaming language. Preserve source uncertainty, say when information is insufficient, and distinguish education from professional care."""
def explain(question, entries, profile):
    """Uses the official Google Gen AI SDK only when configured; deterministic approved fallback otherwise."""
    key=os.getenv("GEMINI_API_KEY")
    context="\n".join(f"- {e.claim} {e.explanation}" for e in entries)
    if key:
        try:
            from google import genai
            client=genai.Client(api_key=key)
            result=client.models.generate_content(model=os.getenv("GEMINI_MODEL","gemini-2.0-flash"),contents=f"{SYSTEM}\n\nQuestion: {question}\nPreferences: {profile.diet if profile else 'not provided'}\nApproved context:\n{context}")
            answer=result.text
            if answer and validate_ai_output(answer)[0]: return answer,"gemini"
        except Exception: pass
    answer="Based on HealthMate's approved guidance: "+" ".join(e.explanation for e in entries[:3])+" This is general education, so a qualified healthcare professional can help adapt it to your situation."
    return answer,"approved-context-fallback"
