# /app/backend/routers/project_modules.py
# Router pour tous les modules projet: métré, analyse, gestion, exports

import sys
import io
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso, security
from services import quantity_takeoff, project_analysis, project_management, export_service
import jwt
import os

router = APIRouter(tags=["Project Modules"])

JWT_SECRET = os.environ.get("JWT_SECRET")

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=["HS256"])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")


# =============================================================================
# QUANTITY TAKEOFF (MÉTRÉ AUTOMATIQUE)
# =============================================================================

class QuantityTakeoffRequest(BaseModel):
    surface_m2: Optional[float] = None
    floors: Optional[int] = 4
    quality_level: Optional[str] = "standard"

@router.post("/projects/{project_id}/quantity-takeoff/generate")
async def generate_takeoff(
    project_id: str,
    request: QuantityTakeoffRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """Génère un métré automatique pour le projet"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    surface = request.surface_m2 if request and request.surface_m2 else project.get("target_surface_m2", 2000)
    floors = request.floors if request else 4
    quality = request.quality_level if request else project.get("quality_level", "standard")
    
    result = await quantity_takeoff.generate_quantity_takeoff(
        project_id, surface, floors, quality
    )
    return result

@router.get("/projects/{project_id}/quantity-takeoff")
async def get_takeoff(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère le dernier métré du projet"""
    result = await quantity_takeoff.get_quantity_takeoff(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Aucun métré trouvé")
    return result

@router.get("/projects/{project_id}/quantity-takeoffs")
async def list_takeoffs(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Liste tous les métrés du projet"""
    return await quantity_takeoff.get_quantity_takeoffs(project_id)

class UpdateLotRequest(BaseModel):
    lot_code: str
    quantity: float

@router.put("/projects/{project_id}/quantity-takeoff/{takeoff_id}/lot")
async def update_lot(
    project_id: str,
    takeoff_id: str,
    request: UpdateLotRequest,
    current_user: dict = Depends(get_current_user)
):
    """Met à jour la quantité d'un lot"""
    result = await quantity_takeoff.update_lot_quantity(
        takeoff_id, request.lot_code, request.quantity
    )
    if not result:
        raise HTTPException(status_code=404, detail="Métré non trouvé")
    return result


# =============================================================================
# PROJECT ANALYSIS (DIAGNOSTIC, ALERTES, SCÉNARIOS)
# =============================================================================

@router.get("/projects/{project_id}/diagnostic")
async def get_diagnostic(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Génère un diagnostic IA du projet"""
    result = await project_analysis.generate_ai_diagnostic(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/projects/{project_id}/alerts")
async def get_alerts(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les alertes du projet"""
    return await project_analysis.get_project_alerts(project_id)

class ScenarioRequest(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

@router.post("/projects/{project_id}/scenarios")
async def create_scenario(
    project_id: str,
    request: ScenarioRequest,
    current_user: dict = Depends(get_current_user)
):
    """Crée un scénario pour le projet"""
    result = await project_analysis.create_scenario(
        project_id, request.name, request.description, request.parameters
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/projects/{project_id}/scenarios")
async def list_scenarios(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Liste les scénarios du projet"""
    return await project_analysis.get_scenarios(project_id)

@router.get("/projects/{project_id}/arbitrage")
async def get_arbitrage(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Génère des suggestions d'arbitrage"""
    result = await project_analysis.generate_arbitrage_suggestions(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/projects/{project_id}/feasibility")
async def get_feasibility(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Génère une analyse de faisabilité"""
    result = await project_analysis.generate_feasibility_analysis(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# =============================================================================
# PROJECT MANAGEMENT (PLANNING, ÉQUIPE, JOURNAL)
# =============================================================================

@router.get("/projects/{project_id}/planning")
async def get_planning(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère le planning du projet"""
    result = await project_management.get_project_planning(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

class PhaseUpdateRequest(BaseModel):
    phase_id: str
    progress: int
    status: Optional[str] = None

@router.put("/projects/{project_id}/planning/phase")
async def update_phase(
    project_id: str,
    request: PhaseUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Met à jour la progression d'une phase"""
    result = await project_management.update_phase_progress(
        project_id, request.phase_id, request.progress, request.status
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/projects/{project_id}/team")
async def get_team(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère l'équipe du projet"""
    return await project_management.get_project_team(project_id)

class TeamMemberRequest(BaseModel):
    name: str
    role_code: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

@router.post("/projects/{project_id}/team/member")
async def add_member(
    project_id: str,
    request: TeamMemberRequest,
    current_user: dict = Depends(get_current_user)
):
    """Ajoute un membre à l'équipe"""
    return await project_management.add_team_member(
        project_id, request.name, request.role_code,
        request.company, request.email, request.phone
    )

@router.delete("/projects/{project_id}/team/member/{member_id}")
async def remove_member(
    project_id: str,
    member_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retire un membre de l'équipe"""
    return await project_management.remove_team_member(project_id, member_id)

@router.get("/projects/{project_id}/decisions")
async def get_decisions(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère le journal des décisions"""
    return await project_management.get_decision_journal(project_id)

class DecisionRequest(BaseModel):
    title: str
    description: str
    category: str
    impact: Optional[str] = "medium"
    decision_maker: Optional[str] = None
    participants: Optional[List[str]] = None

@router.post("/projects/{project_id}/decisions")
async def add_decision(
    project_id: str,
    request: DecisionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Ajoute une décision au journal"""
    return await project_management.add_decision(
        project_id, request.title, request.description,
        request.category, request.impact, request.decision_maker,
        request.participants
    )


# =============================================================================
# EXPORTS
# =============================================================================

@router.get("/projects/{project_id}/exports")
async def list_exports(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Liste les exports disponibles"""
    return await export_service.get_available_exports(project_id)

@router.get("/projects/{project_id}/export/csv")
async def export_csv(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Exporte les données projet en CSV"""
    result = await export_service.export_project_to_excel(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return StreamingResponse(
        io.BytesIO(result["content"].encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

@router.get("/projects/{project_id}/export/dpgf")
async def export_dpgf(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Exporte le DPGF en CSV"""
    result = await export_service.export_dpgf_to_excel(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return StreamingResponse(
        io.BytesIO(result["content"].encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

@router.get("/projects/{project_id}/export/client-report")
async def export_client_report(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Génère le rapport client en PDF"""
    result = await export_service.generate_client_report_pdf(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return StreamingResponse(
        io.BytesIO(result["pdf_data"]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

@router.get("/projects/{project_id}/export/technical-report")
async def export_technical_report(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Génère le rapport technique en PDF"""
    result = await export_service.generate_technical_report_pdf(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return StreamingResponse(
        io.BytesIO(result["pdf_data"]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )
