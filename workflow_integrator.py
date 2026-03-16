# /app/backend/services/workflow_integrator.py
# Service d'intégration du workflow économiste - connecte tous les modules

import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso

from services import plan_analysis, bim_ifc_service, carbon_analysis


async def connect_plan_to_quantities(
    project_id: str,
    plan_analysis_id: str
) -> Dict:
    """
    Connecte une analyse de plan aux quantités et génère une estimation de coûts.
    Cette fonction intègre le flux:
    Plan -> Pièces/Surfaces -> Quantités -> Estimation de coûts
    """
    
    # Récupérer l'analyse de plan
    analysis = await plan_analysis.get_plan_analysis(plan_analysis_id)
    if not analysis:
        return {"error": "Analyse de plan non trouvée"}
    
    # Récupérer le projet
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    # Extraire les quantités de l'analyse de plan
    rooms = analysis.get("rooms", [])
    walls = analysis.get("walls", [])
    openings = analysis.get("openings", [])
    summary = analysis.get("summary", {})
    
    # Calculs des quantités dérivées
    total_surface = summary.get("habitable_surface_m2", 0) + summary.get("circulation_surface_m2", 0)
    
    # Surface de plancher (estimation basée sur les pièces)
    floor_surface = total_surface * 1.05  # +5% pour éléments non comptabilisés
    
    # Surface de murs (estimation)
    wall_lengths = sum(w.get("estimated_length_m", 0) for w in walls)
    avg_height = 2.7  # Hauteur standard
    wall_surface = wall_lengths * avg_height
    
    # Portes et fenêtres
    doors = [o for o in openings if o.get("type") == "porte"]
    windows = [o for o in openings if o.get("type") in ["fenetre", "baie"]]
    
    # Quantités extraites
    quantities = {
        "surfaces": {
            "plancher_brut_m2": round(floor_surface, 2),
            "habitable_m2": round(summary.get("habitable_surface_m2", 0), 2),
            "circulation_m2": round(summary.get("circulation_surface_m2", 0), 2),
            "murs_m2": round(wall_surface, 2),
        },
        "counts": {
            "pieces": len(rooms),
            "portes": len(doors),
            "fenetres": len(windows),
            "murs": len(walls)
        },
        "details": {
            "rooms": [{
                "name": r.get("name"),
                "type": r.get("type"),
                "surface_m2": r.get("surface_m2")
            } for r in rooms],
            "openings": [{
                "type": o.get("type"),
                "dimensions": f"{o.get('estimated_width_m', 0)}x{o.get('estimated_height_m', 0)}m"
            } for o in openings]
        },
        "source": {
            "type": "plan_analysis",
            "analysis_id": plan_analysis_id,
            "confidence": analysis.get("overall_confidence_percent", 50)
        }
    }
    
    # Générer une estimation de coûts basée sur ces quantités
    quality_level = project.get("quality_level", "standard")
    project_type = project.get("project_usage", "housing")
    
    # Ratios de base
    base_ratios = {
        "housing": {"economic": 1350, "standard": 1800, "premium": 2400, "luxury": 3200},
        "office": {"economic": 1200, "standard": 1600, "premium": 2200, "luxury": 3000},
    }
    
    type_ratios = base_ratios.get(project_type, base_ratios["housing"])
    ratio = type_ratios.get(quality_level, 1800)
    
    # Estimation
    construction_cost = floor_surface * ratio
    
    cost_estimation = {
        "total_ht": round(construction_cost, 2),
        "ratio_m2": ratio,
        "breakdown": {
            "structure": round(construction_cost * 0.30, 2),
            "second_oeuvre": round(construction_cost * 0.35, 2),
            "lots_techniques": round(construction_cost * 0.25, 2),
            "facade": round(construction_cost * 0.10, 2)
        },
        "quality_level": quality_level,
        "confidence": "medium" if analysis.get("overall_confidence_percent", 0) >= 60 else "low"
    }
    
    # Sauvegarder les quantités extraites
    quantity_record = {
        "id": generate_uuid(),
        "project_id": project_id,
        "source_type": "plan_analysis",
        "source_id": plan_analysis_id,
        "quantities": quantities,
        "cost_estimation": cost_estimation,
        "created_at": now_iso()
    }
    
    await db.quantity_extractions.insert_one(quantity_record)
    quantity_record.pop("_id", None)
    
    # Mettre à jour le projet avec les nouvelles surfaces
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "extracted_surface_m2": floor_surface,
            "last_quantity_extraction": now_iso()
        }}
    )
    
    return {
        "status": "success",
        "quantities": quantities,
        "cost_estimation": cost_estimation,
        "extraction_id": quantity_record["id"]
    }


