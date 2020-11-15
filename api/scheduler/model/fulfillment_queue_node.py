class FulfillmentQueueNode(object):
    """ A queue node object for order queue.

    Attributes:
        origin_id: The id of the fulfillment origin of the queue.
        order_id: The id of the customer order that this node represents.
        next: The next node in the queue.
        prev: The previous node in the queue.
    """

    def __init__(self, origin_id, order_id):
        self.origin_id = origin_id
        self.order_id = order_id
        self.next = None
        self.prev = None
