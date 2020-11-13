import datetime
from unittest.mock import patch
import unittest

from scheduler.model.fulfillment_origin import FulfillmentOrigin
from scheduler.manager.fulfillment_origin_manager import FulfillmentOriginManager


class TestFulfillmentOriginManager(unittest.TestCase):
    def test_constructor(self):
        self.assertIsNotNone(FulfillmentOriginManager())

    def test_add_origin(self):
        sut = FulfillmentOriginManager()
        sut.add_origin('site_1', 'product_1', 'id_1')
        self.assertEqual(sut.origin_lookup['id_1'].site_name, 'site_1')
        self.assertEqual(sut.site_product_lookup['site_1']['product_1'], 'id_1')
        sut.add_origin('site_1', 'product_1')
        self.assertEqual(len(sut.origin_lookup), 1)
        self.assertEqual(len(sut.site_product_lookup), 1)
        sut.add_origin('site_1', 'product_2', 'id_2')
        self.assertEqual(sut.origin_lookup['id_2'].site_name, 'site_1')
        self.assertEqual(sut.site_product_lookup['site_1']['product_2'], 'id_2')
        sut.add_origin('site_2', 'product_1', 'id_3')
        self.assertEqual(sut.origin_lookup['id_3'].product_name, 'product_1')
        self.assertEqual(sut.site_product_lookup['site_2']['product_1'], 'id_3')

    def test_get_origin_id(self):
        sut = FulfillmentOriginManager()
        sut.add_origin('site_1', 'product_1', 'id_1')
        with self.assertRaisesRegex(AssertionError, 'unknown origin'):
            sut.get_origin_id('site_2', 'product_1')
        self.assertEqual(sut.get_origin_id('site_1', 'product_1'), 'id_1')

    def test_add_supply(self):
        sut = FulfillmentOriginManager()
        sut.add_origin('site_1', 'product_1', 'id_1')
        quantity, date = 10, datetime.datetime.today()
        with self.assertRaisesRegex(AssertionError, 'add supply for unknown origin'):
            sut.add_supply('site_2', 'product_1', quantity, date)
        with patch.object(FulfillmentOrigin, 'add_supply') as mock_method:
            sut.add_supply('site_1', 'product_1', quantity, date)
            mock_method.assert_called_once_with(quantity, date)

    def test_consume_supply(self):
        sut = FulfillmentOriginManager()
        sut.add_origin('site_1', 'product_1', 'id_1')
        quantity = 10
        with self.assertRaisesRegex(AssertionError, 'consume supply for unknown origin'):
            sut.consume_supply('id_2', quantity)
        with patch.object(FulfillmentOrigin, 'consume_supply') as mock_method:
            sut.consume_supply('id_1', quantity)
            mock_method.assert_called_once_with(quantity)
