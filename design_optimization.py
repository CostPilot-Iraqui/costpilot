# /app/backend/services/design_optimization.py
# Service d'optimisation de conception IA

from typing import List, Dict, Any, Optional
import sys
sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso

async def analyze_design_optimization(
    project_id: str,
    project_data: Dict,
    dpgf_data: Optional[Dict] = None
) -> Dict:
    """Analyse et suggère des optimisations de conception"""
    analysis_id = generate_uuid()
    now = now_iso()
    
    surface = project_data.get("target_surface_m2", 1000) or 1000
    budget = project_data.get("target_budget") or (surface * 1850)
    building_type = project_data.get("project_usage", "housing") or "housing"
    quality_level = project_data.get("quality_level", "standard") or "standard"
    
    # Générer des suggestions d'optimisation
    suggestions = []
    
    # 1. Optimisation de la circulation
    suggestions.append({
        "id": generate_uuid(),
        "category": "circulation",
        "title": "Optimisation du ratio de circulation",
        "description": "Réduction de la surface de circulation de 15% à 12% de la SDP par une conception plus compacte des noyaux de distribution.",
        "current_cost": round(budget * 0.15 * 0.20, 2),
        "optimized_cost": round(budget * 0.12 * 0.20, 2),
        "savings_potential": round(budget * 0.03 * 0.20, 2),
        "savings_percentage": 3.0,
        "implementation_complexity": "medium",
        "impact_on_quality": "low",
        "impact_on_timeline": "none",
        "architectural_implications": [
            "Réduction de la largeur des couloirs de 1.50m à 1.40m",
            "Optimisation de la position des escaliers et ascenseurs",
            "Regroupement des gaines techniques"
        ],
        "technical_requirements": [
            "Vérification des normes PMR",
            "Validation par le bureau de contrôle",
            "Mise à jour des plans APD"
        ],
        "priority": 1,
        "status": "proposed"
    })
    
    # 2. Optimisation structurelle
    suggestions.append({
        "id": generate_uuid(),
        "category": "structure",
        "title": "Rationalisation de la trame structurelle",
        "description": "Adoption d'une trame régulière 7.20m x 7.20m permettant de réduire le nombre de poteaux et d'optimiser les retombées de poutres.",
        "current_cost": round(budget * 0.22, 2),
        "optimized_cost": round(budget * 0.20, 2),
        "savings_potential": round(budget * 0.02, 2),
        "savings_percentage": 2.0,
        "implementation_complexity": "high",
        "impact_on_quality": "none",
        "impact_on_timeline": "low",
        "architectural_implications": [
            "Adaptation du plan masse à la nouvelle trame",
            "Révision des cloisons distributives",
            "Impact possible sur les dimensions des locaux"
        ],
        "technical_requirements": [
            "Étude structure complète",
            "Validation par le BET structure",
            "Mise à jour des descentes de charges"
        ],
        "priority": 2,
        "status": "proposed"
    })
    
    # 3. Optimisation de façade
    suggestions.append({
        "id": generate_uuid(),
        "category": "facade",
        "title": "Standardisation du système de façade",
        "description": "Réduction du nombre de types de modules de façade de 12 à 6 types standards, avec harmonisation des teintes et des dimensions.",
        "current_cost": round(budget * 0.10, 2),
        "optimized_cost": round(budget * 0.085, 2),
        "savings_potential": round(budget * 0.015, 2),
        "savings_percentage": 1.5,
        "implementation_complexity": "medium",
        "impact_on_quality": "low",
        "impact_on_timeline": "none",
        "architectural_implications": [
            "Simplification du calepinage façade",
            "Harmonisation visuelle de l'ensemble",
            "Réduction des angles et points singuliers"
        ],
        "technical_requirements": [
            "Étude thermique de validation",
            "Prototypes de validation esthétique",
            "Mise à jour des carnets de détails"
        ],
        "priority": 2,
        "status": "proposed"
    })
    
    # 4. Optimisation des menuiseries
    suggestions.append({
        "id": generate_uuid(),
        "category": "menuiseries",
        "title": "Rationalisation des menuiseries extérieures",
        "description": "Passage de 18 références à 8 références standard avec châssis aluminium à rupture de pont thermique.",
        "current_cost": round(budget * 0.06, 2),
        "optimized_cost": round(budget * 0.052, 2),
        "savings_potential": round(budget * 0.008, 2),
        "savings_percentage": 0.8,
        "implementation_complexity": "low",
        "impact_on_quality": "none",
        "impact_on_timeline": "none",
        "architectural_implications": [
            "Dimensions standard des baies",
            "Simplification des détails d'étanchéité",
            "Homogénéité de l'aspect des menuiseries"
        ],
        "technical_requirements": [
            "Validation des performances thermiques",
            "Échantillons de validation",
            "Mise à jour du CCTP menuiseries"
        ],
        "priority": 3,
        "status": "proposed"
    })
    
    # 5. Optimisation CVC
    suggestions.append({
        "id": generate_uuid(),
        "category": "technique",
        "title": "Optimisation du système de chauffage/climatisation",
        "description": "Passage d'un système VRV multi-zones à une solution PAC air/eau centralisée avec plancher chauffant/rafraîchissant.",
        "current_cost": round(budget * 0.10, 2),
        "optimized_cost": round(budget * 0.085, 2),
        "savings_potential": round(budget * 0.015, 2),
        "savings_percentage": 1.5,
        "implementation_complexity": "high",
        "impact_on_quality": "positive",
        "impact_on_timeline": "medium",
        "architectural_implications": [
            "Intégration de la chaufferie en sous-sol ou toiture",
            "Réservations pour les réseaux hydrauliques",
            "Suppression des unités intérieures visibles"
        ],
        "technical_requirements": [
            "Étude thermique réglementaire",
            "Dimensionnement par BET fluides",
            "Vérification des contraintes acoustiques"
        ],
        "priority": 2,
        "status": "proposed"
    })
    
    # 6. Préfabrication
    if building_type in ["housing", "hotel", "office"]:
        suggestions.append({
            "id": generate_uuid(),
            "category": "process",
            "title": "Introduction de la préfabrication",
            "description": "Utilisation de modules préfabriqués pour les salles de bains (30%) permettant de réduire les délais et d'améliorer la qualité.",
            "current_cost": round(budget * 0.06, 2),
            "optimized_cost": round(budget * 0.055, 2),
            "savings_potential": round(budget * 0.005, 2),
            "savings_percentage": 0.5,
            "implementation_complexity": "high",
            "impact_on_quality": "positive",
            "impact_on_timeline": "positive",
            "architectural_implications": [
                "Standardisation des dimensions de salles de bains",
                "Coordination avec la structure pour la pose",
                "Points de raccordement standardisés"
            ],
            "technical_requirements": [
                "Sélection des fournisseurs de modules",
                "Études de raccordement",
                "Planning de livraison adapté"
            ],
            "priority": 4,
            "status": "proposed"
        })
    
    # 7. Optimisation électrique
    suggestions.append({
        "id": generate_uuid(),
        "category": "technique",
        "title": "Rationalisation du réseau électrique",
        "description": "Optimisation du nombre de points lumineux par zone et regroupement des tableaux divisionnaires.",
        "current_cost": round(budget * 0.07, 2),
        "optimized_cost": round(budget * 0.063, 2),
        "savings_potential": round(budget * 0.007, 2),
        "savings_percentage": 0.7,
        "implementation_complexity": "low",
        "impact_on_quality": "none",
        "impact_on_timeline": "none",
        "architectural_implications": [
            "Révision du plan lumière",
            "Implantation optimisée des tableaux",
            "Parcours de câbles simplifiés"
        ],
        "technical_requirements": [
            "Étude d'éclairement",
            "Validation des niveaux d'éclairage réglementaires",
            "Mise à jour des plans électriques"
        ],
        "priority": 3,
        "status": "proposed"
    })
    
    # Calculer les totaux
    total_savings = sum(s["savings_potential"] for s in suggestions)
    total_savings_pct = (total_savings / budget * 100) if budget > 0 else 0
    
    analysis = {
        "id": analysis_id,
        "type": "design_optimization",
        "project_id": project_id,
        "analysis_date": now,
        "current_budget": budget,
        "optimized_budget": round(budget - total_savings, 2),
        "total_potential_savings": round(total_savings, 2),
        "total_savings_percentage": round(total_savings_pct, 1),
        "suggestions_count": len(suggestions),
        "suggestions": suggestions,
        "by_category": {
            "circulation": len([s for s in suggestions if s["category"] == "circulation"]),
            "structure": len([s for s in suggestions if s["category"] == "structure"]),
            "facade": len([s for s in suggestions if s["category"] == "facade"]),
            "menuiseries": len([s for s in suggestions if s["category"] == "menuiseries"]),
            "technique": len([s for s in suggestions if s["category"] == "technique"]),
            "process": len([s for s in suggestions if s["category"] == "process"])
        },
        "by_complexity": {
            "low": len([s for s in suggestions if s["implementation_complexity"] == "low"]),
            "medium": len([s for s in suggestions if s["implementation_complexity"] == "medium"]),
            "high": len([s for s in suggestions if s["implementation_complexity"] == "high"])
        },
        "implementation_roadmap": [
            {"phase": "Court terme (0-2 mois)", "actions": ["Standardisation menuiseries", "Optimisation électrique"], "savings": round(budget * 0.015, 2)},
            {"phase": "Moyen terme (2-4 mois)", "actions": ["Optimisation circulation", "Standardisation façade"], "savings": round(budget * 0.045, 2)},
            {"phase": "Long terme (4-6 mois)", "actions": ["Rationalisation structure", "Optimisation CVC", "Préfabrication"], "savings": round(budget * 0.04, 2)}
        ],
        "created_at": now
    }
    
    await db.design_optimizations.insert_one(analysis)
    # Remove MongoDB _id before returning
    analysis.pop("_id", None)
    return analysis

async def get_design_optimizations(project_id: str) -> List[Dict]:
    """Récupère les analyses d'optimisation de conception"""
    analyses = await db.design_optimizations.find(
        {"project_id": project_id},
        {"_id": 0}
    ).to_list(50)
    return sorted(analyses, key=lambda x: x.get("created_at", ""), reverse=True)

async def update_suggestion_status(
    project_id: str,
    analysis_id: str,
    suggestion_id: str,
    new_status: str
) -> Dict:
    """Met à jour le statut d'une suggestion d'optimisation"""
    analysis = await db.design_optimizations.find_one(
        {"id": analysis_id, "project_id": project_id},
        {"_id": 0}
    )
    
    if not analysis:
        return None
    
    for suggestion in analysis.get("suggestions", []):
        if suggestion["id"] == suggestion_id:
            suggestion["status"] = new_status
            break
    
    await db.design_optimizations.update_one(
        {"id": analysis_id},
        {"$set": {"suggestions": analysis["suggestions"]}}
    )
    
    return analysis
