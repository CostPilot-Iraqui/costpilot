# /app/backend/services/cost_prediction.py
# Service de prédiction de coûts IA

from typing import List, Dict, Any, Optional
import sys
sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso, DEFAULT_COST_REFERENCES, REGIONAL_COEFFICIENTS

async def predict_project_cost(
    project_id: str,
    project_data: Dict
) -> Dict:
    """Prédit le coût d'un projet basé sur ses caractéristiques"""
    prediction_id = generate_uuid()
    now = now_iso()
    
    # Extraire les caractéristiques du projet
    building_type = project_data.get("project_usage", "housing") or "housing"
    surface = project_data.get("target_surface_m2", 1000) or 1000
    location = project_data.get("location", "idf") or "idf"
    quality_level = project_data.get("quality_level", "standard") or "standard"
    complexity = project_data.get("complexity_level", "medium") or "medium"
    sustainability = project_data.get("sustainability_target", "none") or "none"
    basement = project_data.get("basement_presence", "none") or "none"
    parking = project_data.get("parking_requirement", "none") or "none"
    facade_ambition = project_data.get("facade_ambition", "moderate") or "moderate"
    technical_ambition = project_data.get("technical_ambition", "standard") or "standard"
    
    # Récupérer le coût de base
    base_cost = DEFAULT_COST_REFERENCES.get(building_type, DEFAULT_COST_REFERENCES["housing"]).get(quality_level, 1850)
    
    # Appliquer les coefficients
    regional_coef = REGIONAL_COEFFICIENTS.get(location, {"coefficient": 1.0})["coefficient"]
    
    # Coefficient de complexité
    complexity_coefs = {"simple": 0.90, "medium": 1.0, "complex": 1.15, "very_complex": 1.30}
    complexity_coef = complexity_coefs.get(complexity, 1.0)
    
    # Coefficient durabilité
    sustainability_coefs = {"none": 1.0, "standard": 1.03, "hqe_breeam_leed": 1.08, "high_performance": 1.15}
    sustainability_coef = sustainability_coefs.get(sustainability, 1.0)
    
    # Coefficient sous-sol
    basement_coefs = {"none": 1.0, "partial": 1.05, "full": 1.12}
    basement_coef = basement_coefs.get(basement, 1.0)
    
    # Coefficient parking
    parking_coefs = {"none": 1.0, "external": 1.02, "underground": 1.10}
    parking_coef = parking_coefs.get(parking, 1.0)
    
    # Coefficient façade
    facade_coefs = {"simple": 0.95, "moderate": 1.0, "premium": 1.10, "iconic": 1.25}
    facade_coef = facade_coefs.get(facade_ambition, 1.0)
    
    # Coefficient technique
    technical_coefs = {"low": 0.95, "standard": 1.0, "high": 1.12}
    technical_coef = technical_coefs.get(technical_ambition, 1.0)
    
    # Calcul du coût prédit
    combined_coef = (regional_coef * complexity_coef * sustainability_coef * 
                     basement_coef * parking_coef * facade_coef * technical_coef)
    
    predicted_avg = base_cost * combined_coef
    predicted_min = predicted_avg * 0.90  # -10%
    predicted_max = predicted_avg * 1.12  # +12%
    
    # Intervalle de confiance basé sur les données disponibles
    confidence = 0.75  # Base
    if building_type in ["housing", "office"]:
        confidence += 0.10  # Plus de données disponibles
    if quality_level == "standard":
        confidence += 0.05  # Niveau le plus documenté
    
    # Facteurs contributifs
    contributing_factors = [
        {"factor": "Localisation", "value": location, "coefficient": regional_coef, "impact": round((regional_coef - 1) * 100, 1)},
        {"factor": "Complexité", "value": complexity, "coefficient": complexity_coef, "impact": round((complexity_coef - 1) * 100, 1)},
        {"factor": "Durabilité", "value": sustainability, "coefficient": sustainability_coef, "impact": round((sustainability_coef - 1) * 100, 1)},
        {"factor": "Sous-sol", "value": basement, "coefficient": basement_coef, "impact": round((basement_coef - 1) * 100, 1)},
        {"factor": "Stationnement", "value": parking, "coefficient": parking_coef, "impact": round((parking_coef - 1) * 100, 1)},
        {"factor": "Ambition façade", "value": facade_ambition, "coefficient": facade_coef, "impact": round((facade_coef - 1) * 100, 1)},
        {"factor": "Ambition technique", "value": technical_ambition, "coefficient": technical_coef, "impact": round((technical_coef - 1) * 100, 1)}
    ]
    
    # Trier par impact
    contributing_factors.sort(key=lambda x: abs(x["impact"]), reverse=True)
    
    prediction = {
        "id": prediction_id,
        "type": "cost_prediction",
        "project_id": project_id,
        "input_parameters": {
            "building_type": building_type,
            "surface_m2": surface,
            "location": location,
            "quality_level": quality_level,
            "complexity": complexity,
            "sustainability": sustainability
        },
        "predicted_cost_min": round(predicted_min * surface, 2),
        "predicted_cost_avg": round(predicted_avg * surface, 2),
        "predicted_cost_max": round(predicted_max * surface, 2),
        "predicted_cost_m2_min": round(predicted_min, 2),
        "predicted_cost_m2_avg": round(predicted_avg, 2),
        "predicted_cost_m2_max": round(predicted_max, 2),
        "base_cost_m2": base_cost,
        "combined_coefficient": round(combined_coef, 3),
        "confidence_interval": round(confidence, 2),
        "contributing_factors": contributing_factors,
        "model_version": "1.0.0",
        "methodology": "Modèle paramétrique basé sur ratios de référence et coefficients d'ajustement",
        "similar_projects": [],  # À enrichir avec les benchmarks
        "recommendations": generate_cost_recommendations(contributing_factors, predicted_avg, base_cost),
        "created_at": now
    }
    
    await db.cost_predictions.insert_one(prediction)
    # Remove MongoDB _id before returning
    prediction.pop("_id", None)
    return prediction

