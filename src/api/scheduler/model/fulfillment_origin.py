import shortuuid


class FulfillmentOrigin(object):
    def __init__(self, site_name, product_name, origin_id=None):
        self.site_name = site_name
        self.product_name = product_name
        self.origin_id = origin_id if origin_id is not None else shortuuid.uuid()
        self.cached_supply_quantity = 0
        self.history_supply_dates = []
        self.history_supply_quantities = []

    def add_supply(self, quantity, date):
        self.cached_supply_quantity += quantity
        self.history_supply_dates.append(date)
        self.history_supply_quantities.append(quantity)

    def consume_supply(self, quantity):
        assert quantity <= self.cached_supply_quantity, 'supply consumption quantity greater than cache'
        self.cached_supply_quantity -= quantity

    def average_daily_supply(self, today):
        if len(self.history_supply_dates) == 0:
            return 0
        day_count = (today - self.history_supply_dates[0]).days
        return sum(self.history_supply_quantities) if day_count == 0 else sum(self.history_supply_quantities) / day_count
