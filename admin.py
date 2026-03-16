# /app/backend/routers/admin.py
# Routes d'administration pour CostPilot Senior

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import sys

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso, hash_password, security
from services import company_service
import jwt
import os

router = APIRouter(prefix="/admin", tags=["Administration"])

JWT_SECRET = os.environ.get('JWT_SECRET', 'costpilot-senior-secret-key-2024')

ADMIN_ROLES = ["administrator"]
ECONOMIST_ROLES = ["administrator", "senior_cost_manager", "economist"]


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


def require_admin(user: dict):
    """Vérifie que l'utilisateur est administrateur"""
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")


# =============================================================================
# COMPANY MANAGEMENT
# =============================================================================

class CompanyCreate(BaseModel):
    name: str
    subscription_plan: str = "starter"

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None

@router.get("/companies")
async def list_companies(current_user: dict = Depends(get_current_user)):
    """Liste toutes les entreprises (admin only)"""
    require_admin(current_user)
    companies = await company_service.get_all_companies()
    
    # Enrichir avec les stats
    result = []
    for company in companies:
        stats = await company_service.get_company_stats(company["id"])
        result.append({**company, "stats": stats})
    
    return result

@router.post("/companies")
async def create_company(
    data: CompanyCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crée une nouvelle entreprise"""
    require_admin(current_user)
    company = await company_service.create_company(
        name=data.name,
        admin_user_id=current_user["id"],
        subscription_plan=data.subscription_plan
    )
    return company

@router.get("/companies/{company_id}")
async def get_company(
    company_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère une entreprise"""
    require_admin(current_user)
    company = await company_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    
    stats = await company_service.get_company_stats(company_id)
    return {**company, "stats": stats}

@router.put("/companies/{company_id}")
async def update_company(
    company_id: str,
    data: CompanyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Met à jour une entreprise"""
    require_admin(current_user)
    
    updates = data.dict(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune modification")
    
    # Si changement de plan
    if "subscription_plan" in updates:
        company = await company_service.update_subscription(
            company_id,
            updates["subscription_plan"],
            updates.get("subscription_status", "active")
        )
    else:
        company = await company_service.update_company(company_id, updates)
    
    if not company:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    
    return company

@router.get("/companies/{company_id}/stats")
async def get_company_stats(
    company_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les statistiques d'une entreprise"""
    require_admin(current_user)
    stats = await company_service.get_company_stats(company_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    return stats

# =============================================================================
# USER MANAGEMENT
# =============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "viewer"
    company_id: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    company_id: Optional[str] = None
    is_active: Optional[bool] = None

class UserInvite(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "economist"

@router.get("/users")
async def list_users(
    company_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Liste tous les utilisateurs"""
    require_admin(current_user)
    
    query = {}
    if company_id:
        query["company_id"] = company_id
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@router.post("/users")
async def create_user(
    data: UserCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crée un nouvel utilisateur"""
    require_admin(current_user)
    
    # Vérifier si l'email existe
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    # Déterminer company_id
    company_id = data.company_id or current_user.get("company_id")
    
    # Vérifier limite utilisateurs
    if company_id:
        limit_check = await company_service.check_user_limit(company_id)
        if not limit_check["allowed"]:
            raise HTTPException(status_code=403, detail=limit_check["reason"])
    
    user_id = generate_uuid()
    now = now_iso()
    
    user_doc = {
        "id": user_id,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "role": data.role,
        "company_id": company_id,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    await db.users.insert_one(user_doc)
    user_doc.pop("password_hash")
    user_doc.pop("_id", None)
    
    return user_doc

@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère un utilisateur"""
    require_admin(current_user)
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Met à jour un utilisateur"""
    require_admin(current_user)
    
    updates = data.dict(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune modification")
    
    updates["updated_at"] = now_iso()
    
    await db.users.update_one({"id": user_id}, {"$set": updates})
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Désactive un utilisateur"""
    require_admin(current_user)
    
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Impossible de supprimer son propre compte")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": False, "updated_at": now_iso()}}
    )
    
    return {"message": "Utilisateur désactivé"}

@router.post("/users/invite")
async def invite_user(
    data: UserInvite,
    current_user: dict = Depends(get_current_user)
):
    """Invite un utilisateur dans l'entreprise"""
    require_admin(current_user)
    
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="Aucune entreprise associée")
    
    # Vérifier limite
    limit_check = await company_service.check_user_limit(company_id)
    if not limit_check["allowed"]:
        raise HTTPException(status_code=403, detail=limit_check["reason"])
    
    # Vérifier si l'email existe
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    # Créer l'utilisateur avec mot de passe temporaire
    import secrets
    temp_password = secrets.token_urlsafe(12)
    
    user_id = generate_uuid()
    now = now_iso()
    
    user_doc = {
        "id": user_id,
        "email": data.email,
        "password_hash": hash_password(temp_password),
        "full_name": data.full_name,
        "role": data.role,
        "company_id": company_id,
        "is_active": True,
        "must_change_password": True,
        "created_at": now,
        "updated_at": now
    }
    
    await db.users.insert_one(user_doc)
    
    return {
        "message": "Utilisateur invité",
        "user_id": user_id,
        "email": data.email,
        "temp_password": temp_password  # En production, envoyer par email
    }

# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

@router.get("/subscriptions/plans")
async def list_subscription_plans(current_user: dict = Depends(get_current_user)):
    """Liste les plans d'abonnement disponibles"""
    return company_service.SUBSCRIPTION_PLANS

@router.post("/subscriptions/{company_id}/upgrade")
async def upgrade_subscription(
    company_id: str,
    plan: str,
    current_user: dict = Depends(get_current_user)
):
    """Upgrade l'abonnement d'une entreprise"""
    require_admin(current_user)
    
    if plan not in company_service.SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    company = await company_service.update_subscription(company_id, plan)
    if not company:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    
    return company

# =============================================================================
# GLOBAL STATISTICS
# =============================================================================

@router.get("/stats/global")
async def get_global_stats(current_user: dict = Depends(get_current_user)):
    """Statistiques globales de la plateforme"""
    require_admin(current_user)
    
    total_companies = await db.companies.count_documents({})
    total_users = await db.users.count_documents({})
    total_projects = await db.projects.count_documents({})
    active_users = await db.users.count_documents({"is_active": {"$ne": False}})
    
    # Budget total
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$target_budget"}}}
    ]
    result = await db.projects.aggregate(pipeline).to_list(1)
    total_budget = result[0]["total"] if result else 0
    
    # Répartition par plan
    plans_pipeline = [
        {"$group": {"_id": "$subscription_plan", "count": {"$sum": 1}}}
    ]
    plans_result = await db.companies.aggregate(plans_pipeline).to_list(10)
    plans_distribution = {r["_id"]: r["count"] for r in plans_result if r["_id"]}
    
    return {
        "total_companies": total_companies,
        "total_users": total_users,
        "active_users": active_users,
        "total_projects": total_projects,
        "total_budget": total_budget,
        "plans_distribution": plans_distribution
    }

# =============================================================================
# DATA MIGRATION
# =============================================================================

@router.post("/migrate")
async def migrate_data(current_user: dict = Depends(get_current_user)):
    """Migration des données existantes vers le système multi-entreprise"""
    require_admin(current_user)
    result = await company_service.migrate_existing_data()
    return result
