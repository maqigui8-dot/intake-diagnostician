# MySQL Full Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace in-memory sessions and JSON record storage with transactional MySQL persistence while preserving existing API responses and intake-rule behavior.

**Architecture:** Add SQLAlchemy models and a repository that reconstructs the existing intake-state dictionaries consumed by the domain modules. FastAPI routes continue calling the existing flow functions, while those functions persist each mutation through the repository. Alembic owns schema evolution and a separate importer migrates legacy JSON records idempotently.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, PyMySQL, MySQL 8, unittest, SQLite for repository unit tests

**Test convention:** Every test snippet below is a method on `unittest.TestCase` or `unittest.IsolatedAsyncioTestCase`; shared repositories, temporary directories and application overrides are created in `setUp()` and exposed through `self`.

## Global Constraints

- `DATABASE_URL` is mandatory; production code must not silently fall back to JSON or memory.
- Existing API paths and patient-safe response structures remain compatible.
- Completeness scoring, question selection and stop decisions remain in domain modules, not ORM models or SQL.
- All patient queries explicitly include `patient_id`; the initial default remains `demo-zhang`.
- Follow-up answer insertion and session-state mutation commit atomically.
- Existing 153 backend tests and 33 frontend tests must continue to pass.
- Legacy JSON files remain untouched after import.
- The current directory is not a Git repository; commit steps are documented but skipped unless Git is initialized.

---

## File Structure

- Create `backend/db.py`: engine, session factory, declarative base and database health check.
- Create `backend/models.py`: SQLAlchemy table mappings only.
- Create `backend/repository.py`: persistence interface and SQLAlchemy implementation.
- Create `backend/migrations/env.py`, `backend/migrations/script.py.mako`, `backend/migrations/versions/20260916_01_initial_persistence.py`: Alembic environment and initial schema.
- Create `backend/alembic.ini`: migration configuration using application `DATABASE_URL`.
- Create `backend/scripts/migrate_json_records.py`: idempotent legacy importer.
- Create `backend/tests/test_db_models.py`: schema constraints and relationship tests.
- Create `backend/tests/test_repository.py`: CRUD, isolation, atomicity and idempotency tests.
- Create `backend/tests/test_session_persistence.py`: flow restart and recovery tests.
- Create `backend/tests/test_json_migration.py`: importer tests.
- Modify `backend/intake_flow.py`: replace global dictionary store with repository-backed session store.
- Modify `backend/main.py`: database lifecycle, report persistence, patient-history queries and health status.
- Modify `backend/requirements.txt`: persistence dependencies.
- Create `.env.example`: documented runtime variables without credentials.
- Modify `README.md`: MySQL setup, migrations, import and test commands.

---

### Task 1: Database foundation and schema

**Files:**
- Create: `backend/db.py`
- Create: `backend/models.py`
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`
- Create: `backend/migrations/versions/20260916_01_initial_persistence.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_db_models.py`

**Interfaces:**
- Produces: `Base`, `SessionLocal`, `get_database_session()`, `check_database()`, and ORM classes `Patient`, `IntakeSessionModel`, `BaselineMeasurement`, `IntakeFieldState`, `FollowUpAnswer`, `RecommendedExam`, `IntakeReport`, `AuditEvent`, `DoctorReview`.

- [ ] **Step 1: Add a failing schema test**

```python
from sqlalchemy import create_engine, inspect
from models import Base


def test_all_persistence_tables_are_created(self):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    self.assertEqual(set(inspect(engine).get_table_names()), {
        "patients", "intake_sessions", "baseline_measurements",
        "intake_field_states", "follow_up_answers", "recommended_exams",
        "intake_reports", "audit_events", "doctor_reviews",
    })
```

- [ ] **Step 2: Run the schema test and verify failure**

Run: `python -m unittest tests.test_db_models -v`

Expected: import failure for `models` or missing tables.

- [ ] **Step 3: Add dependencies and database primitives**

Append to `backend/requirements.txt`:

```text
SQLAlchemy>=2.0,<3.0
alembic>=1.13,<2.0
PyMySQL>=1.1,<2.0
```

Implement `backend/db.py` with lazy configuration so tests may inject an engine:

```python
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL", "")
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False) if engine else None


