# /app/backend/services/program_generator.py
# Service de génération automatique de programmes immobiliers

import sys
from typing import Dict, List, Any, Optional

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso

# Coefficients et ratios par type de programme
PROGRAM_RATIOS = {
    "housing": {
        "collective": {
            "sdp_to_shab": 0.82,  # Surface habitable / SDP
            "circulation_ratio": 0.15,
            "technical_ratio": 0.03,
            "avg_unit_size_m2": 65,
            "parking_ratio": 1.2,  # places par logement
            "balcony_ratio": 0.08,  # surface balcon / SHAB
        },
        "individual": {
            "sdp_to_shab": 0.90,
            "circulation_ratio": 0.08,
            "technical_ratio": 0.02,
            "avg_unit_size_m2": 110,
            "parking_ratio": 2.0,
            "garden_ratio": 2.5,  # surface jardin / SHAB
        }
    },
    "office": {
        "sdp_to_sub": 0.85,  # Surface utile brute / SDP
        "circulation_ratio": 0.15,
        "technical_ratio": 0.05,
        "parking_ratio": 1/25,  # places par m² SUB
        "density_m2_per_person": 12,
    },
    "hotel": {
        "room_size_m2": {
            "economic": 18,
            "standard": 24,
            "premium": 32,
            "luxury": 45
        },
        "circulation_ratio": 0.25,
        "common_areas_ratio": 0.20,
        "parking_ratio": 0.3,  # places par chambre
    },
    "retail": {
        "sdp_to_sgv": 0.88,  # Surface de vente / SDP
        "storage_ratio": 0.15,
        "circulation_ratio": 0.10,
        "parking_ratio": 1/25,  # places par m² surface de vente
    }
}

# PLU - Coefficients d'emprise et hauteur par zone
PLU_ZONES = {
    "UA": {"ces": 0.80, "cos": 3.0, "height_max_m": 25, "description": "Zone urbaine dense"},
    "UB": {"ces": 0.60, "cos": 2.0, "height_max_m": 18, "description": "Zone urbaine mixte"},
    "UC": {"ces": 0.40, "cos": 1.2, "height_max_m": 12, "description": "Zone urbaine résidentielle"},
    "UD": {"ces": 0.30, "cos": 0.8, "height_max_m": 9, "description": "Zone pavillonnaire"},
    "AU": {"ces": 0.50, "cos": 1.5, "height_max_m": 15, "description": "Zone à urbaniser"},
}


async def generate_building_program(
    project_id: str,
    land_surface_m2: float,
    plu_zone: str = "UB",
    building_type: str = "housing",
    quality_level: str = "standard",
    specific_requirements: Optional[Dict] = None
) -> Dict:
    """Génère un programme immobilier automatiquement"""
    
    program_id = generate_uuid()
    now = now_iso()
    
    # Récupérer les données PLU
    plu_data = PLU_ZONES.get(plu_zone, PLU_ZONES["UB"])
    ces = plu_data["ces"]  # Coefficient d'emprise au sol
    cos = plu_data["cos"]  # Coefficient d'occupation des sols
    height_max = plu_data["height_max_m"]
    
    # Calculer les surfaces constructibles
    emprise_max_m2 = land_surface_m2 * ces
    sdp_max_m2 = land_surface_m2 * cos
    
    # Estimer le nombre de niveaux
    level_height_m = 3.0  # Hauteur par niveau
    max_levels = int(height_max / level_height_m)
    optimal_levels = min(max_levels, int(sdp_max_m2 / emprise_max_m2))
    
    # Calculer la SDP optimale
    sdp_optimal_m2 = emprise_max_m2 * optimal_levels
    if sdp_optimal_m2 > sdp_max_m2:
        sdp_optimal_m2 = sdp_max_m2
    
    # Générer le programme selon le type
    program = {
        "id": program_id,
        "project_id": project_id,
        "type": "building_program",
        "land_surface_m2": land_surface_m2,
        "plu_zone": plu_zone,
        "plu_description": plu_data["description"],
        "building_type": building_type,
        "quality_level": quality_level,
        "regulatory_constraints": {
            "ces": ces,
            "cos": cos,
            "height_max_m": height_max,
            "emprise_max_m2": round(emprise_max_m2, 2),
            "sdp_max_m2": round(sdp_max_m2, 2)
        },
        "created_at": now,
        "updated_at": now
    }
    
    if building_type == "housing":
        program.update(await _generate_housing_program(
            sdp_optimal_m2, optimal_levels, quality_level, specific_requirements
        ))
    elif building_type == "office":
        program.update(await _generate_office_program(
            sdp_optimal_m2, optimal_levels, quality_level
        ))
    elif building_type == "hotel":
        program.update(await _generate_hotel_program(
            sdp_optimal_m2, optimal_levels, quality_level
        ))
    elif building_type == "retail":
        program.update(await _generate_retail_program(
            sdp_optimal_m2, optimal_levels, quality_level
        ))
    else:
        program.update(await _generate_housing_program(
            sdp_optimal_m2, optimal_levels, quality_level, specific_requirements
        ))
    
    # Sauvegarder
    await db.programs.update_one(
        {"project_id": project_id},
        {"$set": program},
        upsert=True
    )
    
    return program


