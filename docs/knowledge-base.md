# Vetted knowledge base

The knowledge base is the source of truth for condition-specific educational information. Claims are intentionally atomic and source-attributed.

## Review lifecycle

1. Identify an authoritative source.
2. Extract and rewrite one neutral claim.
3. Record population scope and limitations.
4. Submit as `pending_review`.
5. A human reviewer records `reviewed_by`, `reviewed_at`, and `next_review_at`.
6. Approve only when source and review metadata are complete.
7. Record review actions in `knowledge_review_log`.

Only `approved` entries are eligible for normal user-facing retrieval. This MVP exposes the approval guard in the backend and has an admin listing endpoint; authentication and role enforcement should be added before deployment.

## Source policy

Prefer official WHO, CDC, NIH/NIDDK, AHA, national public-health agencies, government health departments, and professional medical organizations. Secondary literature can supplement primary sources when needed. Blogs, influencers, marketing pages, and AI-generated articles are not medical authority.

## Scope

The current seed set covers general education for diabetes, high blood pressure, high cholesterol, anemia, and PCOS. It does not diagnose, prescribe, set individualized targets, or recommend medication changes.
