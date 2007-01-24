
""" test session config options
"""

import py
from py.__.test.rsession.rsession import session_options, SessionOptions,\
   remote_options

def test_session_opts():
    tmpdir = py.test.ensuretemp("sessionopts")
    tmpdir.ensure("conftest.py").write("""class SessionOptions:
        max_tasks_per_node = 5
        nice_level = 10
    """)
    tmp2 = py.test.ensuretemp("xxx")
    args = [str(tmpdir)]
    config = py.test.config._reparse(args)
    session_options.bind_config(config)
    assert session_options.max_tasks_per_node == 5
    assert remote_options.nice_level == 10
    config = py.test.config._reparse([str(tmp2)])
    session_options.bind_config(config)
    assert session_options.max_tasks_per_node == \
        SessionOptions.defaults['max_tasks_per_node']
