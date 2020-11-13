import datetime

from scheduler.model.fulfillment_queue_node import FulfillmentQueueNode


class OrderQueueManager(object):
    def __init__(self):
        self.origin_queue_lookup = {}
        self.order_lookup = {}
        self.queued_orders = {}
        self.current_date = datetime.datetime.min

    def add_origins(self, fulfillment_origin_ids):
        self.origin_queue_lookup = {origin_id : None for origin_id in fulfillment_origin_ids}

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
        if quantity < self.queued_orders[order_id].quantity:
            self.queued_orders[order_id].quantity -= quantity
        elif quantity == self.queued_orders[order_id].quantity:
            self.queued_orders.pop(order_id, None)
            for node in self.order_lookup[order_id]:
                if node.prev is None:
                    self.origin_queue_lookup[node.origin_id] = node.next
                dequeue_node(node)

    def orders_in_origin_queue(self, origin_id):
        order_ids = []
        assert origin_id in self.origin_queue_lookup, 'origin does not exist'
        head = self.origin_queue_lookup[origin_id]
        while head is not None:
            order_ids.append(head.order_id)
            head = head.next
        return [self.queued_orders[order_id] for order_id in order_ids]

    def _enqueue_order(self, customer_order):
        def enqueue_node(head, node):
            tail = head
            while tail.next is not None:
                tail = tail.next
            tail.next = node
            node.prev = tail
            node.next = None
        assert customer_order.order_id not in self.order_lookup, 'one order can only be added once'
        self.order_lookup[customer_order.order_id] = []
        self.queued_orders[customer_order.order_id] = customer_order
        for origin_id in customer_order.fulfillment_origin_ids:
            node = FulfillmentQueueNode(origin_id, customer_order.order_id)
            if self.origin_queue_lookup[origin_id] is None:
                self.origin_queue_lookup[origin_id] = node
            else:
                enqueue_node(self.origin_queue_lookup[origin_id], node)
            self.order_lookup[customer_order.order_id].append(node)
