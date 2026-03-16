# /app/backend/services/company_service.py
# Service de gestion des entreprises et abonnements SaaS

import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso

# Plans SaaS
SUBSCRIPTION_PLANS = {
    "starter": {
        "name": "Starter",
        "max_projects": 5,
        "max_users": 2,
        "features": ["basic_estimation", "pdf_export_basic"],
        "price_monthly": 49,
        "price_yearly": 490
    },
    "pro": {
        "name": "Pro",
        "max_projects": -1,  # unlimited
        "max_users": 10,
        "features": ["basic_estimation", "advanced_analysis", "pdf_export", "ai_optimization", "scenarios"],
        "price_monthly": 149,
        "price_yearly": 1490
    },
    "enterprise": {
        "name": "Enterprise",
        "max_projects": -1,
        "max_users": -1,
        "features": ["basic_estimation", "advanced_analysis", "pdf_export", "ai_optimization", 
                     "scenarios", "benchmark", "multi_company", "api_access", "custom_reports"],
        "price_monthly": 399,
        "price_yearly": 3990
    }
}

DEFAULT_COMPANY_ID = "default-company-001"


async def ensure_default_company():
    """Crée l'entreprise par défaut si elle n'existe pas"""
    existing = await db.companies.find_one({"id": DEFAULT_COMPANY_ID})
    if not existing:
        company_doc = {
            "id": DEFAULT_COMPANY_ID,
            "name": "Entreprise par défaut",
            "subscription_plan": "pro",
            "subscription_status": "active",
            "subscription_expires": None,
            "max_projects": -1,
            "max_users": -1,
            "created_at": now_iso(),
            "updated_at": now_iso()
        }
        await db.companies.insert_one(company_doc)
    return DEFAULT_COMPANY_ID


async def create_company(
    name: str,
    admin_user_id: str,
    subscription_plan: str = "starter"
) -> Dict:
    """Crée une nouvelle entreprise"""
    company_id = generate_uuid()
    now = now_iso()
    
    plan = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["starter"])
    
    company_doc = {
        "id": company_id,
        "name": name,
        "admin_user_id": admin_user_id,
        "subscription_plan": subscription_plan,
        "subscription_status": "active",
        "subscription_expires": None,
        "max_projects": plan["max_projects"],
        "max_users": plan["max_users"],
        "features": plan["features"],
        "created_at": now,
        "updated_at": now
    }
    
    await db.companies.insert_one(company_doc)
    company_doc.pop('_id', None)
    
    # Mettre à jour l'utilisateur admin
    await db.users.update_one(
        {"id": admin_user_id},
        {"$set": {"company_id": company_id, "role": "administrator"}}
    )
    
    return company_doc


async def get_company(company_id: str) -> Optional[Dict]:
    """Récupère une entreprise"""
    return await db.companies.find_one({"id": company_id}, {"_id": 0})


async def get_all_companies() -> List[Dict]:
    """Récupère toutes les entreprises"""
    companies = await db.companies.find({}, {"_id": 0}).to_list(1000)
    return companies


async def update_company(company_id: str, updates: Dict) -> Optional[Dict]:
    """Met à jour une entreprise"""
    updates["updated_at"] = now_iso()
    await db.companies.update_one({"id": company_id}, {"$set": updates})
    return await get_company(company_id)


async def update_subscription(
    company_id: str,
    plan: str,
    status: str = "active"
) -> Optional[Dict]:
    """Met à jour l'abonnement d'une entreprise"""
    plan_data = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["starter"])
    
    updates = {
        "subscription_plan": plan,
        "subscription_status": status,
        "max_projects": plan_data["max_projects"],
        "max_users": plan_data["max_users"],
        "features": plan_data["features"],
        "updated_at": now_iso()
    }
    
    await db.companies.update_one({"id": company_id}, {"$set": updates})
    return await get_company(company_id)


async def check_project_limit(company_id: str) -> Dict:
    """Vérifie si l'entreprise peut créer un nouveau projet"""
    company = await get_company(company_id)
    if not company:
        return {"allowed": False, "reason": "Entreprise non trouvée"}
    
    max_projects = company.get("max_projects", 5)
    if max_projects == -1:
        return {"allowed": True, "remaining": -1}
    
    current_count = await db.projects.count_documents({"company_id": company_id})
    
    if current_count >= max_projects:
        return {
            "allowed": False,
            "reason": f"Limite de {max_projects} projets atteinte",
            "current": current_count,
            "max": max_projects
        }
    
    return {
        "allowed": True,
        "remaining": max_projects - current_count,
        "current": current_count,
        "max": max_projects
    }


async def check_user_limit(company_id: str) -> Dict:
    """Vérifie si l'entreprise peut ajouter un nouvel utilisateur"""
    company = await get_company(company_id)
    if not company:
        return {"allowed": False, "reason": "Entreprise non trouvée"}
    
    max_users = company.get("max_users", 2)
    if max_users == -1:
        return {"allowed": True, "remaining": -1}
    
    current_count = await db.users.count_documents({"company_id": company_id})
    
    if current_count >= max_users:
        return {
            "allowed": False,
            "reason": f"Limite de {max_users} utilisateurs atteinte",
            "current": current_count,
            "max": max_users
        }
    
    return {
        "allowed": True,
        "remaining": max_users - current_count,
        "current": current_count,
        "max": max_users
    }


async def has_feature(company_id: str, feature: str) -> bool:
    """Vérifie si l'entreprise a accès à une fonctionnalité"""
    company = await get_company(company_id)
    if not company:
        return False
    
    features = company.get("features", [])
    return feature in features


async def get_company_stats(company_id: str) -> Dict:
    """Récupère les statistiques d'une entreprise"""
    company = await get_company(company_id)
    if not company:
        return {}
    
    project_count = await db.projects.count_documents({"company_id": company_id})
    user_count = await db.users.count_documents({"company_id": company_id})
    
    # Budget total des projets
    pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": None, "total_budget": {"$sum": "$target_budget"}}}
    ]
    result = await db.projects.aggregate(pipeline).to_list(1)
    total_budget = result[0]["total_budget"] if result else 0
    
    return {
        "company": company,
        "project_count": project_count,
        "user_count": user_count,
        "total_budget": total_budget,
        "project_limit": company.get("max_projects", 5),
        "user_limit": company.get("max_users", 2),
        "subscription_plan": company.get("subscription_plan", "starter"),
        "subscription_status": company.get("subscription_status", "active")
    }


async def migrate_existing_data():
    """Migration des données existantes vers le système multi-entreprise"""
    default_company_id = await ensure_default_company()
    
    # Migrer les utilisateurs sans company_id
    await db.users.update_many(
        {"company_id": {"$exists": False}},
        {"$set": {"company_id": default_company_id}}
    )
    
    # Migrer les projets sans company_id
    await db.projects.update_many(
        {"company_id": {"$exists": False}},
        {"$set": {"company_id": default_company_id}}
    )
    
    return {"migrated": True, "default_company_id": default_company_id}
