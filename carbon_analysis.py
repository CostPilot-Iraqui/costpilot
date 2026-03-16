# /app/backend/services/carbon_analysis.py
# Service d'analyse carbone et environnementale

import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso


# Facteurs d'émission carbone (kgCO2e/unité)
CARBON_FACTORS = {
    # Structure
    "beton_m3": 350,  # Béton armé standard
    "beton_bas_carbone_m3": 220,  # Béton bas carbone
    "acier_kg": 2.5,  # Acier de construction
    "bois_m3": -500,  # Bois (stockage carbone)
    "clt_m3": -450,  # CLT
    
    # Façade
    "brique_m2": 45,
    "enduit_m2": 8,
    "bardage_alu_m2": 85,
    "bardage_bois_m2": 5,
    "mur_rideau_m2": 120,
    "isolation_laine_m2": 4,
    "isolation_pse_m2": 12,
    
    # Second œuvre
    "platre_m2": 6,
    "carrelage_m2": 25,
    "parquet_m2": 8,
    "peinture_m2": 2,
    
    # Équipements
    "menuiserie_alu_m2": 180,
    "menuiserie_pvc_m2": 90,
    "menuiserie_bois_m2": 45,
    
    # Réseaux
    "cuivre_kg": 3.5,
    "pvc_kg": 3.0,
    "acier_galva_kg": 2.8
}

# Ratios carbone par m² selon typologie (kgCO2e/m²)
CARBON_RATIOS_M2 = {
    "housing": {
        "low_carbon": 450,
        "standard": 750,
        "high_carbon": 1100
    },
    "office": {
        "low_carbon": 500,
        "standard": 850,
        "high_carbon": 1250
    },
    "school": {
        "low_carbon": 480,
        "standard": 800,
        "high_carbon": 1150
    },
    "hotel": {
        "low_carbon": 550,
        "standard": 900,
        "high_carbon": 1350
    },
    "hospital": {
        "low_carbon": 650,
        "standard": 1050,
        "high_carbon": 1500
    }
}

# Seuils RE2020 (kgCO2e/m²)
RE2020_THRESHOLDS = {
    "housing": {"2022": 640, "2025": 530, "2028": 475, "2031": 415},
    "office": {"2022": 740, "2025": 650, "2028": 580, "2031": 490},
    "school": {"2022": 700, "2025": 610, "2028": 540, "2031": 460}
}


