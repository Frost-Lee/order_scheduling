import shortuuid


class CustomerOrder(object):
    """ A customer's order.

    Attributes:
        customer_name: The name of the customer who issues the order.
        product_name: The product's name that the order demands.
        quantity: The product's quantity that the order demands.
        order_date: The date that the order was issued.
        fulfillment_origin_ids: The id of the origins that could fulfill this
            order.
        order_id: The identifier of the order for external reference. If pass 
            `None`, this value would be an auto-generated UUID string.
    """
    
    def __init__(self, customer_name, product_name, quantity, order_date, order_id=None):
        self.customer_name = customer_name
        self.product_name = product_name
        self.quantity = quantity
        self.order_date = order_date
        self.fulfillment_origin_ids = set()
        self.order_id = order_id if order_id is not None else shortuuid.uuid()

    def origin_average_quantity(self):
        """ Get the origin average quantity of this order.
        
        The value would be the quotient of the order's quantity and the number
        of origins that could fulfill the order. If there is no origin that
        could fulfill the order, the order's quantity will be returned.
        """
        if len(self.fulfillment_origin_ids) == 0:
            return self.quantity
        return self.quantity / len(self.fulfillment_origin_ids)
