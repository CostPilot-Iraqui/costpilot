# /app/backend/services/plan_analysis.py
# Service d'analyse automatique des plans de construction avec GPT Vision

import os
import sys
import base64
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso

from dotenv import load_dotenv
load_dotenv()

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Prompts pour l'analyse de plans
PLAN_ANALYSIS_SYSTEM_PROMPT = """Tu es un expert en économie de la construction et en lecture de plans architecturaux.
Ton rôle est d'analyser des plans de bâtiments (PDF, PNG, JPG) pour en extraire des informations précises.

Tu dois identifier et mesurer :
1. Les pièces (chambres, séjour, cuisine, salles de bain, etc.)
2. Les murs porteurs et cloisons
3. Les circulations (couloirs, escaliers, halls)
4. Les ouvertures (portes, fenêtres)
5. L'échelle du plan si indiquée

Pour chaque élément détecté, fournis :
- Le type d'élément
- Les dimensions estimées (en mètres)
- La surface calculée (en m²)
- Un niveau de confiance (0-100%)

IMPORTANT: Réponds UNIQUEMENT en JSON valide avec cette structure exacte :
{
  "scale_detected": "1:100" ou null si non détecté,
  "total_surface_m2": nombre,
  "rooms": [
    {
      "id": "room_1",
      "type": "chambre|sejour|cuisine|sdb|wc|bureau|circulation|rangement|autre",
      "name": "Chambre 1",
      "estimated_length_m": nombre,
      "estimated_width_m": nombre,
      "surface_m2": nombre,
      "confidence_percent": nombre
    }
  ],
  "walls": [
    {
      "id": "wall_1",
      "type": "porteur|cloison",
      "estimated_length_m": nombre,
      "estimated_thickness_cm": nombre,
      "confidence_percent": nombre
    }
  ],
  "openings": [
    {
      "id": "opening_1",
      "type": "porte|fenetre|baie",
      "estimated_width_m": nombre,
      "estimated_height_m": nombre,
      "confidence_percent": nombre
    }
  ],
  "circulation_ratio_percent": nombre,
  "summary": {
    "habitable_surface_m2": nombre,
    "circulation_surface_m2": nombre,
    "technical_surface_m2": nombre,
    "room_count": nombre,
    "opening_count": nombre
  },
  "notes": ["observation 1", "observation 2"],
  "overall_confidence_percent": nombre
}"""

PLAN_ANALYSIS_USER_PROMPT = """Analyse ce plan de construction et extrais toutes les informations sur les pièces, murs et ouvertures.

Si tu détectes une échelle sur le plan, utilise-la pour calculer les dimensions réelles.
Sinon, estime les dimensions en te basant sur les proportions standard (hauteur de porte 2.10m, largeur de fenêtre standard, etc.).

Fournis une analyse complète en JSON avec les surfaces de chaque pièce et un résumé global."""


