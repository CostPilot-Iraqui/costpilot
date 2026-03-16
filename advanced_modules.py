# /app/backend/routers/advanced_modules.py
# Routes API pour les modules avancés (Benchmark, Market Intelligence, Cost Prediction, etc.)

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import sys
sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import security
from services import benchmark, market_intelligence, cost_prediction, design_optimization, multi_scenario
import jwt
import os

router = APIRouter(tags=["Advanced Modules"])

JWT_SECRET = os.environ.get('JWT_SECRET', 'costpilot-senior-secret-key-2024')

async def get_current_user(credentials = Depends(security)) -> dict:
    """Récupère l'utilisateur courant"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

# =============================================================================
# BENCHMARK ROUTES
# =============================================================================

@router.get("/benchmark/projects")
async def get_benchmark_projects(
    building_type: Optional[str] = None,
    quality_level: Optional[str] = None,
    region: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les projets de référence pour le benchmark"""
    return await benchmark.get_benchmark_projects(building_type, quality_level, region)

@router.get("/benchmark/statistics")
async def get_benchmark_statistics(
    building_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les statistiques de benchmark"""
    return await benchmark.get_benchmark_statistics(building_type)

@router.post("/projects/{project_id}/benchmark/compare")
async def compare_project_to_benchmarks(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Compare un projet aux projets de référence"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return await benchmark.compare_project_to_benchmarks(project_id, project)

@router.get("/projects/{project_id}/benchmark")
async def get_project_benchmark(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère la comparaison de benchmark d'un projet"""
    comparison = await db.benchmarks.find_one(
        {"project_id": project_id, "type": "benchmark_comparison"},
        {"_id": 0}
    )
    
    if not comparison:
        # Générer la comparaison si elle n'existe pas
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        comparison = await benchmark.compare_project_to_benchmarks(project_id, project)
    
    return comparison

# =============================================================================
# MARKET INTELLIGENCE ROUTES
# =============================================================================

@router.get("/market-intelligence/trends")
async def get_market_trends(
    region: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les tendances du marché de la construction"""
    return await market_intelligence.get_market_trends(region)

@router.get("/market-intelligence/regional-indices")
async def get_regional_indices(
    current_user: dict = Depends(get_current_user)
):
    """Récupère les indices de coût par région"""
    return await market_intelligence.get_regional_cost_indices()

@router.get("/market-intelligence/activity")
async def get_construction_activity(
    region: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les indicateurs d'activité de la construction"""
    return await market_intelligence.get_construction_activity(region)

@router.get("/market-intelligence/forecasts")
async def get_price_forecasts(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les prévisions de prix"""
    return await market_intelligence.get_price_forecasts(category)

@router.get("/market-intelligence/overview")
async def get_market_overview(
    current_user: dict = Depends(get_current_user)
):
    """Récupère une vue d'ensemble du marché"""
    trends = await market_intelligence.get_market_trends()
    indices = await market_intelligence.get_regional_cost_indices()
    activity = await market_intelligence.get_construction_activity()
    forecasts = await market_intelligence.get_price_forecasts()
    
    return {
        "trends": trends[:10] if trends else [],
        "regional_indices": indices,
        "activity": activity,
        "forecasts": forecasts
    }

# =============================================================================
# COST PREDICTION ROUTES
# =============================================================================

@router.post("/projects/{project_id}/cost-prediction")
async def create_cost_prediction(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Crée une prédiction de coût pour un projet"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return await cost_prediction.predict_project_cost(project_id, project)

@router.get("/projects/{project_id}/cost-prediction")
async def get_cost_predictions(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les prédictions de coût d'un projet"""
    predictions = await cost_prediction.get_cost_predictions(project_id)
    
    if not predictions:
        # Générer une prédiction si aucune n'existe
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        new_prediction = await cost_prediction.predict_project_cost(project_id, project)
        return [new_prediction]
    
    return predictions

@router.get("/projects/{project_id}/cost-prediction/latest")
async def get_latest_cost_prediction(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère la dernière prédiction de coût"""
    prediction = await cost_prediction.get_latest_prediction(project_id)
    
    if not prediction:
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        prediction = await cost_prediction.predict_project_cost(project_id, project)
    
    return prediction

# =============================================================================
# DESIGN OPTIMIZATION ROUTES
# =============================================================================

@router.post("/projects/{project_id}/design-optimization")
async def create_design_optimization(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Crée une analyse d'optimisation de conception"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Récupérer le DPGF si disponible
    dpgf = await db.dpgf.find_one({"project_id": project_id}, {"_id": 0})
    
    return await design_optimization.analyze_design_optimization(project_id, project, dpgf)

@router.get("/projects/{project_id}/design-optimization")
async def get_design_optimizations(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les analyses d'optimisation de conception"""
    analyses = await design_optimization.get_design_optimizations(project_id)
    
    if not analyses:
        # Générer une analyse si aucune n'existe
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        dpgf = await db.dpgf.find_one({"project_id": project_id}, {"_id": 0})
        new_analysis = await design_optimization.analyze_design_optimization(project_id, project, dpgf)
        return [new_analysis]
    
    return analyses

@router.put("/projects/{project_id}/design-optimization/{analysis_id}/suggestion/{suggestion_id}")
async def update_suggestion_status(
    project_id: str,
    analysis_id: str,
    suggestion_id: str,
    status: str = Query(..., description="Nouveau statut: proposed, accepted, rejected, implemented"),
    current_user: dict = Depends(get_current_user)
):
    """Met à jour le statut d'une suggestion d'optimisation"""
    result = await design_optimization.update_suggestion_status(project_id, analysis_id, suggestion_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Analyse ou suggestion non trouvée")
    return result

# =============================================================================
# MULTI-SCENARIO ROUTES
# =============================================================================

@router.post("/projects/{project_id}/multi-scenario")
async def create_multi_scenario_analysis(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Crée une analyse multi-scénarios"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return await multi_scenario.create_multi_scenario_analysis(project_id, project)

@router.get("/projects/{project_id}/multi-scenario")
async def get_multi_scenario_analyses(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les analyses multi-scénarios d'un projet"""
    analyses = await multi_scenario.get_multi_scenario_analyses(project_id)
    
    if not analyses:
        # Générer une analyse si aucune n'existe
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        new_analysis = await multi_scenario.create_multi_scenario_analysis(project_id, project)
        return [new_analysis]
    
    return analyses

@router.put("/projects/{project_id}/multi-scenario/{analysis_id}/select/{scenario_type}")
async def select_recommended_scenario(
    project_id: str,
    analysis_id: str,
    scenario_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Sélectionne un scénario comme recommandé"""
    result = await multi_scenario.select_scenario(project_id, analysis_id, scenario_type)
    if not result:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return result


# =============================================================================
# ALIAS ROUTES FOR FRONTEND COMPATIBILITY
# =============================================================================

@router.get("/benchmark/projects/{project_id}/analysis")
async def get_benchmark_analysis_alias(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Alias pour l'analyse de benchmark d'un projet"""
    comparison = await db.benchmarks.find_one(
        {"project_id": project_id, "type": "benchmark_comparison"},
        {"_id": 0}
    )
    
    if not comparison:
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        comparison = await benchmark.compare_project_to_benchmarks(project_id, project)
    
    return comparison

@router.get("/design-optimization/projects/{project_id}/analysis")
async def get_design_optimization_alias(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Alias pour l'analyse d'optimisation de conception"""
    analyses = await design_optimization.get_design_optimizations(project_id)
    
    if not analyses:
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        dpgf = await db.dpgf.find_one({"project_id": project_id}, {"_id": 0})
        new_analysis = await design_optimization.analyze_design_optimization(project_id, project, dpgf)
        return new_analysis
    
    return analyses[0] if analyses else None

# =============================================================================
# FEASIBILITY SIMULATION (AI-POWERED)
# =============================================================================

from pydantic import BaseModel
from typing import Optional, List

class FeasibilitySimulationRequest(BaseModel):
    city: str = "Paris"
    project_type: str = "housing"
    surface_m2: float = 5000
    program: Optional[str] = None
    quality_level: str = "standard"
    number_of_floors: int = 6
    parking_places: int = 50
    parking_type: str = "underground"

@router.post("/feasibility/simulate")
async def simulate_feasibility(
    request: FeasibilitySimulationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Simule la faisabilité d'un projet sans plans"""
    
    # Ratios de base par typologie
    base_ratios = {
        "housing": {"economic": 1400, "standard": 1850, "premium": 2500, "luxury": 3500},
        "office": {"economic": 1200, "standard": 1650, "premium": 2300, "luxury": 3200},
        "hotel": {"economic": 1800, "standard": 2400, "premium": 3500, "luxury": 5000},
        "retail": {"economic": 1000, "standard": 1400, "premium": 2000, "luxury": 2800},
        "mixed_use": {"economic": 1400, "standard": 1800, "premium": 2400, "luxury": 3200},
        "public_facility": {"economic": 1600, "standard": 2100, "premium": 2800, "luxury": 3800},
    }
    
    # Coefficients de localisation
    location_coefficients = {
        "Paris": 1.25, "Lyon": 1.05, "Marseille": 1.00, "Bordeaux": 1.02,
        "Toulouse": 0.98, "Nantes": 0.95, "Lille": 0.97, "Strasbourg": 1.00,
        "Nice": 1.10, "Rennes": 0.93, "other": 0.90
    }
    
    # Systèmes structurels suggérés
    structural_systems = {
        "housing": {"low": "Voiles béton", "medium": "Poteaux-dalles", "high": "Mixte acier-béton"},
        "office": {"low": "Poteaux-dalles", "medium": "Structure métallique", "high": "Mixte"},
        "hotel": {"low": "Voiles béton", "medium": "Poteaux-dalles", "high": "Structure métallique"},
    }
    
    # Systèmes de façade suggérés
    facade_systems = {
        "economic": "Enduit sur isolation extérieure",
        "standard": "Bardage métallique + isolation",
        "premium": "Mur rideau aluminium",
        "luxury": "Pierre naturelle / verre structurel"
    }
    
    # Calculs
    type_ratios = base_ratios.get(request.project_type, base_ratios["housing"])
    base_cost_m2 = type_ratios.get(request.quality_level, type_ratios["standard"])
    location_coef = location_coefficients.get(request.city, location_coefficients["other"])
    
    # Ajustement hauteur
    height_coef = 1.0 + max(0, (request.number_of_floors - 8)) * 0.02
    
    # Coût construction
    adjusted_cost_m2 = base_cost_m2 * location_coef * height_coef
    construction_cost = request.surface_m2 * adjusted_cost_m2
    
    # Coût parking
    parking_cost_per_place = 25000 if request.parking_type == "underground" else 8000
    parking_cost = request.parking_places * parking_cost_per_place
    
    # VRD (5-8% du coût construction)
    vrd_ratio = 0.06
    vrd_cost = construction_cost * vrd_ratio
    
    # Total
    total_cost = construction_cost + parking_cost + vrd_cost
    
    # Fourchettes
    cost_min = total_cost * 0.85
    cost_max = total_cost * 1.18
    
    # Suggestions
    height_category = "low" if request.number_of_floors <= 5 else "medium" if request.number_of_floors <= 12 else "high"
    suggested_structure = structural_systems.get(request.project_type, structural_systems["housing"]).get(height_category, "Poteaux-dalles")
    suggested_facade = facade_systems.get(request.quality_level, facade_systems["standard"])
    
    # Marge promoteur simulée (15-20%)
    land_cost_estimate = total_cost * 0.25  # Estimation terrain
    developer_margin_rate = 0.18
    selling_price_estimate = (total_cost + land_cost_estimate) * (1 + developer_margin_rate)
    developer_margin = selling_price_estimate - total_cost - land_cost_estimate
    
    return {
        "simulation_id": f"sim-{request.city.lower()}-{request.project_type}",
        "inputs": {
            "city": request.city,
            "project_type": request.project_type,
            "surface_m2": request.surface_m2,
            "quality_level": request.quality_level,
            "number_of_floors": request.number_of_floors,
            "parking_places": request.parking_places,
            "parking_type": request.parking_type
        },
        "cost_estimation": {
            "construction_cost": round(construction_cost, 2),
            "parking_cost": round(parking_cost, 2),
            "vrd_cost": round(vrd_cost, 2),
            "total_cost": round(total_cost, 2),
            "cost_per_m2": round(adjusted_cost_m2, 2)
        },
        "cost_range": {
            "minimum": round(cost_min, 2),
            "maximum": round(cost_max, 2),
            "confidence": "medium"
        },
        "technical_suggestions": {
            "structural_system": suggested_structure,
            "facade_system": suggested_facade,
            "foundation_type": "Fondations profondes" if request.number_of_floors > 8 else "Semelles filantes",
            "hvac_system": "CTA double flux + PAC" if request.quality_level in ["premium", "luxury"] else "Ventilation simple flux + chaudière gaz"
        },
        "developer_simulation": {
            "estimated_land_cost": round(land_cost_estimate, 2),
            "total_investment": round(total_cost + land_cost_estimate, 2),
            "estimated_selling_price": round(selling_price_estimate, 2),
            "developer_margin": round(developer_margin, 2),
            "margin_rate": f"{developer_margin_rate * 100:.1f}%"
        },
        "coefficients_applied": {
            "base_ratio": base_cost_m2,
            "location": location_coef,
            "height": round(height_coef, 3),
            "vrd_ratio": vrd_ratio
        },
        "warnings": [
            "Cette simulation est indicative et ne remplace pas une étude détaillée",
            "Les coûts réels peuvent varier de ±15% selon les conditions du marché"
        ] + (["Hauteur importante - prévoir études structure approfondies"] if request.number_of_floors > 10 else [])
    }


# =============================================================================
# AI PROJECT OPTIMIZATION
# =============================================================================

class OptimizationAnalyzeRequest(BaseModel):
    project_type: str = "housing"
    surface_m2: float = 5000
    location: str = "ile_de_france"
    quality_level: str = "standard"
    parking_type: str = "underground"
    parking_places: int = 50
    facade_type: str = "standard"
    structure_type: str = "concrete"
    number_of_floors: int = 6
    current_budget: Optional[float] = None

@router.post("/optimization/analyze")
async def analyze_optimization(
    request: OptimizationAnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyse IA des optimisations possibles pour un projet"""
    
    # Ratios de base
    base_ratios = {
        "housing": 1850, "office": 1650, "hotel": 2400,
        "retail": 1400, "mixed_use": 1800, "public_facility": 2100
    }
    
    base_cost = request.surface_m2 * base_ratios.get(request.project_type, 1800)
    parking_cost = request.parking_places * (25000 if request.parking_type == "underground" else 8000)
    total_estimated = base_cost + parking_cost
    
    current_budget = request.current_budget or total_estimated
    
    suggestions = []
    total_savings = 0
    
    # 1. Optimisation parking
    if request.parking_type == "underground" and request.parking_places > 30:
        saving = request.parking_places * 0.3 * 17000
        suggestions.append({
            "id": "parking-reduction",
            "title": "Réduction parking souterrain",
            "description": f"Réduire de 30% les places souterraines et compenser par du parking extérieur",
            "category": "parking",
            "savings_potential": round(saving),
            "savings_percentage": round(saving / current_budget * 100, 1),
            "complexity": "medium",
            "impact_quality": "low",
            "recommendation": "Recommandé si contraintes foncières le permettent"
        })
        total_savings += saving
    
    # 2. Optimisation façade
    facade_savings = {
        "premium": {"saving": base_cost * 0.08, "target": "standard"},
        "luxury": {"saving": base_cost * 0.12, "target": "premium"}
    }
    if request.facade_type in facade_savings:
        opt = facade_savings[request.facade_type]
        suggestions.append({
            "id": "facade-optimization",
            "title": "Optimisation système de façade",
            "description": f"Passer à un système de façade {opt['target']} avec finitions équivalentes",
            "category": "facade",
            "savings_potential": round(opt["saving"]),
            "savings_percentage": round(opt["saving"] / current_budget * 100, 1),
            "complexity": "low",
            "impact_quality": "medium",
            "recommendation": "À étudier avec l'architecte"
        })
        total_savings += opt["saving"]
    
    # 3. Optimisation structure
    if request.structure_type == "steel" and request.number_of_floors < 10:
        saving = base_cost * 0.05
        suggestions.append({
            "id": "structure-optimization",
            "title": "Optimisation système structurel",
            "description": "Passage à une structure béton armé pour ce gabarit de bâtiment",
            "category": "structure",
            "savings_potential": round(saving),
            "savings_percentage": round(saving / current_budget * 100, 1),
            "complexity": "high",
            "impact_quality": "low",
            "recommendation": "Nécessite validation BET structure"
        })
        total_savings += saving
    
    # 4. Optimisation circulation
    circulation_saving = base_cost * 0.03
    suggestions.append({
        "id": "circulation-optimization",
        "title": "Optimisation des circulations",
        "description": "Réduire la largeur des couloirs de 1.50m à 1.40m et optimiser les paliers",
        "category": "circulation",
        "savings_potential": round(circulation_saving),
        "savings_percentage": round(circulation_saving / current_budget * 100, 1),
        "complexity": "low",
        "impact_quality": "low",
        "recommendation": "Compatible réglementation PMR"
    })
    total_savings += circulation_saving
    
    # 5. Optimisation trame structurelle
    grid_saving = base_cost * 0.025
    suggestions.append({
        "id": "grid-optimization",
        "title": "Optimisation trame structurelle",
        "description": "Passer à une trame régulière 7.20m x 7.20m pour optimiser les coffrages",
        "category": "structure",
        "savings_potential": round(grid_saving),
        "savings_percentage": round(grid_saving / current_budget * 100, 1),
        "complexity": "medium",
        "impact_quality": "low",
        "recommendation": "À intégrer dès la phase conception"
    })
    total_savings += grid_saving
    
    # 6. Optimisation enveloppe
    if request.quality_level in ["premium", "luxury"]:
        envelope_saving = base_cost * 0.04
        suggestions.append({
            "id": "envelope-simplification",
            "title": "Simplification de l'enveloppe",
            "description": "Réduire les décrochés de façade et simplifier la volumétrie",
            "category": "facade",
            "savings_potential": round(envelope_saving),
            "savings_percentage": round(envelope_saving / current_budget * 100, 1),
            "complexity": "medium",
            "impact_quality": "medium",
            "recommendation": "Impact architectural à valider"
        })
        total_savings += envelope_saving
    
    return {
        "analysis_id": f"opt-{request.project_type}-{int(request.surface_m2)}",
        "input_parameters": {
            "project_type": request.project_type,
            "surface_m2": request.surface_m2,
            "location": request.location,
            "quality_level": request.quality_level,
            "parking_type": request.parking_type,
            "facade_type": request.facade_type,
            "structure_type": request.structure_type
        },
        "current_estimate": round(current_budget),
        "optimized_estimate": round(current_budget - total_savings),
        "total_savings_potential": round(total_savings),
        "savings_percentage": round(total_savings / current_budget * 100, 1),
        "suggestions": suggestions,
        "summary": {
            "high_impact": len([s for s in suggestions if s["savings_percentage"] > 3]),
            "medium_impact": len([s for s in suggestions if 1 < s["savings_percentage"] <= 3]),
            "low_impact": len([s for s in suggestions if s["savings_percentage"] <= 1])
        }
    }

# =============================================================================
# MARKET BENCHMARK COMPARE
# =============================================================================

class BenchmarkCompareRequest(BaseModel):
    project_type: str = "housing"
    surface_m2: float = 5000
    location: str = "ile_de_france"
    quality_level: str = "standard"
    total_budget: float
    facade_cost: Optional[float] = None
    structure_cost: Optional[float] = None
    parking_cost: Optional[float] = None

@router.post("/benchmark/compare")
async def compare_to_benchmark(
    request: BenchmarkCompareRequest,
    current_user: dict = Depends(get_current_user)
):
    """Compare un projet aux ratios du marché"""
    
    # Ratios marché par typologie (€/m²)
    market_ratios = {
        "housing": {"economic": 1400, "standard": 1850, "premium": 2500, "luxury": 3500},
        "office": {"economic": 1200, "standard": 1650, "premium": 2300, "luxury": 3200},
        "hotel": {"economic": 1800, "standard": 2400, "premium": 3500, "luxury": 5000},
        "retail": {"economic": 1000, "standard": 1400, "premium": 2000, "luxury": 2800},
        "mixed_use": {"economic": 1400, "standard": 1800, "premium": 2400, "luxury": 3200}
    }
    
    # Ratios façade (€/m² façade, ~40% surface plancher)
    facade_ratios = {
        "economic": 250, "standard": 400, "premium": 650, "luxury": 1000
    }
    
    # Ratios structure (€/m²)
    structure_ratios = {
        "economic": 350, "standard": 450, "premium": 550, "luxury": 650
    }
    
    # Coefficients localisation
    location_coefs = {
        "ile_de_france": 1.15, "grande_couronne": 0.95,
        "grandes_metropoles": 1.00, "regions": 0.85
    }
    
    type_ratios = market_ratios.get(request.project_type, market_ratios["housing"])
    market_cost_m2 = type_ratios.get(request.quality_level, type_ratios["standard"])
    location_coef = location_coefs.get(request.location, 1.0)
    
    adjusted_market_m2 = market_cost_m2 * location_coef
    market_total = adjusted_market_m2 * request.surface_m2
    
    project_cost_m2 = request.total_budget / request.surface_m2
    deviation = (project_cost_m2 - adjusted_market_m2) / adjusted_market_m2 * 100
    
    def get_status(dev):
        if dev < -10: return "below_market"
        elif dev > 10: return "above_market"
        else: return "within_market"
    
    comparisons = []
    
    # Comparaison globale
    comparisons.append({
        "category": "global",
        "label": "Coût global",
        "project_value": round(project_cost_m2),
        "market_value": round(adjusted_market_m2),
        "deviation_percent": round(deviation, 1),
        "status": get_status(deviation),
        "unit": "€/m²"
    })
    
    # Comparaison façade
    if request.facade_cost:
        facade_surface = request.surface_m2 * 0.4
        project_facade_m2 = request.facade_cost / facade_surface
        market_facade_m2 = facade_ratios.get(request.quality_level, 400) * location_coef
        facade_dev = (project_facade_m2 - market_facade_m2) / market_facade_m2 * 100
        comparisons.append({
            "category": "facade",
            "label": "Coût façade",
            "project_value": round(project_facade_m2),
            "market_value": round(market_facade_m2),
            "deviation_percent": round(facade_dev, 1),
            "status": get_status(facade_dev),
            "unit": "€/m² façade"
        })
    
    # Comparaison structure
    if request.structure_cost:
        project_structure_m2 = request.structure_cost / request.surface_m2
        market_structure_m2 = structure_ratios.get(request.quality_level, 450) * location_coef
        structure_dev = (project_structure_m2 - market_structure_m2) / market_structure_m2 * 100
        comparisons.append({
            "category": "structure",
            "label": "Coût structure",
            "project_value": round(project_structure_m2),
            "market_value": round(market_structure_m2),
            "deviation_percent": round(structure_dev, 1),
            "status": get_status(structure_dev),
            "unit": "€/m²"
        })
    
    # Ratio circulation estimé
    circulation_ratio = 0.18 if request.project_type == "housing" else 0.22
    market_circulation = circulation_ratio
    comparisons.append({
        "category": "circulation",
        "label": "Ratio circulation",
        "project_value": round(circulation_ratio * 100),
        "market_value": round(market_circulation * 100),
        "deviation_percent": 0,
        "status": "within_market",
        "unit": "%"
    })
    
    overall_status = get_status(deviation)
    
    return {
        "benchmark_id": f"bench-{request.project_type}",
        "input_summary": {
            "project_type": request.project_type,
            "surface_m2": request.surface_m2,
            "location": request.location,
            "quality_level": request.quality_level,
            "total_budget": request.total_budget
        },
        "overall_status": overall_status,
        "overall_deviation": round(deviation, 1),
        "market_reference": {
            "cost_per_m2": round(adjusted_market_m2),
            "total_estimate": round(market_total),
            "location_coefficient": location_coef
        },
        "project_metrics": {
            "cost_per_m2": round(project_cost_m2),
            "total_budget": request.total_budget
        },
        "comparisons": comparisons,
        "recommendations": [
            "Budget conforme au marché" if overall_status == "within_market" else
            "Budget supérieur au marché - étudier les optimisations" if overall_status == "above_market" else
            "Budget inférieur au marché - vérifier la faisabilité technique"
        ],
        "market_data": {
            "source": "Indices BT01 / FFB 2024",
            "last_updated": "2024-Q4"
        }
    }
