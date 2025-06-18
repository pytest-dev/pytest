import decimal
import pytest

def test_decimal_approx_repr_issue():
    trap = decimal.getcontext().traps[decimal.FloatOperation]
    decimal.getcontext().traps[decimal.FloatOperation] = False

    approx_obj = pytest.approx(decimal.Decimal("2.60"))
    print(f"Attempting to represent pytest.approx(Decimal): {approx_obj}")
    assert decimal.Decimal("2.600001") == approx_obj

    decimal.getcontext().traps[decimal.FloatOperation] = trap
