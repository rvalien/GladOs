import pytest


def divide(a):
    return a / 0


def test_ok():
    assert 1 == 1


@pytest.mark.xfail(raises=ZeroDivisionError)
def test_nor_ok():
    result = divide(10 / 0)

    assert result == 2


def test_ok_2():
    assert True is True
