# ENGINEERING_STANDARD.md

## Philosophy

Optimize for:

- maintainability
- clarity
- reliability
- testability
- recoverability
- long-term development

Avoid cleverness that makes the project harder to understand.

---

## Repository Is the Source of Truth

Important knowledge belongs in files, not chat.

Required memory files:

- AGENTS.md
- PLAYBOOK.md
- PROJECT_STATE.md
- TASKS.md
- CHANGELOG.md
- DECISIONS.md
- WORKLOG.md
- ARCHITECTURE.md

---

## Code Quality

Prefer:

- small functions
- clear names
- explicit behavior
- simple architecture
- low coupling
- high cohesion

Avoid:

- hidden side effects
- duplicated logic
- over-engineering
- dead code
- undocumented assumptions

---

## Testing

Add tests for:

- important features
- bug fixes
- risky logic
- core business rules

Do not delete failing tests just to make the project pass.

---

## Documentation

Docs must change when behavior, setup, architecture, APIs, database, or deployment change.

---

## Review Checklist

Before completion:

- code works
- tests pass if applicable
- docs updated
- tasks updated
- state updated
- changelog updated
- worklog updated
- risks recorded
- next steps clear
