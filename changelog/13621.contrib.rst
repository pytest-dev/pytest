pytest's own testsuite now handles the ``lsof`` command hanging (e.g. due to unreachable network filesystems), with the affected selftests being skipped after 10 seconds.