@contextmanager
def get_database_session():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is required")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database() -> bool:
    if engine is None:
        return False
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
```

- [ ] **Step 4: Implement ORM models and constraints**

Use SQLAlchemy 2 typed mappings. Define foreign keys with `ondelete="CASCADE"`, `utf8mb4`-safe text columns, JSON columns for structured payloads, unique constraints on `(patient_id, id)`, `(session_id, field_key)`, `(session_id, sequence_no)` and `IntakeReport.session_id`, plus `version` defaulting to `1`.

- [ ] **Step 5: Add Alembic configuration and initial migration**

The migration must create the nine tables, indexes on `patient_id`, `session_id`, `created_at`, and every uniqueness constraint declared by the models. `migrations/env.py` must read `DATABASE_URL` from the environment and set `target_metadata = Base.metadata`.

- [ ] **Step 6: Run schema tests**

Run: `python -m unittest tests.test_db_models -v`

Expected: all schema tests pass.

- [ ] **Step 7: Commit when Git is available**

```bash
git add backend/db.py backend/models.py backend/alembic.ini backend/migrations backend/requirements.txt backend/tests/test_db_models.py
git commit -m "feat: add mysql persistence schema"
```

---

### Task 2: Repository and state serialization

**Files:**
- Create: `backend/repository.py`
- Test: `backend/tests/test_repository.py`

**Interfaces:**
- Consumes: ORM classes and a SQLAlchemy `Session`.
- Produces: `SqlAlchemyIntakeRepository`, `create_initial_state(session_id, patient_id)`, `get_or_create_session()`, `save_session_state()`, `save_report()`, `list_patient_reports()`, and `get_patient_report()`.

- [ ] **Step 1: Write failing repository tests**

```python
def test_session_round_trip_preserves_follow_up_state(self):
    state = self.repository.get_or_create_session("session-a", "patient-a")
    state.update({"phase": "follow_up", "turn": 2, "current_field_key": "allergies"})
    state["follow_up_answers"].append({
        "question": "有药物过敏吗？", "answer": "没有",
        "question_key": "allergies", "question_kind": "required",
        "attempt_number": 1, "answer_quality": "provided",
        "created_at": "2026-09-16T10:00:00",
    })
    self.repository.save_session_state(state)
    restored = self.repository.get_or_create_session("session-a", "patient-a")
    self.assertEqual(restored["phase"], "follow_up")
    self.assertEqual(restored["follow_up_answers"][0]["answer"], "没有")


def test_patient_cannot_read_another_patients_report(self):
    self.repository.save_report("patient-a", {
        "record_id": "record-a", "session_id": "s1", "report_markdown": "A"
    })
    self.assertIsNone(
        self.repository.get_patient_report("patient-b", "record-a")
    )
```

- [ ] **Step 2: Run repository tests and verify failure**

Run: `python -m unittest tests.test_repository -v`

Expected: import failure for `repository`.

- [ ] **Step 3: Implement dictionary-to-row serialization**

`get_or_create_session(session_id, patient_id)` must create the patient, session and initial field rows when absent. Reconstructed dictionaries must retain every key currently initialized by `IntakeSessionStore.get`, including `audit`, `field_states`, `execution`, `blocking_keys`, `conflicts`, `safety_alerts` and `recommended_exams`.

- [ ] **Step 4: Implement atomic snapshot persistence**

`save_session_state(state, expected_version=None)` must update the session row, upsert one baseline row, upsert field rows, insert only missing follow-up sequence numbers, replace recommended exams, append only new audit events and flush inside the caller transaction. When `expected_version` differs from the stored version, raise `ConcurrentSessionUpdate`.

- [ ] **Step 5: Implement report and history methods**

`save_report()` must be idempotent on `session_id`; list and detail methods must always filter by `patient_id` and return the existing patient-facing dictionary shape expected by `patient_history.py`.

- [ ] **Step 6: Run repository tests**

Run: `python -m unittest tests.test_repository -v`

Expected: CRUD, isolation, idempotency and conflict tests pass.

- [ ] **Step 7: Commit when Git is available**

```bash
git add backend/repository.py backend/tests/test_repository.py
git commit -m "feat: add transactional intake repository"
```

---

### Task 3: Persist the intake flow and restore sessions

**Files:**
- Modify: `backend/intake_flow.py`
- Modify: `backend/skill_analysis.py`
- Test: `backend/tests/test_session_persistence.py`

**Interfaces:**
- Consumes: `SqlAlchemyIntakeRepository`.
- Produces: `configure_intake_repository(repository)`, repository-backed `IntakeSessionStore`, and persisted versions of all state-mutating flow functions.

- [ ] **Step 1: Write a failing restart-recovery test**

```python
def test_unfinished_session_resumes_after_store_recreation(self):
    first = self.repository_factory()
    configure_intake_repository(first)
    set_baseline("resume-a", baseline_payload())
    submit_open_answer("resume-a", "近半年体重增加")

    second = self.repository_factory()
    configure_intake_repository(second)
    restored = get_intake_state("resume-a")

    self.assertEqual(restored["open_answer"], "近半年体重增加")
    self.assertEqual(restored["phase"], "processing")
