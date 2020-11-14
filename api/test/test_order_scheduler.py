import datetime
from scheduler.manager.order_queue_manager import OrderQueueManager
from scheduler.manager.fulfillment_origin_manager import FulfillmentOriginManager
import unittest
from unittest.mock import patch

from scheduler.order_scheduler import OrderScheduler
from scheduler.manager.sourcing_rule_manager import SourcingRuleManager


class TestOrderScheduler(unittest.TestCase):
    def test_constructor(self):
        self.assertIsNotNone(OrderScheduler())

    def test_add_sourcing_rule(self):
        sut = OrderScheduler()
        with patch.object(FulfillmentOriginManager, 'add_origin') as mock_fom_add_origin,\
            patch.object(FulfillmentOriginManager, 'get_origin_id', return_value='origin_id') as mock_fom_get_origin_id,\
            patch.object(SourcingRuleManager, 'add_sourcing_rule') as mock_srm_add_sourcing_rule,\
            patch.object(OrderQueueManager, 'add_origin') as mock_oqm_add_origin:
            sut.add_sourcing_rule('customer', 'site', 'product')
            mock_fom_add_origin.assert_called_once_with('site', 'product')
            mock_srm_add_sourcing_rule.assert_called_once_with('customer', 'site', 'product')
            mock_fom_get_origin_id.assert_called_once_with('site', 'product')
            mock_oqm_add_origin.assert_called_once_with('origin_id')

    def test_claim_supply_plan(self):
        sut = OrderScheduler()
        sut.current_date = datetime.datetime(2020, 1, 2)
        with self.assertRaisesRegex(AssertionError, 'you cannot add plan for the past'):
            sut.claim_supply_plan('site', 'product', 1, datetime.datetime(2020, 1, 1))
        date = datetime.datetime(2020, 1, 3)
        sut.claim_supply_plan('site_1', 'product_1', 100, date)
        sut.claim_supply_plan('site_1', 'product_1', 100, date)
        self.assertEqual(sut.supply_plan_pool[date], [('site_1', 'product_1', date, 100)] * 2)

    def test_claim_order(self):
        sut = OrderScheduler()
        sut.current_date = datetime.datetime(2020, 1, 2)
        with self.assertRaisesRegex(AssertionError, 'you cannot add order in the past'):
            sut.claim_order('customer', 'product', 1, datetime.datetime(2020, 1, 1))
        date = datetime.datetime(2020, 1, 3)
        sut.claim_order('customer_1', 'product_1', 100, date)
        sut.claim_order('customer_1', 'product_1', 100, date)
        self.assertEqual(sut.order_pool[date], [('customer_1', 'product_1', date, 100)] * 2)

    def test_plan_fulfillment(self):
        sut = OrderScheduler()
        self.assertEqual(len(sut.plan_fulfillment(datetime.datetime(2020, 1, 1))), 0)
        sut = self._default_sut()
        fulfill_date = datetime.datetime(2020, 1, 2)
        sut.claim_supply_plan('site_1', 'product_1', 10, fulfill_date)
        self.assertEqual(len(sut.plan_fulfillment(fulfill_date)), 1)
        fulfill_date = datetime.datetime(2020, 1, 3)
        sut.claim_supply_plan('site_2', 'product_1', 7, fulfill_date)
        self.assertEqual(len(sut.plan_fulfillment(fulfill_date)), 2)
        sut = self._default_sut()
        fulfill_date = datetime.datetime(2020, 1, 2)
        sut.claim_supply_plan('site_1', 'product_1', 10, fulfill_date)
        sut.plan_fulfillment(fulfill_date)
        fulfill_date = datetime.datetime(2020, 1, 3)
        sut.claim_supply_plan('site_1', 'product_1', 20, fulfill_date)
        sut.claim_supply_plan('site_3', 'product_1', 10, fulfill_date)
        plans = sut.plan_fulfillment(fulfill_date)
        self.assertIn(('customer_3', 'product_1', datetime.datetime(2020, 1, 2), 'site_1', fulfill_date, 20), plans)
        self.assertIn(('customer_2', 'product_1', datetime.datetime(2020, 1, 1), 'site_3', fulfill_date, 5), plans)
        self.assertNotIn(('customer_3', 'product_1', datetime.datetime(2020, 1, 2), 'site_3', fulfill_date, 20), plans)

    def test__distribute_supply(self):
        sut = OrderScheduler()
        with self.assertRaisesRegex(AssertionError, 'supply quantity must be greater than 0'):
            sut._distribute_supply([1, 1, 1], 0)
        self.assertEqual(sut._distribute_supply([], 1), ([], 1))
        self.assertEqual(sut._distribute_supply([1, 1, 1], 5), ([1, 1, 1], 2))
        self.assertEqual(sut._distribute_supply([2, 2], 5), ([2, 2], 1))
        self.assertEqual(sut._distribute_supply([5], 5), ([5], 0))
        self.assertEqual(sut._distribute_supply([5, 10], 5), ([5, 0], 0))
        self.assertEqual(sut._distribute_supply([5, 10, 5, 5], 18), ([5, 10, 3, 0], 0))
        self.assertEqual(sut._distribute_supply([10], 5), ([5], 0))
        self.assertEqual(sut._distribute_supply([11, 3, 2], 10), ([7, 2, 1], 0))
        self.assertEqual(sut._distribute_supply([10, 10, 10, 10], 9), ([8, 1, 0, 0], 0))
        self.assertEqual(sut._distribute_supply([15, 1, 1, 1], 10), ([8, 1, 1, 0], 0))

    def test__import_order_supply(self):
        sut = OrderScheduler()
        sut.add_sourcing_rule('customer_1', 'site_1', 'product_1')
        sut.add_sourcing_rule('customer_1', 'site_1', 'product_2')
        sut.add_sourcing_rule('customer_2', 'site_1', 'product_1')
        sut.add_sourcing_rule('customer_2', 'site_2', 'product_2')
        date_1 = datetime.datetime(2020, 1, 1)
        date_2 = datetime.datetime(2020, 1, 3)
        sut.claim_order('customer_1', 'product_1', 100, date_1)
        sut.claim_order('customer_1', 'product_1', 200, date_1)
        sut.claim_order('customer_1', 'product_2', 50, date_1)
        sut.claim_order('customer_2', 'product_1', 50, date_1)
        sut.claim_order('customer_2', 'product_2', 50, date_2)
        sut.claim_supply_plan('site_1', 'product_1', 100, date_1)
        sut.claim_supply_plan('site_1', 'product_1', 200, date_1)
        sut.claim_supply_plan('site_1', 'product_2', 50, date_1)
        sut.claim_supply_plan('site_2', 'product_2', 50, date_2)
        sut.current_date = datetime.datetime(2020, 1, 2)
        sut._import_order_supply()
        self.assertNotIn(date_1, sut.supply_plan_pool)
        self.assertNotIn(date_1, sut.order_pool)
        self.assertEqual(sut.order_pool[date_2], [('customer_2', 'product_2', date_2, 50)])
        self.assertEqual(sut.supply_plan_pool[date_2], [('site_2', 'product_2', date_2, 50)])
        self.assertEqual([*map(
            lambda x: x.quantity,
            sut.order_queue_manager.order_queue_content(sut.fulfillment_origin_manager.get_origin_id('site_1', 'product_1'))
        )], [50, 300])

    def _default_sut(self):
        sut = OrderScheduler()
        sut.add_sourcing_rule('customer_1', 'site_1', 'product_1')
        sut.add_sourcing_rule('customer_1', 'site_2', 'product_1')
        sut.add_sourcing_rule('customer_2', 'site_2', 'product_1')
        sut.add_sourcing_rule('customer_2', 'site_3', 'product_1')
        sut.add_sourcing_rule('customer_3', 'site_1', 'product_1')
        sut.add_sourcing_rule('customer_3', 'site_2', 'product_1')
        sut.add_sourcing_rule('customer_3', 'site_3', 'product_1')
        sut.claim_order('customer_1', 'product_1', 10, datetime.datetime(2020, 1, 1))
        sut.claim_order('customer_2', 'product_1', 5, datetime.datetime(2020, 1, 1))
        sut.claim_order('customer_3', 'product_1', 20, datetime.datetime(2020, 1, 2))
        return sut
