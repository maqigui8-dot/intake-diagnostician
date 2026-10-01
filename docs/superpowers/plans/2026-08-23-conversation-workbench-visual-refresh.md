# Conversation Workbench Visual Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the patient-facing intake interface into a focused, modern conversation workbench without changing intake rules or backend APIs.

**Architecture:** Keep `App.vue` as the state and workflow owner. Update only presentational structure and CSS: a compact utility sidebar, an information-focused baseline panel, and a fixed-composer chat surface. Existing data attributes and workflow expressions remain stable so the API contract and doctor view continue to work unchanged.

**Tech Stack:** Vue 3, Vite, CSS, Node built-in test runner.

## Global Constraints

- Do not change the FastAPI routes, session schema, follow-up policy, or completeness calculation.
- Keep patient-facing pages free of internal execution/completeness details.
- Retain keyboard behavior: Enter submits and Shift+Enter inserts a newline.
- Preserve the existing mobile breakpoint and all current patient-flow test hooks.
- Do not create a git commit unless the user asks for one.

---

### Task 1: Lock the visual-workbench contract with tests

**Files:**
- Modify: `frontend/tests/patient-visibility.test.mjs`
- Test: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Consumes: `frontend/src/App.vue` template and `frontend/src/style.css`.
- Produces: regression checks for semantic selectors used by the revised shell, optional baseline disclosure, and fixed chat composer.

- [x] **Step 1: Write the failing test**

```js
test('patient workbench keeps a compact sidebar and progressive baseline disclosure', () => {
  assert.match(template, /class="sidebar-primary-action"/)
  assert.match(template, /class="baseline-optional"/)
  assert.match(styleSource, /\.workspace\s*\{[^}]*grid-template-columns:\s*248px minmax\(0, 1fr\)/s)
})

test('follow-up chat uses a persistent composer surface', () => {
  assert.match(template, /class="chat-workbench"/)
  assert.match(template, /class="chat-composer"/)
  assert.match(styleSource, /\.chat-composer\s*\{[^}]*position:\s*sticky/s)
})
```

- [x] **Step 2: Run test to verify it fails**

Run: `npm test -- patient-visibility.test.mjs`

Expected: failure because `sidebar-primary-action` and `chat-workbench` are not yet present.

- [x] **Step 3: Implement the minimum UI hooks**

Add `sidebar-primary-action` to the sidebar action, add `chat-workbench` to both chat sections, and add the CSS rules asserted above.

- [x] **Step 4: Run test to verify it passes**

Run: `npm test -- patient-visibility.test.mjs`

Expected: all assertions pass.

### Task 2: Recompose the patient-facing shell and baseline form

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Test: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Consumes: `baseline`, `baselineValid`, `flowStages`, `formError`, and existing submit handlers.
- Produces: unchanged field bindings in a visually compact baseline start surface.

- [x] **Step 1: Keep baseline bindings stable**

The form must continue using these bindings exactly:

```vue
v-model.number="baseline.age"
v-model="baseline.sex"
v-model.number="baseline.height_cm"
v-model.number="baseline.weight_kg"
v-model.number="baseline.waist_cm"
v-model.number="baseline.hip_cm"
v-model="baseline.measured_at"
```

- [x] **Step 2: Apply the visual layout**

Use a 248px sidebar, remove ornamental shadows, use neutral `#F5F7FA` surfaces with an ink-green primary `#176B52`, make the optional measurements a visually subordinate disclosure, and keep the primary submit action visible at the bottom of the baseline panel.

- [x] **Step 3: Run patient-flow regression tests**

Run: `npm test -- patient-visibility.test.mjs`

Expected: all existing baseline, patient-visibility, and keyboard behavior assertions pass.

### Task 3: Make follow-up feel like a chat workbench and verify the build

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Test: `frontend/tests/patient-visibility.test.mjs`

**Interfaces:**
- Consumes: `state.open_answer`, `state.follow_up_answers`, `state.next_question`, `followUpAnswer`, and `submitFollowUp`.
- Produces: the existing question/answer history in a scrollable timeline and a sticky answer composer.

- [x] **Step 1: Preserve the existing chat history contract**

Both chat stages must retain:

```vue
ref="messageList"
state.open_answer
state.follow_up_answers
state.next_question
@keydown.enter="handleFollowUpEnter"
```

- [x] **Step 2: Apply the workbench layout**

Use an elevated chat surface with an independently scrolling message area, assistant and patient message alignment, a subdued context label, and a sticky composer within the main panel. Keep the safety notice visible but visually secondary to the current question.

- [x] **Step 3: Run full verification**

Run: `npm test`

Expected: all frontend tests pass.

Run: `npm run build`

Expected: Vite produces `frontend/output` without compile errors.

- [x] **Step 4: Visually inspect desktop and mobile**

Open the local app at `http://127.0.0.1:5173/`, verify the baseline screen at desktop width and the chat screen at both desktop and mobile widths, and confirm that the primary action is visible and text does not overlap.
