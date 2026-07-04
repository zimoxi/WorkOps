# PLAYBOOK.md
# AI Daily Working Procedure

## 1. New Session Procedure

When a new session starts:

1. Read AGENTS.md.
2. Read README.md.
3. Read ARCHITECTURE.md.
4. Read PROJECT_STATE.md.
5. Read TASKS.md.
6. Read DECISIONS.md.
7. Read latest WORKLOG.md entries.
8. Identify current task.
9. Continue development.

Output a brief project recovery summary before coding.

---

## 2. Feature Procedure

For a new feature:

1. Understand requirement.
2. Check TASKS.md.
3. Add or update task.
4. Review architecture impact.
5. Implement smallest useful version.
6. Add or update tests where appropriate.
7. Update documentation.
8. Update PROJECT_STATE.md.
9. Update CHANGELOG.md.
10. Add WORKLOG.md entry.

---

## 3. Bugfix Procedure

For a bug:

1. Reproduce or reason about the bug.
2. Identify root cause.
3. Fix minimally.
4. Add regression test where practical.
5. Record root cause in WORKLOG.md.
6. Update CHANGELOG.md.
7. Update PROJECT_STATE.md if relevant.

---

## 4. Refactor Procedure

For refactoring:

1. Confirm behavior must remain unchanged.
2. Identify scope.
3. Avoid unrelated rewrites.
4. Keep changes reviewable.
5. Update architecture docs if structure changes.
6. Record technical debt reduction.

---

## 5. End Session Procedure

Before ending:

1. Update TASKS.md.
2. Update PROJECT_STATE.md.
3. Update CHANGELOG.md.
4. Update WORKLOG.md.
5. Record blockers and risks.
6. Record next recommended action.
7. Recommend commit message if useful.

---

## 6. Recovery Procedure

If chat history is lost:

1. Read AGENTS.md.
2. Read PROJECT_STATE.md.
3. Read TASKS.md.
4. Read ARCHITECTURE.md.
5. Read DECISIONS.md.
6. Continue from Resume Guide in PROJECT_STATE.md.
