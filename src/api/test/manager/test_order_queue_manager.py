import datetime
import unittest

from scheduler.model.customer_order import CustomerOrder
from scheduler.manager.order_queue_manager import OrderQueueManager


class TestOrderQueueManager(unittest.TestCase):
    def test_constructor(self):
        self.assertIsNotNone(OrderQueueManager())

    def test_add_origins(self):
        sut = self._default_sut()
        self.assertEqual(len(sut.origin_queue_lookup), 3)
        origin_ids = set([*sut.origin_queue_lookup.keys()])
        self.assertEqual(origin_ids, set(['origin_a', 'origin_b', 'origin_c']))

    def test_enqueue_daily_order(self):
        sut = self._default_sut()
        orders_1 = [
            CustomerOrder('c0', 'p1', 10, datetime.datetime(2020, 1, 1), 'order_a'),
            CustomerOrder('c1', 'p1', 20, datetime.datetime(2020, 1, 2), 'order_b')
        ]
        with self.assertRaisesRegex(Exception, 'please add the daily orders in an ascending manner'):
            sut.enqueue_daily_order(orders_1)
        orders_2 = [
            CustomerOrder('c0', 'p1', 10, datetime.datetime(2020, 1, 2), 'order_a'),
            CustomerOrder('c1', 'p1', 20, datetime.datetime(2020, 1, 2), 'order_b')
        ]
        sut.enqueue_daily_order(orders_2)
        self.assertEqual(sut.current_date, datetime.datetime(2020, 1, 2))
        self.assertEqual(len(sut.order_lookup), 2)
        self.assertEqual(len(sut.queued_orders), 2)
        orders_3 = [CustomerOrder('c0', 'p1', 10, datetime.datetime(2020, 1, 1), 'order_a')]
        with self.assertRaisesRegex(Exception, 'please add the daily orders in an ascending manner'):
            sut.enqueue_daily_order(orders_3)
        sut = self._sut_with_orders()
        self.assertListEqual([*map(lambda x: x.order_id, sut.orders_in_origin_queue('origin_a'))], ['order_a', 'order_c'])
        self.assertListEqual([*map(lambda x: x.order_id, sut.orders_in_origin_queue('origin_b'))], ['order_b', 'order_a', 'order_c'])
        self.assertListEqual([*map(lambda x: x.order_id, sut.orders_in_origin_queue('origin_c'))], ['order_b', 'order_c'])

    def test_claim_fulfillment(self):
        sut = self._sut_with_orders()
        with self.assertRaisesRegex(AssertionError, 'fulfill for unknown order'):
            sut.claim_fulfillment('origina', 'order_a', 1)
        with self.assertRaisesRegex(AssertionError, 'fulfill for unknown order'):
            sut.claim_fulfillment('origin_a', 'ordera', 1)
        with self.assertRaisesRegex(AssertionError, 'fulfillment overflow'):
            sut.claim_fulfillment('origin_a', 'order_a', 10000)
        sut.claim_fulfillment('origin_a', 'order_a', 5)
        self.assertEqual(sut.queued_orders['order_a'].quantity, 5)
        sut.claim_fulfillment('origin_b', 'order_a', 5)
        self.assertListEqual([*map(lambda x: x.order_id, sut.orders_in_origin_queue('origin_a'))], ['order_c'])
        self.assertListEqual([*map(lambda x: x.order_id, sut.orders_in_origin_queue('origin_b'))], ['order_b', 'order_c'])
        sut.claim_fulfillment('origin_c', 'order_c', 20)
        self.assertListEqual([*map(lambda x: x.order_id, sut.orders_in_origin_queue('origin_a'))], [])

    def test_orders_in_origin_queue(self):
        sut = self._sut_with_orders()
        self.assertListEqual([*map(lambda x: x.order_id, sut.orders_in_origin_queue('origin_a'))], ['order_a', 'order_c'])
        with self.assertRaisesRegex(AssertionError, 'origin does not exist'):
            sut.orders_in_origin_queue('origina')
        sut = self._default_sut()
        self.assertListEqual([*map(lambda x: x.order_id, sut.orders_in_origin_queue('origin_a'))], [])

    def test__euqueue_order(self):
        sut = self._default_sut()
        order_1 = CustomerOrder('c0', 'p1', 10, datetime.datetime(2020, 1, 1), 'order_a')
        sut._enqueue_order(order_1)
        self.assertEqual(len(sut.order_lookup['order_a']), 0)
        self.assertEqual(len(sut.queued_orders), 1)
        self.assertEqual(sut.queued_orders['order_a'].customer_name, 'c0')
        order_2 = CustomerOrder('c1', 'p1', 20, datetime.datetime(2020, 1, 2), 'order_b')
        order_2.fulfillment_origin_ids = set(['origin_a', 'origin_b'])
        sut._enqueue_order(order_2)
        self.assertEqual(len(sut.order_lookup['order_b']), 2)
        self.assertIn('origin_a', [*map(lambda x: x.origin_id, sut.order_lookup['order_b'])])
        self.assertIn('origin_b', [*map(lambda x: x.origin_id, sut.order_lookup['order_b'])])
        self.assertEqual(sut.origin_queue_lookup['origin_a'].order_id, 'order_b')
        order_3 = CustomerOrder('c2', 'p1', 15, datetime.datetime(2020, 1, 3), 'order_c')
        order_3.fulfillment_origin_ids = set(['origin_b', 'origin_c'])
        sut._enqueue_order(order_3)
        self.assertEqual(sut.origin_queue_lookup['origin_b'].next.order_id, 'order_c')
        self.assertEqual(sut.origin_queue_lookup['origin_b'].next.prev.order_id, 'order_b')
        with self.assertRaisesRegex(Exception, 'one order can only be added once'):
            sut._enqueue_order(order_1)

    def _default_sut(self):
        sut = OrderQueueManager()
        sut.add_origins(['origin_a', 'origin_b', 'origin_c'])
        return sut

    def _sut_with_orders(self):
        sut = self._default_sut()
        order_1 = CustomerOrder('c0', 'p1', 10, datetime.datetime(2020, 1, 1), 'order_a')
        order_1.fulfillment_origin_ids = ['origin_a', 'origin_b']
        order_2 = CustomerOrder('c1', 'p1', 5, datetime.datetime(2020, 1, 1), 'order_b')
        order_2.fulfillment_origin_ids = ['origin_b', 'origin_c']
        order_3 = CustomerOrder('c0', 'p1', 20, datetime.datetime(2020, 1, 2), 'order_c')
        order_3.fulfillment_origin_ids = ['origin_a', 'origin_b', 'origin_c']
        sut.enqueue_daily_order([order_1, order_2])
        sut.enqueue_daily_order([order_3])
        return sut
