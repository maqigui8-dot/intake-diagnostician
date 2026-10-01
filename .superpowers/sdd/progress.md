# SDD Progress

Baseline: backend 76/76 passed; frontend 16/16 passed.
Task 1: in progress
Task 1: complete (snapshot review clean; backend 80/80, frontend 17/17)
Task 2: complete (snapshot review clean; backend 93/93)
Task 3: complete (independent review approved; backend 121/121, frontend 18/18, build passed)
Task 4: complete (review + 2 re-review fixes; backend 132/132, frontend 18/18)
Task 5: complete (review approved; backend 134/134)
  Minor (defer to final review): tcm-intake-checklist/SKILL.md:33 references 妊娠与生育信息 in conditional example but it is not enumerated in the layer list.
Task 6: complete (review approved; 1 Important + 4 Minor fixed and re-reviewed; backend 135/135, frontend 26/26, build passed)
Task 7: complete (review approved; backend 144/144, frontend 29/29, build passed)
  Minor (accepted/deferred):
  - test_exam_recommendations.py duplicate red-flag test — REMOVED (suite now 143 tests).
  - DoctorExecutionPanel drops 基础测量 field-group raw evidence (parsed values still shown in baseline_assessment).
  - doctor-view.test.mjs checks are shallow source-string checks (no Vue harness).
  - waist (layer=risk) grouped under 肥胖病程与可能病因 rather than 基础测量 — debatable.
  - doctor-view.js scoreTone now a dead export (no production caller).
Task 8: complete (backend 143/143, frontend 29/29, build passed; backend :8000 + frontend :5173 served; API flow smoke test passed baseline→open→analyze(LLM)→doctor-summary)
