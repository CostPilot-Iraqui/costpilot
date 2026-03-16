# /app/backend/services/project_management.py
# Services de gestion de projet: planning, équipe, journal de décisions

import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso


async def get_project_planning(project_id: str) -> Dict:
    """Récupère ou génère le planning d'un projet"""
    
    # Chercher un planning existant
    planning = await db.project_plannings.find_one(
        {"project_id": project_id},
        {"_id": 0}
    )
    
    if planning:
        return planning
    
    # Générer un planning par défaut
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    return await generate_default_planning(project_id, project)


async def generate_default_planning(project_id: str, project: Dict) -> Dict:
    """Génère un planning par défaut basé sur le projet"""
    
    planning_id = generate_uuid()
    now = now_iso()
    today = datetime.now(timezone.utc)
    
    surface = project.get("target_surface_m2", 0) or 2000
    
    # Durées estimées en mois selon la surface
    if surface < 1000:
        duration_months = 12
    elif surface < 3000:
        duration_months = 18
    elif surface < 10000:
        duration_months = 24
    else:
        duration_months = 36
    
    # Phases du projet
    phases = [
        {
            "id": generate_uuid(),
            "name": "Études préliminaires",
            "code": "ESQ",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
            "duration_days": 30,
            "progress": 0,
            "status": "not_started",
            "deliverables": ["Esquisse", "Estimation préliminaire", "Note de faisabilité"]
        },
        {
            "id": generate_uuid(),
            "name": "Avant-projet sommaire",
            "code": "APS",
            "start_date": (today + timedelta(days=30)).isoformat(),
            "end_date": (today + timedelta(days=75)).isoformat(),
            "duration_days": 45,
            "progress": 0,
            "status": "not_started",
            "deliverables": ["Plans APS", "Estimation APS", "Planning prévisionnel"]
        },
        {
            "id": generate_uuid(),
            "name": "Avant-projet définitif",
            "code": "APD",
            "start_date": (today + timedelta(days=75)).isoformat(),
            "end_date": (today + timedelta(days=135)).isoformat(),
            "duration_days": 60,
            "progress": 0,
            "status": "not_started",
            "deliverables": ["Plans APD", "CCTP provisoire", "Estimation détaillée"]
        },
        {
            "id": generate_uuid(),
            "name": "Permis de construire",
            "code": "PC",
            "start_date": (today + timedelta(days=135)).isoformat(),
            "end_date": (today + timedelta(days=255)).isoformat(),
            "duration_days": 120,
            "progress": 0,
            "status": "not_started",
            "deliverables": ["Dossier PC", "Obtention permis"]
        },
        {
            "id": generate_uuid(),
            "name": "Études d'exécution",
            "code": "PRO/EXE",
            "start_date": (today + timedelta(days=255)).isoformat(),
            "end_date": (today + timedelta(days=315)).isoformat(),
            "duration_days": 60,
            "progress": 0,
            "status": "not_started",
            "deliverables": ["DCE complet", "Plans EXE", "Synthèse"]
        },
        {
            "id": generate_uuid(),
            "name": "Consultation entreprises",
            "code": "ACT",
            "start_date": (today + timedelta(days=315)).isoformat(),
            "end_date": (today + timedelta(days=375)).isoformat(),
            "duration_days": 60,
            "progress": 0,
            "status": "not_started",
            "deliverables": ["Analyse des offres", "Marchés signés"]
        },
        {
            "id": generate_uuid(),
            "name": "Travaux",
            "code": "DET",
            "start_date": (today + timedelta(days=375)).isoformat(),
            "end_date": (today + timedelta(days=375 + duration_months * 20)).isoformat(),
            "duration_days": duration_months * 20,
            "progress": 0,
            "status": "not_started",
            "deliverables": ["Réception travaux", "DOE", "DIUO"]
        }
    ]
    
    planning = {
        "id": planning_id,
        "project_id": project_id,
        "type": "project_planning",
        "phases": phases,
        "total_duration_months": duration_months + 12,  # +12 pour études
        "milestones": [
            {"name": "Validation APS", "date": (today + timedelta(days=75)).isoformat()},
            {"name": "Dépôt PC", "date": (today + timedelta(days=140)).isoformat()},
            {"name": "Obtention PC", "date": (today + timedelta(days=255)).isoformat()},
            {"name": "Démarrage travaux", "date": (today + timedelta(days=375)).isoformat()},
            {"name": "Livraison", "date": (today + timedelta(days=375 + duration_months * 20)).isoformat()},
        ],
        "created_at": now,
        "updated_at": now
    }
    
    await db.project_plannings.insert_one(planning)
    planning.pop("_id", None)
    
    return planning


