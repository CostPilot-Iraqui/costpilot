# /app/backend/services/benchmark.py
# Service pour le benchmark de projets

from typing import List, Dict, Any, Optional
import sys
sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso, DEFAULT_COST_REFERENCES, REGIONAL_COEFFICIENTS

async def get_benchmark_projects(
    building_type: Optional[str] = None,
    quality_level: Optional[str] = None,
    region: Optional[str] = None
) -> List[Dict]:
    """Récupère les projets de référence pour le benchmark"""
    query = {"type": "benchmark_project"}
    if building_type:
        query["building_type"] = building_type
    if quality_level:
        query["quality_level"] = quality_level
    if region:
        query["region"] = region
    
    projects = await db.benchmarks.find(query, {"_id": 0}).to_list(100)
    
    if not projects:
        projects = await generate_default_benchmarks()
    
    return projects

async def generate_default_benchmarks() -> List[Dict]:
    """Génère des projets de benchmark par défaut"""
    now = now_iso()
    projects = []
    
    benchmark_data = [
        # Logements
        {"name": "Résidence Les Jardins", "type": "housing", "quality": "standard", "region": "idf", "surface": 4500, "cost_m2": 2100, "year": 2023},
        {"name": "Le Clos des Vignes", "type": "housing", "quality": "premium", "region": "paca", "surface": 3200, "cost_m2": 2800, "year": 2023},
        {"name": "Éco-quartier Durable", "type": "housing", "quality": "standard", "region": "occitanie", "surface": 8500, "cost_m2": 1850, "year": 2024},
        {"name": "Résidence Seniors", "type": "housing", "quality": "premium", "region": "aura", "surface": 2800, "cost_m2": 2600, "year": 2022},
        {"name": "Logements Sociaux HLM", "type": "housing", "quality": "economic", "region": "hauts_de_france", "surface": 6200, "cost_m2": 1550, "year": 2023},
        # Bureaux
        {"name": "Tour Horizon", "type": "office", "quality": "premium", "region": "idf", "surface": 25000, "cost_m2": 2450, "year": 2023},
        {"name": "Parc d'affaires Green", "type": "office", "quality": "standard", "region": "aura", "surface": 12000, "cost_m2": 1700, "year": 2024},
        {"name": "Immeuble de bureaux R+4", "type": "office", "quality": "standard", "region": "bretagne", "surface": 4500, "cost_m2": 1580, "year": 2023},
        # Hôtels
        {"name": "Hôtel 4 étoiles Centre-ville", "type": "hotel", "quality": "premium", "region": "paca", "surface": 8500, "cost_m2": 3200, "year": 2023},
        {"name": "Résidence Tourisme", "type": "hotel", "quality": "standard", "region": "occitanie", "surface": 5200, "cost_m2": 2400, "year": 2024},
        # Commerce
        {"name": "Centre commercial régional", "type": "retail", "quality": "standard", "region": "nouvelle_aquitaine", "surface": 35000, "cost_m2": 1450, "year": 2023},
        {"name": "Retail park périurbain", "type": "retail", "quality": "economic", "region": "grand_est", "surface": 18000, "cost_m2": 1100, "year": 2024},
        # Équipements publics
        {"name": "Groupe scolaire", "type": "public_facility", "quality": "standard", "region": "idf", "surface": 6500, "cost_m2": 2250, "year": 2023},
        {"name": "Médiathèque", "type": "public_facility", "quality": "premium", "region": "pays_de_la_loire", "surface": 3800, "cost_m2": 2900, "year": 2024},
        {"name": "EHPAD 80 lits", "type": "public_facility", "quality": "standard", "region": "bretagne", "surface": 5500, "cost_m2": 2100, "year": 2023},
        # Industriel / Logistique
        {"name": "Entrepôt logistique classe A", "type": "logistics", "quality": "standard", "region": "aura", "surface": 45000, "cost_m2": 850, "year": 2024},
        {"name": "Usine agroalimentaire", "type": "industrial", "quality": "standard", "region": "bretagne", "surface": 12000, "cost_m2": 1250, "year": 2023},
    ]
    
    for data in benchmark_data:
        region_coef = REGIONAL_COEFFICIENTS.get(data["region"], {"coefficient": 1.0})["coefficient"]
        total_cost = data["surface"] * data["cost_m2"]
        
        project = {
            "id": generate_uuid(),
            "type": "benchmark_project",
            "name": data["name"],
            "location": REGIONAL_COEFFICIENTS.get(data["region"], {"label": "France"})["label"],
            "region": data["region"],
            "building_type": data["type"],
            "surface_m2": data["surface"],
            "total_cost": total_cost,
            "cost_per_m2": data["cost_m2"],
            "year_completed": data["year"],
            "quality_level": data["quality"],
            "complexity": "medium",
            "regional_coefficient": region_coef,
            "key_metrics": {
                "ratio_su_sdp": 0.82,
                "ratio_circulation": 0.15,
                "ratio_technique": 0.08,
                "nb_niveaux": 4 if data["type"] != "logistics" else 1
            },
            "lots_breakdown": {
                "01_terrassements": round(total_cost * 0.02, 0),
                "02_vrd": round(total_cost * 0.03, 0),
                "03_gros_oeuvre": round(total_cost * 0.22, 0),
                "04_charpente": round(total_cost * 0.04, 0),
                "05_couverture": round(total_cost * 0.03, 0),
                "06_facade": round(total_cost * 0.10, 0),
                "07_menuiseries_ext": round(total_cost * 0.06, 0),
                "08_cloisonnement": round(total_cost * 0.05, 0),
                "09_revetements_sols": round(total_cost * 0.05, 0),
                "10_revetements_muraux": round(total_cost * 0.02, 0),
                "11_peinture": round(total_cost * 0.03, 0),
                "12_menuiseries_int": round(total_cost * 0.04, 0),
                "13_plomberie": round(total_cost * 0.06, 0),
                "14_cvc": round(total_cost * 0.10, 0),
                "15_electricite": round(total_cost * 0.07, 0),
                "16_courants_faibles": round(total_cost * 0.02, 0),
                "17_ascenseurs": round(total_cost * 0.02, 0),
                "18_equipements_speciaux": round(total_cost * 0.01, 0),
                "19_amenagements_ext": round(total_cost * 0.02, 0),
                "20_aleas": round(total_cost * 0.05, 0)
            },
            "source": "Base interne CostPilot",
            "validated": True,
            "created_at": now
        }
        projects.append(project)
        await db.benchmarks.insert_one(project)
        # Remove MongoDB _id after insert
        project.pop("_id", None)
    
    return projects

