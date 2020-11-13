class FulfillmentQueueNode(object):

    def __init__(self, origin_id, order_id):
        self.origin_id = origin_id
        self.order_id = order_id
        self.next = None
        self.prev = None