async def get_project_workflow_status(project_id: str) -> Dict:
    """
    Récupère le statut du workflow économiste pour un projet.
    Indique les étapes complétées et les prochaines actions.
    """
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    # Vérifier les différentes étapes
    plan_analyses = await db.plan_analyses.count_documents({"project_id": project_id})
    ifc_analyses = await db.ifc_analyses.count_documents({"project_id": project_id})
    quantity_extractions = await db.quantity_extractions.count_documents({"project_id": project_id})
    cctp_documents = await db.cctp_documents.count_documents({"project_id": project_id})
    carbon_analyses = await db.carbon_analyses.count_documents({"project_id": project_id})
    
    workflow = {
        "project_id": project_id,
        "project_name": project.get("project_name"),
        "stages": {
            "plan_analysis": {
                "completed": plan_analyses > 0,
                "count": plan_analyses,
                "description": "Lecture automatique des plans"
            },
            "bim_import": {
                "completed": ifc_analyses > 0,
                "count": ifc_analyses,
                "description": "Import BIM/IFC"
            },
            "quantity_extraction": {
                "completed": quantity_extractions > 0,
                "count": quantity_extractions,
                "description": "Extraction des quantités"
            },
            "cost_estimation": {
                "completed": project.get("extracted_surface_m2") is not None,
                "surface_m2": project.get("extracted_surface_m2", 0),
                "description": "Estimation de coûts"
            },
            "cctp_generation": {
                "completed": cctp_documents > 0,
                "count": cctp_documents,
                "description": "Génération CCTP"
            },
            "carbon_analysis": {
                "completed": carbon_analyses > 0,
                "count": carbon_analyses,
                "description": "Analyse carbone RE2020"
            }
        },
        "completion_percent": 0,
        "next_recommended_action": None
    }
    
    # Calculer le pourcentage de complétion
    completed = sum(1 for s in workflow["stages"].values() if s.get("completed"))
    workflow["completion_percent"] = round(completed / len(workflow["stages"]) * 100)
    
    # Recommander la prochaine action
    if not workflow["stages"]["plan_analysis"]["completed"] and not workflow["stages"]["bim_import"]["completed"]:
        workflow["next_recommended_action"] = "Importer un plan ou un fichier BIM pour extraire les quantités"
    elif not workflow["stages"]["quantity_extraction"]["completed"]:
        workflow["next_recommended_action"] = "Connecter l'analyse au module d'extraction de quantités"
    elif not workflow["stages"]["cctp_generation"]["completed"]:
        workflow["next_recommended_action"] = "Générer le CCTP technique"
    elif not workflow["stages"]["carbon_analysis"]["completed"]:
        workflow["next_recommended_action"] = "Lancer l'analyse carbone RE2020"
    else:
        workflow["next_recommended_action"] = "Workflow complet - Exporter le rapport final"
    
    return workflow


async def generate_integrated_report(project_id: str) -> Dict:
    """
    Génère un rapport intégré combinant toutes les analyses du projet.
    """
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    # Récupérer toutes les données
    plan_data = await db.plan_analyses.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1)
    
    ifc_data = await db.ifc_analyses.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1)
    
    carbon_data = await db.carbon_analyses.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1)
    
    cctp_data = await db.cctp_documents.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("generated_at", -1).to_list(1)
    
    # Construire le rapport
    report = {
        "id": generate_uuid(),
        "project_id": project_id,
        "project": {
            "name": project.get("project_name"),
            "client": project.get("client_name"),
            "surface_m2": project.get("target_surface_m2", 0),
            "extracted_surface_m2": project.get("extracted_surface_m2"),
            "type": project.get("project_usage"),
            "quality": project.get("quality_level")
        },
        "plan_analysis": plan_data[0] if plan_data else None,
        "bim_analysis": ifc_data[0] if ifc_data else None,
        "carbon_analysis": carbon_data[0] if carbon_data else None,
        "cctp_summary": {
            "lots_count": len(cctp_data[0].get("lots", [])) if cctp_data else 0,
            "generated": bool(cctp_data)
        },
        "generated_at": now_iso()
    }
    
    return report
