# /app/backend/services/multi_scenario.py
# Service de simulation multi-scénarios

from typing import List, Dict, Any, Optional
import sys
sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso, DEFAULT_COST_REFERENCES

async def create_multi_scenario_analysis(
    project_id: str,
    project_data: Dict
) -> Dict:
    """Crée une analyse multi-scénarios pour un projet"""
    analysis_id = generate_uuid()
    now = now_iso()
    
    surface = project_data.get("target_surface_m2", 1000) or 1000
    building_type = project_data.get("project_usage", "housing") or "housing"
    location = project_data.get("location", "idf") or "idf"
    
    # Récupérer les coûts de référence
    refs = DEFAULT_COST_REFERENCES.get(building_type, DEFAULT_COST_REFERENCES["housing"])
    
    # Créer les 3 scénarios standards
    scenarios = []
    
    # Scénario Économique
    eco_cost_m2 = refs.get("economic", 1400)
    scenarios.append({
        "id": generate_uuid(),
        "name": "Scénario Économique",
        "type": "economic",
        "description": "Version optimisée avec matériaux standards et prestations minimales conformes aux réglementations.",
        "cost_per_m2": eco_cost_m2,
        "total_cost": round(eco_cost_m2 * surface, 2),
        "quality_level": "economic",
        "characteristics": {
            "facade": "Enduit simple, menuiseries PVC",
            "sols": "Carrelage standard, moquette basique",
            "equipements": "Sanitaires entrée de gamme",
            "cvc": "Chauffage collectif gaz, pas de climatisation",
            "finitions": "Peinture standard, plinthes PVC"
        },
        "lots_distribution": generate_lots_distribution(eco_cost_m2 * surface, "economic"),
        "pros": [
            "Coût d'investissement minimal",
            "Rapidité de mise en œuvre",
            "Entretien simplifié"
        ],
        "cons": [
            "Confort limité",
            "Performances énergétiques minimales",
            "Valorisation locative moindre"
        ],
        "roi_estimate": "6-8 ans",
        "risk_level": "low"
    })
    
    # Scénario Standard
    std_cost_m2 = refs.get("standard", 1850)
    scenarios.append({
        "id": generate_uuid(),
        "name": "Scénario Standard",
        "type": "standard",
        "description": "Version équilibrée offrant un bon rapport qualité/prix avec des prestations courantes du marché.",
        "cost_per_m2": std_cost_m2,
        "total_cost": round(std_cost_m2 * surface, 2),
        "quality_level": "standard",
        "characteristics": {
            "facade": "Bardage mixte, menuiseries aluminium",
            "sols": "Carrelage grand format, parquet stratifié",
            "equipements": "Sanitaires milieu de gamme",
            "cvc": "PAC air/eau, VMC double flux",
            "finitions": "Peinture qualité, plinthes bois"
        },
        "lots_distribution": generate_lots_distribution(std_cost_m2 * surface, "standard"),
        "pros": [
            "Équilibre qualité/prix optimal",
            "Conformité RE2020",
            "Valorisation correcte à la revente"
        ],
        "cons": [
            "Différenciation limitée",
            "Performances moyennes"
        ],
        "roi_estimate": "8-10 ans",
        "risk_level": "medium"
    })
    
    # Scénario Premium
    premium_cost_m2 = refs.get("premium", 2500)
    scenarios.append({
        "id": generate_uuid(),
        "name": "Scénario Premium",
        "type": "premium",
        "description": "Version haut de gamme avec prestations soignées et équipements performants.",
        "cost_per_m2": premium_cost_m2,
        "total_cost": round(premium_cost_m2 * surface, 2),
        "quality_level": "premium",
        "characteristics": {
            "facade": "Façade composite haute performance, triple vitrage",
            "sols": "Parquet massif, carrelage grand format rectifié",
            "equipements": "Sanitaires design, robinetterie haut de gamme",
            "cvc": "Géothermie, plancher chauffant/rafraîchissant",
            "finitions": "Peinture premium, moulures, LED intégrées"
        },
        "lots_distribution": generate_lots_distribution(premium_cost_m2 * surface, "premium"),
        "pros": [
            "Confort optimal",
            "Haute performance énergétique",
            "Forte valorisation patrimoniale",
            "Image qualitative"
        ],
        "cons": [
            "Investissement initial élevé",
            "Délais de réalisation plus longs",
            "Maintenance plus coûteuse"
        ],
        "roi_estimate": "10-15 ans",
        "risk_level": "medium"
    })
    
    # Analyse comparative
    comparison_metrics = {
        "cost_per_m2": {
            "economic": eco_cost_m2,
            "standard": std_cost_m2,
            "premium": premium_cost_m2,
            "unit": "€/m²"
        },
        "total_cost": {
            "economic": round(eco_cost_m2 * surface, 2),
            "standard": round(std_cost_m2 * surface, 2),
            "premium": round(premium_cost_m2 * surface, 2),
            "unit": "€"
        },
        "variance_vs_standard": {
            "economic": round((eco_cost_m2 - std_cost_m2) / std_cost_m2 * 100, 1),
            "standard": 0,
            "premium": round((premium_cost_m2 - std_cost_m2) / std_cost_m2 * 100, 1),
            "unit": "%"
        },
        "energy_performance": {
            "economic": "C",
            "standard": "B",
            "premium": "A"
        },
        "estimated_charges_m2_year": {
            "economic": 35,
            "standard": 28,
            "premium": 22,
            "unit": "€/m²/an"
        }
    }
    
    # Analyse de sensibilité
    sensitivity_analysis = {
        "surface_impact": [
            {"surface_variation": -10, "cost_impact_eco": round(eco_cost_m2 * surface * -0.10, 0), "cost_impact_std": round(std_cost_m2 * surface * -0.10, 0), "cost_impact_premium": round(premium_cost_m2 * surface * -0.10, 0)},
            {"surface_variation": 0, "cost_impact_eco": 0, "cost_impact_std": 0, "cost_impact_premium": 0},
            {"surface_variation": 10, "cost_impact_eco": round(eco_cost_m2 * surface * 0.10, 0), "cost_impact_std": round(std_cost_m2 * surface * 0.10, 0), "cost_impact_premium": round(premium_cost_m2 * surface * 0.10, 0)}
        ],
        "inflation_impact": [
            {"inflation": 2, "eco_final": round(eco_cost_m2 * 1.02 * surface, 0), "std_final": round(std_cost_m2 * 1.02 * surface, 0), "premium_final": round(premium_cost_m2 * 1.02 * surface, 0)},
            {"inflation": 4, "eco_final": round(eco_cost_m2 * 1.04 * surface, 0), "std_final": round(std_cost_m2 * 1.04 * surface, 0), "premium_final": round(premium_cost_m2 * 1.04 * surface, 0)},
            {"inflation": 6, "eco_final": round(eco_cost_m2 * 1.06 * surface, 0), "std_final": round(std_cost_m2 * 1.06 * surface, 0), "premium_final": round(premium_cost_m2 * 1.06 * surface, 0)}
        ]
    }
    
    # Recommandation
    recommended_scenario = "standard"  # Par défaut
    recommendation_reason = "Le scénario Standard offre le meilleur équilibre entre coût d'investissement, qualité des prestations et valorisation à long terme."
    
    analysis = {
        "id": analysis_id,
        "type": "multi_scenario",
        "project_id": project_id,
        "surface_m2": surface,
        "building_type": building_type,
        "scenarios": scenarios,
        "comparison_metrics": comparison_metrics,
        "sensitivity_analysis": sensitivity_analysis,
        "recommended_scenario": recommended_scenario,
        "recommendation_reason": recommendation_reason,
        "created_at": now,
        "updated_at": now
    }
    
    await db.multi_scenarios.insert_one(analysis)
    # Remove MongoDB _id before returning
    analysis.pop("_id", None)
    return analysis

