from typing import Counter


def aggregate_tuples(tuples, key_indices, value_index):
    if len(tuples) == 0:
        return []
    assert len(tuples[0]) > max(max(key_indices), value_index), 'index out of range'
    counter = Counter()
    for t in tuples:
        counter[tuple([t[key_index] for key_index in key_indices])] += t[value_index]
    return [(*key, counter[key]) for key in counter.keys()]
