# /app/backend/services/project_analysis.py
# Services d'analyse projet: diagnostics IA, alertes, scénarios, arbitrages, faisabilité

import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso


async def generate_ai_diagnostic(project_id: str) -> Dict:
    """Génère un diagnostic IA complet du projet"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    diagnostic_id = generate_uuid()
    now = now_iso()
    
    surface = project.get("target_surface_m2", 0) or 0
    budget = project.get("target_budget", 0) or 0
    quality = project.get("quality_level", "standard")
    
    # Calcul du ratio cible
    target_ratio = budget / surface if surface > 0 else 0
    
    # Ratios de référence
    reference_ratios = {
        "economic": 1400,
        "standard": 1800,
        "premium": 2400,
        "luxury": 3200
    }
    ref_ratio = reference_ratios.get(quality, 1800)
    
    # Analyse des écarts
    gap_percent = ((target_ratio - ref_ratio) / ref_ratio * 100) if ref_ratio > 0 else 0
    
    # Score de santé
    health_score = 100
    issues = []
    recommendations = []
    
    # Vérifications
    if surface <= 0:
        health_score -= 20
        issues.append({
            "severity": "high",
            "category": "data",
            "message": "Surface non définie",
            "impact": "Impossible de calculer les ratios"
        })
    
    if budget <= 0:
        health_score -= 15
        issues.append({
            "severity": "medium",
            "category": "data",
            "message": "Budget non défini",
            "impact": "Analyse financière limitée"
        })
    
    if target_ratio > 0 and gap_percent > 20:
        health_score -= 25
        issues.append({
            "severity": "high",
            "category": "budget",
            "message": f"Budget supérieur de {gap_percent:.0f}% à la référence",
            "impact": "Risque de surévaluation"
        })
        recommendations.append({
            "priority": "high",
            "action": "Revoir les spécifications techniques",
            "expected_saving": f"{gap_percent/2:.0f}%"
        })
    elif target_ratio > 0 and gap_percent < -15:
        health_score -= 20
        issues.append({
            "severity": "medium",
            "category": "budget",
            "message": f"Budget inférieur de {abs(gap_percent):.0f}% à la référence",
            "impact": "Risque de sous-estimation"
        })
        recommendations.append({
            "priority": "high",
            "action": "Valider la faisabilité technique avec ce budget",
            "expected_saving": "N/A"
        })
    
    # Vérifier le planning
    if not project.get("start_date"):
        health_score -= 10
        issues.append({
            "severity": "low",
            "category": "planning",
            "message": "Date de démarrage non définie",
            "impact": "Planning non établi"
        })
    
    # Recommandations générales
    if health_score >= 80:
        recommendations.append({
            "priority": "low",
            "action": "Projet bien défini - Continuer vers l'estimation détaillée",
            "expected_saving": "N/A"
        })
    
    diagnostic = {
        "id": diagnostic_id,
        "project_id": project_id,
        "type": "ai_diagnostic",
        "health_score": max(0, min(100, health_score)),
        "status": "healthy" if health_score >= 70 else "warning" if health_score >= 50 else "critical",
        "analysis": {
            "surface_m2": surface,
            "budget": budget,
            "target_ratio": round(target_ratio, 2),
            "reference_ratio": ref_ratio,
            "gap_percent": round(gap_percent, 1),
            "quality_level": quality
        },
        "issues": issues,
        "recommendations": recommendations,
        "created_at": now
    }
    
    await db.diagnostics.insert_one(diagnostic)
    diagnostic.pop("_id", None)
    
    return diagnostic


async def get_project_alerts(project_id: str) -> List[Dict]:
    """Récupère les alertes d'un projet"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return []
    
    alerts = []
    now = now_iso()
    
    # Alerte budget
    budget = project.get("target_budget", 0) or 0
    surface = project.get("target_surface_m2", 0) or 0
    
    if budget > 0 and surface > 0:
        ratio = budget / surface
        if ratio > 2500:
            alerts.append({
                "id": generate_uuid(),
                "type": "budget",
                "severity": "warning",
                "title": "Ratio élevé",
                "message": f"Le ratio de {ratio:.0f} €/m² est supérieur aux références du marché",
                "created_at": now
            })
        elif ratio < 1200:
            alerts.append({
                "id": generate_uuid(),
                "type": "budget",
                "severity": "critical",
                "title": "Budget insuffisant",
                "message": f"Le ratio de {ratio:.0f} €/m² semble insuffisant pour ce type de projet",
                "created_at": now
            })
    
    # Alerte planning
    start_date = project.get("start_date")
    if start_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if start < datetime.now(timezone.utc):
                alerts.append({
                    "id": generate_uuid(),
                    "type": "planning",
                    "severity": "warning",
                    "title": "Date dépassée",
                    "message": "La date de démarrage prévue est dans le passé",
                    "created_at": now
                })
        except:
            pass
    
    # Alerte données manquantes
    if not project.get("client_name"):
        alerts.append({
            "id": generate_uuid(),
            "type": "data",
            "severity": "info",
            "title": "Client non renseigné",
            "message": "Le nom du client n'est pas défini",
            "created_at": now
        })
    
    return alerts


