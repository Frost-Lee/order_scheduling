from scheduler.model.fulfillment_origin import FulfillmentOrigin


class FulfillmentOriginManager(object):
    """ A manager object that maintains the attributes of fulfillment origins.

    Attributes:
        origin_lookup: A dictionary for looking up `FulfillmentOrigin` object
            with its `origin_id`.
        site_product_lookup: A dictionary for looking up the `origin_id` of an
            `FulfillmentOrigin` object with its `site_name` and `product_name`.
    """

    def __init__(self):
        self.origin_lookup = {}
        self.site_product_lookup = {}

    def add_origin(self, site_name, product_name, origin_id=None):
        """ Add a fulfillment origin to the manager.

        Args:
            site_name: The site name of the fulfillment origin.
            product_name: The product name of the fulfillment origin.
            origin_id: The id of the fulfillment origin. If `None`, an
            auto-generated UUID string would be used.
        """
        if self._origin_exists(site_name, product_name):
            return
        new_origin = FulfillmentOrigin(site_name, product_name, origin_id)
        self.origin_lookup[new_origin.origin_id] = new_origin
        if site_name not in self.site_product_lookup:
            self.site_product_lookup[site_name] = {}
        self.site_product_lookup[site_name][product_name] = new_origin.origin_id

    def get_origin_id(self, site_name, product_name):
        """ Get the origin id of a fulfillment origin by its site name and
            product name.

        Args:
            site_name: The site name of the fulfillment origin.
            product_name: The product name of the fulfillment origin.
        """
        assert self._origin_exists(site_name, product_name), 'unknown origin'
        return self.site_product_lookup[site_name][product_name]
    
    def get_origin(self, origin_id):
        """ Get the `FulfillmentOrigin` object by its `origin_id`.

        Args:
            origin_id: The id of the fulfillment origin.
        """
        assert origin_id in self.origin_lookup, 'unknown origin'
        return self.origin_lookup[origin_id]

    def get_available_origin_ids(self):
        """ Get the origin id of the fulfillment origins that have cached quantity.
        """
        return [key for key, value in self.origin_lookup.items() if value.cached_supply_quantity > 0]

    def get_origin_cache_quantity(self, origin_id):
        """ Get the cached quantity of a fulfillment origin with given origin id.

        Args:
            origin_id: The id of the fulfillment origin.
        """
        assert origin_id in self.origin_lookup, 'unknown origin'
        return self.origin_lookup[origin_id].cached_supply_quantity

    def get_origin_average_daily_supply_quantity(self, origin_id, until_date):
        """ Get the average daily supply of a fulfillment origin.

        Args:
            origin_id: The id of the fulfillment origin.
            until_date: The end date for fetching the history supply data.
        """
        assert origin_id in self.origin_lookup, 'unknown origin'
        return self.origin_lookup[origin_id].average_daily_supply_quantity(until_date)

    def add_supply(self, site_name, product_name, quantity, date):
        """ Add supply to a fulfillment origin.

        Args:
            site_name: The site name of the fulfillment origin.
            product_name: The product name of the fulfillment origin.
            quantity: The quantity of the supply.
            date: The date of the supply.
        """
        assert self._origin_exists(site_name, product_name), 'add supply for unknown origin'
        self.origin_lookup[self.get_origin_id(site_name, product_name)].add_supply(quantity, date)

    def consume_supply(self, origin_id, quantity):
        """ Declear a product consumption of a fulfillment origin.

        Args:
            origin_id: The id of the fulfillment origin.
            quantity: The quantity of the consumption.
        """
        assert origin_id in self.origin_lookup, 'consume supply for unknown origin'
        self.origin_lookup[origin_id].consume_supply(quantity)

    def _origin_exists(self, site_name, product_name):
        """ Check whether a fulfillment origin exists in this manager.

        Args:
            site_name: The site name of the fulfillment origin.
            product_name: The product name of the fulfillment origin.
        """
        return site_name in self.site_product_lookup and product_name in self.site_product_lookup[site_name]