async def analyze_project_carbon(
    project_id: str,
    project_data: Dict,
    structure_type: str = "concrete",
    facade_type: str = "brick",
    insulation_type: str = "mineral_wool"
) -> Dict:
    """Analyse l'empreinte carbone d'un projet"""
    
    analysis_id = generate_uuid()
    now = now_iso()
    
    surface_m2 = project_data.get("target_surface_m2", 1000) or 1000
    project_type = project_data.get("project_usage", "housing") or "housing"
    floors = project_data.get("number_of_floors", 5) or 5
    
    # Estimation des quantités
    quantities = estimate_quantities(surface_m2, floors, structure_type)
    
    # Calcul carbone par poste
    carbon_by_category = {}
    
    # 1. Structure
    if structure_type == "concrete":
        structure_carbon = quantities["beton_m3"] * CARBON_FACTORS["beton_m3"]
        structure_carbon += quantities["acier_kg"] * CARBON_FACTORS["acier_kg"]
    elif structure_type == "timber":
        structure_carbon = quantities["bois_m3"] * CARBON_FACTORS["bois_m3"]
        structure_carbon += quantities["acier_kg"] * 0.3 * CARBON_FACTORS["acier_kg"]
    elif structure_type == "steel":
        structure_carbon = quantities["acier_kg"] * 2 * CARBON_FACTORS["acier_kg"]
    else:  # mixed
        structure_carbon = quantities["beton_m3"] * 0.6 * CARBON_FACTORS["beton_m3"]
        structure_carbon += quantities["bois_m3"] * 0.4 * CARBON_FACTORS["bois_m3"]
    
    carbon_by_category["structure"] = {
        "total_kgco2e": round(structure_carbon, 0),
        "per_m2": round(structure_carbon / surface_m2, 1),
        "percentage": 0  # Calculé après
    }
    
    # 2. Façade
    facade_area = surface_m2 * 0.4  # Estimation surface façade
    if facade_type == "brick":
        facade_carbon = facade_area * CARBON_FACTORS["brique_m2"]
    elif facade_type == "curtain_wall":
        facade_carbon = facade_area * CARBON_FACTORS["mur_rideau_m2"]
    elif facade_type == "timber_cladding":
        facade_carbon = facade_area * CARBON_FACTORS["bardage_bois_m2"]
    else:  # render
        facade_carbon = facade_area * CARBON_FACTORS["enduit_m2"]
    
    # Isolation
    if insulation_type == "mineral_wool":
        facade_carbon += facade_area * CARBON_FACTORS["isolation_laine_m2"]
    else:
        facade_carbon += facade_area * CARBON_FACTORS["isolation_pse_m2"]
    
    carbon_by_category["facade"] = {
        "total_kgco2e": round(facade_carbon, 0),
        "per_m2": round(facade_carbon / surface_m2, 1),
        "percentage": 0
    }
    
    # 3. Second œuvre
    second_oeuvre_carbon = surface_m2 * (
        CARBON_FACTORS["platre_m2"] * 1.5 +  # Cloisons + plafonds
        CARBON_FACTORS["carrelage_m2"] * 0.3 +  # 30% carrelage
        CARBON_FACTORS["parquet_m2"] * 0.2 +  # 20% parquet
        CARBON_FACTORS["peinture_m2"] * 2  # Murs et plafonds
    )
    
    carbon_by_category["second_oeuvre"] = {
        "total_kgco2e": round(second_oeuvre_carbon, 0),
        "per_m2": round(second_oeuvre_carbon / surface_m2, 1),
        "percentage": 0
    }
    
    # 4. Menuiseries
    window_area = surface_m2 * 0.15  # 15% de la surface
    menuiserie_carbon = window_area * CARBON_FACTORS["menuiserie_alu_m2"]
    
    carbon_by_category["menuiseries"] = {
        "total_kgco2e": round(menuiserie_carbon, 0),
        "per_m2": round(menuiserie_carbon / surface_m2, 1),
        "percentage": 0
    }
    
    # 5. Équipements techniques (estimation forfaitaire)
    equipment_carbon = surface_m2 * 80  # ~80 kgCO2e/m² pour CVC, élec, plomberie
    
    carbon_by_category["equipements"] = {
        "total_kgco2e": round(equipment_carbon, 0),
        "per_m2": round(equipment_carbon / surface_m2, 1),
        "percentage": 0
    }
    
    # Total
    total_carbon = sum(cat["total_kgco2e"] for cat in carbon_by_category.values())
    carbon_per_m2 = total_carbon / surface_m2
    
    # Calculer les pourcentages
    for category in carbon_by_category.values():
        category["percentage"] = round(category["total_kgco2e"] / total_carbon * 100, 1) if total_carbon > 0 else 0
    
    # Comparaison RE2020
    re2020_thresholds = RE2020_THRESHOLDS.get(project_type, RE2020_THRESHOLDS["housing"])
    re2020_compliance = {}
    for year, threshold in re2020_thresholds.items():
        re2020_compliance[year] = {
            "threshold": threshold,
            "compliant": carbon_per_m2 <= threshold,
            "gap": round(carbon_per_m2 - threshold, 1),
            "gap_percentage": round((carbon_per_m2 - threshold) / threshold * 100, 1)
        }
    
    # Benchmark
    type_ratios = CARBON_RATIOS_M2.get(project_type, CARBON_RATIOS_M2["housing"])
    if carbon_per_m2 <= type_ratios["low_carbon"]:
        benchmark_status = "low_carbon"
        benchmark_label = "Bas carbone"
    elif carbon_per_m2 <= type_ratios["standard"]:
        benchmark_status = "standard"
        benchmark_label = "Standard"
    else:
        benchmark_status = "high_carbon"
        benchmark_label = "Élevé"
    
    # Recommandations
    recommendations = generate_carbon_recommendations(
        carbon_by_category, structure_type, facade_type, carbon_per_m2
    )
    
    return {
        "analysis_id": analysis_id,
        "project_id": project_id,
        "generated_at": now,
        "input_parameters": {
            "surface_m2": surface_m2,
            "project_type": project_type,
            "floors": floors,
            "structure_type": structure_type,
            "facade_type": facade_type,
            "insulation_type": insulation_type
        },
        "carbon_footprint": {
            "total_kgco2e": round(total_carbon, 0),
            "per_m2_kgco2e": round(carbon_per_m2, 1),
            "total_tonnes": round(total_carbon / 1000, 1)
        },
        "breakdown_by_category": carbon_by_category,
        "re2020_compliance": re2020_compliance,
        "benchmark": {
            "status": benchmark_status,
            "label": benchmark_label,
            "reference_values": type_ratios
        },
        "recommendations": recommendations
    }


