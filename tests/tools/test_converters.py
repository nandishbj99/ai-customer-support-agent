import pytest
from app.tools.converters import paise_to_rupees, rupees_to_paise


def test_rupees_to_paise_standard():
    assert rupees_to_paise(5000.0) == 500000
    assert rupees_to_paise(12.34) == 1234
    assert rupees_to_paise(0.0) == 0


def test_paise_to_rupees_standard():
    assert paise_to_rupees(500000) == 5000.0
    assert paise_to_rupees(1234) == 12.34
    assert paise_to_rupees(0) == 0.0


def test_rupees_to_paise_negative_rejected():
    with pytest.raises(ValueError):
        rupees_to_paise(-10.0)


def test_paise_to_rupees_negative_rejected():
    with pytest.raises(ValueError):
        paise_to_rupees(-100)


def test_rupees_to_paise_exceeds_max_limit():
    with pytest.raises(ValueError):
        rupees_to_paise(20_000_000.0)