def generate_lots_distribution(total_cost: float, quality_level: str) -> Dict:
    """Génère la distribution par lots selon le niveau de qualité"""
    # Ajustements selon le niveau de qualité
    adjustments = {
        "economic": {"facade": 0.08, "interior": 0.18, "technical": 0.22},
        "standard": {"facade": 0.10, "interior": 0.22, "technical": 0.25},
        "premium": {"facade": 0.12, "interior": 0.25, "technical": 0.28}
    }
    
    adj = adjustments.get(quality_level, adjustments["standard"])
    
    return {
        "infrastructure": round(total_cost * 0.05, 0),
        "structure": round(total_cost * 0.26, 0),
        "facade": round(total_cost * adj["facade"], 0),
        "interior": round(total_cost * adj["interior"], 0),
        "technical": round(total_cost * adj["technical"], 0),
        "exterior": round(total_cost * 0.02, 0),
        "contingency": round(total_cost * 0.05, 0)
    }

async def get_multi_scenario_analyses(project_id: str) -> List[Dict]:
    """Récupère les analyses multi-scénarios d'un projet"""
    analyses = await db.multi_scenarios.find(
        {"project_id": project_id},
        {"_id": 0}
    ).to_list(50)
    return sorted(analyses, key=lambda x: x.get("created_at", ""), reverse=True)

async def update_scenario(
    project_id: str,
    analysis_id: str,
    scenario_id: str,
    updates: Dict
) -> Dict:
    """Met à jour un scénario spécifique"""
    analysis = await db.multi_scenarios.find_one(
        {"id": analysis_id, "project_id": project_id},
        {"_id": 0}
    )
    
    if not analysis:
        return None
    
    for scenario in analysis.get("scenarios", []):
        if scenario["id"] == scenario_id:
            scenario.update(updates)
            break
    
    analysis["updated_at"] = now_iso()
    
    await db.multi_scenarios.update_one(
        {"id": analysis_id},
        {"$set": {"scenarios": analysis["scenarios"], "updated_at": analysis["updated_at"]}}
    )
    
    return analysis

async def select_scenario(
    project_id: str,
    analysis_id: str,
    scenario_type: str
) -> Dict:
    """Sélectionne un scénario comme recommandé"""
    now = now_iso()
    
    await db.multi_scenarios.update_one(
        {"id": analysis_id, "project_id": project_id},
        {"$set": {"recommended_scenario": scenario_type, "updated_at": now}}
    )
    
    return await db.multi_scenarios.find_one(
        {"id": analysis_id},
        {"_id": 0}
    )
