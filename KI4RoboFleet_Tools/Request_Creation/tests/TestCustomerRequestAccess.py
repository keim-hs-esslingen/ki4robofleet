import unittest
import os
from Python_Tools.Request_Creation.sumohelper.CustomerRequestAccess import CustomerRequestAccess, CustomerRequest
from datetime import datetime, timedelta

SIMU_START_DATETIME = datetime(year=2014, month=10, day=10, hour=12, minute=0, second=0)
SIMU_END_DATETIME = datetime(year=2014, month=10, day=10, hour=12, minute=59, second=59)

LIST_CUSTOMER_REQUESTS = [
    CustomerRequest(1000, "building.apartments", "12345", 12.51, "building.apartments", "67890", 99.0),
    CustomerRequest(2000, "building.apartments", "testfrom", 3.02145, "building.apartments", "testto", -90.23)
]


class TestCustomerRequestAccess(unittest.TestCase):
    def test_something(self):
        creator = CustomerRequestAccess(start_datetime=SIMU_START_DATETIME,
                                     sim_duration_seconds=int(
                                         (SIMU_END_DATETIME - SIMU_START_DATETIME).total_seconds()))
        creator.add_request(LIST_CUSTOMER_REQUESTS[0])
        creator.add_request(LIST_CUSTOMER_REQUESTS[1])
        with self.assertRaises(expected_exception=RuntimeError):
            creator.add_request(
                CustomerRequest(4000, "building.apartments", "bla", 234.01, "building.apartments", "1245", -1.0))
        # if file TestCustomerRequestAccess.xml exists, remove it
        if os.path.exists("TestCustomerRequestAccess.xml"):
            os.remove("TestCustomerRequestAccess.xml")
        creator.dump(filename="TestCustomerRequestAccess.xml", format="xml")
        reader = CustomerRequestAccess.read_from_file(filename="TestCustomerRequestAccess.xml", format="xml")
        self.assertListEqual(LIST_CUSTOMER_REQUESTS, reader.get_all())


if __name__ == '__main__':
    unittest.main()
