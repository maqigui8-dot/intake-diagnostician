import unittest
from unittest.mock import patch

import main


class DatabaseHealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_reports_database_status(self):
        with patch.object(main, "check_database", return_value=True):
            result = await main.health()
        self.assertEqual(result["database"], "ok")

    async def test_health_reports_unavailable_database(self):
        with patch.object(main, "check_database", return_value=False):
            result = await main.health()
        self.assertEqual(result["database"], "unavailable")


if __name__ == "__main__":
    unittest.main()
