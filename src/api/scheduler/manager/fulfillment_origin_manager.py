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
        self.site_product_lookup[site_name][product_name] = origin_id

    def get_origin_id(self, site_name, product_name):
        assert self._origin_exists(site_name, product_name), 'unknown origin'
        return self.site_product_lookup[site_name][product_name]

    def add_supply(self, site_name, product_name, quantity, date):
        assert self._origin_exists(site_name, product_name), 'add supply for unknown origin'
        self.origin_lookup[self.site_product_lookup[site_name][product_name]].add_supply(quantity, date)

    def consume_supply(self, origin_id, quantity):
        assert origin_id in self.origin_lookup, 'consume supply for unknown origin'
        self.origin_lookup[origin_id].consume_supply(quantity)

    def _origin_exists(self, site_name, product_name):
        return site_name in self.site_product_lookup and product_name in self.site_product_lookup[site_name]
