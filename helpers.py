# /app/backend/utils/helpers.py
# Fonctions utilitaires pour CostPilot Senior

import uuid
import bcrypt
import jwt
import os
from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuration JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'costpilot-senior-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    """Crée un token JWT"""
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Décode un token JWT"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

def generate_uuid() -> str:
    """Génère un UUID unique"""
    return str(uuid.uuid4())

def now_iso() -> str:
    """Retourne la date/heure actuelle en format ISO"""
    return datetime.now(timezone.utc).isoformat()

def check_role(user: dict, allowed_roles: List[str]):
    """Vérifie si l'utilisateur a un rôle autorisé"""
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

# Coefficients régionaux pour les coûts
REGIONAL_COEFFICIENTS = {
    "idf": {"label": "Île-de-France", "coefficient": 1.15},
    "paca": {"label": "Provence-Alpes-Côte d'Azur", "coefficient": 1.08},
    "aura": {"label": "Auvergne-Rhône-Alpes", "coefficient": 1.05},
    "occitanie": {"label": "Occitanie", "coefficient": 1.00},
    "nouvelle_aquitaine": {"label": "Nouvelle-Aquitaine", "coefficient": 0.98},
    "bretagne": {"label": "Bretagne", "coefficient": 0.95},
    "normandie": {"label": "Normandie", "coefficient": 0.97},
    "hauts_de_france": {"label": "Hauts-de-France", "coefficient": 0.95},
    "grand_est": {"label": "Grand Est", "coefficient": 0.96},
    "bourgogne_franche_comte": {"label": "Bourgogne-Franche-Comté", "coefficient": 0.94},
    "pays_de_la_loire": {"label": "Pays de la Loire", "coefficient": 0.97},
    "centre_val_de_loire": {"label": "Centre-Val de Loire", "coefficient": 0.95},
    "corse": {"label": "Corse", "coefficient": 1.20},
}

# Ratios de référence par type de bâtiment et niveau de qualité
DEFAULT_COST_REFERENCES = {
    "housing": {"economic": 1400, "standard": 1850, "premium": 2500, "luxury": 3500},
    "office": {"economic": 1200, "standard": 1650, "premium": 2300, "luxury": 3200},
    "hotel": {"economic": 1800, "standard": 2400, "premium": 3500, "luxury": 5000},
    "retail": {"economic": 1000, "standard": 1400, "premium": 2000, "luxury": 2800},
    "public_facility": {"economic": 1600, "standard": 2100, "premium": 2800, "luxury": 3800},
    "industrial": {"economic": 800, "standard": 1100, "premium": 1500, "luxury": 2000},
    "logistics": {"economic": 600, "standard": 850, "premium": 1200, "luxury": 1600},
    "mixed_use": {"economic": 1400, "standard": 1800, "premium": 2400, "luxury": 3200},
}

# Structure des lots DPGF standard
DPGF_LOTS_STRUCTURE = {
    "01": {"name": "Terrassements", "category": "infrastructure", "default_ratio": 0.02},
    "02": {"name": "VRD", "category": "infrastructure", "default_ratio": 0.03},
    "03": {"name": "Gros œuvre", "category": "structure", "default_ratio": 0.22},
    "04": {"name": "Charpente", "category": "structure", "default_ratio": 0.04},
    "05": {"name": "Couverture", "category": "envelope", "default_ratio": 0.03},
    "06": {"name": "Façade / Enveloppe", "category": "envelope", "default_ratio": 0.10},
    "07": {"name": "Menuiseries extérieures", "category": "envelope", "default_ratio": 0.06},
    "08": {"name": "Cloisonnement / Doublage", "category": "interior", "default_ratio": 0.05},
    "09": {"name": "Revêtements sols", "category": "interior", "default_ratio": 0.05},
    "10": {"name": "Revêtements muraux", "category": "interior", "default_ratio": 0.02},
    "11": {"name": "Peinture", "category": "interior", "default_ratio": 0.03},
    "12": {"name": "Menuiseries intérieures", "category": "interior", "default_ratio": 0.04},
    "13": {"name": "Plomberie / Sanitaire", "category": "technical", "default_ratio": 0.06},
    "14": {"name": "CVC", "category": "technical", "default_ratio": 0.10},
    "15": {"name": "Électricité CFO", "category": "technical", "default_ratio": 0.07},
    "16": {"name": "Courants faibles CFA", "category": "technical", "default_ratio": 0.02},
    "17": {"name": "Ascenseurs", "category": "technical", "default_ratio": 0.02},
    "18": {"name": "Équipements spéciaux", "category": "technical", "default_ratio": 0.01},
    "19": {"name": "Aménagements extérieurs", "category": "external", "default_ratio": 0.02},
    "20": {"name": "Aléas / Imprévus", "category": "contingency", "default_ratio": 0.05},
}

# Phases de l'économiste senior
ECONOMIST_PHASES = {
    "macro_analysis": {
        "name": "Analyse Macro-économique",
        "description": "Analyse du contexte économique et des tendances du marché",
        "deliverables": ["Rapport de marché", "Indices économiques", "Prévisions"],
        "order": 1
    },
    "risk_identification": {
        "name": "Identification des Risques",
        "description": "Cartographie et évaluation des risques projet",
        "deliverables": ["Matrice des risques", "Plan de mitigation", "Provisions"],
        "order": 2
    },
    "cost_strategy": {
        "name": "Stratégie Coûts",
        "description": "Définition de la stratégie de maîtrise des coûts",
        "deliverables": ["Budget objectif", "Leviers d'optimisation", "KPIs"],
        "order": 3
    },
    "project_phasing": {
        "name": "Phasage Projet",
        "description": "Planification et découpage du projet en phases",
        "deliverables": ["Planning macro", "Jalons", "Budget par phase"],
        "order": 4
    },
    "team_management": {
        "name": "Gestion Équipe",
        "description": "Organisation et pilotage de l'équipe projet",
        "deliverables": ["Organigramme", "RACI", "Plan de charge"],
        "order": 5
    },
    "workflow_timeline": {
        "name": "Timeline Workflow",
        "description": "Suivi du workflow et des livrables",
        "deliverables": ["Tableau de bord", "Alertes", "Rapports d'avancement"],
        "order": 6
    },
    "final_validation": {
        "name": "Validation Finale",
        "description": "Validation et clôture de phase économique",
        "deliverables": ["Synthèse économique", "Recommandations", "Archivage"],
        "order": 7
    }
}

def get_regional_coefficient(region: str) -> float:
    """Retourne le coefficient régional pour les coûts"""
    return REGIONAL_COEFFICIENTS.get(region, {"coefficient": 1.0})["coefficient"]

def get_reference_cost(building_type: str, quality_level: str) -> float:
    """Retourne le coût de référence au m² pour un type de bâtiment et niveau de qualité"""
    type_refs = DEFAULT_COST_REFERENCES.get(building_type, DEFAULT_COST_REFERENCES["housing"])
    return type_refs.get(quality_level, type_refs["standard"])

def calculate_lot_distribution(total_budget: float, building_type: str) -> dict:
    """Calcule la distribution budgétaire par lot"""
    distribution = {}
    for lot_code, lot_info in DPGF_LOTS_STRUCTURE.items():
        distribution[lot_code] = {
            "name": lot_info["name"],
            "category": lot_info["category"],
            "amount": round(total_budget * lot_info["default_ratio"], 2),
            "ratio": lot_info["default_ratio"]
        }
    return distribution
