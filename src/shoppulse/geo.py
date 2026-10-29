"""Outils géographiques partagés (EDA, features du modèle de retard, audit d'équité)."""

import numpy as np
import numpy.typing as npt

EARTH_RADIUS_KM = 6371.0

# Les 5 grandes régions officielles du Brésil (IBGE).
STATE_REGION: dict[str, str] = {
    **dict.fromkeys(["AC", "AM", "AP", "PA", "RO", "RR", "TO"], "Nord"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "Nordeste"),
    **dict.fromkeys(["DF", "GO", "MS", "MT"], "Centre-Ouest"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "Sudeste"),
    **dict.fromkeys(["PR", "RS", "SC"], "Sud"),
}


def haversine_km(
    lat1: npt.ArrayLike, lng1: npt.ArrayLike, lat2: npt.ArrayLike, lng2: npt.ArrayLike
) -> npt.NDArray[np.float64]:
    """Distance à vol d'oiseau en kilomètres (vectorisée)."""
    lat1, lng1, lat2, lng2 = (
        np.radians(np.asarray(v, float)) for v in (lat1, lng1, lat2, lng2)
    )
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2) ** 2
    )
    distance: npt.NDArray[np.float64] = 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
    return distance