async def _generate_housing_program(
    sdp_m2: float,
    levels: int,
    quality: str,
    requirements: Optional[Dict] = None
) -> Dict:
    """Génère un programme de logements"""
    
    ratios = PROGRAM_RATIOS["housing"]["collective"]
    
    # Surfaces
    shab = sdp_m2 * ratios["sdp_to_shab"]
    circulation = sdp_m2 * ratios["circulation_ratio"]
    technical = sdp_m2 * ratios["technical_ratio"]
    
    # Nombre de logements
    avg_unit_size = ratios["avg_unit_size_m2"]
    if quality == "premium":
        avg_unit_size *= 1.3
    elif quality == "economic":
        avg_unit_size *= 0.85
    
    unit_count = int(shab / avg_unit_size)
    
    # Mix logements (T1 à T5)
    unit_mix = _calculate_housing_mix(unit_count, requirements)
    
    # Parkings
    parking_count = int(unit_count * ratios["parking_ratio"])
    
    # Espaces extérieurs
    balcony_surface = shab * ratios["balcony_ratio"]
    
    return {
        "surfaces": {
            "sdp_m2": round(sdp_m2, 2),
            "shab_m2": round(shab, 2),
            "circulation_m2": round(circulation, 2),
            "technical_m2": round(technical, 2),
            "balcony_m2": round(balcony_surface, 2),
            "ratio_shab_sdp": round(shab / sdp_m2 * 100, 1)
        },
        "levels": levels,
        "units": {
            "total_count": unit_count,
            "avg_size_m2": round(avg_unit_size, 1),
            "mix": unit_mix
        },
        "parking": {
            "total_places": parking_count,
            "ratio_per_unit": ratios["parking_ratio"],
            "type": "underground" if parking_count > 20 else "external"
        },
        "key_ratios": {
            "shab_per_unit_m2": round(shab / unit_count if unit_count > 0 else 0, 1),
            "circulation_percent": round(ratios["circulation_ratio"] * 100, 1),
            "parking_m2_estimate": round(parking_count * 25, 0)
        }
    }


def _calculate_housing_mix(total_units: int, requirements: Optional[Dict] = None) -> List[Dict]:
    """Calcule le mix de typologies de logements"""
    
    # Mix standard (adapté au marché français)
    default_mix = {
        "T1": 0.10,
        "T2": 0.30,
        "T3": 0.35,
        "T4": 0.20,
        "T5": 0.05
    }
    
    sizes = {
        "T1": 30,
        "T2": 45,
        "T3": 65,
        "T4": 85,
        "T5": 110
    }
    
    if requirements and requirements.get("unit_mix"):
        default_mix.update(requirements["unit_mix"])
    
    result = []
    for typology, ratio in default_mix.items():
        count = round(total_units * ratio)
        if count > 0:
            result.append({
                "typology": typology,
                "count": count,
                "percentage": round(ratio * 100, 1),
                "avg_surface_m2": sizes.get(typology, 60),
                "total_surface_m2": round(count * sizes.get(typology, 60), 2)
            })
    
    return result


