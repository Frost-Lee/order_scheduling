from scheduler.model.fulfillment_origin import FulfillmentOrigin


class FulfillmentOriginManager(object):
    def __init__(self):
        self.origin_lookup = {}
        self.site_product_lookup = {}

    def add_origin(self, site_name, product_name, origin_id=None):
        if self._origin_exists(site_name, product_name):
            return
        new_origin = FulfillmentOrigin(site_name, product_name, origin_id)
        self.origin_lookup[new_origin.origin_id] = new_origin
        if site_name not in self.site_product_lookup:
            self.site_product_lookup[site_name] = {}
        self.site_product_lookup[site_name][product_name] = new_origin.origin_id

    def get_origin_id(self, site_name, product_name):
        assert self._origin_exists(site_name, product_name), 'unknown origin'
        return self.site_product_lookup[site_name][product_name]
    
    def get_origin(self, origin_id):
        assert origin_id in self.origin_lookup, 'unknown origin'
        return self.origin_lookup[origin_id]

    def get_available_origin_ids(self):
        return [key for key, value in self.origin_lookup.items() if value.cached_supply_quantity > 0]

    def get_origin_cache_quantity(self, origin_id):
        assert origin_id in self.origin_lookup, 'unknown origin'
        return self.origin_lookup[origin_id].cached_supply_quantity

    def get_origin_average_daily_supply_quantity(self, origin_id, until_date):
        assert origin_id in self.origin_lookup, 'unknown origin'
        return self.origin_lookup[origin_id].average_daily_supply_quantity(until_date)

    def add_supply(self, site_name, product_name, quantity, date):
        assert self._origin_exists(site_name, product_name), 'add supply for unknown origin'
        self.origin_lookup[self.get_origin_id(site_name, product_name)].add_supply(quantity, date)

    def consume_supply(self, origin_id, quantity):
        assert origin_id in self.origin_lookup, 'consume supply for unknown origin'
        self.origin_lookup[origin_id].consume_supply(quantity)

    def _origin_exists(self, site_name, product_name):
        return site_name in self.site_product_lookup and product_name in self.site_product_lookup[site_name]