async def compare_project_to_benchmarks(
    project_id: str,
    project_data: Dict
) -> Dict:
    """Compare un projet aux projets de référence"""
    now = now_iso()
    
    building_type = project_data.get("project_usage", "housing") or "housing"
    quality_level = project_data.get("quality_level", "standard") or "standard"
    surface = project_data.get("target_surface_m2", 1000) or 1000
    budget = project_data.get("target_budget") or (surface * 1850)
    cost_m2 = budget / surface if surface > 0 else 0
    
    # Récupérer les projets similaires
    benchmarks = await get_benchmark_projects(building_type=building_type)
    
    if not benchmarks:
        return {"error": "Pas de projets de référence disponibles"}
    
    # Filtrer par qualité similaire
    similar_projects = [b for b in benchmarks if b.get("quality_level") == quality_level]
    if not similar_projects:
        similar_projects = benchmarks[:5]
    
    # Calculer les statistiques
    costs_m2 = [p.get("cost_per_m2", 0) for p in similar_projects]
    avg_cost = sum(costs_m2) / len(costs_m2) if costs_m2 else 0
    min_cost = min(costs_m2) if costs_m2 else 0
    max_cost = max(costs_m2) if costs_m2 else 0
    
    # Calculer le percentile du projet
    below_count = sum(1 for c in costs_m2 if c < cost_m2)
    percentile = (below_count / len(costs_m2)) * 100 if costs_m2 else 50
    
    # Analyse de variance par lot
    variance_analysis = {}
    if project_data.get("lots_breakdown"):
        ref_breakdown = similar_projects[0].get("lots_breakdown", {}) if similar_projects else {}
        for lot, amount in project_data.get("lots_breakdown", {}).items():
            ref_amount = ref_breakdown.get(lot, amount)
            variance = ((amount - ref_amount) / ref_amount * 100) if ref_amount > 0 else 0
            variance_analysis[lot] = round(variance, 1)
    
    comparison = {
        "id": generate_uuid(),
        "type": "benchmark_comparison",
        "project_id": project_id,
        "project_cost_m2": round(cost_m2, 2),
        "benchmark_count": len(similar_projects),
        "statistics": {
            "average_cost_m2": round(avg_cost, 2),
            "min_cost_m2": round(min_cost, 2),
            "max_cost_m2": round(max_cost, 2),
            "median_cost_m2": round(sorted(costs_m2)[len(costs_m2)//2] if costs_m2 else 0, 2)
        },
        "position_percentile": round(percentile, 1),
        "variance_vs_average": round((cost_m2 - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0, 1),
        "variance_analysis": variance_analysis,
        "similar_projects": [
            {
                "id": p["id"],
                "name": p["name"],
                "surface_m2": p["surface_m2"],
                "cost_per_m2": p["cost_per_m2"],
                "year": p["year_completed"]
            }
            for p in similar_projects[:5]
        ],
        "recommendations": generate_benchmark_recommendations(cost_m2, avg_cost, percentile),
        "created_at": now
    }
    
    await db.benchmarks.update_one(
        {"project_id": project_id, "type": "benchmark_comparison"},
        {"$set": comparison},
        upsert=True
    )
    
    return comparison

def generate_benchmark_recommendations(cost_m2: float, avg_cost: float, percentile: float) -> List[str]:
    """Génère des recommandations basées sur la comparaison"""
    recommendations = []
    
    if percentile > 75:
        recommendations.append("Le projet se situe dans le quartile supérieur des coûts. Une analyse d'optimisation est recommandée.")
        recommendations.append("Vérifier les hypothèses de prestations et comparer avec les projets similaires moins coûteux.")
    elif percentile > 50:
        recommendations.append("Le projet se situe légèrement au-dessus de la moyenne. Des optimisations ciblées sont possibles.")
    elif percentile > 25:
        recommendations.append("Le projet est bien positionné par rapport aux références. Maintenir la vigilance sur les lots critiques.")
    else:
        recommendations.append("Le budget est très compétitif. S'assurer que les prestations sont bien définies et réalistes.")
        recommendations.append("Attention au risque de sous-estimation : prévoir des provisions pour aléas.")
    
    variance = (cost_m2 - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0
    if abs(variance) > 15:
        if variance > 0:
            recommendations.append(f"Écart de +{variance:.0f}% par rapport à la moyenne. Analyser les postes les plus impactants.")
        else:
            recommendations.append(f"Écart de {variance:.0f}% par rapport à la moyenne. Vérifier la cohérence des estimations.")
    
    return recommendations

async def get_benchmark_statistics(building_type: Optional[str] = None) -> Dict:
    """Récupère les statistiques globales de benchmark"""
    benchmarks = await get_benchmark_projects(building_type=building_type)
    
    if not benchmarks:
        return {"error": "Pas de données disponibles"}
    
    # Statistiques par type de bâtiment
    stats_by_type = {}
    for b in benchmarks:
        bt = b.get("building_type", "other")
        if bt not in stats_by_type:
            stats_by_type[bt] = {"count": 0, "costs": [], "surfaces": []}
        stats_by_type[bt]["count"] += 1
        stats_by_type[bt]["costs"].append(b.get("cost_per_m2", 0))
        stats_by_type[bt]["surfaces"].append(b.get("surface_m2", 0))
    
    # Calculer les moyennes
    for bt, data in stats_by_type.items():
        data["avg_cost_m2"] = round(sum(data["costs"]) / len(data["costs"]), 2) if data["costs"] else 0
        data["avg_surface"] = round(sum(data["surfaces"]) / len(data["surfaces"]), 0) if data["surfaces"] else 0
        data["min_cost_m2"] = round(min(data["costs"]), 2) if data["costs"] else 0
        data["max_cost_m2"] = round(max(data["costs"]), 2) if data["costs"] else 0
        del data["costs"]
        del data["surfaces"]
    
    return {
        "total_projects": len(benchmarks),
        "by_building_type": stats_by_type,
        "last_update": now_iso()
    }
