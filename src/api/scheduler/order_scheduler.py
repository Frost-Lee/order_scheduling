import datetime

from scheduler.manager.fulfillment_origin_manager import FulfillmentOriginManager
from scheduler.manager.order_queue_manager import OrderQueueManager
from scheduler.manager.origin_cache_manager import OriginCacheManager

class OrderScheduler(object):
    def __init__(self):
        self.fulfillment_origin_manager = FulfillmentOriginManager()
        self.order_queue_manager = OrderQueueManager()
        self.origin_cache_manager = OriginCacheManager()
        self.current_date = datetime.datetime.min
        self.supply_plan_pool = {}
        self.order_pool = {}

    def add_sourcing_rule(self, customer_name, site_name, product_name):
        self.fulfillment_origin_manager.add_sourcing_rule(customer_name, site_name, product_name)

    def claim_supply_plan(self, site_name, product_name, quantity, plan_date):
        assert plan_date > self.current_date, 'you cannot add plan for the past'
        if plan_date not in self.supply_plan_pool:
            self.supply_plan_pool = []
        self.supply_plan_pool[plan_date] = (site_name, product_name, quantity, plan_date)

    def claim_order(self, customer_name, product_name, quantity, order_date):
        assert order_date > self.current_date, 'you cannot add order in the past'
        if order_date not in self.order_pool:
            self.order_pool = []
        self.order_pool[order_date] = (customer_name, product_name, quantity, order_date)

    def get_fulfillment_plan(self, date):
        self.current_date = date
        # queue all orders before date
        # add all supply before date to cache
        # use counter to accelerate
