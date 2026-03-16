# /app/backend/services/senior_economist.py
# Service pour le module Économiste Senior

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso, ECONOMIST_PHASES, REGIONAL_COEFFICIENTS, DEFAULT_COST_REFERENCES

async def get_macro_analysis(project_id: str) -> Optional[Dict]:
    """Récupère l'analyse macro-économique d'un projet"""
    return await db.senior_economist.find_one(
        {"project_id": project_id, "type": "macro_analysis"},
        {"_id": 0}
    )

async def create_macro_analysis(project_id: str, project_data: Dict) -> Dict:
    """Crée une analyse macro-économique pour un projet"""
    analysis_id = generate_uuid()
    now = now_iso()
    
    # Récupérer la région du projet
    location = project_data.get("location", "idf")
    region_data = REGIONAL_COEFFICIENTS.get(location, REGIONAL_COEFFICIENTS["idf"])
    
    # Calculer les indicateurs économiques
    building_type = project_data.get("project_usage", "housing")
    quality_level = project_data.get("quality_level", "standard")
    ref_cost = DEFAULT_COST_REFERENCES.get(building_type, DEFAULT_COST_REFERENCES["housing"]).get(quality_level, 1850)
    
    # Simuler les tendances du marché (données réalistes)
    analysis = {
        "id": analysis_id,
        "project_id": project_id,
        "type": "macro_analysis",
        "market_context": f"Marché de la construction en {region_data['label']} - Contexte actuel",
        "economic_indicators": {
            "inflation_rate": 4.2,
            "construction_price_index": 108.5,
            "material_index": 112.3,
            "labor_index": 106.8,
            "regional_coefficient": region_data["coefficient"],
            "reference_cost_m2": ref_cost * region_data["coefficient"]
        },
        "regional_factors": {
            "region": location,
            "region_name": region_data["label"],
            "coefficient": region_data["coefficient"],
            "market_tension": "modéré" if region_data["coefficient"] < 1.1 else "élevé",
            "labor_availability": "correcte" if region_data["coefficient"] < 1.1 else "tendue"
        },
        "inflation_forecast": 3.5,
        "material_price_trends": [
            {"material": "Béton", "variation_12m": 8.5, "trend": "hausse"},
            {"material": "Acier", "variation_12m": 12.3, "trend": "hausse"},
            {"material": "Bois", "variation_12m": -2.1, "trend": "stabilisation"},
            {"material": "Aluminium", "variation_12m": 5.4, "trend": "hausse modérée"},
            {"material": "Cuivre", "variation_12m": 15.2, "trend": "forte hausse"},
            {"material": "PVC", "variation_12m": 3.2, "trend": "stable"},
            {"material": "Isolation", "variation_12m": 6.8, "trend": "hausse"},
            {"material": "Verre", "variation_12m": 4.5, "trend": "hausse modérée"}
        ],
        "labor_cost_trends": [
            {"category": "Gros œuvre", "variation_12m": 4.2, "trend": "hausse"},
            {"category": "Second œuvre", "variation_12m": 3.8, "trend": "hausse modérée"},
            {"category": "Corps d'état techniques", "variation_12m": 5.5, "trend": "hausse"},
            {"category": "Finitions", "variation_12m": 3.2, "trend": "stable"}
        ],
        "recommendations": [
            "Anticiper les approvisionnements en acier et cuivre pour limiter l'impact des hausses",
            "Négocier des contrats cadres avec les fournisseurs de béton",
            f"Appliquer un coefficient régional de {region_data['coefficient']} pour {region_data['label']}",
            "Prévoir une provision pour aléas de 5-7% compte tenu du contexte inflationniste",
            "Optimiser les choix de matériaux en privilégiant le bois quand possible"
        ],
        "confidence_level": 0.85,
        "created_at": now,
        "updated_at": now
    }
    
    await db.senior_economist.insert_one(analysis)
    # Remove MongoDB _id before returning
    analysis.pop("_id", None)
    return analysis

async def get_risk_assessment(project_id: str) -> List[Dict]:
    """Récupère l'évaluation des risques d'un projet"""
    risks = await db.senior_economist.find(
        {"project_id": project_id, "type": "risk_assessment"},
        {"_id": 0}
    ).to_list(100)
    return risks

