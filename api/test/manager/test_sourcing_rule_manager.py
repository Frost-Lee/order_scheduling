import unittest

from scheduler.manager.sourcing_rule_manager import SourcingRuleManager


class TestSourcingRuleManager(unittest.TestCase):
    def test_constructor(self):
        self.assertIsNotNone(SourcingRuleManager())

    def test_add_sourcing_rule_get_fulfillment_sites(self):
        sut = SourcingRuleManager()
        sut.add_sourcing_rule('customer_1', 'site_1', 'product_1')
        sut.add_sourcing_rule('customer_1', 'site_2', 'product_1')
        sut.add_sourcing_rule('customer_2', 'site_1', 'product_1')
        sut.add_sourcing_rule('customer_2', 'site_1', 'product_1')
        self.assertEqual(len(sut.rule_lookup['customer_2']), 1)
        with self.assertRaisesRegex(AssertionError, 'no available fulfillment origin'):
            sut.get_fulfillment_sites('customer_3', 'product_1')
        with self.assertRaisesRegex(AssertionError, 'no available fulfillment origin'):
            sut.get_fulfillment_sites('customer_1', 'product_2')
        self.assertEqual(sut.get_fulfillment_sites('customer_1', 'product_1'), set(['site_1', 'site_2']))
        self.assertEqual(sut.get_fulfillment_sites('customer_2', 'product_1'), set(['site_1']))
