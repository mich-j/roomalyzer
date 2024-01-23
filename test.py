"""Unit testing module"""
import unittest

import pandas as pd

from roomalyzer import Roomalyzer


class TestRoomalyzer(unittest.TestCase):
    """Roomalyzer unit test class"""

    @classmethod
    def setUpClass(cls):
        pass

    @staticmethod
    def make_test_instance():
        ra = Roomalyzer()
        df = pd.DataFrame(
            {
                "date": ["2024-01-03 20:00:00+00:00", "2024-01-03 21:00:00+00:00"],
                "temperature": [20, 22],
                "humidity": [70, 80],
            }
        )
        df["date"] = pd.to_datetime(df["date"])
        ra.data = df
        return ra

    def test_read_data(self):
        ra = Roomalyzer()
        ra.read_thingspeak(
            "https://api.thingspeak.com/channels/2394445/feeds.json?results=8000"
        )
        self.assertFalse(ra.data.empty)

    def test_average(self):
        ra = self.make_test_instance()
        avg = ra.calc_average_vals("24H", "0H")
        self.assertEqual(avg["temperature"].iloc[0], 21.0)
        self.assertEqual(avg["humidity"].iloc[0], 75.0)

    def test_summary(self):
        ra = self.make_test_instance()
        self.assertEqual(ra.summary[ra.temp].iloc[0], 20.0)
        self.assertEqual(ra.summary[ra.temp].iloc[1], 22.0)
        self.assertEqual(ra.summary[ra.hum].iloc[0], 70.0)
        self.assertEqual(ra.summary[ra.hum].iloc[1], 80.0)


if __name__ == "__main__":
    unittest.main()
