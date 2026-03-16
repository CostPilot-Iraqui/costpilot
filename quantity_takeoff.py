# /app/backend/services/quantity_takeoff.py
# Service de métré automatique

import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso

# Structure des lots pour le métré
LOTS_STRUCTURE = {
    "01": {"name": "Terrassements", "unit": "m³", "default_ratio": 0.5},
    "02": {"name": "VRD", "unit": "ml", "default_ratio": 0.3},
    "03": {"name": "Gros œuvre", "unit": "m²", "default_ratio": 1.0},
    "04": {"name": "Charpente", "unit": "m²", "default_ratio": 0.85},
    "05": {"name": "Couverture", "unit": "m²", "default_ratio": 0.15},
    "06": {"name": "Étanchéité", "unit": "m²", "default_ratio": 0.12},
    "07": {"name": "Menuiseries extérieures", "unit": "u", "default_ratio": 0.08},
    "08": {"name": "Menuiseries intérieures", "unit": "u", "default_ratio": 0.05},
    "09": {"name": "Cloisons/Doublages", "unit": "m²", "default_ratio": 1.2},
    "10": {"name": "Revêtements de sol", "unit": "m²", "default_ratio": 0.95},
    "11": {"name": "Peinture", "unit": "m²", "default_ratio": 2.5},
    "12": {"name": "Plomberie", "unit": "u", "default_ratio": 0.02},
    "13": {"name": "Électricité", "unit": "ml", "default_ratio": 15},
    "14": {"name": "CVC", "unit": "kW", "default_ratio": 0.08},
    "15": {"name": "Ascenseurs", "unit": "u", "default_ratio": 0.001},
}

# Prix unitaires par lot et qualité
UNIT_PRICES = {
    "01": {"economic": 25, "standard": 35, "premium": 50},
    "02": {"economic": 150, "standard": 200, "premium": 300},
    "03": {"economic": 350, "standard": 450, "premium": 600},
    "04": {"economic": 80, "standard": 120, "premium": 180},
    "05": {"economic": 45, "standard": 65, "premium": 100},
    "06": {"economic": 55, "standard": 80, "premium": 120},
    "07": {"economic": 450, "standard": 650, "premium": 1200},
    "08": {"economic": 200, "standard": 350, "premium": 600},
    "09": {"economic": 35, "standard": 50, "premium": 80},
    "10": {"economic": 40, "standard": 70, "premium": 150},
    "11": {"economic": 12, "standard": 18, "premium": 30},
    "12": {"economic": 1500, "standard": 2500, "premium": 4000},
    "13": {"economic": 8, "standard": 12, "premium": 20},
    "14": {"economic": 120, "standard": 180, "premium": 280},
    "15": {"economic": 35000, "standard": 50000, "premium": 80000},
}


async def generate_quantity_takeoff(
    project_id: str,
    surface_m2: float,
    floors: int = 4,
    quality_level: str = "standard"
) -> Dict:
    """Génère un métré automatique basé sur les paramètres du projet"""
    
    takeoff_id = generate_uuid()
    now = now_iso()
    
    lots = []
    total_cost = 0
    
    for lot_code, lot_info in LOTS_STRUCTURE.items():
        # Calcul de la quantité
        ratio = lot_info["default_ratio"]
        
        # Ajustements selon le lot
        if lot_code == "15":  # Ascenseurs
            quantity = max(1, floors // 3)
        elif lot_code in ["03", "04", "05", "06", "09", "10", "11"]:  # Lots au m²
            quantity = surface_m2 * ratio
        elif lot_code == "13":  # Électricité en ml
            quantity = surface_m2 * ratio
        elif lot_code == "14":  # CVC en kW
            quantity = surface_m2 * ratio
        elif lot_code in ["07", "08", "12"]:  # Lots unitaires
            quantity = surface_m2 * ratio
        else:
            quantity = surface_m2 * ratio
        
        # Prix unitaire selon qualité
        unit_price = UNIT_PRICES.get(lot_code, {}).get(quality_level, 100)
        lot_cost = quantity * unit_price
        total_cost += lot_cost
        
        lots.append({
            "code": lot_code,
            "name": lot_info["name"],
            "unit": lot_info["unit"],
            "quantity": round(quantity, 2),
            "unit_price": unit_price,
            "total_cost": round(lot_cost, 2),
            "percentage": 0  # Will be calculated after
        })
    
    # Calculer les pourcentages
    for lot in lots:
        lot["percentage"] = round(lot["total_cost"] / total_cost * 100, 1) if total_cost > 0 else 0
    
    # Résumé par macro-lot
    macro_lots = {
        "structure": sum(l["total_cost"] for l in lots if l["code"] in ["01", "02", "03", "04", "05", "06"]),
        "second_oeuvre": sum(l["total_cost"] for l in lots if l["code"] in ["07", "08", "09", "10", "11"]),
        "lots_techniques": sum(l["total_cost"] for l in lots if l["code"] in ["12", "13", "14", "15"]),
    }
    
    result = {
        "id": takeoff_id,
        "project_id": project_id,
        "type": "quantity_takeoff",
        "parameters": {
            "surface_m2": surface_m2,
            "floors": floors,
            "quality_level": quality_level
        },
        "lots": lots,
        "macro_lots": macro_lots,
        "total_cost": round(total_cost, 2),
        "cost_per_m2": round(total_cost / surface_m2, 2) if surface_m2 > 0 else 0,
        "created_at": now
    }
    
    # Sauvegarder
    await db.quantity_takeoffs.insert_one(result)
    result.pop("_id", None)
    
    return result


async def get_quantity_takeoff(project_id: str) -> Optional[Dict]:
    """Récupère le dernier métré d'un projet"""
    result = await db.quantity_takeoffs.find_one(
        {"project_id": project_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    return result


async def get_quantity_takeoffs(project_id: str) -> List[Dict]:
    """Récupère tous les métrés d'un projet"""
    cursor = db.quantity_takeoffs.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", -1)
    return await cursor.to_list(length=100)


async def update_lot_quantity(
    takeoff_id: str,
    lot_code: str,
    new_quantity: float
) -> Optional[Dict]:
    """Met à jour la quantité d'un lot"""
    
    takeoff = await db.quantity_takeoffs.find_one({"id": takeoff_id})
    if not takeoff:
        return None
    
    # Mettre à jour le lot
    lots = takeoff.get("lots", [])
    total_cost = 0
    
    for lot in lots:
        if lot["code"] == lot_code:
            lot["quantity"] = new_quantity
            lot["total_cost"] = round(new_quantity * lot["unit_price"], 2)
        total_cost += lot["total_cost"]
    
    # Recalculer les pourcentages
    for lot in lots:
        lot["percentage"] = round(lot["total_cost"] / total_cost * 100, 1) if total_cost > 0 else 0
    
    # Mettre à jour le document
    await db.quantity_takeoffs.update_one(
        {"id": takeoff_id},
        {"$set": {
            "lots": lots,
            "total_cost": round(total_cost, 2),
            "cost_per_m2": round(total_cost / takeoff["parameters"]["surface_m2"], 2),
            "updated_at": now_iso()
        }}
    )
    
    return await db.quantity_takeoffs.find_one({"id": takeoff_id}, {"_id": 0})