async def create_risk_assessment(project_id: str, project_data: Dict) -> List[Dict]:
    """Crée une évaluation des risques pour un projet"""
    now = now_iso()
    surface = project_data.get("target_surface_m2", 1000) or 1000
    budget = project_data.get("target_budget") or (surface * 1850)
    
    # Définir les risques standards par catégorie
    risk_templates = [
        {
            "risk_category": "technique",
            "description": "Découverte de sols pollués ou contraintes géotechniques imprévues",
            "probability": 0.25,
            "impact_level": "high",
            "mitigation_strategy": "Études géotechniques approfondies en phase APS, provisions spécifiques",
            "contingency_ratio": 0.02
        },
        {
            "risk_category": "technique",
            "description": "Modifications des exigences techniques en cours de projet (RE2020, accessibilité)",
            "probability": 0.35,
            "impact_level": "medium",
            "mitigation_strategy": "Veille réglementaire continue, marges de manœuvre dans les ratios",
            "contingency_ratio": 0.015
        },
        {
            "risk_category": "marché",
            "description": "Hausse des prix des matériaux supérieure aux prévisions",
            "probability": 0.45,
            "impact_level": "high",
            "mitigation_strategy": "Clauses de révision de prix, approvisionnements anticipés, alternatives",
            "contingency_ratio": 0.03
        },
        {
            "risk_category": "marché",
            "description": "Défaillance d'entreprises ou sous-traitants",
            "probability": 0.20,
            "impact_level": "medium",
            "mitigation_strategy": "Sélection rigoureuse, garanties financières, plan B pour lots critiques",
            "contingency_ratio": 0.01
        },
        {
            "risk_category": "planning",
            "description": "Retards dans l'obtention des autorisations administratives",
            "probability": 0.30,
            "impact_level": "medium",
            "mitigation_strategy": "Anticipation des démarches, dialogue avec les services instructeurs",
            "contingency_ratio": 0.01
        },
        {
            "risk_category": "planning",
            "description": "Intempéries et conditions climatiques défavorables",
            "probability": 0.40,
            "impact_level": "low",
            "mitigation_strategy": "Planning avec marges, protections de chantier, travaux intérieurs en parallèle",
            "contingency_ratio": 0.005
        },
        {
            "risk_category": "conception",
            "description": "Évolution des demandes du maître d'ouvrage en cours de projet",
            "probability": 0.50,
            "impact_level": "medium",
            "mitigation_strategy": "Validation formelle de chaque phase, avenants encadrés, réserves budgétaires",
            "contingency_ratio": 0.02
        },
        {
            "risk_category": "financier",
            "description": "Évolution défavorable des conditions de financement",
            "probability": 0.25,
            "impact_level": "medium",
            "mitigation_strategy": "Sécurisation précoce du financement, taux fixes si possible",
            "contingency_ratio": 0.01
        }
    ]
    
    risks = []
    for template in risk_templates:
        risk = {
            "id": generate_uuid(),
            "project_id": project_id,
            "type": "risk_assessment",
            "risk_category": template["risk_category"],
            "description": template["description"],
            "probability": template["probability"],
            "impact_level": template["impact_level"],
            "mitigation_strategy": template["mitigation_strategy"],
            "contingency_amount": round(budget * template["contingency_ratio"], 2),
            "responsible_person": None,
            "status": "identified",
            "created_at": now,
            "updated_at": now
        }
        risks.append(risk)
        await db.senior_economist.insert_one(risk)
        # Remove MongoDB _id after insert
        risk.pop("_id", None)
    
    return risks

async def get_cost_strategy(project_id: str) -> Optional[Dict]:
    """Récupère la stratégie de coûts d'un projet"""
    return await db.senior_economist.find_one(
        {"project_id": project_id, "type": "cost_strategy"},
        {"_id": 0}
    )

