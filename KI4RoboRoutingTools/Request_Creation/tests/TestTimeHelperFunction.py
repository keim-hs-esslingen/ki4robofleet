import unittest
from helper.TimeHelperFunction import timediff_seconds, to_car2go_format, CAR2GO_DATETIME_FORMAT
from datetime import datetime


class MyTestCase(unittest.TestCase):
    def test_date_conversion(self):
        first_date = datetime(2014, 10, 10, 12, 00, 00)
        test1_date_str = datetime(2014, 10, 10, 12, 00, 30).strftime(CAR2GO_DATETIME_FORMAT)  # + 30 seconds
        test2_date_str = datetime(2014, 10, 10, 11, 59, 30).strftime(CAR2GO_DATETIME_FORMAT)  # - 30 seconds
        test3_date_str = datetime(2014, 10, 10, 11, 59, 30).isoformat()
        test4_date_str = '2014-10-11 10:37:28'
        self.assertEqual(timediff_seconds(first_date, test1_date_str), 30)
        self.assertEqual(timediff_seconds(first_date, test2_date_str), 30)
        with self.assertRaises(RuntimeError):
            timediff_seconds(first_date, test3_date_str)
        self.assertEqual(timediff_seconds(first_date, test4_date_str), 22 * 3600 + 37 * 60 + 28)

    def test_conversion(self):
        self.assertEqual('2014-10-11 10:37:28', to_car2go_format(datetime(2014, 10, 11, 10, 37, 28)))

if __name__ == '__main__':
    unittest.main()
