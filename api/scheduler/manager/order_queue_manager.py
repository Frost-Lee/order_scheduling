import datetime
from typing import Counter

from scheduler.model.fulfillment_queue_node import FulfillmentQueueNode


class OrderQueueManager(object):
    """ A manager object that maintains the order queue.

    The order queue is maintained on fulfillment origin level. Each fulfillment
    origin have an order queue. The orders would be queued based on their order
    date, for orders lie in the same date, orders with lower quantity are
    prioritized. If an order have multiple fulfillment origins available, there
    would be multiple queue nodes in different origin's queue, while these nodes
    support atomic operations (remove from queue, update order remaining
    quantity, etc.).

    Attributes:
        origin_queue_lookup: A dictionary that maps fulfillment origin id to its
            order queue head.
        order_lookup: A dictionary that maps an order id to a list of the queue
            nodes that represents this order.
        queued_orders: A dictionary that maps an order id to its `CustomerOrder`
            object.
        origin_due_quantity_counter: A counter object that counts the average
            due quantity of an order queue, keyed by fulfillment origin id. See
            also `origin_average_quantity` method of `CustomerOrder`.
        current_date: The date of the last queued order.
    """

    def __init__(self):
        self.origin_queue_lookup = {}
        self.order_lookup = {}
        self.queued_orders = {}
        self.origin_due_quantity_counter = Counter()
        self.current_date = datetime.datetime.min

    def add_origin(self, origin_id):
        """ Add a fulfillment origin to the manager.

        Args:
            origin_id: The id of the fulfillment origin.
        """
        if origin_id not in self.origin_queue_lookup:
            self.origin_queue_lookup[origin_id] = None

    def enqueue_daily_order(self, customer_orders):
        """ Put the orders on the same day to the queue.

        Orders can only be enqueued on an ascending order of its order date.
        When calling this method, add all orders on that date.

        Args:
            customer_orders: The customer orders with the same order date.
        """
        order_dates = [*map(lambda x: x.order_date, customer_orders)]
        assert len(set(order_dates)) == 1 and order_dates[0] >= self.current_date, 'please add the daily orders in an ascending manner'
        self.current_date = order_dates[0]
        customer_orders = sorted(customer_orders, key=lambda x: x.quantity)
        for order in customer_orders:
            self._enqueue_order(order)

    def claim_fulfillment(self, origin_id, order_id, quantity):
        """ Claim a fulfillment operation.

        If this fulfillment finishes all remaining quantities of the order, its
        corresponding nodes will be removed from queue.

        Args:
            origin_id: The fulfillment origin that ships the products.
            order_id: The order id that this operation fulfills.
            quantity: The quantity of products that this operation fulfills.
        """
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
        """ Get the top `CustomerOrder` objects in the queue.

        Only the first k orders in the queue will be returned. The value of k
        depends on `min_quantity_sum` and `min_order_count`. If there is not
        enough orders in the queue that could meet these two requirements, all
        orders will be returned.

        Args:
            origin_id: The id of the fulfillment origin.
            min_quantity_sum: The minimum quantity sum of the returned orders.
            min_order_count: The minimum count of the returned orders.
        """
        assert origin_id in self.origin_queue_lookup, 'origin does not exist'
        order_quantity_sum = 0
        peek_orders, head = [], self.origin_queue_lookup[origin_id]
        while head is not None and (order_quantity_sum < min_quantity_sum or len(peek_orders) < min_order_count):
            peek_orders.append(self.queued_orders[head.order_id])
            order_quantity_sum += peek_orders[-1].quantity
            head = head.next
        return peek_orders

    def order_queue_content(self, origin_id):
        """ Get the `CustomerOrder` objects in the queue.

        Args:
            origin_id: The id of the fulfillment origin.
        """
        assert origin_id in self.origin_queue_lookup, 'origin does not exist'
        order_ids, head = [], self.origin_queue_lookup[origin_id]
        while head is not None:
            order_ids.append(head.order_id)
            head = head.next
        return [self.queued_orders[order_id] for order_id in order_ids]

    def get_origin_average_due_quantity(self, origin_id):
        """ Get the average due order remain quantity sum of a fulfillment origin.

        Args:
            origin_id: The id of the fulfillment origin.
        """
        return self.origin_due_quantity_counter[origin_id]

    def _enqueue_order(self, customer_order):
        """ Put an order to the order queue.

        Args:
            customer_order: A `CustomerOrder` object to be queued.
        """
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