async def create_cost_strategy(project_id: str, project_data: Dict) -> Dict:
    """Crée une stratégie de coûts pour un projet"""
    strategy_id = generate_uuid()
    now = now_iso()
    
    surface = project_data.get("target_surface_m2", 1000) or 1000
    quality = project_data.get("quality_level", "standard") or "standard"
    budget = project_data.get("target_budget") or (surface * 1850)
    
    # Définir les leviers d'optimisation selon le niveau de qualité
    optimization_targets = {
        "economic": 0.05,
        "standard": 0.08,
        "premium": 0.10,
        "luxury": 0.12
    }
    
    target_savings = budget * optimization_targets.get(quality, 0.08)
    
    strategy = {
        "id": strategy_id,
        "project_id": project_id,
        "type": "cost_strategy",
        "strategy_name": f"Stratégie d'optimisation économique - {project_data.get('project_name', 'Projet')}",
        "target_savings": round(target_savings, 2),
        "target_savings_pct": optimization_targets.get(quality, 0.08) * 100,
        "implementation_phases": [
            {
                "phase": "Phase 1 - Conception",
                "actions": ["Optimisation des ratios de surfaces", "Simplification structurelle", "Standardisation des éléments"],
                "potential_savings": round(target_savings * 0.40, 2),
                "timeline": "M1-M3"
            },
            {
                "phase": "Phase 2 - Consultation",
                "actions": ["Allotissement optimisé", "Négociation groupée", "Variantes techniques"],
                "potential_savings": round(target_savings * 0.35, 2),
                "timeline": "M4-M6"
            },
            {
                "phase": "Phase 3 - Exécution",
                "actions": ["Suivi strict des modifications", "Optimisation des approvisionnements", "Réduction des reprises"],
                "potential_savings": round(target_savings * 0.25, 2),
                "timeline": "M7-M24"
            }
        ],
        "key_levers": [
            {"lever": "Ratio SU/SDP", "current": "80%", "target": "82%", "impact": "Réduction des circulations"},
            {"lever": "Standardisation façade", "current": "12 types", "target": "6 types", "impact": "Économie de 3-5% sur le lot"},
            {"lever": "Rationalisation CVC", "current": "Solutions individuelles", "target": "Système centralisé", "impact": "Économie de 8-12%"},
            {"lever": "Préfabrication", "current": "5%", "target": "25%", "impact": "Gain de temps et qualité"},
            {"lever": "Groupement de lots", "current": "20 lots", "target": "12 macrolots", "impact": "Réduction des interfaces"}
        ],
        "monitoring_indicators": [
            {"indicator": "Coût au m² SDP", "target": round(budget / surface, 2), "unit": "€/m²"},
            {"indicator": "Taux de modifications", "target": 5, "unit": "%"},
            {"indicator": "Écart budget/réalisé", "target": 0, "unit": "%"},
            {"indicator": "Taux de litiges", "target": 2, "unit": "%"},
            {"indicator": "Respect du planning", "target": 95, "unit": "%"}
        ],
        "status": "active",
        "created_at": now,
        "updated_at": now
    }
    
    await db.senior_economist.insert_one(strategy)
    # Remove MongoDB _id before returning
    strategy.pop("_id", None)
    return strategy

async def get_project_phasing(project_id: str) -> List[Dict]:
    """Récupère le phasage d'un projet"""
    phases = await db.senior_economist.find(
        {"project_id": project_id, "type": "project_phase"},
        {"_id": 0}
    ).to_list(20)
    return sorted(phases, key=lambda x: x.get("phase_number", 0))

async def create_project_phasing(project_id: str, project_data: Dict) -> List[Dict]:
    """Crée le phasage d'un projet"""
    now = now_iso()
    surface = project_data.get("target_surface_m2", 1000) or 1000
    budget = project_data.get("target_budget") or (surface * 1850)
    
    # Définir les phases standards d'un projet de construction
    phase_templates = [
        {"name": "Études préliminaires", "number": 1, "duration_months": 2, "budget_ratio": 0.02, "deliverables": ["Programme", "Faisabilité", "Budget préliminaire"]},
        {"name": "APS - Avant-Projet Sommaire", "number": 2, "duration_months": 2, "budget_ratio": 0.03, "deliverables": ["Plans APS", "Estimatif APS", "Notice descriptive"]},
        {"name": "APD - Avant-Projet Définitif", "number": 3, "duration_months": 3, "budget_ratio": 0.04, "deliverables": ["Plans APD", "CCTP", "Estimatif APD", "PC"]},
        {"name": "PRO - Projet", "number": 4, "duration_months": 3, "budget_ratio": 0.05, "deliverables": ["DCE", "Plans d'exécution", "Budget définitif"]},
        {"name": "ACT - Consultation", "number": 5, "duration_months": 2, "budget_ratio": 0.02, "deliverables": ["Analyse des offres", "Marchés", "Planning travaux"]},
        {"name": "Travaux - Gros œuvre", "number": 6, "duration_months": 8, "budget_ratio": 0.35, "deliverables": ["Fondations", "Structure", "Clos-couvert"]},
        {"name": "Travaux - Second œuvre", "number": 7, "duration_months": 6, "budget_ratio": 0.30, "deliverables": ["Cloisonnement", "Revêtements", "Menuiseries"]},
        {"name": "Travaux - Lots techniques", "number": 8, "duration_months": 6, "budget_ratio": 0.15, "deliverables": ["CVC", "Électricité", "Plomberie"]},
        {"name": "Réception et livraison", "number": 9, "duration_months": 1, "budget_ratio": 0.02, "deliverables": ["OPR", "Levée de réserves", "DOE", "Réception"]}
    ]
    
    phases = []
    cumulative_months = 0
    
    for template in phase_templates:
        phase = {
            "id": generate_uuid(),
            "project_id": project_id,
            "type": "project_phase",
            "phase_name": template["name"],
            "phase_number": template["number"],
            "start_month": cumulative_months,
            "duration_months": template["duration_months"],
            "end_month": cumulative_months + template["duration_months"],
            "budget_allocation": round(budget * template["budget_ratio"], 2),
            "budget_ratio": template["budget_ratio"],
            "deliverables": template["deliverables"],
            "milestones": [],
            "dependencies": [template["number"] - 1] if template["number"] > 1 else [],
            "status": "planned",
            "progress": 0,
            "created_at": now,
            "updated_at": now
        }
        phases.append(phase)
        await db.senior_economist.insert_one(phase)
        # Remove MongoDB _id after insert
        phase.pop("_id", None)
        cumulative_months += template["duration_months"]
    
    return phases

