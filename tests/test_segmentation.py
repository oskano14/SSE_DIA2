import numpy as np
import pandas as pd
import pytest

from shoppulse.segmentation import (
    campaign_revenue,
    profile_segments,
    segment,
    silhouette_by_k,
)


@pytest.fixture
def rfm() -> pd.DataFrame:
    """Trois groupes nets : fidèles, récents, endormis."""
    rng = np.random.default_rng(0)

    def group(n: int, recency: int, frequency: int, monetary: int) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "recency_days": rng.normal(recency, 5, n).clip(1),
                "frequency": np.full(n, frequency),
                "monetary": rng.normal(monetary, 10, n).clip(1),
            }
        )

    return pd.concat(
        [group(20, 200, 3, 400), group(60, 30, 1, 150), group(80, 500, 1, 120)],
        ignore_index=True,
    )


def test_segment_names_personas_by_business_rule(rfm: pd.DataFrame) -> None:
    personas = segment(rfm)
    assert personas.value_counts().to_dict() == {
        "Endormis": 80,
        "Récents": 60,
        "Fidèles": 20,
    }
    assert set(personas[rfm["frequency"] == 3]) == {"Fidèles"}


def test_profile_segments_shares_sum_to_100(rfm: pd.DataFrame) -> None:
    summary = profile_segments(rfm, segment(rfm))
    assert summary["customer_share_pct"].sum() == pytest.approx(100, abs=0.2)
    assert summary["revenue_share_pct"].sum() == pytest.approx(100, abs=0.2)
    assert summary.loc["Fidèles", "frequency"] == 3


def test_silhouette_prefers_true_number_of_groups(rfm: pd.DataFrame) -> None:
    scores = silhouette_by_k(rfm, range(2, 5), sample_size=len(rfm))
    assert max(scores, key=scores.__getitem__) == 3


def test_campaign_revenue() -> None:
    assert campaign_revenue(1000, 0.05, 200, discount=0.1) == pytest.approx(9000)
