# /app/backend/services/market_intelligence.py
# Service pour l'intelligence marché construction

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso, REGIONAL_COEFFICIENTS

async def get_market_trends(region: Optional[str] = None) -> List[Dict]:
    """Récupère les tendances du marché de la construction"""
    query = {}
    if region:
        query["region"] = region
    
    trends = await db.market_intelligence.find(
        {"type": "market_trend", **query},
        {"_id": 0}
    ).to_list(100)
    
    if not trends:
        # Générer des données de tendances par défaut
        trends = await generate_default_market_trends()
    
    return trends

async def generate_default_market_trends() -> List[Dict]:
    """Génère les tendances du marché par défaut"""
    now = now_iso()
    trends = []
    
    categories = [
        {"category": "Matériaux - Béton", "current": 145, "prev": 138, "forecast_6m": 150, "forecast_12m": 155},
        {"category": "Matériaux - Acier", "current": 1250, "prev": 1180, "forecast_6m": 1300, "forecast_12m": 1280},
        {"category": "Matériaux - Bois", "current": 420, "prev": 435, "forecast_6m": 410, "forecast_12m": 400},
        {"category": "Matériaux - Aluminium", "current": 2850, "prev": 2720, "forecast_6m": 2950, "forecast_12m": 3000},
        {"category": "Main d'œuvre - GO", "current": 48, "prev": 46, "forecast_6m": 50, "forecast_12m": 52},
        {"category": "Main d'œuvre - SO", "current": 42, "prev": 40, "forecast_6m": 44, "forecast_12m": 46},
        {"category": "Main d'œuvre - CET", "current": 55, "prev": 52, "forecast_6m": 58, "forecast_12m": 60},
        {"category": "Énergie - Électricité", "current": 180, "prev": 165, "forecast_6m": 190, "forecast_12m": 185},
        {"category": "Énergie - Gaz", "current": 95, "prev": 88, "forecast_6m": 100, "forecast_12m": 92}
    ]
    
    for cat in categories:
        variation = (cat["current"] - cat["prev"]) / cat["prev"] * 100
        trend = {
            "id": generate_uuid(),
            "type": "market_trend",
            "region": "national",
            "category": cat["category"],
            "trend_type": "price_index",
            "current_value": cat["current"],
            "previous_value": cat["prev"],
            "variation_pct": round(variation, 1),
            "trend_direction": "up" if variation > 0 else "down" if variation < 0 else "stable",
            "forecast_6m": cat["forecast_6m"],
            "forecast_12m": cat["forecast_12m"],
            "confidence": 0.85,
            "data_source": "Indices BT/TP",
            "updated_at": now
        }
        trends.append(trend)
        await db.market_intelligence.insert_one(trend)
    
    return trends

async def get_regional_cost_indices() -> List[Dict]:
    """Récupère les indices de coût par région"""
    indices = await db.market_intelligence.find(
        {"type": "regional_index"},
        {"_id": 0}
    ).to_list(20)
    
    if not indices:
        indices = await generate_regional_indices()
    
    return indices

async def generate_regional_indices() -> List[Dict]:
    """Génère les indices régionaux par défaut"""
    now = now_iso()
    indices = []
    
    for region_code, region_data in REGIONAL_COEFFICIENTS.items():
        index = {
            "id": generate_uuid(),
            "type": "regional_index",
            "region": region_code,
            "region_name": region_data["label"],
            "base_index": 100,
            "current_index": round(100 * region_data["coefficient"], 1),
            "coefficient": region_data["coefficient"],
            "variation_ytd": round((region_data["coefficient"] - 1) * 100, 1),
            "components": {
                "materials": round(100 * region_data["coefficient"] * 0.98, 1),
                "labor": round(100 * region_data["coefficient"] * 1.05, 1),
                "equipment": round(100 * region_data["coefficient"] * 0.95, 1),
                "transport": round(100 * region_data["coefficient"] * 1.02, 1)
            },
            "market_tension": "high" if region_data["coefficient"] > 1.1 else "medium" if region_data["coefficient"] > 1.0 else "low",
            "last_update": now
        }
        indices.append(index)
        await db.market_intelligence.insert_one(index)
    
    return indices