async def get_economist_workflow(project_id: str) -> Optional[Dict]:
    """Récupère le workflow de l'économiste pour un projet"""
    return await db.senior_economist.find_one(
        {"project_id": project_id, "type": "economist_workflow"},
        {"_id": 0}
    )

async def create_economist_workflow(project_id: str) -> Dict:
    """Crée le workflow de l'économiste senior"""
    workflow_id = generate_uuid()
    now = now_iso()
    
    # Créer la timeline avec les phases de l'économiste
    timeline = []
    for phase_key, phase_info in ECONOMIST_PHASES.items():
        timeline.append({
            "phase": phase_key,
            "name": phase_info["name"],
            "description": phase_info["description"],
            "deliverables": phase_info["deliverables"],
            "order": phase_info["order"],
            "status": "pending",
            "progress": 0
        })
    
    workflow = {
        "id": workflow_id,
        "project_id": project_id,
        "type": "economist_workflow",
        "current_phase": "macro_analysis",
        "completed_phases": [],
        "pending_validations": [],
        "action_items": [
            {"id": generate_uuid(), "action": "Analyser le contexte macro-économique", "due": "Semaine 1", "status": "pending", "priority": "high"},
            {"id": generate_uuid(), "action": "Identifier les risques majeurs", "due": "Semaine 2", "status": "pending", "priority": "high"},
            {"id": generate_uuid(), "action": "Définir la stratégie de coûts", "due": "Semaine 3", "status": "pending", "priority": "medium"},
            {"id": generate_uuid(), "action": "Établir le phasage budgétaire", "due": "Semaine 4", "status": "pending", "priority": "medium"},
            {"id": generate_uuid(), "action": "Constituer l'équipe projet", "due": "Semaine 4", "status": "pending", "priority": "low"}
        ],
        "timeline": timeline,
        "last_update": now,
        "created_at": now
    }
    
    await db.senior_economist.insert_one(workflow)
    # Remove MongoDB _id before returning
    workflow.pop("_id", None)
    return workflow

async def update_workflow_phase(project_id: str, phase: str, status: str) -> Dict:
    """Met à jour le statut d'une phase du workflow"""
    now = now_iso()
    
    workflow = await db.senior_economist.find_one(
        {"project_id": project_id, "type": "economist_workflow"},
        {"_id": 0}
    )
    
    if not workflow:
        return None
    
    # Mettre à jour la timeline
    for item in workflow["timeline"]:
        if item["phase"] == phase:
            item["status"] = status
            if status == "completed":
                item["progress"] = 100
                if phase not in workflow["completed_phases"]:
                    workflow["completed_phases"].append(phase)
            break
    
    # Déterminer la phase suivante
    phase_order = ECONOMIST_PHASES[phase]["order"]
    next_phase = None
    for p_key, p_info in ECONOMIST_PHASES.items():
        if p_info["order"] == phase_order + 1:
            next_phase = p_key
            break
    
    if next_phase and status == "completed":
        workflow["current_phase"] = next_phase
    
    workflow["last_update"] = now
    
    await db.senior_economist.update_one(
        {"project_id": project_id, "type": "economist_workflow"},
        {"$set": workflow}
    )
    
    return workflow

async def get_team_structure(project_id: str) -> Optional[Dict]:
    """Récupère la structure d'équipe du projet"""
    return await db.senior_economist.find_one(
        {"project_id": project_id, "type": "team_structure"},
        {"_id": 0}
    )

