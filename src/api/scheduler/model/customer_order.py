import shortuuid


class CustomerOrder(object):
    def __init__(self, customer_name, product_name, quantity, order_date, order_id=None):
        self.customer_name = customer_name
        self.product_name = product_name
        self.quantity = quantity
        self.order_date = order_date
        self.fulfillment_origin_ids = set()
        self.order_id = order_id if order_id is not None else shortuuid.uuid()
