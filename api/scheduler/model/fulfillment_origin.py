import shortuuid


class FulfillmentOrigin(object):
    """ A fulfillment origin.

    A fulfillment origin is an abstraction of site-product tuple, since the
    sourcing rules and the supply data are given on site-product level.

    Attributes:
        site_name: The site name of the origin.
        product_name: The product name of the origin.
        origin_id: The identifier of the origin for external reference. If pass
            `None`, this value would be an auto-generated UUID string.
        cached_supply_quantity: The quantity of the cached supply of this origin.
        history_supply_dates: The history dates that this origin have supply.
            A list of `datetime` objects in ascending order.
        history_supply_quantities: The history supply quantities list that this
            origin have supply. The order is identical as `history_supply_dates`.
    """

    def __init__(self, site_name, product_name, origin_id=None):
        self.site_name = site_name
        self.product_name = product_name
        self.origin_id = origin_id if origin_id is not None else shortuuid.uuid()
        self.cached_supply_quantity = 0
        self.history_supply_dates = []
        self.history_supply_quantities = []

    def add_supply(self, quantity, date):
        """ Declear a product supply of this origin.

        Args:
            quantity: The quantity of the supply.
            date: The date of the supply.
        """
        self.cached_supply_quantity += quantity
        self.history_supply_dates.append(date)
        self.history_supply_quantities.append(quantity)

    def consume_supply(self, quantity):
        """ Declear a product consumption of this origin.

        Args:
            quantity: The quantity of the consumption.
        """
        assert quantity <= self.cached_supply_quantity, 'supply consumption quantity greater than cache'
        self.cached_supply_quantity -= quantity

    def average_daily_supply_quantity(self, today):
        """ Get the average daily supply quantity from this origin's history
            supply data.

        If there is no history data available, an epsilon will be returned.

        Args:
            today: The end date for fetching the history supply data.
        """
        epsilon = 1e-5      # the return value could be the divider
        if len(self.history_supply_dates) == 0:
            return epsilon
        # TODO(canchen.lee@gmail.com): maintain the ascending order of `history_supply_dates`
        # and `history_supply_quantities`.
        day_count = (today - self.history_supply_dates[0]).days
        return max(sum(self.history_supply_quantities) if day_count == 0 else sum(self.history_supply_quantities) / day_count, epsilon)
