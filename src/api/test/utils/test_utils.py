import unittest

from scheduler.utils import utils


class TestUtils(unittest.TestCase):
    def test_aggregate_tuples(self):
        with self.assertRaisesRegex(AssertionError, 'index out of range'):
            utils.aggregate_tuples([('a', 'b', 1)], [2, 3], 0)
            utils.aggregate_tuples([('a', 'b', 1)], [1, 2], 3)
        self.assertEqual(
            set(utils.aggregate_tuples([('a', 'b', 1), ('a', 'b', 2)], [0, 1], 2)),
            set(('a', 'b', 3))
        )
        self.assertEqual(
            set(utils.aggregate_tuples([('a', 'b', 1), ('a', 'b', 2), ('b', 'c', 3)], [0, 1], 2)),
            set(('a', 'b', 3), ('b', 'c', 3))
        )
