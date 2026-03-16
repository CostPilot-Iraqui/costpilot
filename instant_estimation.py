# /app/backend/services/instant_estimation.py
# Service d'estimation instantanée par IA (langage naturel) avec GPT-4

import sys
import re
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso

from dotenv import load_dotenv
load_dotenv()

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Prompt système pour l'extraction de paramètres
AI_EXTRACTION_PROMPT = """Tu es un expert économiste de la construction en France.
Ton rôle est d'extraire les paramètres d'un projet à partir d'une description en langage naturel.

Tu dois identifier :
1. Type de projet (logement, bureau, école, hôtel, commerce, hôpital, industriel, équipement public)
2. Surface (en m²) - si mentionnée ou calculable
3. Nombre d'étages
4. Type de structure (béton, acier, bois/CLT, mixte)
5. Type de façade (enduit, brique, bardage, mur rideau, pierre)
6. Niveau de qualité (économique, standard, premium, luxe)
7. Nombre de places de parking
8. Nombre d'unités/logements/chambres
9. Localisation/région (pour coefficients régionaux)

IMPORTANT: Réponds UNIQUEMENT en JSON valide avec cette structure :
{
  "project_type": "housing|office|school|hotel|retail|hospital|industrial|public_facility",
  "surface_m2": nombre ou null,
  "floors": nombre ou null,
  "structure_type": "concrete|steel|timber|mixed",
  "facade_type": "render|brick|cladding|curtain_wall|stone|composite",
  "quality_level": "economic|standard|premium|luxury",
  "parking": nombre ou null,
  "units": nombre ou null,
  "region": "idf|paca|aura|occitanie|nouvelle_aquitaine|bretagne|normandie|hauts_de_france|grand_est|autre",
  "additional_features": ["liste de caractéristiques spéciales détectées"],
  "confidence_score": 0-100
}

Si une information n'est pas mentionnée, utilise les valeurs par défaut intelligentes basées sur le contexte."""


# Dictionnaire de mapping pour le parsing
PROJECT_TYPES = {
    "logement": "housing", "logements": "housing", "housing": "housing",
    "appartement": "housing", "appartements": "housing", "résidentiel": "housing",
    "bureau": "office", "bureaux": "office", "office": "office", "tertiaire": "office",
    "école": "school", "ecole": "school", "school": "school", "scolaire": "school",
    "collège": "school", "college": "school", "lycée": "school", "lycee": "school",
    "hôtel": "hotel", "hotel": "hotel", "hôtelier": "hotel",
    "commerce": "retail", "commercial": "retail", "retail": "retail",
    "hôpital": "hospital", "hopital": "hospital", "santé": "hospital", "clinique": "hospital",
    "industriel": "industrial", "usine": "industrial", "entrepôt": "logistics",
    "public": "public_facility", "équipement": "public_facility"
}

STRUCTURE_TYPES = {
    "béton": "concrete", "beton": "concrete", "concrete": "concrete",
    "acier": "steel", "métallique": "steel", "steel": "steel",
    "bois": "timber", "timber": "timber", "clb": "timber", "clt": "timber",
    "mixte": "mixed", "hybride": "mixed"
}

FACADE_TYPES = {
    "brique": "brick", "brick": "brick",
    "enduit": "render", "render": "render", "crépi": "render",
    "bardage": "cladding", "cladding": "cladding",
    "verre": "glass", "mur rideau": "curtain_wall", "curtain": "curtain_wall",
    "pierre": "stone", "stone": "stone",
    "composite": "composite", "panneaux": "panels"
}

QUALITY_LEVELS = {
    "économique": "economic", "economique": "economic", "basique": "economic",
    "standard": "standard", "courant": "standard", "classique": "standard",
    "haut de gamme": "premium", "premium": "premium", "qualité": "premium",
    "luxe": "luxury", "prestige": "luxury"
}


