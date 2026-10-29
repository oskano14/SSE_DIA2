import pytest

from shoppulse.geo import STATE_REGION, haversine_km


def test_all_27_states_have_a_region() -> None:
    assert len(STATE_REGION) == 27
    assert set(STATE_REGION.values()) == {
        "Nord",
        "Nordeste",
        "Centre-Ouest",
        "Sudeste",
        "Sud",
    }


def test_haversine_sao_paulo_rio() -> None:
    distance = haversine_km(-23.55, -46.63, -22.91, -43.17)
    assert distance == pytest.approx(360, abs=10)


def test_haversine_zero_distance() -> None:
    assert haversine_km(-10, -50, -10, -50) == pytest.approx(0)