```

- [ ] **Step 2: Run the recovery test and verify failure**

Run: `python -m unittest tests.test_session_persistence -v`

Expected: missing `configure_intake_repository` or state lost after store recreation.

- [ ] **Step 3: Replace the dictionary-only store**

Keep the existing `IntakeSessionStore` public methods, but delegate `get()` to `repository.get_or_create_session()` and add `save(state)` to persist the current snapshot. Preserve `clear()` as a test helper that clears only the configured test repository.

- [ ] **Step 4: Persist every mutation boundary**

Call `intake_sessions.save(session)` after successful mutation in `set_baseline`, `submit_open_answer`, `submit_follow_up_answer`, `apply_analysis_turn` and `complete_intake_session`. Ensure analysis extraction, stop decision, generated question and report are committed as one state snapshot.

- [ ] **Step 5: Preserve deterministic rule behavior**

Run focused tests:

```powershell
python -m unittest tests.test_intake_flow tests.test_intake_execution tests.test_intake_question_policy -v
```

Expected: all existing flow, score and stopping tests pass unchanged.

- [ ] **Step 6: Run restart-recovery tests**

Run: `python -m unittest tests.test_session_persistence -v`

Expected: restart, current-question, attempt-count and completed-report recovery tests pass.

- [ ] **Step 7: Commit when Git is available**

```bash
git add backend/intake_flow.py backend/skill_analysis.py backend/tests/test_session_persistence.py
git commit -m "feat: persist and restore intake sessions"
```

---

### Task 4: Replace JSON history APIs with database queries

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/patient_history.py`
- Test: `backend/tests/test_patient_history.py`
- Test: `backend/tests/test_skill_analysis.py`

**Interfaces:**
- Consumes: repository report and history methods.
- Produces: database-backed `/api/save_record`, `/api/patient/records`, `/api/patient/records/{record_id}`, `/api/records`, and `/api/records/{record_id}`.

- [ ] **Step 1: Add failing API persistence tests**

```python
async def test_save_record_is_idempotent_in_database(self):
    first = await main.save_record(main.SaveRecordRequest(session_id="complete-a"))
    second = await main.save_record(main.SaveRecordRequest(session_id="complete-a"))
    self.assertEqual(first["record_id"], second["record_id"])
    self.assertEqual(len(self.api_repository.list_patient_reports("demo-zhang")), 1)
```

- [ ] **Step 2: Run focused API tests and verify failure**

Run: `python -m unittest tests.test_patient_history tests.test_skill_analysis.ApiIntegrationTests -v`

Expected: assertions show JSON-backed behavior or missing injected repository.

- [ ] **Step 3: Inject repository into FastAPI application code**

Create one repository per request from `get_database_session()` or use a FastAPI dependency. Remove `save_record()`, `load_all_records()` and `load_record()` filesystem calls from live API routes while leaving import-only helpers in the migration script.

- [ ] **Step 4: Map concurrency and ownership errors**

Translate `ConcurrentSessionUpdate` to HTTP 409. Return HTTP 404 when report ownership does not match `DEMO_PATIENT_ID`. Do not include database connection strings or SQL in client responses.

- [ ] **Step 5: Run history and API tests**

Run: `python -m unittest tests.test_patient_history tests.test_skill_analysis.ApiIntegrationTests -v`

Expected: patient isolation, save idempotency and response compatibility tests pass.

- [ ] **Step 6: Commit when Git is available**

```bash
git add backend/main.py backend/patient_history.py backend/tests/test_patient_history.py backend/tests/test_skill_analysis.py
git commit -m "feat: persist patient reports in mysql"
```

---

### Task 5: Database lifecycle and health reporting

**Files:**
- Modify: `backend/main.py`
- Create: `.env.example`
- Test: `backend/tests/test_database_health.py`

**Interfaces:**
- Consumes: `check_database()` and repository configuration.
- Produces: startup validation and database-aware `/api/health`.

- [ ] **Step 1: Write failing health tests**

```python
async def test_health_reports_database_status(self):
    with patch.object(main, "check_database", return_value=True):
        result = await main.health()
    self.assertEqual(result["database"], "ok")
```

- [ ] **Step 2: Run health tests and verify failure**

Run: `python -m unittest tests.test_database_health -v`

Expected: response lacks `database`.

- [ ] **Step 3: Add application startup validation**

