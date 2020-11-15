from typing import Counter


def aggregate_tuples(tuples, key_indices, value_index):
    """ Aggregate the tuples on one of its value by some keys.

    The reduce method for aggregation is addition.

    Args:
        tuples: A list of tuples to be aggregated.
        key_indices: The index list of the element to be used as keys. Pass
            positive indices.
        value_index: The index of the element to be aggregated. Pass positive
            index.

    Returns:
        A list of tuples after aggregation. The value would be placed last in
        the returned tuples, elements that are neither key nor value are removed
        from returned tuples.
    """
    # TODO(canchen.lee@gmail.com): maintain the tuple's element order after aggregation.
    if len(tuples) == 0:
        return []
    assert len(tuples[0]) > max(max(key_indices), value_index), 'index out of range'
    counter = Counter()
    for t in tuples:
        counter[tuple([t[key_index] for key_index in key_indices])] += t[value_index]
    return [(*key, counter[key]) for key in counter.keys()]
