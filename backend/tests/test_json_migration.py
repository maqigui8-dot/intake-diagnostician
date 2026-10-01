import json
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import Base
from repository import SqlAlchemyIntakeRepository


class JsonMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.records_path = Path(self.temp_directory.name)
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.repository = SqlAlchemyIntakeRepository(factory)

    def tearDown(self):
        self.engine.dispose()
        self.temp_directory.cleanup()

    def write_record(self, filename="record-a.json"):
        source = self.records_path / filename
        source.write_text(
            json.dumps(
                {
                    "record_id": "record-a",
                    "session_id": "session-a",
                    "markdown_table": "报告",
                    "follow_up_answers": [],
                    "recommended_exams": [],
                    "legacy_extra": {"source": "old"},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return source

    def test_import_is_idempotent_and_defaults_patient(self):
        from scripts.migrate_json_records import migrate_directory

        self.write_record()
        first = migrate_directory(self.records_path, self.repository)
        second = migrate_directory(self.records_path, self.repository)

        self.assertEqual(first.imported, 1)
        self.assertEqual(second.skipped, 1)
        report = self.repository.get_patient_report("demo-zhang", "record-a")
        self.assertEqual(report["markdown_table"], "报告")

    def test_invalid_json_is_counted_without_aborting(self):
        from scripts.migrate_json_records import migrate_directory

        self.write_record()
        (self.records_path / "broken.json").write_text("{", encoding="utf-8")

        result = migrate_directory(self.records_path, self.repository)

        self.assertEqual(result.scanned, 2)
        self.assertEqual(result.imported, 1)
        self.assertEqual(result.failed, 1)

    def test_dry_run_does_not_write(self):
        from scripts.migrate_json_records import migrate_directory

        self.write_record()
        result = migrate_directory(self.records_path, self.repository, dry_run=True)

        self.assertEqual(result.imported, 1)
        self.assertIsNone(self.repository.get_patient_report("demo-zhang", "record-a"))


if __name__ == "__main__":
    unittest.main()
