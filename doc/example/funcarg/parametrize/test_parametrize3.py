
# following hook can be put unchanged into a local or global plugin 
def pytest_generate_tests(metafunc):
    for scenario in metafunc.cls.scenarios:
        metafunc.addcall(id=scenario[0], funcargs=scenario[1])


scenario1 = ('basic', {'attribute': 'value'})
scenario2 = ('advanced', {'attribute': 'value2'})

class TestSampleWithScenarios:
    scenarios = [scenario1, scenario2]

    def test_demo(self, attribute):
        assert isinstance(attribute, str) 
