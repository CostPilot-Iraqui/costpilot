# /app/backend/routers/professional_tools.py
# Routes API pour les outils professionnels avancés

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
from pydantic import BaseModel
import base64
import io

import sys
sys.path.insert(0, '/app/backend')

from utils.database import db
from utils.helpers import security, generate_uuid, now_iso
from services import plan_analysis, report_generator, program_generator
import jwt
import os

router = APIRouter(tags=["Professional Tools"])

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
# PLAN ANALYSIS ROUTES
# =============================================================================

class PlanAnalysisRequest(BaseModel):
    image_base64: str
    filename: str
    mime_type: str = "image/png"

@router.post("/projects/{project_id}/plan-analysis/upload")
async def upload_and_analyze_plan(
    project_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload et analyse un plan de construction avec GPT Vision"""
    
    # Vérifier le type de fichier
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Type de fichier non supporté. Types acceptés: {', '.join(allowed_types)}"
        )
    
    # Lire et encoder le fichier
    content = await file.read()
    image_base64 = base64.b64encode(content).decode('utf-8')
    
    # Analyser le plan
    result = await plan_analysis.analyze_plan_with_ai(
        image_base64=image_base64,
        project_id=project_id,
        filename=file.filename,
        mime_type=file.content_type
    )
    
    return result

@router.post("/projects/{project_id}/plan-analysis/base64")
async def analyze_plan_base64(
    project_id: str,
    request: PlanAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyse un plan de construction à partir d'une image base64"""
    
    result = await plan_analysis.analyze_plan_with_ai(
        image_base64=request.image_base64,
        project_id=project_id,
        filename=request.filename,
        mime_type=request.mime_type
    )
    
    return result

@router.get("/projects/{project_id}/plan-analysis")
async def get_plan_analyses(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère toutes les analyses de plans d'un projet"""
    return await plan_analysis.get_plan_analyses(project_id)

@router.get("/projects/{project_id}/plan-analysis/{analysis_id}")
async def get_plan_analysis_detail(
    project_id: str,
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère une analyse de plan spécifique"""
    result = await plan_analysis.get_plan_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return result

class PlanAnalysisUpdate(BaseModel):
    rooms: Optional[list] = None
    walls: Optional[list] = None
    openings: Optional[list] = None
    notes: Optional[list] = None

@router.put("/projects/{project_id}/plan-analysis/{analysis_id}")
async def update_plan_analysis(
    project_id: str,
    analysis_id: str,
    updates: PlanAnalysisUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Met à jour une analyse de plan (corrections manuelles)"""
    update_data = updates.dict(exclude_none=True)
    result = await plan_analysis.update_plan_analysis(analysis_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return result

@router.post("/projects/{project_id}/plan-analysis/{analysis_id}/recalculate")
async def recalculate_plan_surfaces(
    project_id: str,
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Recalcule les surfaces après corrections"""
    result = await plan_analysis.recalculate_surfaces(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return result

@router.delete("/projects/{project_id}/plan-analysis/{analysis_id}")
async def delete_plan_analysis(
    project_id: str,
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Supprime une analyse de plan"""
    deleted = await plan_analysis.delete_plan_analysis(analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return {"message": "Analyse supprimée"}


# =============================================================================
# REPORT GENERATION ROUTES
# =============================================================================

@router.post("/projects/{project_id}/reports/generate")
async def generate_full_report(
    project_id: str,
    format: str = Query("pdf", enum=["pdf", "excel"]),
    current_user: dict = Depends(get_current_user)
):
    """Génère un rapport professionnel complet"""
    
    result = await report_generator.generate_project_report(project_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Retourner le PDF
    if format == "pdf":
        return Response(
            content=result["pdf_data"],
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=rapport_projet_{project_id[:8]}.pdf"
            }
        )
    
    return result

@router.get("/projects/{project_id}/reports")
async def list_project_reports(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Liste les rapports générés pour un projet"""
    reports = await db.reports.find(
        {"project_id": project_id},
        {"_id": 0}
    ).to_list(50)
    return reports


# =============================================================================
# PROGRAM GENERATOR ROUTES
# =============================================================================

class ProgramRequest(BaseModel):
    land_surface_m2: float
    plu_zone: str = "UB"
    building_type: str = "housing"
    quality_level: str = "standard"
    specific_requirements: Optional[Dict] = None

@router.post("/projects/{project_id}/program/generate")
async def generate_program(
    project_id: str,
    request: ProgramRequest,
    current_user: dict = Depends(get_current_user)
):
    """Génère un programme immobilier automatiquement"""
    
    result = await program_generator.generate_building_program(
        project_id=project_id,
        land_surface_m2=request.land_surface_m2,
        plu_zone=request.plu_zone,
        building_type=request.building_type,
        quality_level=request.quality_level,
        specific_requirements=request.specific_requirements
    )
    
    return result

@router.get("/projects/{project_id}/program")
async def get_program(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère le programme d'un projet"""
    program = await program_generator.get_program(project_id)
    if not program:
        raise HTTPException(status_code=404, detail="Programme non trouvé")
    return program

class ProgramUpdate(BaseModel):
    surfaces: Optional[Dict] = None
    units: Optional[Dict] = None
    parking: Optional[Dict] = None

@router.put("/projects/{project_id}/program")
async def update_program(
    project_id: str,
    updates: ProgramUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Met à jour un programme"""
    update_data = updates.dict(exclude_none=True)
    result = await program_generator.update_program(project_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Programme non trouvé")
    return result

@router.get("/plu-zones")
async def list_plu_zones(
    current_user: dict = Depends(get_current_user)
):
    """Liste les zones PLU disponibles"""
    from services.program_generator import PLU_ZONES
    return [
        {"code": code, **data}
        for code, data in PLU_ZONES.items()
    ]



# =============================================================================
# PROFESSIONAL REPORT PDF
# =============================================================================

@router.get("/projects/{project_id}/professional-report/pdf")
async def generate_professional_report_pdf(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Génère un rapport PDF professionnel complet pour un projet"""
    
    # Récupérer le projet
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Générer le rapport
    result = await report_generator.generate_project_report(project_id)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    pdf_data = result.get("pdf_data")
    if not pdf_data:
        raise HTTPException(status_code=500, detail="Erreur génération PDF")
    
    project_name = project.get("project_name", "projet").replace(" ", "_")
    
    return StreamingResponse(
        io.BytesIO(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=rapport_{project_name}.pdf"}
    )