def estimate_quantities(surface_m2: float, floors: int, structure_type: str) -> Dict:
    """Estime les quantités de matériaux"""
    
    floor_area = surface_m2 / floors
    
    # Béton
    if structure_type == "concrete":
        beton_m3 = surface_m2 * 0.35  # ~0.35 m³/m² SDP
    elif structure_type == "mixed":
        beton_m3 = surface_m2 * 0.20
    else:
        beton_m3 = surface_m2 * 0.05  # Fondations uniquement
    
    # Acier
    if structure_type == "steel":
        acier_kg = surface_m2 * 50
    elif structure_type == "concrete":
        acier_kg = beton_m3 * 100  # ~100 kg/m³ béton
    else:
        acier_kg = surface_m2 * 15
    
    # Bois
    if structure_type == "timber":
        bois_m3 = surface_m2 * 0.20
    elif structure_type == "mixed":
        bois_m3 = surface_m2 * 0.08
    else:
        bois_m3 = surface_m2 * 0.02  # Menuiseries bois
    
    return {
        "beton_m3": beton_m3,
        "acier_kg": acier_kg,
        "bois_m3": bois_m3
    }


def generate_carbon_recommendations(
    breakdown: Dict,
    structure_type: str,
    facade_type: str,
    carbon_per_m2: float
) -> List[Dict]:
    """Génère des recommandations d'optimisation carbone"""
    
    recommendations = []
    
    # Structure
    if structure_type == "concrete" and breakdown["structure"]["percentage"] > 35:
        recommendations.append({
            "category": "structure",
            "priority": "high",
            "title": "Utiliser du béton bas carbone",
            "description": "Remplacer le béton standard par du béton bas carbone (CEM III ou géopolymère)",
            "potential_reduction_kgco2e": round(breakdown["structure"]["total_kgco2e"] * 0.35, 0),
            "potential_reduction_pct": 35
        })
        recommendations.append({
            "category": "structure",
            "priority": "medium",
            "title": "Optimiser le ferraillage",
            "description": "Utiliser de l'acier recyclé et optimiser les sections",
            "potential_reduction_kgco2e": round(breakdown["structure"]["total_kgco2e"] * 0.10, 0),
            "potential_reduction_pct": 10
        })
    
    if structure_type != "timber":
        recommendations.append({
            "category": "structure",
            "priority": "high",
            "title": "Structure mixte bois-béton",
            "description": "Utiliser du CLT pour les planchers et refends",
            "potential_reduction_kgco2e": round(breakdown["structure"]["total_kgco2e"] * 0.40, 0),
            "potential_reduction_pct": 40
        })
    
    # Façade
    if facade_type == "curtain_wall":
        recommendations.append({
            "category": "facade",
            "priority": "medium",
            "title": "Réduire la surface vitrée",
            "description": "Optimiser le ratio vitrage/opaque pour réduire l'impact carbone",
            "potential_reduction_kgco2e": round(breakdown["facade"]["total_kgco2e"] * 0.25, 0),
            "potential_reduction_pct": 25
        })
    
    recommendations.append({
        "category": "facade",
        "priority": "medium",
        "title": "Isolation biosourcée",
        "description": "Remplacer les isolants synthétiques par de la fibre de bois ou ouate de cellulose",
        "potential_reduction_kgco2e": round(breakdown["facade"]["total_kgco2e"] * 0.15, 0),
        "potential_reduction_pct": 15
    })
    
    # Second œuvre
    recommendations.append({
        "category": "second_oeuvre",
        "priority": "low",
        "title": "Matériaux biosourcés",
        "description": "Utiliser des cloisons en fibre de bois et des revêtements naturels",
        "potential_reduction_kgco2e": round(breakdown["second_oeuvre"]["total_kgco2e"] * 0.20, 0),
        "potential_reduction_pct": 20
    })
    
    # Menuiseries
    recommendations.append({
        "category": "menuiseries",
        "priority": "medium",
        "title": "Menuiseries bois ou mixte",
        "description": "Remplacer l'aluminium par du bois ou bois-alu",
        "potential_reduction_kgco2e": round(breakdown["menuiseries"]["total_kgco2e"] * 0.60, 0),
        "potential_reduction_pct": 60
    })
    
    # Trier par réduction potentielle
    recommendations.sort(key=lambda x: x["potential_reduction_kgco2e"], reverse=True)
    
    return recommendations


async def save_carbon_analysis(project_id: str, analysis: Dict) -> Dict:
    """Sauvegarde une analyse carbone"""
    
    record = {
        "id": analysis["analysis_id"],
        "project_id": project_id,
        **analysis,
        "saved_at": now_iso()
    }
    
    await db.carbon_analyses.insert_one(record)
    record.pop("_id", None)
    
    return record


async def get_carbon_analyses(project_id: str) -> List[Dict]:
    """Récupère les analyses carbone d'un projet"""
    analyses = await db.carbon_analyses.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("generated_at", -1).to_list(100)
    return analyses
