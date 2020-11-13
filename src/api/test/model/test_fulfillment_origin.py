import datetime
import unittest

from scheduler.model.fulfillment_origin import FulfillmentOrigin


class TestFulfillmentOrigin(unittest.TestCase):
    def test_constructor(self):
        self.assertIsNotNone(FulfillmentOrigin('site', 'product'))

    def test_add_supply(self):
        sut = FulfillmentOrigin('site', 'product')
        quantity, date = 10, datetime.datetime.today()
        sut.add_supply(quantity, date)
        self.assertEqual(sut.cached_supply_quantity, quantity)
        self.assertEqual(sut.history_supply_dates, [date])
        self.assertEqual(sut.history_supply_quantities, [quantity])

    def test_consume_supply(self):
        sut = FulfillmentOrigin('site', 'product')
        quantity, date = 10, datetime.datetime.today()
        sut.add_supply(quantity, date)
        with self.assertRaisesRegex(AssertionError, 'supply consumption quantity greater than cache'):
            sut.consume_supply(100)
        sut.consume_supply(5)
        self.assertEqual(sut.cached_supply_quantity, 5)

    def test_average_daily_supply(self):
        sut = FulfillmentOrigin('site', 'product')
        self.assertEqual(sut.average_daily_supply(datetime.datetime.today()), 0)
        quantity, date = 10, datetime.datetime.today()
        sut.add_supply(quantity, date)
        self.assertEqual(sut.average_daily_supply(date), quantity)
        day_shift = 2
        self.assertEqual(sut.average_daily_supply(date + datetime.timedelta(days=day_shift)), quantity / day_shift)
