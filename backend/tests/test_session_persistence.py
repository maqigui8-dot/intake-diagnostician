import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import Base
from intake_flow import (
    configure_intake_repository,
    get_intake_state,
    set_baseline,
    submit_open_answer,
)
from repository import SqlAlchemyIntakeRepository


class SessionPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def tearDown(self):
        configure_intake_repository(None)
        self.engine.dispose()

    def repository_factory(self):
        return SqlAlchemyIntakeRepository(self.session_factory)

    def test_unfinished_session_resumes_after_store_recreation(self):
        configure_intake_repository(self.repository_factory())
        set_baseline(
            "resume-a",
            {
                "age": 32,
                "sex": "female",
                "height_cm": 170,
                "weight_kg": 81,
                "measured_at": "2026-09-16",
            },
        )
        submit_open_answer("resume-a", "近半年体重增加")

        configure_intake_repository(self.repository_factory())
        restored = get_intake_state("resume-a")

        self.assertEqual(restored["open_answer"], "近半年体重增加")
        self.assertEqual(restored["phase"], "processing")


if __name__ == "__main__":
    unittest.main()