async def create_scenario(
    project_id: str,
    name: str,
    description: str,
    parameters: Dict
) -> Dict:
    """Crée un scénario pour un projet"""
    
    scenario_id = generate_uuid()
    now = now_iso()
    
    # Récupérer le projet de base
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    base_surface = project.get("target_surface_m2", 0) or 0
    base_budget = project.get("target_budget", 0) or 0
    
    # Appliquer les variations du scénario
    surface_variation = parameters.get("surface_variation", 0) / 100
    budget_variation = parameters.get("budget_variation", 0) / 100
    
    new_surface = base_surface * (1 + surface_variation)
    new_budget = base_budget * (1 + budget_variation)
    
    scenario = {
        "id": scenario_id,
        "project_id": project_id,
        "name": name,
        "description": description,
        "parameters": parameters,
        "results": {
            "base_surface": base_surface,
            "new_surface": round(new_surface, 2),
            "surface_delta": round(new_surface - base_surface, 2),
            "base_budget": base_budget,
            "new_budget": round(new_budget, 2),
            "budget_delta": round(new_budget - base_budget, 2),
            "base_ratio": round(base_budget / base_surface, 2) if base_surface > 0 else 0,
            "new_ratio": round(new_budget / new_surface, 2) if new_surface > 0 else 0
        },
        "created_at": now
    }
    
    await db.scenarios.insert_one(scenario)
    scenario.pop("_id", None)
    
    return scenario


async def get_scenarios(project_id: str) -> List[Dict]:
    """Récupère tous les scénarios d'un projet"""
    cursor = db.scenarios.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", -1)
    return await cursor.to_list(length=50)


