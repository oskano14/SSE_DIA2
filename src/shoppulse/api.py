"""API REST ShopPulse : un endpoint par modèle, documentation OpenAPI sur /docs.

Lancement : uv run uvicorn shoppulse.api:app --reload
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Any, Literal, Self

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from shoppulse.features import build_features
from shoppulse.training import DELAY_FILE, SENTIMENT_FILE, Artifact, load


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Charge les artefacts une seule fois, au démarrage du serveur."""
    app.state.delay = load(DELAY_FILE)
    app.state.sentiment = load(SENTIMENT_FILE)
    yield


app = FastAPI(
    title="ShopPulse API",
    version="1.0.0",
    description="Prédiction du retard de livraison et sentiment des avis clients.",
    lifespan=lifespan,
)


# --- Schémas -----------------------------------------------------------------


class DelayRequest(BaseModel):
    """Commande au moment de l'achat (aucune information de livraison réelle)."""

    customer_zip_code_prefix: str = Field(pattern=r"^\d{5}$", examples=["40010"])
    seller_id: str = Field(
        pattern=r"^[0-9a-f]{32}$", examples=["6560211a19b47992c3666cc44a7e94c0"]
    )
    purchase_timestamp: datetime = Field(examples=["2018-03-10T14:30:00"])
    estimated_delivery_date: date = Field(examples=["2018-03-20"])
    n_items: int = Field(ge=1, le=100, examples=[1])
    total_price: float = Field(gt=0, examples=[129.9])
    total_freight: float = Field(ge=0, examples=[18.5])
    total_weight_g: float | None = Field(default=None, ge=0, examples=[800])
    total_volume_cm3: float | None = Field(default=None, ge=0, examples=[6000])

    @model_validator(mode="after")
    def estimated_after_purchase(self) -> Self:
        if self.estimated_delivery_date < self.purchase_timestamp.date():
            raise ValueError("estimated_delivery_date est antérieure à l'achat")
        return self


class DelayResponse(BaseModel):
    late_probability: float = Field(description="Probabilité estimée de retard")
    high_risk: bool = Field(description="Dans les 10 % de commandes les plus risquées")
    threshold: float = Field(description="Seuil d'alerte appliqué à la probabilité")


class SentimentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000, examples=["Não recebi o produto"])


class SentimentResponse(BaseModel):
    sentiment: Literal["positive", "negative"]
    positive_probability: float


# --- Endpoints ---------------------------------------------------------------


@app.get("/health")
def health(request: Request) -> dict[str, Any]:
    """État du service et métriques des modèles chargés."""
    return {
        "status": "ok",
        "delay_model": request.app.state.delay["metrics"],
        "sentiment_model": request.app.state.sentiment["metrics"],
    }


def _lookup(table: pd.DataFrame, key: str, label: str) -> pd.Series:
    if key not in table.index:
        raise HTTPException(status_code=404, detail=f"{label} inconnu : {key}")
    return table.loc[[key]].iloc[0]


def _delay_row(order: DelayRequest, artifact: Artifact) -> pd.DataFrame:
    """Reconstitue les colonnes brutes attendues par build_features."""
    seller = _lookup(artifact["sellers"], order.seller_id, "Vendeur")
    customer = _lookup(artifact["zips"], order.customer_zip_code_prefix, "Code postal")
    row = {
        "order_purchase_timestamp": order.purchase_timestamp,
        "order_estimated_delivery_date": pd.Timestamp(order.estimated_delivery_date),
        "customer_state": customer["geolocation_state"],
        "seller_state": seller["seller_state"],
        "customer_lat": customer["geolocation_lat"],
        "customer_lng": customer["geolocation_lng"],
        "seller_lat": seller["seller_lat"],
        "seller_lng": seller["seller_lng"],
        "n_items": order.n_items,
        "total_price": order.total_price,
        "total_freight": order.total_freight,
        "total_weight_g": order.total_weight_g,
        "total_volume_cm3": order.total_volume_cm3,
        "seller_prior_orders": seller["orders"],
        "seller_late_rate": seller["late_rate"],
    }
    return pd.DataFrame([row])


@app.post("/predict/delay", response_model=DelayResponse)
def predict_delay(order: DelayRequest, request: Request) -> DelayResponse:
    """Risque de retard d'une commande (modèle gradient boosting)."""
    artifact = request.app.state.delay
    features = build_features(_delay_row(order, artifact))
    probability = float(artifact["model"].predict_proba(features)[0, 1])
    return DelayResponse(
        late_probability=round(probability, 4),
        high_risk=probability >= artifact["threshold"],
        threshold=round(artifact["threshold"], 4),
    )


@app.post("/predict/sentiment", response_model=SentimentResponse)
def predict_sentiment(review: SentimentRequest, request: Request) -> SentimentResponse:
    """Sentiment d'un avis en portugais (TF-IDF + régression logistique)."""
    model = request.app.state.sentiment["model"]
    probability = float(model.predict_proba([review.text])[0, 1])
    return SentimentResponse(
        sentiment="positive" if probability >= 0.5 else "negative",
        positive_probability=round(probability, 4),
    )