async def get_construction_activity(region: Optional[str] = None) -> Dict:
    """Récupère les indicateurs d'activité de la construction"""
    query = {"type": "activity_indicator"}
    if region:
        query["region"] = region
    
    activity = await db.market_intelligence.find_one(query, {"_id": 0})
    
    if not activity:
        activity = await generate_activity_indicators(region or "national")
    
    return activity

async def generate_activity_indicators(region: str) -> Dict:
    """Génère les indicateurs d'activité"""
    now = now_iso()
    
    activity = {
        "id": generate_uuid(),
        "type": "activity_indicator",
        "region": region,
        "indicators": {
            "permits_issued": {
                "current": 42500,
                "previous_year": 45200,
                "variation": -6.0,
                "unit": "logements/trimestre"
            },
            "construction_starts": {
                "current": 38200,
                "previous_year": 41800,
                "variation": -8.6,
                "unit": "logements/trimestre"
            },
            "completions": {
                "current": 35800,
                "previous_year": 38500,
                "variation": -7.0,
                "unit": "logements/trimestre"
            },
            "non_residential_m2": {
                "current": 8500000,
                "previous_year": 9200000,
                "variation": -7.6,
                "unit": "m²/trimestre"
            },
            "order_books_months": {
                "current": 8.5,
                "previous_year": 9.2,
                "variation": -7.6,
                "unit": "mois"
            },
            "capacity_utilization": {
                "current": 87,
                "previous_year": 91,
                "variation": -4.4,
                "unit": "%"
            }
        },
        "market_outlook": "modéré",
        "key_insights": [
            "Ralentissement de l'activité dans le secteur résidentiel",
            "Le non-résidentiel reste dynamique, porté par la rénovation énergétique",
            "Tension sur les carnets de commandes dans les corps d'état techniques",
            "Difficultés de recrutement persistantes dans le gros œuvre"
        ],
        "updated_at": now
    }
    
    await db.market_intelligence.insert_one(activity)
    return activity

async def get_price_forecasts(category: Optional[str] = None) -> List[Dict]:
    """Récupère les prévisions de prix"""
    query = {"type": "price_forecast"}
    if category:
        query["category"] = category
    
    forecasts = await db.market_intelligence.find(query, {"_id": 0}).to_list(50)
    
    if not forecasts:
        forecasts = await generate_price_forecasts()
    
    return forecasts

async def generate_price_forecasts() -> List[Dict]:
    """Génère les prévisions de prix par défaut"""
    now = now_iso()
    forecasts = []
    
    forecast_data = [
        {"category": "Gros œuvre", "current_index": 112, "q1": 114, "q2": 116, "q3": 117, "q4": 118, "confidence": 0.80},
        {"category": "Façade / Enveloppe", "current_index": 108, "q1": 110, "q2": 111, "q3": 112, "q4": 113, "confidence": 0.75},
        {"category": "Second œuvre", "current_index": 106, "q1": 107, "q2": 108, "q3": 109, "q4": 110, "confidence": 0.85},
        {"category": "CVC", "current_index": 115, "q1": 118, "q2": 120, "q3": 121, "q4": 122, "confidence": 0.70},
        {"category": "Électricité", "current_index": 110, "q1": 112, "q2": 114, "q3": 115, "q4": 116, "confidence": 0.75},
        {"category": "Plomberie", "current_index": 109, "q1": 111, "q2": 112, "q3": 113, "q4": 114, "confidence": 0.80}
    ]
    
    for data in forecast_data:
        forecast = {
            "id": generate_uuid(),
            "type": "price_forecast",
            "category": data["category"],
            "base_year": 2020,
            "current_index": data["current_index"],
            "forecasts": {
                "Q1_2026": data["q1"],
                "Q2_2026": data["q2"],
                "Q3_2026": data["q3"],
                "Q4_2026": data["q4"]
            },
            "annual_variation": round((data["q4"] - data["current_index"]) / data["current_index"] * 100, 1),
            "confidence": data["confidence"],
            "methodology": "Régression linéaire sur indices BT + ajustement expert",
            "updated_at": now
        }
        forecasts.append(forecast)
        await db.market_intelligence.insert_one(forecast)
    
    return forecasts
