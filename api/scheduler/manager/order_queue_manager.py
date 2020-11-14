import datetime
from typing import Counter

from scheduler.model.fulfillment_queue_node import FulfillmentQueueNode


class OrderQueueManager(object):
    def __init__(self):
        self.origin_queue_lookup = {}
        self.order_lookup = {}
        self.queued_orders = {}
        self.origin_due_quantity_counter = Counter()
        self.current_date = datetime.datetime.min

    def add_origin(self, origin_id):
        if origin_id not in self.origin_queue_lookup:
            self.origin_queue_lookup[origin_id] = None

    def enqueue_daily_order(self, customer_orders):
        order_dates = [*map(lambda x: x.order_date, customer_orders)]
        assert len(set(order_dates)) == 1 and order_dates[0] >= self.current_date, 'please add the daily orders in an ascending manner'
        self.current_date = order_dates[0]
        customer_orders = sorted(customer_orders, key=lambda x: x.quantity)
        for order in customer_orders:
            self._enqueue_order(order)

    def claim_fulfillment(self, origin_id, order_id, quantity):
        def dequeue_node(node):
            if node.prev is not None:
                node.prev.next = node.next
            if node.next is not None:
                node.next.prev = node.prev
        assert origin_id in self.origin_queue_lookup and order_id in self.queued_orders, 'fulfill for unknown order'
        assert quantity <= self.queued_orders[order_id].quantity, 'fulfillment overflow'
        average_quantity_before = self.queued_orders[order_id].origin_average_quantity()
        oids = self.queued_orders[order_id].fulfillment_origin_ids
        if quantity < self.queued_orders[order_id].quantity:
            self.queued_orders[order_id].quantity -= quantity
            average_quantity_after = self.queued_orders[order_id].origin_average_quantity()
        elif quantity == self.queued_orders[order_id].quantity:
            self.queued_orders.pop(order_id, None)
            for node in self.order_lookup[order_id]:
                if node.prev is None:
                    self.origin_queue_lookup[node.origin_id] = node.next
                dequeue_node(node)
        average_quantity_after = 0 if order_id not in self.queued_orders else self.queued_orders[order_id].origin_average_quantity()
        for oid in oids:
            self.origin_due_quantity_counter[oid] -= average_quantity_before - average_quantity_after

    def peek_order_queue_content(self, origin_id, min_quantity_sum, min_order_count):
        assert origin_id in self.origin_queue_lookup, 'origin does not exist'
        order_quantity_sum = 0
        peek_orders, head = [], self.origin_queue_lookup[origin_id]
        while head is not None and (order_quantity_sum < min_quantity_sum or len(peek_orders) < min_order_count):
            peek_orders.append(self.queued_orders[head.order_id])
            order_quantity_sum += peek_orders[-1].quantity
            head = head.next
        return peek_orders

    def order_queue_content(self, origin_id):
        assert origin_id in self.origin_queue_lookup, 'origin does not exist'
        order_ids, head = [], self.origin_queue_lookup[origin_id]
        while head is not None:
            order_ids.append(head.order_id)
            head = head.next
        return [self.queued_orders[order_id] for order_id in order_ids]

    def get_origin_average_due_quantity(self, origin_id):
        return self.origin_due_quantity_counter[origin_id]

    def _enqueue_order(self, customer_order):
        def enqueue_node(head, node):
            tail = head
            while tail.next is not None:
                tail = tail.next
            tail.next = node
            node.prev = tail
            node.next = None
        assert customer_order.order_id not in self.order_lookup, 'one order can only be added once'
        for origin_id in customer_order.fulfillment_origin_ids:
            self.origin_due_quantity_counter[origin_id] += customer_order.origin_average_quantity()
        self.order_lookup[customer_order.order_id] = []
        self.queued_orders[customer_order.order_id] = customer_order
        for origin_id in customer_order.fulfillment_origin_ids:
            node = FulfillmentQueueNode(origin_id, customer_order.order_id)
            if self.origin_queue_lookup[origin_id] is None:
                self.origin_queue_lookup[origin_id] = node
            else:
                enqueue_node(self.origin_queue_lookup[origin_id], node)
            self.order_lookup[customer_order.order_id].append(node)