async def analyze_plan_with_ai(
    image_base64: str,
    project_id: str,
    filename: str,
    mime_type: str = "image/png"
) -> Dict[str, Any]:
    """Analyse un plan de construction avec GPT Vision"""
    
    analysis_id = generate_uuid()
    now = now_iso()
    
    print(f"[Plan Analysis] Starting analysis for {filename}")
    print(f"[Plan Analysis] Image size: {len(image_base64)} chars")
    print(f"[Plan Analysis] MIME type: {mime_type}")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
        
        print(f"[Plan Analysis] Key present: {bool(EMERGENT_LLM_KEY)}")
        
        # Initialiser le chat avec GPT Vision
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"plan_analysis_{analysis_id}",
            system_message=PLAN_ANALYSIS_SYSTEM_PROMPT
        ).with_model("openai", "gpt-4o")
        
        print("[Plan Analysis] Creating ImageContent...")
        # Créer le contenu image
        image_content = ImageContent(image_base64=image_base64)
        
        print("[Plan Analysis] Creating message with image...")
        # Créer le message avec l'image - utiliser file_contents pas image_contents
        user_message = UserMessage(
            text=PLAN_ANALYSIS_USER_PROMPT,
            file_contents=[image_content]
        )
        
        print("[Plan Analysis] Sending to GPT Vision...")
        # Envoyer et recevoir la réponse
        response = await chat.send_message(user_message)
        
        print(f"[Plan Analysis] Got response: {response[:200]}...")
        
        # Parser la réponse JSON
        # Nettoyer la réponse si elle contient des marqueurs de code
        json_str = response
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        try:
            analysis_data = json.loads(json_str.strip())
            print(f"[Plan Analysis] Parsed JSON successfully, {len(analysis_data.get('rooms',[]))} rooms found")
        except json.JSONDecodeError as je:
            print(f"[Plan Analysis] JSON parse error: {je}")
            # Si le parsing échoue, créer une structure de base
            analysis_data = {
                "scale_detected": None,
                "total_surface_m2": 0,
                "rooms": [],
                "walls": [],
                "openings": [],
                "circulation_ratio_percent": 15,
                "summary": {
                    "habitable_surface_m2": 0,
                    "circulation_surface_m2": 0,
                    "technical_surface_m2": 0,
                    "room_count": 0,
                    "opening_count": 0
                },
                "notes": ["Analyse partielle - réponse non structurée"],
                "overall_confidence_percent": 30,
                "raw_response": response[:500]
            }
        
        # Construire le résultat final
        result = {
            "id": analysis_id,
            "project_id": project_id,
            "type": "plan_analysis",
            "filename": filename,
            "mime_type": mime_type,
            "analysis_status": "completed",
            "ai_model": "gpt-4o",
            "scale_detected": analysis_data.get("scale_detected"),
            "total_surface_m2": analysis_data.get("total_surface_m2", 0),
            "rooms": analysis_data.get("rooms", []),
            "walls": analysis_data.get("walls", []),
            "openings": analysis_data.get("openings", []),
            "circulation_ratio_percent": analysis_data.get("circulation_ratio_percent", 15),
            "summary": analysis_data.get("summary", {}),
            "notes": analysis_data.get("notes", []),
            "overall_confidence_percent": analysis_data.get("overall_confidence_percent", 50),
            "created_at": now,
            "updated_at": now
        }
        
        # Sauvegarder dans la base de données
        await db.plan_analyses.insert_one(result)
        result.pop('_id', None)
        
        return result
        
    except Exception as e:
        # En cas d'erreur, créer un enregistrement d'échec
        print(f"[Plan Analysis] ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        error_result = {
            "id": analysis_id,
            "project_id": project_id,
            "type": "plan_analysis",
            "filename": filename,
            "analysis_status": "failed",
            "error": str(e),
            "rooms": [],
            "walls": [],
            "openings": [],
            "summary": {},
            "overall_confidence_percent": 0,
            "created_at": now,
            "updated_at": now
        }
        
        await db.plan_analyses.insert_one(error_result)
        error_result.pop('_id', None)
        
        return error_result


async def get_plan_analyses(project_id: str) -> List[Dict]:
    """Récupère toutes les analyses de plans d'un projet"""
    analyses = await db.plan_analyses.find(
        {"project_id": project_id},
        {"_id": 0}
    ).to_list(100)
    return sorted(analyses, key=lambda x: x.get("created_at", ""), reverse=True)


async def get_plan_analysis(analysis_id: str) -> Optional[Dict]:
    """Récupère une analyse de plan spécifique"""
    return await db.plan_analyses.find_one(
        {"id": analysis_id},
        {"_id": 0}
    )


async def update_plan_analysis(
    analysis_id: str,
    updates: Dict[str, Any]
) -> Optional[Dict]:
    """Met à jour une analyse de plan (corrections manuelles)"""
    updates["updated_at"] = now_iso()
    
    await db.plan_analyses.update_one(
        {"id": analysis_id},
        {"$set": updates}
    )
    
    return await get_plan_analysis(analysis_id)


async def recalculate_surfaces(analysis_id: str) -> Optional[Dict]:
    """Recalcule les surfaces à partir des pièces"""
    analysis = await get_plan_analysis(analysis_id)
    if not analysis:
        return None
    
    rooms = analysis.get("rooms", [])
    
    # Recalculer les surfaces
    habitable = sum(r.get("surface_m2", 0) for r in rooms if r.get("type") not in ["circulation", "rangement"])
    circulation = sum(r.get("surface_m2", 0) for r in rooms if r.get("type") == "circulation")
    technical = sum(r.get("surface_m2", 0) for r in rooms if r.get("type") == "rangement")
    total = habitable + circulation + technical
    
    circulation_ratio = (circulation / total * 100) if total > 0 else 15
    
    updates = {
        "total_surface_m2": total,
        "circulation_ratio_percent": round(circulation_ratio, 1),
        "summary": {
            "habitable_surface_m2": round(habitable, 2),
            "circulation_surface_m2": round(circulation, 2),
            "technical_surface_m2": round(technical, 2),
            "room_count": len(rooms),
            "opening_count": len(analysis.get("openings", []))
        }
    }
    
    return await update_plan_analysis(analysis_id, updates)


async def delete_plan_analysis(analysis_id: str) -> bool:
    """Supprime une analyse de plan"""
    result = await db.plan_analyses.delete_one({"id": analysis_id})
    return result.deleted_count > 0
