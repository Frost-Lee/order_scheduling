class SourcingRuleManager(object):
    def __init__(self):
        self.rule_lookup = {}

    def add_sourcing_rule(self, customer_name, site_name, product_name):
        if customer_name not in self.rule_lookup:
            self.rule_lookup[customer_name] = set()
        self.rule_lookup[customer_name].add((site_name, product_name))

    def get_fulfillment_sites(self, customer_name, product_name):
        assert customer_name in self.rule_lookup, 'no available fulfillment origin'
        fulfillment_sites = [s for s, p in self.rule_lookup[customer_name] if p == product_name]
        assert len(fulfillment_sites) != 0, 'no available fulfillment origin'
        return set(fulfillment_sites)
