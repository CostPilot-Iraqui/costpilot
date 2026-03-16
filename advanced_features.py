# /app/backend/routers/advanced_features.py
# Routes pour les fonctionnalités avancées de CostPilot

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import io

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso, security
from services import bim_ifc_service, instant_estimation, cctp_generator, carbon_analysis, program_generator, plan_analysis, workflow_integrator
from services.report_generator import generate_plan_analysis_pdf
import jwt
import os
import base64

router = APIRouter(tags=["Advanced Features"])

JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    JWT_SECRET = 'dev-secret-key'


async def get_current_user(credentials=Depends(security)) -> dict:
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
# BIM IFC IMPORT
# =============================================================================

@router.post("/projects/{project_id}/ifc/upload")
async def upload_ifc_file(
    project_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload et analyse un fichier IFC"""
    
    if not file.filename.lower().endswith('.ifc'):
        raise HTTPException(status_code=400, detail="Format de fichier invalide. Seuls les fichiers .ifc sont acceptés.")
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    content = await file.read()
    
    # Parser le fichier IFC
    analysis = await bim_ifc_service.parse_ifc_file(content, file.filename)
    
    # Générer l'estimation de coûts
    project_type = project.get("project_usage", "housing")
    cost_estimation = await bim_ifc_service.generate_cost_from_ifc(
        analysis["analysis_id"],
        analysis["quantities"],
        project_type
    )
    
    # Sauvegarder
    result = await bim_ifc_service.save_ifc_analysis(project_id, analysis, cost_estimation)
    
    return result


@router.get("/projects/{project_id}/ifc/analyses")
async def get_ifc_analyses(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les analyses IFC d'un projet"""
    analyses = await bim_ifc_service.get_ifc_analyses(project_id)
    return analyses


@router.get("/projects/{project_id}/ifc/{analysis_id}")
async def get_ifc_analysis(
    project_id: str,
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère une analyse IFC spécifique"""
    analysis = await db.ifc_analyses.find_one(
        {"id": analysis_id, "project_id": project_id},
        {"_id": 0}
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return analysis


# =============================================================================
# AI INSTANT ESTIMATION
# =============================================================================

class InstantEstimationRequest(BaseModel):
    description: str
    project_id: Optional[str] = None

@router.post("/instant-estimation")
async def create_instant_estimation(
    request: InstantEstimationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Génère une estimation instantanée à partir d'une description en langage naturel"""
    
    if not request.description or len(request.description) < 10:
        raise HTTPException(status_code=400, detail="Description trop courte")
    
    # Parser la description avec l'IA
    parsed = await instant_estimation.parse_with_ai(request.description)
    
    # Générer l'estimation
    estimation = await instant_estimation.generate_instant_estimation(parsed)
    
    # Sauvegarder si un projet est associé
    if request.project_id:
        await instant_estimation.save_instant_estimation(request.project_id, estimation)
    
    return estimation


@router.get("/instant-estimation/history")
async def get_estimation_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Récupère l'historique des estimations instantanées"""
    estimations = await db.instant_estimations.find(
        {},
        {"_id": 0}
    ).sort("generated_at", -1).limit(limit).to_list(limit)
    return estimations


# =============================================================================
# CCTP GENERATION
# =============================================================================

class CCTPRequest(BaseModel):
    structure_type: str = "concrete"
    facade_type: str = "render"
    selected_lots: Optional[List[str]] = None

@router.post("/projects/{project_id}/cctp/generate")
async def generate_cctp(
    project_id: str,
    request: CCTPRequest,
    current_user: dict = Depends(get_current_user)
):
    """Génère un CCTP pour un projet"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    cctp_content = await cctp_generator.generate_cctp(
        project,
        request.structure_type,
        request.facade_type,
        request.selected_lots
    )
    
    await cctp_generator.save_cctp(project_id, cctp_content)
    
    return cctp_content


@router.get("/projects/{project_id}/cctp/{cctp_id}/pdf")
async def export_cctp_pdf(
    project_id: str,
    cctp_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Exporte un CCTP en PDF"""
    
    cctp = await db.cctp_documents.find_one(
        {"id": cctp_id, "project_id": project_id},
        {"_id": 0}
    )
    if not cctp:
        raise HTTPException(status_code=404, detail="CCTP non trouvé")
    
    pdf_bytes = await cctp_generator.generate_cctp_pdf(cctp)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CCTP_{project_id}.pdf"}
    )


@router.get("/projects/{project_id}/cctp")
async def get_project_cctps(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les CCTP d'un projet"""
    cctps = await db.cctp_documents.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("generated_at", -1).to_list(100)
    return cctps


@router.get("/cctp/lots")
async def get_cctp_lots(current_user: dict = Depends(get_current_user)):
    """Récupère la liste des lots CCTP disponibles"""
    return cctp_generator.CCTP_LOTS


# =============================================================================
# CARBON ANALYSIS
# =============================================================================

class CarbonAnalysisRequest(BaseModel):
    structure_type: str = "concrete"
    facade_type: str = "brick"
    insulation_type: str = "mineral_wool"

@router.post("/projects/{project_id}/carbon/analyze")
async def analyze_carbon(
    project_id: str,
    request: CarbonAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyse l'empreinte carbone d'un projet"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    analysis = await carbon_analysis.analyze_project_carbon(
        project_id,
        project,
        request.structure_type,
        request.facade_type,
        request.insulation_type
    )
    
    await carbon_analysis.save_carbon_analysis(project_id, analysis)
    
    return analysis


@router.get("/projects/{project_id}/carbon")
async def get_carbon_analyses(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les analyses carbone d'un projet"""
    analyses = await carbon_analysis.get_carbon_analyses(project_id)
    return analyses


@router.get("/carbon/factors")
async def get_carbon_factors(current_user: dict = Depends(get_current_user)):
    """Récupère les facteurs d'émission carbone"""
    return carbon_analysis.CARBON_FACTORS


@router.get("/carbon/re2020-thresholds")
async def get_re2020_thresholds(current_user: dict = Depends(get_current_user)):
    """Récupère les seuils RE2020"""
    return carbon_analysis.RE2020_THRESHOLDS


# =============================================================================
# ENHANCED PROGRAM GENERATOR
# =============================================================================

class ProgramGeneratorRequest(BaseModel):
    description: str
    project_type: str = "housing"
    target_units: Optional[int] = None

@router.post("/program/generate-from-brief")
async def generate_program_from_brief(
    request: ProgramGeneratorRequest,
    current_user: dict = Depends(get_current_user)
):
    """Génère un programme à partir d'un brief"""
    
    # Ratios par type de programme
    housing_typologies = {
        "T1": {"surface": 30, "ratio": 0.10},
        "T2": {"surface": 45, "ratio": 0.25},
        "T3": {"surface": 65, "ratio": 0.35},
        "T4": {"surface": 85, "ratio": 0.20},
        "T5": {"surface": 105, "ratio": 0.10}
    }
    
    target_units = request.target_units
    if not target_units:
        # Extraire du brief
        import re
        match = re.search(r'(\d+)\s*(?:logements?|appartements?|units?)', request.description.lower())
        if match:
            target_units = int(match.group(1))
        else:
            target_units = 50  # Défaut
    
    # Générer la distribution des typologies
    program = {
        "id": generate_uuid(),
        "brief": request.description,
        "project_type": request.project_type,
        "target_units": target_units,
        "generated_at": now_iso()
    }
    
    if request.project_type == "housing":
        typologies = []
        total_shab = 0
        
        for typo, data in housing_typologies.items():
            count = round(target_units * data["ratio"])
            if count > 0:
                typo_shab = count * data["surface"]
                total_shab += typo_shab
                typologies.append({
                    "type": typo,
                    "count": count,
                    "surface_unit": data["surface"],
                    "surface_total": typo_shab
                })
        
        # Calcul des surfaces
        circulation_ratio = 0.18
        locaux_communs = total_shab * 0.03
        
        program["typologies"] = typologies
        program["surfaces"] = {
            "shab_total": round(total_shab, 2),
            "circulations": round(total_shab * circulation_ratio, 2),
            "locaux_communs": round(locaux_communs, 2),
            "sdp_estimee": round(total_shab * (1 + circulation_ratio) + locaux_communs, 2)
        }
        program["parking"] = {
            "places_requises": target_units,
            "ratio": 1.0,
            "type_suggere": "souterrain" if target_units > 30 else "extérieur"
        }
        
    elif request.project_type == "office":
        surface_per_poste = 12
        estimated_postes = target_units if target_units else 100
        
        program["programme"] = {
            "postes_travail": estimated_postes,
            "surface_bureaux": estimated_postes * surface_per_poste,
            "salles_reunion": max(3, estimated_postes // 20),
            "surface_reunion": max(3, estimated_postes // 20) * 25,
            "accueil": 50,
            "sanitaires": estimated_postes * 2,
            "archives": estimated_postes * 3,
            "locaux_techniques": 100
        }
        total_sun = sum(program["programme"].values())
        program["surfaces"] = {
            "sun_total": total_sun,
            "circulations": round(total_sun * 0.22, 2),
            "sdp_estimee": round(total_sun * 1.25, 2)
        }
        program["parking"] = {
            "places_requises": estimated_postes // 3,
            "ratio": 0.33
        }
    
    elif request.project_type == "school":
        classes = target_units if target_units else 12
        students_per_class = 25
        
        program["programme"] = {
            "salles_classe": classes,
            "surface_classes": classes * 60,
            "cdi_mediatheque": 150,
            "salle_polyvalente": 200,
            "restauration": classes * students_per_class * 1.2,
            "administration": 100,
            "sanitaires": classes * 15,
            "vestiaires": 80,
            "locaux_techniques": 80
        }
        total = sum(program["programme"].values())
        program["surfaces"] = {
            "sun_total": total,
            "circulations": round(total * 0.25, 2),
            "sdp_estimee": round(total * 1.30, 2)
        }
        program["capacite"] = {
            "classes": classes,
            "eleves": classes * students_per_class
        }
    
    # Estimation macro
    sdp = program["surfaces"]["sdp_estimee"]
    base_ratios = {"housing": 1850, "office": 1650, "school": 1950}
    ratio = base_ratios.get(request.project_type, 1800)
    
    program["estimation_macro"] = {
        "cout_construction": round(sdp * ratio, 2),
        "cout_m2": ratio,
        "fourchette_basse": round(sdp * ratio * 0.88, 2),
        "fourchette_haute": round(sdp * ratio * 1.15, 2)
    }
    
    return program


# =============================================================================
# WORKFLOW STATUS
# =============================================================================

@router.get("/projects/{project_id}/workflow-status")
async def get_workflow_status(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère le statut du workflow économiste pour un projet"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Vérifier chaque étape
    steps = {
        "1_project": {"name": "Création projet", "status": "completed" if project else "pending"},
        "2_program": {"name": "Définition programme", "status": "pending"},
        "3_macro": {"name": "Estimation macro", "status": "pending"},
        "4_risk": {"name": "Analyse risques", "status": "pending"},
        "5_arbitration": {"name": "Arbitrage économique", "status": "pending"},
        "6_scenarios": {"name": "Comparaison scénarios", "status": "pending"},
        "7_micro": {"name": "Estimation détaillée", "status": "pending"},
        "8_dpgf": {"name": "Génération DPGF", "status": "pending"},
        "9_report": {"name": "Rapport client", "status": "pending"}
    }
    
    # Vérifier les données
    if project.get("target_surface_m2"):
        steps["2_program"]["status"] = "completed"
    
    categories = await db.macro_categories.count_documents({"project_id": project_id})
    if categories > 0:
        steps["3_macro"]["status"] = "completed"
    
    risks = await db.risk_assessments.count_documents({"project_id": project_id})
    if risks > 0:
        steps["4_risk"]["status"] = "completed"
    
    optimizations = await db.cost_optimizations.count_documents({"project_id": project_id})
    if optimizations > 0:
        steps["5_arbitration"]["status"] = "completed"
    
    scenarios = await db.multi_scenarios.count_documents({"project_id": project_id})
    if scenarios > 0:
        steps["6_scenarios"]["status"] = "completed"
    
    items = await db.micro_items.count_documents({"project_id": project_id})
    if items > 0:
        steps["7_micro"]["status"] = "completed"
    
    dpgf = await db.dpgf.count_documents({"project_id": project_id})
    if dpgf > 0:
        steps["8_dpgf"]["status"] = "completed"
    
    reports = await db.reports.count_documents({"project_id": project_id})
    if reports > 0:
        steps["9_report"]["status"] = "completed"
    
    # Calculer la progression
    completed = sum(1 for s in steps.values() if s["status"] == "completed")
    total = len(steps)
    
    return {
        "project_id": project_id,
        "steps": steps,
        "progress": {
            "completed": completed,
            "total": total,
            "percentage": round(completed / total * 100, 1)
        },
        "current_stage": project.get("current_stage", "early_feasibility")
    }



# =============================================================================
# PROGRAM GENERATOR
# =============================================================================

class ProgramRequest(BaseModel):
    land_surface_m2: float
    plu_zone: str = "UB"
    building_type: str = "housing"
    quality_level: str = "standard"
    specific_requirements: Optional[Dict[str, Any]] = None

@router.post("/projects/{project_id}/program/generate")
async def generate_program(
    project_id: str,
    request: ProgramRequest,
    current_user: dict = Depends(get_current_user)
):
    """Génère un programme immobilier automatique"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    program = await program_generator.generate_building_program(
        project_id,
        request.land_surface_m2,
        request.plu_zone,
        request.building_type,
        request.quality_level,
        request.specific_requirements
    )
    
    return program


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


@router.put("/projects/{project_id}/program")
async def update_program(
    project_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Met à jour le programme d'un projet"""
    program = await program_generator.update_program(project_id, updates)
    if not program:
        raise HTTPException(status_code=404, detail="Programme non trouvé")
    return program


@router.get("/plu-zones")
async def get_plu_zones(current_user: dict = Depends(get_current_user)):
    """Récupère les zones PLU disponibles"""
    return program_generator.PLU_ZONES


# =============================================================================
# AI PLAN READING
# =============================================================================

class PlanUploadRequest(BaseModel):
    filename: str
    mime_type: str = "image/png"
    image_data: str  # Base64 encoded

@router.post("/projects/{project_id}/plan-ai/analyze")
async def analyze_plan_with_ai(
    project_id: str,
    request: PlanUploadRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyse un plan avec l'IA GPT Vision"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Décoder et analyser
    result = await plan_analysis.analyze_plan_with_ai(
        request.image_data,
        project_id,
        request.filename,
        request.mime_type
    )
    
    return result


@router.post("/projects/{project_id}/plan-ai/upload")
async def upload_plan_for_ai_analysis(
    project_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload et analyse un plan avec l'IA"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Vérifier le type de fichier
    allowed_types = [".png", ".jpg", ".jpeg", ".pdf"]
    ext = "." + file.filename.lower().split(".")[-1]
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Format non supporté. Formats acceptés: {', '.join(allowed_types)}"
        )
    
    content = await file.read()
    image_base64 = base64.b64encode(content).decode('utf-8')
    
    # Déterminer le type MIME
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".pdf": "application/pdf"
    }
    mime_type = mime_types.get(ext, "image/png")
    
    result = await plan_analysis.analyze_plan_with_ai(
        image_base64,
        project_id,
        file.filename,
        mime_type
    )
    
    return result


@router.get("/projects/{project_id}/plan-ai/analyses")
async def get_ai_plan_analyses(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les analyses IA de plans d'un projet"""
    analyses = await plan_analysis.get_plan_analyses(project_id)
    return analyses


@router.get("/projects/{project_id}/plan-ai/{analysis_id}")
async def get_ai_plan_analysis(
    project_id: str,
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère une analyse IA de plan"""
    analysis = await plan_analysis.get_plan_analysis(analysis_id)
    if not analysis or analysis.get("project_id") != project_id:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return analysis


@router.put("/projects/{project_id}/plan-ai/{analysis_id}")
async def update_ai_plan_analysis(
    project_id: str,
    analysis_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Met à jour une analyse IA (corrections manuelles)"""
    analysis = await plan_analysis.update_plan_analysis(analysis_id, updates)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return analysis


@router.post("/projects/{project_id}/plan-ai/{analysis_id}/recalculate")
async def recalculate_plan_surfaces(
    project_id: str,
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Recalcule les surfaces d'une analyse après modifications"""
    analysis = await plan_analysis.recalculate_surfaces(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return analysis


@router.delete("/projects/{project_id}/plan-ai/{analysis_id}")
async def delete_ai_plan_analysis(
    project_id: str,
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Supprime une analyse IA de plan"""
    deleted = await plan_analysis.delete_plan_analysis(analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return {"message": "Analyse supprimée"}


@router.get("/projects/{project_id}/plan-ai/{analysis_id}/export-pdf")
async def export_plan_analysis_pdf(
    project_id: str,
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Exporte une analyse de plan en PDF professionnel"""
    
    result = await generate_plan_analysis_pdf(project_id, analysis_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return StreamingResponse(
        io.BytesIO(result["pdf_data"]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={result['filename']}"
        }
    )



# =============================================================================
# WORKFLOW INTEGRATION
# =============================================================================

@router.post("/projects/{project_id}/workflow/connect-plan")
async def connect_plan_to_workflow(
    project_id: str,
    plan_analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Connecte une analyse de plan aux quantités et estimations de coûts"""
    result = await workflow_integrator.connect_plan_to_quantities(project_id, plan_analysis_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/projects/{project_id}/workflow-status")
async def get_workflow_status(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère le statut du workflow économiste pour un projet"""
    status = await workflow_integrator.get_project_workflow_status(project_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@router.get("/projects/{project_id}/integrated-report")
async def get_integrated_report(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Génère un rapport intégré combinant toutes les analyses du projet"""
    report = await workflow_integrator.generate_integrated_report(project_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report