Use a FastAPI lifespan handler to call `check_database()` and configure the intake repository. Raise `RuntimeError("Database is unavailable")` before serving requests when the connection fails.

- [ ] **Step 4: Add environment example**

Create `.env.example`:

```dotenv
DATABASE_URL=mysql+pymysql://intake_user:change_me@127.0.0.1:3306/intake_diagnostician?charset=utf8mb4
DEEPSEEK_API_KEY=
```

- [ ] **Step 5: Run health tests**

Run: `python -m unittest tests.test_database_health -v`

Expected: available and unavailable database states are both covered.

- [ ] **Step 6: Commit when Git is available**

```bash
git add backend/main.py backend/tests/test_database_health.py .env.example
git commit -m "feat: validate database lifecycle"
```

---

### Task 6: Legacy JSON migration

**Files:**
- Create: `backend/scripts/migrate_json_records.py`
- Create: `backend/scripts/__init__.py`
- Test: `backend/tests/test_json_migration.py`

**Interfaces:**
- Consumes: `SqlAlchemyIntakeRepository` and legacy `backend/records/*.json` files.
- Produces: `import_record(path, repository)`, `migrate_directory(path, repository, dry_run=False)` and CLI flags `--records-dir`, `--dry-run`.

- [ ] **Step 1: Write failing importer tests**

```python
def test_import_is_idempotent(self):
    source = self.tmp_path / "record-a.json"
    source.write_text(json.dumps({
        "record_id": "record-a", "session_id": "session-a",
        "patient_id": "demo-zhang", "markdown_table": "报告",
        "follow_up_answers": [], "recommended_exams": [],
    }, ensure_ascii=False), encoding="utf-8")
    first = migrate_directory(self.tmp_path, self.repository)
    second = migrate_directory(self.tmp_path, self.repository)
    self.assertEqual(first.imported, 1)
    self.assertEqual(second.skipped, 1)
```

- [ ] **Step 2: Run importer tests and verify failure**

Run: `python -m unittest tests.test_json_migration -v`

Expected: missing migration module.

- [ ] **Step 3: Implement parser and dry-run mode**

Map missing `patient_id` to `demo-zhang`, retain timestamps and known report fields, store unmapped keys in an `audit_events` payload with `event_type="legacy_record_imported"`, and collect per-file errors without aborting the directory.

- [ ] **Step 4: Implement idempotent database import**

Skip an existing `record_id` or `session_id`, do not modify the source file, and return a summary dataclass with `scanned`, `imported`, `skipped` and `failed` counts.

- [ ] **Step 5: Run importer tests**

Run: `python -m unittest tests.test_json_migration -v`

Expected: normal, duplicate, missing-patient, invalid-JSON and dry-run tests pass.

- [ ] **Step 6: Commit when Git is available**

```bash
git add backend/scripts backend/tests/test_json_migration.py
git commit -m "feat: migrate legacy json records"
```

---

### Task 7: Documentation and full regression

**Files:**
- Modify: `README.md`
- Modify: `backend/tests/test_skill_analysis.py` only if dependency injection requires fixture updates without weakening assertions.

**Interfaces:**
- Produces: reproducible MySQL setup and verified compatibility.

- [ ] **Step 1: Document local database setup**

Add exact commands:

```sql
CREATE DATABASE intake_diagnostician CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'intake_user'@'localhost' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON intake_diagnostician.* TO 'intake_user'@'localhost';
```

Document `copy .env.example backend/.env`, `alembic upgrade head`, JSON dry-run/import and application startup.

- [ ] **Step 2: Run all backend tests**

Run: `python -m unittest discover -s tests -v`

Expected: existing and new backend tests all pass.

- [ ] **Step 3: Run all frontend tests**

Run: `npm.cmd test`

Expected: 33 tests pass.

- [ ] **Step 4: Run frontend production build**

Run: `npm.cmd run build`

Expected: Vite build succeeds with no unresolved API-contract imports.

- [ ] **Step 5: Verify migrations against MySQL**

Run from `backend` with a test `DATABASE_URL`:

```powershell
python -m alembic upgrade head
python -m alembic current
```

Expected: current revision is `20260916_01`.

- [ ] **Step 6: Verify restart recovery manually**

Create a session, submit baseline and an open answer, stop Uvicorn, restart it, fetch `/api/intake/session/{session_id}`, and verify the phase, answer, current question and attempts match the pre-restart state.

- [ ] **Step 7: Commit when Git is available**

```bash
git add README.md backend/tests
git commit -m "docs: add mysql setup and verification"
```