async def _generate_office_program(sdp_m2: float, levels: int, quality: str) -> Dict:
    """Génère un programme de bureaux"""
    
    ratios = PROGRAM_RATIOS["office"]
    
    sub = sdp_m2 * ratios["sdp_to_sub"]
    circulation = sdp_m2 * ratios["circulation_ratio"]
    technical = sdp_m2 * ratios["technical_ratio"]
    
    # Capacité
    workstations = int(sub / ratios["density_m2_per_person"])
    parking_count = int(sub * ratios["parking_ratio"])
    
    return {
        "surfaces": {
            "sdp_m2": round(sdp_m2, 2),
            "sub_m2": round(sub, 2),
            "circulation_m2": round(circulation, 2),
            "technical_m2": round(technical, 2),
            "ratio_sub_sdp": round(sub / sdp_m2 * 100, 1)
        },
        "levels": levels,
        "capacity": {
            "workstations": workstations,
            "density_m2_per_person": ratios["density_m2_per_person"],
            "floor_plate_m2": round(sdp_m2 / levels, 1)
        },
        "parking": {
            "total_places": parking_count,
            "type": "underground"
        },
        "specifications": {
            "ceiling_height_m": 2.70 if quality == "premium" else 2.50,
            "raised_floor": True,
            "suspended_ceiling": True
        }
    }


async def _generate_hotel_program(sdp_m2: float, levels: int, quality: str) -> Dict:
    """Génère un programme hôtelier"""
    
    ratios = PROGRAM_RATIOS["hotel"]
    room_size = ratios["room_size_m2"].get(quality, 24)
    
    # Surface disponible pour les chambres (après déduction circulations et parties communes)
    net_ratio = 1 - ratios["circulation_ratio"] - ratios["common_areas_ratio"]
    net_surface = sdp_m2 * net_ratio
    
    room_count = int(net_surface / room_size)
    circulation = sdp_m2 * ratios["circulation_ratio"]
    common_areas = sdp_m2 * ratios["common_areas_ratio"]
    parking_count = int(room_count * ratios["parking_ratio"])
    
    return {
        "surfaces": {
            "sdp_m2": round(sdp_m2, 2),
            "rooms_surface_m2": round(net_surface, 2),
            "circulation_m2": round(circulation, 2),
            "common_areas_m2": round(common_areas, 2)
        },
        "levels": levels,
        "rooms": {
            "total_count": room_count,
            "avg_size_m2": room_size,
            "rooms_per_floor": round(room_count / levels) if levels > 0 else 0
        },
        "facilities": {
            "lobby_m2": round(common_areas * 0.20, 1),
            "restaurant_m2": round(common_areas * 0.35, 1),
            "meeting_rooms_m2": round(common_areas * 0.15, 1),
            "spa_fitness_m2": round(common_areas * 0.15, 1) if quality in ["premium", "luxury"] else 0,
            "back_of_house_m2": round(common_areas * 0.15, 1)
        },
        "parking": {
            "total_places": parking_count,
            "type": "underground"
        },
        "classification": {
            "stars": 5 if quality == "luxury" else 4 if quality == "premium" else 3,
            "quality_level": quality
        }
    }


async def _generate_retail_program(sdp_m2: float, levels: int, quality: str) -> Dict:
    """Génère un programme commercial"""
    
    ratios = PROGRAM_RATIOS["retail"]
    
    sgv = sdp_m2 * ratios["sdp_to_sgv"]  # Surface de vente
    storage = sdp_m2 * ratios["storage_ratio"]
    circulation = sdp_m2 * ratios["circulation_ratio"]
    parking_count = int(sgv * ratios["parking_ratio"])
    
    return {
        "surfaces": {
            "sdp_m2": round(sdp_m2, 2),
            "sgv_m2": round(sgv, 2),
            "storage_m2": round(storage, 2),
            "circulation_m2": round(circulation, 2),
            "ratio_sgv_sdp": round(sgv / sdp_m2 * 100, 1)
        },
        "levels": levels,
        "retail_units": {
            "estimated_count": max(1, int(sgv / 200)),  # 200m² moyens par cellule
            "avg_size_m2": 200
        },
        "parking": {
            "total_places": parking_count,
            "type": "surface" if parking_count < 50 else "underground"
        },
        "specifications": {
            "ceiling_height_m": 4.0 if quality == "premium" else 3.5,
            "loading_docks": max(1, int(sdp_m2 / 2000))
        }
    }


async def get_program(project_id: str) -> Optional[Dict]:
    """Récupère le programme d'un projet"""
    program = await db.programs.find_one({"project_id": project_id}, {"_id": 0})
    return program


async def update_program(project_id: str, updates: Dict) -> Optional[Dict]:
    """Met à jour un programme"""
    updates["updated_at"] = now_iso()
    
    await db.programs.update_one(
        {"project_id": project_id},
        {"$set": updates}
    )
    
    return await get_program(project_id)