async def create_team_structure(project_id: str, project_data: Dict) -> Dict:
    """Crée la structure d'équipe pour un projet"""
    team_id = generate_uuid()
    now = now_iso()
    
    team = {
        "id": team_id,
        "project_id": project_id,
        "type": "team_structure",
        "roles": [
            {"role": "Directeur de projet", "responsibility": "Pilotage global, décisions stratégiques", "allocation": 0.2},
            {"role": "Économiste senior", "responsibility": "Maîtrise des coûts, arbitrages", "allocation": 0.5},
            {"role": "Économiste junior", "responsibility": "Métrés, consultation, suivi", "allocation": 1.0},
            {"role": "Architecte", "responsibility": "Conception, coordination technique", "allocation": 0.3},
            {"role": "BET Structure", "responsibility": "Études structure, dimensionnement", "allocation": 0.2},
            {"role": "BET Fluides", "responsibility": "CVC, plomberie, électricité", "allocation": 0.2},
            {"role": "OPC", "responsibility": "Ordonnancement, pilotage chantier", "allocation": 0.3}
        ],
        "raci_matrix": {
            "Budget global": {"Économiste senior": "R", "Directeur": "A", "Architecte": "C"},
            "Estimatif lots": {"Économiste junior": "R", "Économiste senior": "A", "BET": "C"},
            "Arbitrages": {"Économiste senior": "R", "Directeur": "A", "Architecte": "C", "Client": "I"},
            "Planning": {"OPC": "R", "Directeur": "A", "Économiste senior": "C"},
            "Consultation": {"Économiste junior": "R", "Économiste senior": "A"},
            "Suivi travaux": {"OPC": "R", "Économiste senior": "A", "Économiste junior": "C"}
        },
        "communication_plan": [
            {"meeting": "Comité de pilotage", "frequency": "Mensuel", "participants": ["Directeur", "Économiste senior", "Architecte", "Client"]},
            {"meeting": "Réunion technique", "frequency": "Hebdomadaire", "participants": ["Économiste senior", "Architecte", "BET"]},
            {"meeting": "Point budget", "frequency": "Bi-mensuel", "participants": ["Économiste senior", "Économiste junior"]},
            {"meeting": "Réunion de chantier", "frequency": "Hebdomadaire", "participants": ["OPC", "Économiste junior", "Entreprises"]}
        ],
        "created_at": now,
        "updated_at": now
    }
    
    await db.senior_economist.insert_one(team)
    # Remove MongoDB _id before returning
    team.pop("_id", None)
    return team

async def get_final_validation(project_id: str) -> Optional[Dict]:
    """Récupère la validation finale d'un projet"""
    return await db.senior_economist.find_one(
        {"project_id": project_id, "type": "final_validation"},
        {"_id": 0}
    )

async def create_final_validation(project_id: str, project_data: Dict, analyses: Dict) -> Dict:
    """Crée la validation finale économique"""
    validation_id = generate_uuid()
    now = now_iso()
    
    surface = project_data.get("target_surface_m2", 1000) or 1000
    budget = project_data.get("target_budget") or (surface * 1850)
    
    validation = {
        "id": validation_id,
        "project_id": project_id,
        "type": "final_validation",
        "summary": {
            "project_name": project_data.get("project_name", "Projet"),
            "surface_m2": surface,
            "initial_budget": budget,
            "validated_budget": budget,
            "cost_per_m2": round(budget / surface, 2),
            "confidence_level": "high"
        },
        "checklist": [
            {"item": "Analyse macro-économique réalisée", "status": "completed" if analyses.get("macro") else "pending"},
            {"item": "Risques identifiés et provisionnés", "status": "completed" if analyses.get("risks") else "pending"},
            {"item": "Stratégie de coûts définie", "status": "completed" if analyses.get("strategy") else "pending"},
            {"item": "Phasage budgétaire validé", "status": "completed" if analyses.get("phasing") else "pending"},
            {"item": "Équipe projet constituée", "status": "completed" if analyses.get("team") else "pending"},
            {"item": "Budget approuvé par le client", "status": "pending"},
            {"item": "Documentation archivée", "status": "pending"}
        ],
        "recommendations": [
            "Maintenir une veille active sur les prix des matériaux stratégiques",
            "Réviser le budget tous les trimestres avec les indices de coût",
            "Prévoir des réunions d'arbitrage régulières avec la maîtrise d'ouvrage",
            "Documenter toutes les décisions impactant le budget"
        ],
        "validation_status": "draft",
        "validated_by": None,
        "validation_date": None,
        "created_at": now,
        "updated_at": now
    }
    
    await db.senior_economist.insert_one(validation)
    # Remove MongoDB _id before returning
    validation.pop("_id", None)
    return validation
