# Intake Skills Refactor Implementation Plan

**Goal:** Replace structured intake syndrome analysis with completeness and recommended-exam analysis powered by two focused Skills.

**Architecture:** Keep the deterministic ten-question flow. After completion, an Agent loaded with `tcm-intake-checklist` and `tcm-questioning-guide` returns normalized JSON for completeness, missing items, follow-up questions, safety alerts, and recommended exams.

## Tasks

- [ ] Write failing tests for the new result schema and removal of syndrome output.
- [ ] Implement the normalized backend schema and prompt.
- [ ] Add the two new Skill directories and load them in the Agent.
- [ ] Replace the Vue result sections with completeness and recommended exams.
- [ ] Run all backend tests, frontend build, and a live Qwen endpoint check.
