Fix assertion diff output to preserve dictionary insertion order.

When comparing dictionaries with extra keys, pytest could incorrectly inject
those keys into the structured diff output, producing misleading results.
The assertion diff now correctly preserves insertion order and reports extra
keys separately.