def generate_cost_recommendations(factors: List[Dict], predicted: float, base: float) -> List[str]:
    """Génère des recommandations basées sur la prédiction"""
    recommendations = []
    
    # Analyser les facteurs d'impact majeur
    high_impact_factors = [f for f in factors if abs(f["impact"]) > 5]
    
    for factor in high_impact_factors:
        if factor["impact"] > 10:
            recommendations.append(f"Le facteur '{factor['factor']}' ({factor['value']}) augmente significativement le coût de +{factor['impact']}%. Évaluer les alternatives.")
        elif factor["impact"] < -5:
            recommendations.append(f"Le facteur '{factor['factor']}' ({factor['value']}) permet une économie de {abs(factor['impact'])}%.")
    
    # Recommandations générales
    variance = (predicted - base) / base * 100
    if variance > 20:
        recommendations.append("Le projet présente un surcoût important par rapport à la référence. Une revue des hypothèses est recommandée.")
    elif variance > 10:
        recommendations.append("Projet légèrement au-dessus des moyennes. Identifier les leviers d'optimisation prioritaires.")
    elif variance < -5:
        recommendations.append("Budget optimiste. Vérifier la cohérence des hypothèses avec le programme.")
    
    return recommendations

async def get_cost_predictions(project_id: str) -> List[Dict]:
    """Récupère l'historique des prédictions de coût pour un projet"""
    predictions = await db.cost_predictions.find(
        {"project_id": project_id},
        {"_id": 0}
    ).to_list(50)
    return sorted(predictions, key=lambda x: x.get("created_at", ""), reverse=True)

async def get_latest_prediction(project_id: str) -> Optional[Dict]:
    """Récupère la dernière prédiction de coût"""
    return await db.cost_predictions.find_one(
        {"project_id": project_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
