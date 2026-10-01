# Structured Intake Skills Implementation Plan

**Goal:** Connect the two existing TCM Skills to structured intake and add one PPT slide.

**Architecture:** Keep deterministic intake independent from LLM availability. A focused analysis module invokes the existing Deep Agent after completion, normalizes output, and returns a stable fallback.

## Tasks

- [ ] Write failing analysis service tests.
- [ ] Implement analysis service and API.
- [ ] Persist `skill_analysis` with records.
- [ ] Add Vue completion analysis states.
- [ ] Run backend tests and frontend build.
- [ ] Add and verify PPT slide 11.
