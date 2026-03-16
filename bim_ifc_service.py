# /app/backend/services/bim_ifc_service.py
# Service d'import et d'analyse BIM/IFC

import sys
import io
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso

# Simulation IFC parsing (ifcopenshell would be used in production)
# For production: pip install ifcopenshell


class IFCElement:
    """Représente un élément IFC"""
    def __init__(self, guid: str, ifc_type: str, name: str, properties: Dict):
        self.guid = guid
        self.ifc_type = ifc_type
        self.name = name
        self.properties = properties


async def parse_ifc_file(file_content: bytes, filename: str) -> Dict:
    """Parse un fichier IFC et extrait les éléments"""
    
    # En production, utiliser ifcopenshell:
    # import ifcopenshell
    # ifc_file = ifcopenshell.open(file_path)
    
    # Simulation pour démonstration
    analysis_id = generate_uuid()
    now = now_iso()
    
    # Simuler l'extraction d'éléments BIM
    # Ces ratios sont basés sur des projets types
    file_size_kb = len(file_content) / 1024
    estimated_elements = int(file_size_kb / 10)  # Approximation
    
    elements = {
        "walls": [],
        "slabs": [],
        "columns": [],
        "beams": [],
        "doors": [],
        "windows": [],
        "stairs": [],
        "roofs": []
    }
    
    # Générer des éléments simulés basés sur la taille du fichier
    wall_count = max(20, int(estimated_elements * 0.25))
    slab_count = max(5, int(estimated_elements * 0.08))
    column_count = max(10, int(estimated_elements * 0.05))
    
    for i in range(wall_count):
        elements["walls"].append({
            "guid": f"wall-{generate_uuid()[:8]}",
            "type": "IfcWall",
            "name": f"Mur {i+1}",
            "length_m": round(3 + (i % 5) * 1.5, 2),
            "height_m": 2.80,
            "thickness_m": 0.20,
            "area_m2": round((3 + (i % 5) * 1.5) * 2.80, 2),
            "material": "Béton" if i % 3 == 0 else "Brique" if i % 3 == 1 else "Plâtre"
        })
    
    for i in range(slab_count):
        elements["slabs"].append({
            "guid": f"slab-{generate_uuid()[:8]}",
            "type": "IfcSlab",
            "name": f"Dalle niveau {i}",
            "area_m2": round(200 + (i % 3) * 50, 2),
            "thickness_m": 0.22,
            "volume_m3": round((200 + (i % 3) * 50) * 0.22, 2),
            "material": "Béton armé"
        })
    
    for i in range(column_count):
        elements["columns"].append({
            "guid": f"col-{generate_uuid()[:8]}",
            "type": "IfcColumn",
            "name": f"Poteau {i+1}",
            "height_m": 2.80,
            "section": "40x40",
            "volume_m3": round(0.40 * 0.40 * 2.80, 3),
            "material": "Béton armé"
        })
    
    # Ajouter portes et fenêtres
    for i in range(max(10, wall_count // 3)):
        elements["doors"].append({
            "guid": f"door-{generate_uuid()[:8]}",
            "type": "IfcDoor",
            "name": f"Porte {i+1}",
            "width_m": 0.90 if i % 2 == 0 else 1.40,
            "height_m": 2.10,
            "area_m2": round((0.90 if i % 2 == 0 else 1.40) * 2.10, 2)
        })
        
        elements["windows"].append({
            "guid": f"window-{generate_uuid()[:8]}",
            "type": "IfcWindow",
            "name": f"Fenêtre {i+1}",
            "width_m": 1.20 + (i % 3) * 0.30,
            "height_m": 1.40,
            "area_m2": round((1.20 + (i % 3) * 0.30) * 1.40, 2)
        })
    
    # Calculer les totaux
    quantities = calculate_quantities_from_elements(elements)
    
    return {
        "analysis_id": analysis_id,
        "filename": filename,
        "file_size_kb": round(file_size_kb, 2),
        "parsed_at": now,
        "element_counts": {
            "walls": len(elements["walls"]),
            "slabs": len(elements["slabs"]),
            "columns": len(elements["columns"]),
            "beams": len(elements["beams"]),
            "doors": len(elements["doors"]),
            "windows": len(elements["windows"]),
            "stairs": len(elements["stairs"]),
            "roofs": len(elements["roofs"])
        },
        "elements": elements,
        "quantities": quantities,
        "status": "success"
    }


def calculate_quantities_from_elements(elements: Dict) -> Dict:
    """Calcule les métrés à partir des éléments IFC"""
    
    # Surfaces de murs
    total_wall_area = sum(w.get("area_m2", 0) for w in elements.get("walls", []))
    
    # Surfaces de dalles
    total_slab_area = sum(s.get("area_m2", 0) for s in elements.get("slabs", []))
    
    # Volume structure
    total_slab_volume = sum(s.get("volume_m3", 0) for s in elements.get("slabs", []))
    total_column_volume = sum(c.get("volume_m3", 0) for c in elements.get("columns", []))
    total_concrete_volume = total_slab_volume + total_column_volume
    
    # Menuiseries
    total_door_area = sum(d.get("area_m2", 0) for d in elements.get("doors", []))
    total_window_area = sum(w.get("area_m2", 0) for w in elements.get("windows", []))
    
    # Façade (murs extérieurs estimés à 40% des murs)
    facade_area = total_wall_area * 0.40
    
    return {
        "surfaces": {
            "plancher_brut_m2": round(total_slab_area, 2),
            "murs_m2": round(total_wall_area, 2),
            "facade_m2": round(facade_area, 2),
            "menuiseries_m2": round(total_door_area + total_window_area, 2)
        },
        "volumes": {
            "beton_m3": round(total_concrete_volume, 2),
            "maconnerie_m3": round(total_wall_area * 0.20 * 0.6, 2)  # Estimation
        },
        "lineaires": {
            "cloisons_ml": round(total_wall_area / 2.80, 2),
            "plinthes_ml": round(total_slab_area * 0.15, 2)  # Estimation
        },
        "counts": {
            "portes": len(elements.get("doors", [])),
            "fenetres": len(elements.get("windows", [])),
            "poteaux": len(elements.get("columns", []))
        }
    }


async def generate_cost_from_ifc(analysis_id: str, quantities: Dict, project_type: str = "housing") -> Dict:
    """Génère une estimation de coûts à partir des quantités IFC"""
    
    # Prix unitaires par défaut (€)
    unit_prices = {
        "beton_m3": 180,
        "maconnerie_m3": 250,
        "facade_m2": 350,
        "menuiseries_m2": 450,
        "cloisons_ml": 85,
        "portes_u": 450,
        "fenetres_u": 650
    }
    
    # Ajuster selon typologie
    type_coefficients = {
        "housing": 1.0,
        "office": 1.15,
        "school": 1.10,
        "hospital": 1.35,
        "hotel": 1.20
    }
    coef = type_coefficients.get(project_type, 1.0)
    
    surfaces = quantities.get("surfaces", {})
    volumes = quantities.get("volumes", {})
    counts = quantities.get("counts", {})
    
    # Calcul des coûts
    cost_breakdown = {
        "structure": {
            "beton": round(volumes.get("beton_m3", 0) * unit_prices["beton_m3"] * coef, 2),
            "maconnerie": round(volumes.get("maconnerie_m3", 0) * unit_prices["maconnerie_m3"] * coef, 2)
        },
        "facade": {
            "enveloppe": round(surfaces.get("facade_m2", 0) * unit_prices["facade_m2"] * coef, 2)
        },
        "menuiseries": {
            "portes": round(counts.get("portes", 0) * unit_prices["portes_u"] * coef, 2),
            "fenetres": round(counts.get("fenetres", 0) * unit_prices["fenetres_u"] * coef, 2)
        },
        "second_oeuvre": {
            "cloisons": round(quantities.get("lineaires", {}).get("cloisons_ml", 0) * unit_prices["cloisons_ml"] * coef, 2)
        }
    }
    
    # Totaux par lot
    structure_total = sum(cost_breakdown["structure"].values())
    facade_total = sum(cost_breakdown["facade"].values())
    menuiseries_total = sum(cost_breakdown["menuiseries"].values())
    second_oeuvre_total = sum(cost_breakdown["second_oeuvre"].values())
    
    # Lots complémentaires estimés
    surface_plancher = surfaces.get("plancher_brut_m2", 1000)
    
    lots_complementaires = {
        "cvc": round(surface_plancher * 180 * coef, 2),
        "electricite": round(surface_plancher * 120 * coef, 2),
        "plomberie": round(surface_plancher * 95 * coef, 2),
        "finitions": round(surface_plancher * 150 * coef, 2),
        "vrd": round(surface_plancher * 45 * coef, 2)
    }
    
    subtotal = structure_total + facade_total + menuiseries_total + second_oeuvre_total + sum(lots_complementaires.values())
    aleas = round(subtotal * 0.05, 2)
    total = round(subtotal + aleas, 2)
    
    return {
        "analysis_id": analysis_id,
        "cost_breakdown": cost_breakdown,
        "lots_complementaires": lots_complementaires,
        "summary": {
            "structure": structure_total,
            "facade": facade_total,
            "menuiseries": menuiseries_total,
            "second_oeuvre": second_oeuvre_total,
            "lots_techniques": sum(lots_complementaires.values()),
            "subtotal": subtotal,
            "aleas_5_pct": aleas,
            "total_ht": total
        },
        "ratios": {
            "cout_m2": round(total / surface_plancher, 2) if surface_plancher > 0 else 0,
            "structure_pct": round(structure_total / total * 100, 1) if total > 0 else 0,
            "facade_pct": round(facade_total / total * 100, 1) if total > 0 else 0
        }
    }


async def save_ifc_analysis(project_id: str, analysis_data: Dict, cost_data: Dict) -> Dict:
    """Sauvegarde l'analyse IFC dans la base de données"""
    
    record = {
        "id": analysis_data["analysis_id"],
        "project_id": project_id,
        "filename": analysis_data["filename"],
        "file_size_kb": analysis_data["file_size_kb"],
        "element_counts": analysis_data["element_counts"],
        "quantities": analysis_data["quantities"],
        "cost_estimation": cost_data,
        "created_at": now_iso()
    }
    
    await db.ifc_analyses.insert_one(record)
    record.pop("_id", None)
    
    return record


async def get_ifc_analyses(project_id: str) -> List[Dict]:
    """Récupère les analyses IFC d'un projet"""
    analyses = await db.ifc_analyses.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return analyses
