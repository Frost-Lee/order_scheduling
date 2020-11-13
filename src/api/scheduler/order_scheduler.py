import datetime
import math

from scheduler import config
from scheduler.model.customer_order import CustomerOrder
from scheduler.manager.fulfillment_origin_manager import FulfillmentOriginManager
from scheduler.manager.order_queue_manager import OrderQueueManager
from scheduler.manager.sourcing_rule_manager import SourcingRuleManager
from scheduler.utils import utils


class OrderScheduler(object):
    def __init__(self):
        self.fulfillment_origin_manager = FulfillmentOriginManager()
        self.order_queue_manager = OrderQueueManager()
        self.sourcing_rule_manager = SourcingRuleManager()
        self.current_date = datetime.datetime.min
        self.supply_plan_pool = {}
        self.order_pool = {}

    def add_sourcing_rule(self, customer_name, site_name, product_name):
        self.fulfillment_origin_manager.add_origin(site_name, product_name)
        self.sourcing_rule_manager.add_sourcing_rule(customer_name, site_name, product_name)
        self.order_queue_manager.add_origin(self.fulfillment_origin_manager.get_origin_id(site_name, product_name))

    def claim_supply_plan(self, site_name, product_name, quantity, plan_date):
        assert plan_date > self.current_date, 'you cannot add plan for the past'
        if plan_date not in self.supply_plan_pool:
            self.supply_plan_pool[plan_date] = []
        self.supply_plan_pool[plan_date].append((site_name, product_name, plan_date, quantity))

    def claim_order(self, customer_name, product_name, quantity, order_date):
        assert order_date > self.current_date, 'you cannot add order in the past'
        if order_date not in self.order_pool:
            self.order_pool[order_date] = []
        self.order_pool[order_date].append((customer_name, product_name, order_date, quantity))

    def plan_fulfillment(self, date):
        self.current_date = date
        fulfillment_plans = []
        self._import_order_supply()
        available_origin_ids = sorted(
            self.fulfillment_origin_manager.get_available_origin_ids(),
            key=lambda x:self.order_queue_manager.get_origin_average_due_quantity(x) / self.fulfillment_origin_manager.get_origin_average_daily_supply_quantity(x, date)
        )
        for origin_id in available_origin_ids:
            supply_quantity = self.fulfillment_origin_manager.get_origin_cache_quantity(origin_id)
            queue_top_orders = self.order_queue_manager.peek_order_queue_content(origin_id,supply_quantity,len(config.SUPPLY_DISTRIBUTION_RATES))
            supply_quantity_distribution, remain_quantity = self._distribute_supply([*map(lambda x: x.quantity, queue_top_orders)], supply_quantity)
            self.fulfillment_origin_manager.consume_supply(origin_id, supply_quantity - remain_quantity)
            for index in range(len(queue_top_orders)):
                self.order_queue_manager.claim_fulfillment(origin_id, queue_top_orders[index].order_id, supply_quantity_distribution[index])
                fulfillment_plans.append((
                    queue_top_orders[index].customer_name,
                    queue_top_orders[index].product_name,
                    queue_top_orders[index].order_date,
                    self.fulfillment_origin_manager.get_origin(origin_id).site_name,
                    supply_quantity_distribution[index]
                ))
        return [*filter(lambda x: x[-1] > 0, fulfillment_plans)]

    def _distribute_supply(self, order_quantities, supply_quantity):
        assert supply_quantity > 0, 'supply quantity must be greater than 0'
        quantity_distribution = [0 for _ in range(len(order_quantities))]
        if len(order_quantities) == 0:
            return quantity_distribution, supply_quantity
        if sum(order_quantities) <= supply_quantity:
            quantity_distribution = order_quantities
            return quantity_distribution, supply_quantity - sum(order_quantities)
        if order_quantities[0] <= supply_quantity:
            order_index = 0
            while supply_quantity >= 0:
                quantity_distribution[order_index] = min(supply_quantity, order_quantities[order_index])
                supply_quantity -= order_quantities[order_index]
                order_index += 1
            return quantity_distribution, 0
        else:
            remain_quantity = supply_quantity
            for index, ratio in enumerate(config.SUPPLY_DISTRIBUTION_RATES):
                if index < len(order_quantities):
                    base_quantity = min(order_quantities[index], math.floor(ratio * supply_quantity))
                    quantity_distribution[index] = base_quantity
                    remain_quantity -= base_quantity
                else:
                    break
            for index in range(len(order_quantities)):
                if remain_quantity <= 0:
                    break
                if quantity_distribution[index] < order_quantities[index]:
                    extra_quantity = min(order_quantities[index] - quantity_distribution[index], remain_quantity)
                    quantity_distribution[index] += extra_quantity
                    remain_quantity -= extra_quantity
            return quantity_distribution, 0

    def _import_order_supply(self):
        order_dates = sorted([date for date in self.order_pool.keys() if date <= self.current_date])
        supply_dates = sorted([date for date in self.supply_plan_pool.keys() if date <= self.current_date])
        for supply_date in supply_dates:
            daily_supplies = utils.aggregate_tuples(self.supply_plan_pool[supply_date], [0, 1, 2], 3)
            for supply in daily_supplies:
                self.fulfillment_origin_manager.add_supply(
                    site_name=supply[0],
                    product_name=supply[1],
                    quantity=supply[3],
                    date=supply[2]
                )
            self.supply_plan_pool.pop(supply_date, None)
        for order_date in order_dates:
            daily_orders = utils.aggregate_tuples(self.order_pool[order_date], [0, 1, 2], 3)
            casted_orders = []
            for order in daily_orders:
                new_order = CustomerOrder(
                    customer_name=order[0],
                    product_name=order[1],
                    quantity=order[3],
                    order_date=order[2]
                )
                new_order.fulfillment_origin_ids = set([self.fulfillment_origin_manager.get_origin_id(
                    site_name,
                    order[1]
                ) for site_name in self.sourcing_rule_manager.get_fulfillment_sites(order[0], order[1])])
                casted_orders.append(new_order)
            self.order_queue_manager.enqueue_daily_order(casted_orders)
            self.order_pool.pop(order_date, None)
