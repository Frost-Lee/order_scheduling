class SourcingRuleManager(object):
    """ A manager object that maintains the sourcing rules.

    A sourcing rule defines which product that which customer orders could be
    fulfilled by which site.
    """
    def __init__(self):
        self.rule_lookup = {}

    def add_sourcing_rule(self, customer_name, site_name, product_name):
        """ Add a sourcing rule to the manager.

        If customer with `customer_name` orders product with `product_name`,
        then this order could be fulfilled by site with `site_name`.

        Args:
            customer_name: The name of the customer.
            site_name: The name of the site.
            product_name: The name of the product.
        """
        if customer_name not in self.rule_lookup:
            self.rule_lookup[customer_name] = set()
        self.rule_lookup[customer_name].add((site_name, product_name))

    def get_fulfillment_sites(self, customer_name, product_name):
        """ Get the fulfillment sites' names given a customer's product demand.

        Args:
            customer_name: The name of the customer.
            product_name: The name of the product.
        """
        assert customer_name in self.rule_lookup, 'no available fulfillment origin'
        fulfillment_sites = [s for s, p in self.rule_lookup[customer_name] if p == product_name]
        assert len(fulfillment_sites) != 0, 'no available fulfillment origin'
        return set(fulfillment_sites)