def parse_natural_language(text: str) -> Dict:
    """Parse une description en langage naturel (fallback heuristique)"""
    
    text_lower = text.lower()
    result = {
        "project_type": "housing",
        "surface_m2": None,
        "floors": None,
        "structure_type": "concrete",
        "facade_type": "render",
        "quality_level": "standard",
        "parking": None,
        "units": None,
        "region": "idf",
        "raw_text": text
    }
    
    # Détecter le type de projet
    for keyword, ptype in PROJECT_TYPES.items():
        if keyword in text_lower:
            result["project_type"] = ptype
            break
    
    # Détecter la surface
    surface_patterns = [
        r'(\d+[\s,.]?\d*)\s*m[²2]',
        r'(\d+[\s,.]?\d*)\s*metres?\s*carr[ée]s?',
        r'surface[:\s]+(\d+[\s,.]?\d*)',
    ]
    for pattern in surface_patterns:
        match = re.search(pattern, text_lower)
        if match:
            surface_str = match.group(1).replace(' ', '').replace(',', '.')
            result["surface_m2"] = float(surface_str)
            break
    
    # Détecter le nombre d'étages
    floor_patterns = [
        r'r\+(\d+)',
        r'(\d+)\s*[ée]tages?',
        r'(\d+)\s*niveaux?',
    ]
    for pattern in floor_patterns:
        match = re.search(pattern, text_lower)
        if match:
            result["floors"] = int(match.group(1))
            break
    
    # Détecter la structure
    for keyword, stype in STRUCTURE_TYPES.items():
        if keyword in text_lower:
            result["structure_type"] = stype
            break
    
    # Détecter la façade
    for keyword, ftype in FACADE_TYPES.items():
        if keyword in text_lower:
            result["facade_type"] = ftype
            break
    
    # Détecter le niveau de qualité
    for keyword, qlevel in QUALITY_LEVELS.items():
        if keyword in text_lower:
            result["quality_level"] = qlevel
            break
    
    # Détecter le parking
    parking_match = re.search(r'(\d+)\s*(?:places?|parking|stationnement)', text_lower)
    if parking_match:
        result["parking"] = int(parking_match.group(1))
    
    # Détecter le nombre de logements
    units_match = re.search(r'(\d+)\s*(?:logements?|appartements?|units?|chambres?)', text_lower)
    if units_match:
        result["units"] = int(units_match.group(1))
    
    return result


async def parse_with_ai(text: str) -> Dict:
    """Parse une description avec GPT-4 pour une extraction intelligente"""
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        print(f"[AI Parse] Starting with text: {text[:50]}...")
        print(f"[AI Parse] Key present: {bool(EMERGENT_LLM_KEY)}")
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"instant_est_{generate_uuid()[:8]}",
            system_message=AI_EXTRACTION_PROMPT
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(
            text=f"Analyse cette description de projet et extrais les paramètres:\n\n{text}"
        )
        
        print("[AI Parse] Sending message to LLM...")
        response = await chat.send_message(user_message)
        print(f"[AI Parse] Got response: {response[:100]}...")
        
        # Nettoyer la réponse
        json_str = response
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        ai_result = json.loads(json_str.strip())
        ai_result["raw_text"] = text
        ai_result["ai_parsed"] = True
        
        print(f"[AI Parse] Success! ai_parsed=True")
        return ai_result
        
    except Exception as e:
        # Fallback vers le parsing heuristique
        print(f"[AI Parse] Exception: {type(e).__name__}: {e}")
        result = parse_natural_language(text)
        result["ai_parsed"] = False
        result["parse_error"] = str(e)
        return result