async def update_phase_progress(
    project_id: str,
    phase_id: str,
    progress: int,
    status: str = None
) -> Dict:
    """Met à jour la progression d'une phase"""
    
    planning = await db.project_plannings.find_one({"project_id": project_id})
    if not planning:
        return {"error": "Planning non trouvé"}
    
    phases = planning.get("phases", [])
    for phase in phases:
        if phase["id"] == phase_id:
            phase["progress"] = min(100, max(0, progress))
            if status:
                phase["status"] = status
            elif progress >= 100:
                phase["status"] = "completed"
            elif progress > 0:
                phase["status"] = "in_progress"
            break
    
    await db.project_plannings.update_one(
        {"project_id": project_id},
        {"$set": {"phases": phases, "updated_at": now_iso()}}
    )
    
    return await db.project_plannings.find_one({"project_id": project_id}, {"_id": 0})


async def get_project_team(project_id: str) -> Dict:
    """Récupère l'équipe du projet"""
    
    team = await db.project_teams.find_one(
        {"project_id": project_id},
        {"_id": 0}
    )
    
    if not team:
        # Créer une équipe par défaut
        team = {
            "id": generate_uuid(),
            "project_id": project_id,
            "members": [],
            "roles": [
                {"code": "MOA", "name": "Maître d'ouvrage", "required": True},
                {"code": "MOE", "name": "Maître d'œuvre", "required": True},
                {"code": "ECO", "name": "Économiste", "required": True},
                {"code": "BET_S", "name": "BET Structure", "required": True},
                {"code": "BET_F", "name": "BET Fluides", "required": True},
                {"code": "ARCHI", "name": "Architecte", "required": True},
                {"code": "OPC", "name": "OPC", "required": False},
                {"code": "SPS", "name": "Coordonnateur SPS", "required": False},
                {"code": "CT", "name": "Contrôleur Technique", "required": False},
            ],
            "created_at": now_iso()
        }
        await db.project_teams.insert_one(team)
        team.pop("_id", None)
    
    return team


async def add_team_member(
    project_id: str,
    name: str,
    role_code: str,
    company: str = None,
    email: str = None,
    phone: str = None
) -> Dict:
    """Ajoute un membre à l'équipe projet"""
    
    member = {
        "id": generate_uuid(),
        "name": name,
        "role_code": role_code,
        "company": company,
        "email": email,
        "phone": phone,
        "added_at": now_iso()
    }
    
    await db.project_teams.update_one(
        {"project_id": project_id},
        {"$push": {"members": member}, "$set": {"updated_at": now_iso()}},
        upsert=True
    )
    
    return await get_project_team(project_id)


async def remove_team_member(project_id: str, member_id: str) -> Dict:
    """Retire un membre de l'équipe"""
    
    await db.project_teams.update_one(
        {"project_id": project_id},
        {"$pull": {"members": {"id": member_id}}, "$set": {"updated_at": now_iso()}}
    )
    
    return await get_project_team(project_id)


async def get_decision_journal(project_id: str) -> List[Dict]:
    """Récupère le journal des décisions du projet"""
    
    cursor = db.decision_journal.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("date", -1)
    
    return await cursor.to_list(length=100)


async def add_decision(
    project_id: str,
    title: str,
    description: str,
    category: str,
    impact: str = "medium",
    decision_maker: str = None,
    participants: List[str] = None
) -> Dict:
    """Ajoute une décision au journal"""
    
    decision = {
        "id": generate_uuid(),
        "project_id": project_id,
        "title": title,
        "description": description,
        "category": category,
        "impact": impact,
        "decision_maker": decision_maker,
        "participants": participants or [],
        "date": now_iso(),
        "status": "active"
    }
    
    await db.decision_journal.insert_one(decision)
    decision.pop("_id", None)
    
    return decision


async def update_decision_status(
    decision_id: str,
    status: str,
    notes: str = None
) -> Dict:
    """Met à jour le statut d'une décision"""
    
    update = {"status": status, "updated_at": now_iso()}
    if notes:
        update["notes"] = notes
    
    await db.decision_journal.update_one(
        {"id": decision_id},
        {"$set": update}
    )
    
    return await db.decision_journal.find_one({"id": decision_id}, {"_id": 0})
