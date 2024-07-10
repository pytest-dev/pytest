import functools

import pytest

cur_request = None

# Should logically be scope="item", but we want to store a function-scoped
# request. Ugly hack to avoid signature-rewriting ugliness in inner_runner.
@pytest.fixture(scope="function", autouse=True)
def fetch_request(request):
    global cur_request
    cur_request = request
    yield
    cur_request = None


def run_many_times(n=5):
    executions = 0

    def update(kwargs):
        nonlocal executions
        if executions > 0:
            updated = cur_request._reset_function_scoped_fixtures()
            kwargs |= {k: v for k, v in updated.items() if k in kwargs}
        executions += 1

    def wrapper(fn):

        @functools.wraps(fn)
        def wrapped(**kwargs):
            for i in range(n):
                update(kwargs)
                fn(**kwargs)

        return wrapped

    return wrapper


num_func = num_item = num_param = num_ex = num_test = 0
params_seen = set()

@pytest.fixture()
def fixture_func():
    """once per example"""
    global num_func
    num_func += 1
    print("->func")
    return num_func


@pytest.fixture(scope="item")
def fixture_item():
    """once per test item"""
    global num_item
    num_item += 1
    print("->item")
    return num_item


@pytest.fixture()
def fixture_func_item(fixture_func, fixture_item):
    """mixed-scope transitivity"""
    return (fixture_func, fixture_item)


@pytest.fixture()
def fixture_test(fixture_test):
    """overrides conftest fixture of same name"""
    global num_test
    num_test += 1
    print("->test")
    return (fixture_test, num_test)


@pytest.fixture(params=range(4))
def fixture_param(request):
    """parameterized, per-example"""
    global num_param
    print("->param")
    num_param += 1
    return (num_param, request.param)


@run_many_times()
def test_function_scoped_fixtures(fixture_func_item, fixture_test, fixture_param, fixture_test_2):
    global num_ex
    num_ex += 1

    # All these should be used only by this test, to avoid counter headaches
    print(f"{fixture_func_item=} {fixture_test=} {fixture_param=} {fixture_test_2=}")

    # 1. fixture_test is a tuple (num_conftest_calls, num_module_calls), and
    #    both are function-scoped so should be called per-example
    assert fixture_test == (num_ex, num_ex)
    # 2. fixture_test_2 should have picked up the module-level fixture_test, not
    #    the conftest-level one
    assert fixture_test_2 == fixture_test
    # 3. check that the parameterized fixture was also re-executed for each example
    assert fixture_param[0] == num_ex
    # 4. number of calls to _func should be the same as number of examples, while
    #    number of calls to _item should be the number of parametrized items seen
    params_seen.add(fixture_param[1])
    assert fixture_func_item == (num_ex, len(params_seen))
    #
    print("---------")


@pytest.fixture
def fixt_1(fixt_1, fixt_2):
    return f"f1_m({fixt_1}, {fixt_2})"


@pytest.fixture
def fixt_2(fixt_1, fixt_2):
    return f"f2_m({fixt_1}, {fixt_2})"


@pytest.fixture
def fixt_3(fixt_1, fixt_3):
    return f"f3_m({fixt_1}, {fixt_3})"


@run_many_times()
def test_cyclic_fixture_dependency(fixt_1, fixt_2, fixt_3):
    # Notice how fixt_2 and fixt_3 resolve different values for fixt_1
    # (module.fixt_2 receives conftest.fixt_1, while
    #  module.fixt_3 receives module.fixt_1).
    # However, what we want to ensure here is that the result stays the same
    # after fixture reset, not why it is what it is in the first place.
    assert fixt_1 == "f1_m(f1_c, f2_m(f1_c, f2_c(f1_c)))"
    assert fixt_2 == "f2_m(f1_c, f2_c(f1_c))"
    assert fixt_3 == "f3_m(f1_m(f1_c, f2_m(f1_c, f2_c(f1_c))), f3_c(f1_m(f1_c, f2_m(f1_c, f2_c(f1_c)))))"