async def generate_instant_estimation(parsed_input: Dict) -> Dict:
    """Génère une estimation instantanée à partir des paramètres parsés"""
    
    estimation_id = generate_uuid()
    now = now_iso()
    
    # Récupérer ou estimer la surface avec protection NoneType
    surface_m2 = parsed_input.get("surface_m2") or 0
    if not surface_m2 or surface_m2 == 0:
        # Estimer à partir du nombre de logements ou d'un défaut
        units = parsed_input.get("units") or 0
        if units and units > 0:
            avg_unit_size = 65 if parsed_input.get("project_type") == "housing" else 25
            surface_m2 = units * avg_unit_size * 1.15  # +15% circulations
        else:
            surface_m2 = 2000  # Défaut
    
    floors = parsed_input.get("floors") or 4
    
    # Ratios de base par m² selon typologie
    base_ratios = {
        "housing": {"economic": 1350, "standard": 1800, "premium": 2400, "luxury": 3200},
        "office": {"economic": 1200, "standard": 1600, "premium": 2200, "luxury": 3000},
        "school": {"economic": 1500, "standard": 1950, "premium": 2500, "luxury": 3100},
        "hotel": {"economic": 1700, "standard": 2300, "premium": 3200, "luxury": 4500},
        "retail": {"economic": 1000, "standard": 1350, "premium": 1900, "luxury": 2600},
        "hospital": {"economic": 2200, "standard": 2800, "premium": 3600, "luxury": 4500},
        "public_facility": {"economic": 1600, "standard": 2100, "premium": 2700, "luxury": 3400}
    }
    
    # Coefficients structure
    structure_coefficients = {
        "concrete": 1.00,
        "steel": 1.08,
        "timber": 1.12,
        "mixed": 1.05
    }
    
    # Coefficients façade
    facade_coefficients = {
        "render": 0.95,
        "brick": 1.00,
        "cladding": 1.02,
        "stone": 1.15,
        "curtain_wall": 1.20,
        "glass": 1.18,
        "composite": 1.05,
        "panels": 0.98
    }
    
    project_type = parsed_input.get("project_type") or "housing"
    quality_level = parsed_input.get("quality_level") or "standard"
    structure_type = parsed_input.get("structure_type") or "concrete"
    facade_type = parsed_input.get("facade_type") or "render"
    
    # Calcul du ratio de base
    type_ratios = base_ratios.get(project_type, base_ratios["housing"])
    base_ratio = type_ratios.get(quality_level, type_ratios["standard"])
    
    # Appliquer les coefficients
    structure_coef = structure_coefficients.get(structure_type, 1.0)
    facade_coef = facade_coefficients.get(facade_type, 1.0)
    
    # Coefficient hauteur (plus d'étages = légèrement moins cher/m²)
    floors_int = int(floors) if floors else 4
    height_coef = 1.0 - (floors_int - 4) * 0.005 if floors_int > 4 else 1.0
    height_coef = max(0.92, min(1.05, height_coef))
    
    final_ratio = base_ratio * structure_coef * facade_coef * height_coef
    
    # Estimation totale
    construction_cost = surface_m2 * final_ratio
    
    # Coût parking
    parking_places = parsed_input.get("parking") or int(surface_m2 / 80)
    parking_cost = (parking_places or 0) * 22000
    
    # Total
    total_cost = construction_cost + parking_cost
    
    # Fourchette
    cost_min = total_cost * 0.88
    cost_max = total_cost * 1.15
    
    # Distribution des coûts
    cost_distribution = {
        "infrastructure": round(construction_cost * 0.08, 2),
        "superstructure": round(construction_cost * 0.22, 2),
        "facade_enveloppe": round(construction_cost * 0.18, 2),
        "second_oeuvre": round(construction_cost * 0.20, 2),
        "lots_techniques": round(construction_cost * 0.24, 2),
        "vrd_exterieurs": round(construction_cost * 0.05, 2),
        "aleas": round(construction_cost * 0.03, 2),
        "parking": round(parking_cost, 2)
    }
    
    # Indicateurs de risque
    risk_indicators = []
    if floors > 10:
        risk_indicators.append({"level": "medium", "message": "Hauteur importante - vérifier contraintes structurelles"})
    if structure_type == "timber" and floors > 6:
        risk_indicators.append({"level": "high", "message": "Structure bois sur grande hauteur - étude spécifique requise"})
    if quality_level == "luxury":
        risk_indicators.append({"level": "low", "message": "Niveau luxe - prévoir marge pour prestations haut de gamme"})
    if surface_m2 > 15000:
        risk_indicators.append({"level": "low", "message": "Grande surface - économies d'échelle possibles"})
    
    return {
        "estimation_id": estimation_id,
        "generated_at": now,
        "input": {
            "raw_text": parsed_input.get("raw_text", ""),
            "parsed": {
                "project_type": project_type,
                "surface_m2": surface_m2,
                "floors": floors_int,
                "structure_type": structure_type,
                "facade_type": facade_type,
                "quality_level": quality_level,
                "parking_places": parking_places,
                "ai_parsed": parsed_input.get("ai_parsed", False),
                "additional_features": parsed_input.get("additional_features", []),
                "region": parsed_input.get("region", "idf")
            }
        },
        "estimation": {
            "total_cost": round(total_cost, 2),
            "construction_cost": round(construction_cost, 2),
            "parking_cost": round(parking_cost, 2),
            "cost_per_m2": round(final_ratio, 2),
            "cost_range": {
                "min": round(cost_min, 2),
                "max": round(cost_max, 2)
            }
        },
        "cost_distribution": cost_distribution,
        "coefficients": {
            "base_ratio": base_ratio,
            "structure": structure_coef,
            "facade": facade_coef,
            "height": round(height_coef, 3),
            "final_ratio": round(final_ratio, 2)
        },
        "risk_indicators": risk_indicators,
        "confidence": "high" if parsed_input.get("ai_parsed") else ("medium" if surface_m2 and floors_int else "low")
    }


async def save_instant_estimation(project_id: Optional[str], estimation: Dict) -> Dict:
    """Sauvegarde une estimation instantanée"""
    
    record = {
        "id": estimation["estimation_id"],
        "project_id": project_id,
        **estimation,
        "saved_at": now_iso()
    }
    
    await db.instant_estimations.insert_one(record)
    record.pop("_id", None)
    
    return record
