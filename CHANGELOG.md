# Changelog

## v2.0 — Pattern-Based Rule Engine Upgrade

- Replaced if-else rules with weighted risk patterns
- Added confidence scoring (0.3–1.0 range)
- Implemented missing data penalty (clamped)
- Added vitals support in structured input
- Integrated India-specific clinical patterns (dengue, TB, poisoning, etc.)
- Added key drug interaction rules (warfarin, paracetamol, opioid combinations)
- Improved explainability via signal-level outputs

## intake_agent
- Full pipeline: LLM → Pydantic → negation → normalization → timeline → quality scoring
- Hindi negation support
- Markdown fence stripping for LLM output
- External mappings.json for term normalization