async def generate_arbitrage_suggestions(project_id: str) -> Dict:
    """Génère des suggestions d'arbitrage pour optimiser le projet"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    arbitrage_id = generate_uuid()
    now = now_iso()
    
    surface = project.get("target_surface_m2", 0) or 0
    budget = project.get("target_budget", 0) or 0
    quality = project.get("quality_level", "standard")
    
    suggestions = []
    
    # Suggestion qualité
    if quality == "premium" or quality == "luxury":
        savings = budget * 0.15
        suggestions.append({
            "id": generate_uuid(),
            "category": "quality",
            "title": "Réduction du niveau de finition",
            "description": f"Passer de {quality} à standard permettrait d'économiser environ 15%",
            "estimated_savings": round(savings, 0),
            "impact": "medium",
            "feasibility": "high"
        })
    
    # Suggestion surface
    if surface > 2000:
        savings = budget * 0.08
        suggestions.append({
            "id": generate_uuid(),
            "category": "surface",
            "title": "Optimisation des circulations",
            "description": "Réduire les circulations de 10% permettrait d'optimiser le budget",
            "estimated_savings": round(savings, 0),
            "impact": "low",
            "feasibility": "high"
        })
    
    # Suggestion structure
    suggestions.append({
        "id": generate_uuid(),
        "category": "structure",
        "title": "Structure mixte bois-béton",
        "description": "Une structure mixte pourrait réduire les coûts de gros œuvre de 5%",
        "estimated_savings": round(budget * 0.05, 0),
        "impact": "medium",
        "feasibility": "medium"
    })
    
    # Suggestion lots techniques
    suggestions.append({
        "id": generate_uuid(),
        "category": "technical",
        "title": "Optimisation CVC",
        "description": "Un système CVC centralisé pourrait réduire les coûts de 8%",
        "estimated_savings": round(budget * 0.03, 0),
        "impact": "low",
        "feasibility": "high"
    })
    
    total_potential_savings = sum(s["estimated_savings"] for s in suggestions)
    
    result = {
        "id": arbitrage_id,
        "project_id": project_id,
        "type": "arbitrage_suggestions",
        "suggestions": suggestions,
        "total_potential_savings": round(total_potential_savings, 0),
        "savings_percentage": round(total_potential_savings / budget * 100, 1) if budget > 0 else 0,
        "created_at": now
    }
    
    await db.arbitrages.insert_one(result)
    result.pop("_id", None)
    
    return result


async def generate_feasibility_analysis(project_id: str) -> Dict:
    """Génère une analyse de faisabilité complète"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    feasibility_id = generate_uuid()
    now = now_iso()
    
    surface = project.get("target_surface_m2", 0) or 0
    budget = project.get("target_budget", 0) or 0
    quality = project.get("quality_level", "standard")
    building_type = project.get("project_usage", "housing")
    
    # Analyse technique
    technical_score = 85
    technical_issues = []
    
    if surface > 10000:
        technical_score -= 10
        technical_issues.append("Surface importante nécessitant une étude structurelle approfondie")
    
    # Analyse financière
    financial_score = 80
    ratio = budget / surface if surface > 0 else 0
    
    reference_ratios = {
        "housing": {"economic": 1400, "standard": 1800, "premium": 2400},
        "office": {"economic": 1200, "standard": 1600, "premium": 2200},
        "hotel": {"economic": 1800, "standard": 2500, "premium": 3500},
    }
    
    ref = reference_ratios.get(building_type, reference_ratios["housing"]).get(quality, 1800)
    
    if ratio > 0:
        if ratio < ref * 0.8:
            financial_score -= 25
        elif ratio < ref * 0.9:
            financial_score -= 15
        elif ratio > ref * 1.2:
            financial_score -= 10
    
    # Analyse planning
    planning_score = 75
    
    # Analyse réglementaire
    regulatory_score = 90
    
    # Score global
    overall_score = (technical_score + financial_score + planning_score + regulatory_score) / 4
    
    result = {
        "id": feasibility_id,
        "project_id": project_id,
        "type": "feasibility_analysis",
        "overall_score": round(overall_score, 0),
        "status": "feasible" if overall_score >= 70 else "conditional" if overall_score >= 50 else "not_feasible",
        "analyses": {
            "technical": {
                "score": technical_score,
                "status": "pass" if technical_score >= 70 else "warning",
                "issues": technical_issues
            },
            "financial": {
                "score": financial_score,
                "status": "pass" if financial_score >= 70 else "warning",
                "ratio": round(ratio, 0),
                "reference_ratio": ref,
                "gap_percent": round((ratio - ref) / ref * 100, 1) if ref > 0 else 0
            },
            "planning": {
                "score": planning_score,
                "status": "pass" if planning_score >= 70 else "warning",
            },
            "regulatory": {
                "score": regulatory_score,
                "status": "pass" if regulatory_score >= 70 else "warning",
            }
        },
        "recommendations": [
            "Valider les études techniques préliminaires",
            "Confirmer le budget avec une estimation détaillée",
            "Vérifier les contraintes PLU"
        ],
        "created_at": now
    }
    
    await db.feasibility_analyses.insert_one(result)
    result.pop("_id", None)
    
    return result
