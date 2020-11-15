import datetime
import math

from scheduler import config
from scheduler.model.customer_order import CustomerOrder
from scheduler.manager.fulfillment_origin_manager import FulfillmentOriginManager
from scheduler.manager.order_queue_manager import OrderQueueManager
from scheduler.manager.sourcing_rule_manager import SourcingRuleManager
from scheduler.utils import utils


class OrderScheduler(object):
    """ A scheduler that helps solving sourcing optimization problem.

    This scheduler follows first come first serve (FCFS) strategy, with shortest
    job first (SCF) strategy for orders that lies in the same date. To reduce
    the average waiting time and prevent huge orders from blocking the pipeline
    for too long, "supply leak" strategy is used, where subsequent orders get
    part of the supply from the origin. If there are multiple origins available
    for fulfilling the order, the fulfillment priorities are based on the origin's
    estimated waiting time (The quotient of its average due order quantity and
    its history daily supply quantity).

    The user could claim the order information and supply plan of future to the
    cheduler, and get the fulfillment plan of dates in an ascending way.
    Currently, the scheduler don't use future supply plan and order information
    for optimization.

    Attributes:
        fulfillment_origin_manager: The manager object that maintains the
            attributes of fulfillment origins.
        order_queue_manager: The manager object that maintains the order queue.
        sourcing_rule_manager: The manager oejct that manages the sourcing rules.
        current_date: The last date of the fulfillment plan.
        supply_plan_pool: The dictionary that maps dates to the imported supply
            plan raw data.
        order_pool: The dictionary that maps dates to the imported order raw data.
    """

    def __init__(self):
        self.fulfillment_origin_manager = FulfillmentOriginManager()
        self.order_queue_manager = OrderQueueManager()
        self.sourcing_rule_manager = SourcingRuleManager()
        self.current_date = datetime.datetime.min
        self.supply_plan_pool = {}
        self.order_pool = {}

    def add_sourcing_rule(self, customer_name, site_name, product_name):
        """ Add a sourcing rule to the scheduler.

        If customer with `customer_name` orders product with `product_name`,
        then this order could be fulfilled by site with `site_name`.

        Args:
            customer_name: The name of the customer.
            site_name: The name of the site.
            product_name: The name of the product.
        """
        self.fulfillment_origin_manager.add_origin(site_name, product_name)
        self.sourcing_rule_manager.add_sourcing_rule(customer_name, site_name, product_name)
        self.order_queue_manager.add_origin(self.fulfillment_origin_manager.get_origin_id(site_name, product_name))

    def claim_supply_plan(self, site_name, product_name, quantity, plan_date):
        """ Claim a supply plan to the scheduler.

        Args:
            site_name: The site that provides the supply.
            product_name: The product name of the supply.
            quantity: The product quantity of the supply.
            plan_date: The date that the planned supply ships.
        """
        assert plan_date > self.current_date, 'you cannot add plan for the past'
        if plan_date not in self.supply_plan_pool:
            self.supply_plan_pool[plan_date] = []
        self.supply_plan_pool[plan_date].append((site_name, product_name, plan_date, quantity))

    def claim_order(self, customer_name, product_name, quantity, order_date):
        """ Claim an order to the scheduler.

        Args:
            customer_name: The name of the customer that initiates the order.
            product_name: The product name of the order.
            quantity: The product quantity of the order.
            order_date: The date that the order initiates.
        """
        assert order_date > self.current_date, 'you cannot add order in the past'
        if order_date not in self.order_pool:
            self.order_pool[order_date] = []
        self.order_pool[order_date].append((customer_name, product_name, order_date, quantity))

    def plan_fulfillment(self, date):
        """ Get the fulfillment plan of the date.

        This method updates the internal state of the scheduler, thus you should
        call this method in an date-ascending manner. Once you got the plan for
        the day, you could no longer add orders and supply plans before it.

        Args:
            date: The ship date of the fulfillment plan.

        Returns:
            A list of tuples. Each tuple represents a fulfillment plan, the
            elements are customer name, product name, order date, site name,
            ship date, ship quantity.
        """
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
                    date,
                    supply_quantity_distribution[index]
                ))
        return [*filter(lambda x: x[-1] > 0, fulfillment_plans)]

    def _distribute_supply(self, order_quantities, supply_quantity):
        """ Distribute a supply to fulfill multiple demands.

        Args:
            order_quantities: The demand quantity of the orders. The list order
                represents the priority order.
            supply_quantity: The available supply quantity.

        Returns:
            The quantity distribution list and remaining supply.
        """
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
        """ Import cached supply plan and order data.

        When the scheduler gets supply plan and order claims, the data will be
        first put into `supply_plan_pool` and `order_pool`. When the `current_date`
        updates, the scheduler add all previous and current supply plans to
        origin's cache, and the orders to the order queue.
        """
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
