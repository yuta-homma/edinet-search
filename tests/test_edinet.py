import unittest
import freezegun
from unittest import TestCase
from app.edinet import Edinet
from unittest_data_provider import data_provider

class TestEdinet(TestCase):

    __make_day_list_data_provider = lambda: [
        # 1-3月のケース
        ({'start':'2021-04-01', 'end': '2022-03-31'}, '2022-03-31 00:00:00'),
        # それ以外のケース
        ({'start':'2022-04-01', 'end': '2022-11-22'}, '2022-11-22 00:00:00')
    ]

    @data_provider(__make_day_list_data_provider)
    def test_init(self, expect, freeze) -> None:
        # Arrange
        freezer = freezegun.freeze_time(freeze)
        freezer.start()

        # Act
        edinet = Edinet()
        freezer.stop()

        # Assert
        self.assertEqual(expect['start'], edinet.start_date.strftime('%Y-%m-%d'))
        self.assertEqual(expect['end'], edinet.end_date.strftime('%Y-%m-%d'))

if __name__ == "__main__":
    unittest.main()
