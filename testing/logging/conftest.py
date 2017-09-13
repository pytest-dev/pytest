# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import pytest


pytest_plugins = 'pytester'


def pytest_addoption(parser):
    parser.addoption('--run-perf',
        action='store', dest='run_perf',
        choices=['yes', 'no', 'only', 'check'],
        nargs='?', default='check', const='yes',
        help='Run performance tests (can be slow)',
    )

    parser.addoption('--perf-graph',
        action='store', dest='perf_graph_name',
        nargs='?', default=None, const='graph.svg',
        help='Plot a graph using data found in --benchmark-storage',
    )
    parser.addoption('--perf-expr',
        action='store', dest='perf_expr_primary',
        default='log_emit',
        help='Benchmark (or expression combining benchmarks) to plot',
    )
    parser.addoption('--perf-expr-secondary',
        action='store', dest='perf_expr_secondary',
        default='caplog - stub',
        help=('Benchmark (or expression combining benchmarks) to plot '
              'as a secondary line'),
    )
