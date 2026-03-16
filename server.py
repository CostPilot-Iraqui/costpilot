from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum
import io

# PDF Generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A3, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable must be set")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="CostPilot Senior API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# ENUMS
# =============================================================================

class UserRole(str, Enum):
    ADMINISTRATOR = "administrator"
    SENIOR_COST_MANAGER = "senior_cost_manager"
    JUNIOR_ESTIMATOR = "junior_estimator"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    DEVELOPER_INVESTOR = "developer_investor"
    READONLY_CLIENT = "readonly_client"

class ProjectUsage(str, Enum):
    HOUSING = "housing"
    OFFICE = "office"
    HOTEL = "hotel"
    RETAIL = "retail"
    MIXED_USE = "mixed_use"
    PUBLIC_FACILITY = "public_facility"
    INDUSTRIAL = "industrial"
    LOGISTICS = "logistics"
    OTHER = "other"

class QualityLevel(str, Enum):
    ECONOMIC = "economic"
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"

class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"

class FacadeAmbition(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    PREMIUM = "premium"
    ICONIC = "iconic"

class TechnicalAmbition(str, Enum):
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"

class SustainabilityTarget(str, Enum):
    NONE = "none"
    STANDARD = "standard"
    HQE_BREEAM_LEED = "hqe_breeam_leed"
    HIGH_PERFORMANCE = "high_performance"

class BasementPresence(str, Enum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"

class ParkingType(str, Enum):
    NONE = "none"
    EXTERNAL = "external"
    UNDERGROUND = "underground"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ValidationStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"

class AlertSeverity(str, Enum):
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"

class WorkflowStage(str, Enum):
    EARLY_FEASIBILITY = "early_feasibility"
    CONCEPT_PROGRAM = "concept_program"
    APS = "aps"
    APD = "apd"
    PRO = "pro"
    TENDER_NEGOTIATION = "tender_negotiation"
    CLIENT_VALIDATION = "client_validation"

class SourceType(str, Enum):
    INTERNAL_BENCHMARK = "internal_benchmark"
    HISTORICAL_PROJECT = "historical_project"
    MANUAL_INPUT = "manual_input"
    ADJUSTED_VALUE = "adjusted_value"

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.READONLY_CLIENT
    company: Optional[str] = None
    company_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    full_name: str
    role: UserRole
    company: Optional[str] = None
    company_id: Optional[str] = None
    subscription_plan: Optional[str] = None
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Project Models
class ProjectCreate(BaseModel):
    project_name: str
    client_name: str
    location: Optional[str] = None
    project_usage: ProjectUsage
    target_surface_m2: float
    estimated_usable_area_m2: Optional[float] = None
    number_of_levels_estimate: Optional[int] = None
    basement_presence: BasementPresence = BasementPresence.NONE
    parking_requirement: ParkingType = ParkingType.NONE
    quality_level: QualityLevel = QualityLevel.STANDARD
    complexity_level: ComplexityLevel = ComplexityLevel.MEDIUM
    facade_ambition: FacadeAmbition = FacadeAmbition.MODERATE
    technical_ambition: TechnicalAmbition = TechnicalAmbition.STANDARD
    sustainability_target: SustainabilityTarget = SustainabilityTarget.NONE
    specific_constraints: Optional[str] = None
    timeline_target: Optional[str] = None
    target_budget: Optional[float] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM

class ProjectResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_name: str
    client_name: str
    location: Optional[str] = None
    project_usage: ProjectUsage
    target_surface_m2: float
    estimated_usable_area_m2: Optional[float] = None
    number_of_levels_estimate: Optional[int] = None
    basement_presence: BasementPresence
    parking_requirement: ParkingType
    quality_level: QualityLevel
    complexity_level: ComplexityLevel
    facade_ambition: FacadeAmbition
    technical_ambition: TechnicalAmbition
    sustainability_target: SustainabilityTarget
    specific_constraints: Optional[str] = None
    timeline_target: Optional[str] = None
    target_budget: Optional[float] = None
    confidence_level: ConfidenceLevel
    current_stage: WorkflowStage = WorkflowStage.EARLY_FEASIBILITY
    macro_envelope_locked: bool = False
    created_by: str
    created_at: str
    updated_at: str

# Macro Category Models
class MacroCategoryCreate(BaseModel):
    project_id: str
    name: str
    code: str
    target_amount: float
    estimated_amount: float = 0
    percentage_allocation: float = 0
    notes: Optional[str] = None

class MacroCategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    name: str
    code: str
    target_amount: float
    estimated_amount: float
    percentage_allocation: float
    notes: Optional[str] = None
    is_locked: bool = False
    created_at: str

# Micro Item Models
class MicroItemCreate(BaseModel):
    project_id: str
    macro_category_id: str
    lot_code: str
    lot_name: str
    sub_lot_code: Optional[str] = None
    sub_lot_name: Optional[str] = None
    item_code: str
    description: str
    unit: str
    quantity: float
    unit_price: float
    pricing_source: SourceType = SourceType.MANUAL_INPUT
    responsible_user_id: Optional[str] = None
    notes: Optional[str] = None

class MicroItemResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    macro_category_id: str
    lot_code: str
    lot_name: str
    sub_lot_code: Optional[str] = None
    sub_lot_name: Optional[str] = None
    item_code: str
    description: str
    unit: str
    quantity: float
    unit_price: float
    amount: float
    cost_ratio: float
    pricing_source: SourceType
    validation_status: ValidationStatus = ValidationStatus.DRAFT
    responsible_user_id: Optional[str] = None
    notes: Optional[str] = None
    revision_number: int = 1
    created_at: str
    updated_at: str

class MicroItemUpdate(BaseModel):
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    validation_status: Optional[ValidationStatus] = None

# Pricing Library Models
class PricingEntryCreate(BaseModel):
    building_type: ProjectUsage
    geographic_region: Optional[str] = None
    region: Optional[str] = None  # Code région (idf, paca, etc.)
    year_reference: int
    quality_level: QualityLevel
    complexity_level: ComplexityLevel
    category: str
    lot_code: Optional[str] = None  # Code lot (INF.01, SUP.02, etc.)
    lot: str
    sub_lot: Optional[str] = None
    item: str
    unit: str
    unit_price_min: float
    unit_price_avg: float
    unit_price_max: float
    confidence_score: float = 0.8
    source_type: SourceType = SourceType.INTERNAL_BENCHMARK
    notes: Optional[str] = None

class PricingEntryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    building_type: ProjectUsage
    geographic_region: Optional[str] = None
    region: Optional[str] = None
    year_reference: int
    quality_level: QualityLevel
    complexity_level: ComplexityLevel
    category: str
    lot_code: Optional[str] = None
    lot: str
    sub_lot: Optional[str] = None
    item: str
    unit: str
    unit_price_min: float
    unit_price_avg: float
    unit_price_max: float
    confidence_score: float
    source_type: SourceType
    notes: Optional[str] = None
    created_at: str
    updated_at: str

# Reference Ratio Models
class ReferenceRatioCreate(BaseModel):
    building_type: ProjectUsage
    geographic_region: Optional[str] = None
    year_reference: int
    quality_level: QualityLevel
    complexity_level: ComplexityLevel
    facade_ambition: FacadeAmbition
    technical_ambition: TechnicalAmbition
    basement_presence: BasementPresence
    parking_type: ParkingType
    sustainability_target: SustainabilityTarget
    total_cost_m2: float
    infrastructure_cost_m2: float = 0
    superstructure_cost_m2: float = 0
    facade_cost_m2: float = 0
    interior_works_cost_m2: float = 0
    technical_systems_cost_m2: float = 0
    external_works_cost_m2: float = 0
    parking_cost_unit: float = 0
    contingency_percentage: float = 5
    fees_percentage: float = 10
    notes: Optional[str] = None

class ReferenceRatioResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    building_type: str  # Accept any string for flexibility
    geographic_region: Optional[str] = None
    region_label: Optional[str] = None
    location: Optional[str] = None
    year_reference: int = 2025
    quality_level: str = "standard"
    complexity_level: str = "medium"
    facade_ambition: str = "moderate"
    technical_ambition: str = "standard"
    basement_presence: str = "none"
    parking_type: str = "none"
    sustainability_target: str = "rt2020"
    total_cost_m2: float = 0
    cost_min_m2: Optional[float] = None
    cost_avg_m2: Optional[float] = None
    cost_max_m2: Optional[float] = None
    confidence_level: Optional[str] = None
    infrastructure_cost_m2: float = 0
    superstructure_cost_m2: float = 0
    facade_cost_m2: float = 0
    interior_works_cost_m2: float = 0
    technical_systems_cost_m2: float = 0
    external_works_cost_m2: float = 0
    parking_cost_unit: float = 0
    contingency_percentage: float = 5
    fees_percentage: float = 10
    source: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

# Scenario Models
class ScenarioCreate(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    macro_adjustments: Dict[str, float] = {}
    notes: Optional[str] = None

class ScenarioResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    total_cost: float = 0
    cost_per_m2: float = 0
    macro_adjustments: Dict[str, float] = {}
    notes: Optional[str] = None
    created_at: str
    updated_at: str

# Arbitration Models
class ArbitrationCreate(BaseModel):
    project_id: str
    subject: str
    linked_category_id: Optional[str] = None
    linked_lot: Optional[str] = None
    initial_assumption: str
    current_cost_impact: float
    reason_for_drift: str
    design_option_a: Optional[str] = None
    design_option_b: Optional[str] = None
    suggested_optimization: Optional[str] = None
    estimated_saving: float = 0
    planning_impact: Optional[str] = None
    quality_impact: Optional[str] = None
    responsible_persons: List[str] = []

class ArbitrationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    subject: str
    linked_category_id: Optional[str] = None
    linked_lot: Optional[str] = None
    initial_assumption: str
    current_cost_impact: float
    reason_for_drift: str
    design_option_a: Optional[str] = None
    design_option_b: Optional[str] = None
    suggested_optimization: Optional[str] = None
    estimated_saving: float
    planning_impact: Optional[str] = None
    quality_impact: Optional[str] = None
    decision_status: ValidationStatus = ValidationStatus.PENDING
    responsible_persons: List[str]
    created_at: str
    updated_at: str

# Alert Models
class AlertResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    type: str
    message: str
    severity: AlertSeverity
    linked_category_id: Optional[str] = None
    linked_item_id: Optional[str] = None
    value: float = 0
    threshold: float = 0
    is_resolved: bool = False
    created_at: str

# Task Models
class TaskCreate(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    deadline: Optional[str] = None
    priority: int = 2
    stage: WorkflowStage

class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    deadline: Optional[str] = None
    priority: int
    stage: WorkflowStage
    progress: int = 0
    status: ValidationStatus = ValidationStatus.DRAFT
    created_at: str
    updated_at: str

# Workflow Stage Models
class WorkflowStageCreate(BaseModel):
    project_id: str
    stage: WorkflowStage
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsible_users: List[str] = []
    deliverables: List[str] = []
    notes: Optional[str] = None

class WorkflowStageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    stage: WorkflowStage
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsible_users: List[str]
    deliverables: List[str]
    validation_status: ValidationStatus = ValidationStatus.DRAFT
    completion_percentage: int = 0
    notes: Optional[str] = None
    created_at: str
    updated_at: str

# Comment Models
class CommentCreate(BaseModel):
    project_id: str
    target_type: str  # project, macro_category, micro_item, arbitration
    target_id: str
    content: str

class CommentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    target_type: str
    target_id: str
    content: str
    author_id: str
    author_name: str
    created_at: str

# Feasibility Analysis Models
class FeasibilityCreate(BaseModel):
    project_id: str
    land_price: float
    acquisition_fees: float = 0
    construction_cost: float
    developer_fees: float = 0
    financing_cost: float = 0
    sales_price_per_m2: float
    rental_income_assumption: float = 0
    project_duration_months: int = 24
    marketing_costs: float = 0
    contingencies: float = 0
    taxes_assumptions: float = 0
    notes: Optional[str] = None

class FeasibilityResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    land_price: float
    acquisition_fees: float
    construction_cost: float
    developer_fees: float
    financing_cost: float
    sales_price_per_m2: float
    rental_income_assumption: float
    project_duration_months: int
    marketing_costs: float
    contingencies: float
    taxes_assumptions: float
    total_revenue: float
    total_project_cost: float
    gross_margin: float
    margin_percentage: float
    break_even_sales_price_m2: float
    residual_land_value: float
    notes: Optional[str] = None
    created_at: str
    updated_at: str

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

def check_role(user: dict, allowed_roles: List[UserRole]):
    if user["role"] not in [r.value for r in allowed_roles]:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

def generate_uuid() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# =============================================================================
# AUTH ROUTES
# =============================================================================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    user_id = generate_uuid()
    
    # Créer ou assigner l'entreprise par défaut
    company_id = user_data.company_id
    if not company_id:
        default_company = await db.companies.find_one({"id": "default-company-001"})
        if not default_company:
            default_company = {
                "id": "default-company-001",
                "name": "Entreprise par défaut",
                "subscription_plan": "pro",
                "subscription_status": "active",
                "max_projects": -1,
                "max_users": -1,
                "features": ["basic_estimation", "advanced_analysis", "pdf_export", "ai_optimization", "scenarios"],
                "created_at": now_iso(),
                "updated_at": now_iso()
            }
            await db.companies.insert_one(default_company)
        company_id = "default-company-001"
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "role": user_data.role.value,
        "company": user_data.company,
        "company_id": company_id,
        "is_active": True,
        "created_at": now_iso()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user_data.email, user_data.role.value)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            company=user_data.company,
            company_id=company_id,
            subscription_plan="pro",
            created_at=user_doc["created_at"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    
    # Récupérer l'abonnement de l'entreprise
    subscription_plan = "pro"
    company_id = user.get("company_id")
    if company_id:
        company = await db.companies.find_one({"id": company_id}, {"_id": 0})
        if company:
            subscription_plan = company.get("subscription_plan", "pro")
    
    token = create_token(user["id"], user["email"], user["role"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=UserRole(user["role"]),
            company=user.get("company"),
            company_id=user.get("company_id"),
            subscription_plan=subscription_plan,
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    # Récupérer l'abonnement de l'entreprise
    subscription_plan = "pro"
    company_id = current_user.get("company_id")
    if company_id:
        company = await db.companies.find_one({"id": company_id}, {"_id": 0})
        if company:
            subscription_plan = company.get("subscription_plan", "pro")
    
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=UserRole(current_user["role"]),
        company=current_user.get("company"),
        company_id=current_user.get("company_id"),
        subscription_plan=subscription_plan,
        created_at=current_user["created_at"]
    )

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

# =============================================================================
# PROJECT ROUTES
# =============================================================================

@api_router.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    # Vérifier la limite de projets de l'entreprise
    company_id = current_user.get("company_id")
    if company_id:
        company = await db.companies.find_one({"id": company_id})
        if company:
            max_projects = company.get("max_projects", 5)
            if max_projects != -1:
                current_count = await db.projects.count_documents({"company_id": company_id})
                if current_count >= max_projects:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Limite de {max_projects} projets atteinte. Veuillez upgrader votre abonnement."
                    )
    
    project_id = generate_uuid()
    now = now_iso()
    project_doc = {
        "id": project_id,
        **project.model_dump(),
        "current_stage": WorkflowStage.EARLY_FEASIBILITY.value,
        "macro_envelope_locked": False,
        "created_by": current_user["id"],
        "company_id": company_id,
        "created_at": now,
        "updated_at": now
    }
    # Convert enums to values
    for key in ["project_usage", "basement_presence", "parking_requirement", "quality_level", 
                "complexity_level", "facade_ambition", "technical_ambition", "sustainability_target", "confidence_level"]:
        if key in project_doc and hasattr(project_doc[key], 'value'):
            project_doc[key] = project_doc[key].value
    
    await db.projects.insert_one(project_doc)
    
    # Create default macro categories
    default_categories = [
        {"name": "Infrastructure", "code": "INF", "percentage": 8},
        {"name": "Superstructure", "code": "SUP", "percentage": 25},
        {"name": "Façade / Enveloppe", "code": "FAC", "percentage": 15},
        {"name": "Travaux Intérieurs", "code": "INT", "percentage": 22},
        {"name": "Systèmes Techniques", "code": "TEC", "percentage": 20},
        {"name": "Travaux Extérieurs", "code": "EXT", "percentage": 5},
        {"name": "Aléas", "code": "ALE", "percentage": 5},
    ]
    
    target_budget = project.target_budget or 0
    for cat in default_categories:
        cat_doc = {
            "id": generate_uuid(),
            "project_id": project_id,
            "name": cat["name"],
            "code": cat["code"],
            "target_amount": target_budget * cat["percentage"] / 100,
            "estimated_amount": 0,
            "percentage_allocation": cat["percentage"],
            "is_locked": False,
            "created_at": now
        }
        await db.macro_categories.insert_one(cat_doc)
    
    return ProjectResponse(**project_doc)

@api_router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(current_user: dict = Depends(get_current_user)):
    # Filtrer par company_id si l'utilisateur n'est pas admin global
    query = {}
    company_id = current_user.get("company_id")
    if company_id and current_user.get("role") != "administrator":
        query["company_id"] = company_id
    
    projects = await db.projects.find(query, {"_id": 0}).to_list(1000)
    return [ProjectResponse(**p) for p in projects]

@api_router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return ProjectResponse(**project)

@api_router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, updates: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    updates["updated_at"] = now_iso()
    await db.projects.update_one({"id": project_id}, {"$set": updates})
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return ProjectResponse(**project)

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR])
    
    result = await db.projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Delete related data
    await db.macro_categories.delete_many({"project_id": project_id})
    await db.micro_items.delete_many({"project_id": project_id})
    await db.scenarios.delete_many({"project_id": project_id})
    await db.arbitrations.delete_many({"project_id": project_id})
    await db.alerts.delete_many({"project_id": project_id})
    await db.tasks.delete_many({"project_id": project_id})
    await db.workflow_stages.delete_many({"project_id": project_id})
    await db.comments.delete_many({"project_id": project_id})
    await db.feasibility_analyses.delete_many({"project_id": project_id})
    
    return {"message": "Projet supprimé"}

@api_router.post("/projects/{project_id}/lock-macro")
async def lock_macro_envelope(project_id: str, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    await db.projects.update_one({"id": project_id}, {"$set": {"macro_envelope_locked": True, "updated_at": now_iso()}})
    await db.macro_categories.update_many({"project_id": project_id}, {"$set": {"is_locked": True}})
    return {"message": "Enveloppe macro verrouillée"}

@api_router.post("/projects/{project_id}/unlock-macro")
async def unlock_macro_envelope(project_id: str, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    await db.projects.update_one({"id": project_id}, {"$set": {"macro_envelope_locked": False, "updated_at": now_iso()}})
    await db.macro_categories.update_many({"project_id": project_id}, {"$set": {"is_locked": False}})
    return {"message": "Enveloppe macro déverrouillée"}

# =============================================================================
# MACRO CATEGORY ROUTES
# =============================================================================

@api_router.get("/projects/{project_id}/macro-categories", response_model=List[MacroCategoryResponse])
async def get_macro_categories(project_id: str, current_user: dict = Depends(get_current_user)):
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    return [MacroCategoryResponse(**c) for c in categories]

@api_router.put("/projects/{project_id}/macro-categories/{category_id}")
async def update_macro_category(project_id: str, category_id: str, updates: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    # Check if locked
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if project and project.get("macro_envelope_locked"):
        raise HTTPException(status_code=403, detail="L'enveloppe macro est verrouillée")
    
    await db.macro_categories.update_one({"id": category_id}, {"$set": updates})
    category = await db.macro_categories.find_one({"id": category_id}, {"_id": 0})
    return MacroCategoryResponse(**category)

# =============================================================================
# MICRO ITEM ROUTES
# =============================================================================

@api_router.post("/projects/{project_id}/micro-items", response_model=MicroItemResponse)
async def create_micro_item(project_id: str, item: MicroItemCreate, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER, UserRole.JUNIOR_ESTIMATOR])
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    item_id = generate_uuid()
    now = now_iso()
    amount = item.quantity * item.unit_price
    cost_ratio = amount / project.get("target_surface_m2", 1) if project.get("target_surface_m2") else 0
    
    item_doc = {
        "id": item_id,
        **item.model_dump(),
        "amount": amount,
        "cost_ratio": cost_ratio,
        "validation_status": ValidationStatus.DRAFT.value,
        "revision_number": 1,
        "created_at": now,
        "updated_at": now
    }
    # Convert enum
    item_doc["pricing_source"] = item_doc["pricing_source"].value
    
    await db.micro_items.insert_one(item_doc)
    
    # Update macro category estimated amount
    await update_macro_estimated_amount(project_id, item.macro_category_id)
    
    # Check for alerts
    await check_and_create_alerts(project_id)
    
    return MicroItemResponse(**item_doc)

@api_router.get("/projects/{project_id}/micro-items", response_model=List[MicroItemResponse])
async def get_micro_items(
    project_id: str, 
    macro_category_id: Optional[str] = None,
    lot_code: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"project_id": project_id}
    if macro_category_id:
        query["macro_category_id"] = macro_category_id
    if lot_code:
        query["lot_code"] = lot_code
    
    items = await db.micro_items.find(query, {"_id": 0}).to_list(10000)
    return [MicroItemResponse(**i) for i in items]

@api_router.put("/projects/{project_id}/micro-items/{item_id}", response_model=MicroItemResponse)
async def update_micro_item(project_id: str, item_id: str, updates: MicroItemUpdate, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER, UserRole.JUNIOR_ESTIMATOR])
    
    item = await db.micro_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Élément non trouvé")
    
    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    # Recalculate amount if quantity or unit_price changed
    quantity = update_dict.get("quantity", item["quantity"])
    unit_price = update_dict.get("unit_price", item["unit_price"])
    update_dict["amount"] = quantity * unit_price
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if project and project.get("target_surface_m2"):
        update_dict["cost_ratio"] = update_dict["amount"] / project["target_surface_m2"]
    
    update_dict["updated_at"] = now_iso()
    update_dict["revision_number"] = item.get("revision_number", 1) + 1
    
    # Convert enum if present
    if "validation_status" in update_dict and hasattr(update_dict["validation_status"], 'value'):
        update_dict["validation_status"] = update_dict["validation_status"].value
    
    await db.micro_items.update_one({"id": item_id}, {"$set": update_dict})
    
    # Update macro category estimated amount
    await update_macro_estimated_amount(project_id, item["macro_category_id"])
    
    # Check for alerts
    await check_and_create_alerts(project_id)
    
    updated_item = await db.micro_items.find_one({"id": item_id}, {"_id": 0})
    return MicroItemResponse(**updated_item)

@api_router.delete("/projects/{project_id}/micro-items/{item_id}")
async def delete_micro_item(project_id: str, item_id: str, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    item = await db.micro_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Élément non trouvé")
    
    macro_category_id = item["macro_category_id"]
    await db.micro_items.delete_one({"id": item_id})
    
    # Update macro category estimated amount
    await update_macro_estimated_amount(project_id, macro_category_id)
    
    return {"message": "Élément supprimé"}

async def update_macro_estimated_amount(project_id: str, macro_category_id: str):
    """Recalculate macro category estimated amount from micro items"""
    pipeline = [
        {"$match": {"project_id": project_id, "macro_category_id": macro_category_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    result = await db.micro_items.aggregate(pipeline).to_list(1)
    total = result[0]["total"] if result else 0
    await db.macro_categories.update_one({"id": macro_category_id}, {"$set": {"estimated_amount": total}})

# =============================================================================
# PRICING LIBRARY ROUTES
# =============================================================================

@api_router.post("/pricing-library", response_model=PricingEntryResponse)
async def create_pricing_entry(entry: PricingEntryCreate, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    entry_id = generate_uuid()
    now = now_iso()
    entry_doc = {
        "id": entry_id,
        **entry.model_dump(),
        "created_at": now,
        "updated_at": now
    }
    # Convert enums
    for key in ["building_type", "quality_level", "complexity_level", "source_type"]:
        if key in entry_doc and hasattr(entry_doc[key], 'value'):
            entry_doc[key] = entry_doc[key].value
    
    await db.pricing_library.insert_one(entry_doc)
    return PricingEntryResponse(**entry_doc)

@api_router.get("/pricing-library", response_model=List[PricingEntryResponse])
async def get_pricing_entries(
    building_type: Optional[str] = None,
    quality_level: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if building_type:
        query["building_type"] = building_type
    if quality_level:
        query["quality_level"] = quality_level
    if category:
        query["category"] = category
    
    entries = await db.pricing_library.find(query, {"_id": 0}).to_list(10000)
    return [PricingEntryResponse(**e) for e in entries]

@api_router.put("/pricing-library/{entry_id}", response_model=PricingEntryResponse)
async def update_pricing_entry(entry_id: str, updates: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    updates["updated_at"] = now_iso()
    await db.pricing_library.update_one({"id": entry_id}, {"$set": updates})
    entry = await db.pricing_library.find_one({"id": entry_id}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Entrée non trouvée")
    return PricingEntryResponse(**entry)

@api_router.delete("/pricing-library/{entry_id}")
async def delete_pricing_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    result = await db.pricing_library.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entrée non trouvée")
    return {"message": "Entrée supprimée"}

# =============================================================================
# REFERENCE RATIOS ROUTES
# =============================================================================

@api_router.post("/reference-ratios", response_model=ReferenceRatioResponse)
async def create_reference_ratio(ratio: ReferenceRatioCreate, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    ratio_id = generate_uuid()
    now = now_iso()
    ratio_doc = {
        "id": ratio_id,
        **ratio.model_dump(),
        "created_at": now,
        "updated_at": now
    }
    # Convert enums
    for key in ["building_type", "quality_level", "complexity_level", "facade_ambition", 
                "technical_ambition", "basement_presence", "parking_type", "sustainability_target"]:
        if key in ratio_doc and hasattr(ratio_doc[key], 'value'):
            ratio_doc[key] = ratio_doc[key].value
    
    await db.reference_ratios.insert_one(ratio_doc)
    return ReferenceRatioResponse(**ratio_doc)

@api_router.get("/reference-ratios", response_model=List[ReferenceRatioResponse])
async def get_reference_ratios(
    building_type: Optional[str] = None,
    quality_level: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if building_type:
        query["building_type"] = building_type
    if quality_level:
        query["quality_level"] = quality_level
    
    ratios = await db.reference_ratios.find(query, {"_id": 0}).to_list(1000)
    return [ReferenceRatioResponse(**r) for r in ratios]

@api_router.put("/reference-ratios/{ratio_id}", response_model=ReferenceRatioResponse)
async def update_reference_ratio(ratio_id: str, updates: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    updates["updated_at"] = now_iso()
    await db.reference_ratios.update_one({"id": ratio_id}, {"$set": updates})
    ratio = await db.reference_ratios.find_one({"id": ratio_id}, {"_id": 0})
    if not ratio:
        raise HTTPException(status_code=404, detail="Ratio non trouvé")
    return ReferenceRatioResponse(**ratio)

@api_router.delete("/reference-ratios/{ratio_id}")
async def delete_reference_ratio(ratio_id: str, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    result = await db.reference_ratios.delete_one({"id": ratio_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ratio non trouvé")
    return {"message": "Ratio supprimé"}

# =============================================================================
# SCENARIOS ROUTES
# =============================================================================

@api_router.post("/projects/{project_id}/scenarios", response_model=ScenarioResponse)
async def create_scenario(project_id: str, scenario: ScenarioCreate, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    scenario_id = generate_uuid()
    now = now_iso()
    
    # Calculate totals based on macro adjustments
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    total_cost = sum(c.get("target_amount", 0) * (1 + scenario.macro_adjustments.get(c["code"], 0) / 100) for c in categories)
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    cost_per_m2 = total_cost / project.get("target_surface_m2", 1) if project and project.get("target_surface_m2") else 0
    
    scenario_doc = {
        "id": scenario_id,
        **scenario.model_dump(),
        "total_cost": total_cost,
        "cost_per_m2": cost_per_m2,
        "created_at": now,
        "updated_at": now
    }
    
    await db.scenarios.insert_one(scenario_doc)
    return ScenarioResponse(**scenario_doc)

@api_router.get("/projects/{project_id}/scenarios", response_model=List[ScenarioResponse])
async def get_scenarios(project_id: str, current_user: dict = Depends(get_current_user)):
    scenarios = await db.scenarios.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    return [ScenarioResponse(**s) for s in scenarios]

@api_router.delete("/projects/{project_id}/scenarios/{scenario_id}")
async def delete_scenario(project_id: str, scenario_id: str, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER])
    
    result = await db.scenarios.delete_one({"id": scenario_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scénario non trouvé")
    return {"message": "Scénario supprimé"}

# =============================================================================
# ARBITRATIONS ROUTES
# =============================================================================

@api_router.post("/projects/{project_id}/arbitrations", response_model=ArbitrationResponse)
async def create_arbitration(project_id: str, arbitration: ArbitrationCreate, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER, UserRole.JUNIOR_ESTIMATOR])
    
    arb_id = generate_uuid()
    now = now_iso()
    arb_doc = {
        "id": arb_id,
        **arbitration.model_dump(),
        "decision_status": ValidationStatus.PENDING.value,
        "created_at": now,
        "updated_at": now
    }
    
    await db.arbitrations.insert_one(arb_doc)
    return ArbitrationResponse(**arb_doc)

@api_router.get("/projects/{project_id}/arbitrations", response_model=List[ArbitrationResponse])
async def get_arbitrations(project_id: str, current_user: dict = Depends(get_current_user)):
    arbitrations = await db.arbitrations.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    return [ArbitrationResponse(**a) for a in arbitrations]

@api_router.put("/projects/{project_id}/arbitrations/{arbitration_id}", response_model=ArbitrationResponse)
async def update_arbitration(project_id: str, arbitration_id: str, updates: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    updates["updated_at"] = now_iso()
    await db.arbitrations.update_one({"id": arbitration_id}, {"$set": updates})
    arb = await db.arbitrations.find_one({"id": arbitration_id}, {"_id": 0})
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrage non trouvé")
    return ArbitrationResponse(**arb)

# =============================================================================
# ALERTS ROUTES
# =============================================================================

async def check_and_create_alerts(project_id: str):
    """Check conditions and create alerts"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return
    
    # Clear old alerts
    await db.alerts.delete_many({"project_id": project_id, "is_resolved": False})
    
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    
    for cat in categories:
        if cat["estimated_amount"] > cat["target_amount"]:
            variance = ((cat["estimated_amount"] - cat["target_amount"]) / cat["target_amount"] * 100) if cat["target_amount"] > 0 else 0
            severity = AlertSeverity.RED if variance > 10 else AlertSeverity.ORANGE
            
            alert_doc = {
                "id": generate_uuid(),
                "project_id": project_id,
                "type": "macro_overrun",
                "message": f"Dépassement {cat['name']}: {variance:.1f}%",
                "severity": severity.value,
                "linked_category_id": cat["id"],
                "value": cat["estimated_amount"],
                "threshold": cat["target_amount"],
                "is_resolved": False,
                "created_at": now_iso()
            }
            await db.alerts.insert_one(alert_doc)
    
    # Check for top 20 most expensive items
    items = await db.micro_items.find({"project_id": project_id}, {"_id": 0}).sort("amount", -1).to_list(20)
    for i, item in enumerate(items[:5]):  # Alert for top 5
        alert_doc = {
            "id": generate_uuid(),
            "project_id": project_id,
            "type": "high_cost_item",
            "message": f"Poste coûteux #{i+1}: {item['description']} ({item['amount']:,.0f} €)",
            "severity": AlertSeverity.ORANGE.value,
            "linked_item_id": item["id"],
            "value": item["amount"],
            "threshold": 0,
            "is_resolved": False,
            "created_at": now_iso()
        }
        await db.alerts.insert_one(alert_doc)

@api_router.get("/projects/{project_id}/alerts", response_model=List[AlertResponse])
async def get_alerts(project_id: str, current_user: dict = Depends(get_current_user)):
    alerts = await db.alerts.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    return [AlertResponse(**a) for a in alerts]

@api_router.put("/projects/{project_id}/alerts/{alert_id}/resolve")
async def resolve_alert(project_id: str, alert_id: str, current_user: dict = Depends(get_current_user)):
    await db.alerts.update_one({"id": alert_id}, {"$set": {"is_resolved": True}})
    return {"message": "Alerte résolue"}

# =============================================================================
# TASKS ROUTES
# =============================================================================

@api_router.post("/projects/{project_id}/tasks", response_model=TaskResponse)
async def create_task(project_id: str, task: TaskCreate, current_user: dict = Depends(get_current_user)):
    task_id = generate_uuid()
    now = now_iso()
    task_doc = {
        "id": task_id,
        **task.model_dump(),
        "progress": 0,
        "status": ValidationStatus.DRAFT.value,
        "created_at": now,
        "updated_at": now
    }
    task_doc["stage"] = task_doc["stage"].value
    
    await db.tasks.insert_one(task_doc)
    return TaskResponse(**task_doc)

@api_router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
async def get_tasks(project_id: str, current_user: dict = Depends(get_current_user)):
    tasks = await db.tasks.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    return [TaskResponse(**t) for t in tasks]

@api_router.put("/projects/{project_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(project_id: str, task_id: str, updates: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    updates["updated_at"] = now_iso()
    await db.tasks.update_one({"id": task_id}, {"$set": updates})
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return TaskResponse(**task)

@api_router.delete("/projects/{project_id}/tasks/{task_id}")
async def delete_task(project_id: str, task_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return {"message": "Tâche supprimée"}

# =============================================================================
# WORKFLOW STAGES ROUTES
# =============================================================================

@api_router.post("/projects/{project_id}/workflow-stages", response_model=WorkflowStageResponse)
async def create_workflow_stage(project_id: str, stage: WorkflowStageCreate, current_user: dict = Depends(get_current_user)):
    stage_id = generate_uuid()
    now = now_iso()
    stage_doc = {
        "id": stage_id,
        **stage.model_dump(),
        "validation_status": ValidationStatus.DRAFT.value,
        "completion_percentage": 0,
        "created_at": now,
        "updated_at": now
    }
    stage_doc["stage"] = stage_doc["stage"].value
    
    await db.workflow_stages.insert_one(stage_doc)
    return WorkflowStageResponse(**stage_doc)

@api_router.get("/projects/{project_id}/workflow-stages", response_model=List[WorkflowStageResponse])
async def get_workflow_stages(project_id: str, current_user: dict = Depends(get_current_user)):
    stages = await db.workflow_stages.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    return [WorkflowStageResponse(**s) for s in stages]

@api_router.put("/projects/{project_id}/workflow-stages/{stage_id}", response_model=WorkflowStageResponse)
async def update_workflow_stage(project_id: str, stage_id: str, updates: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    updates["updated_at"] = now_iso()
    await db.workflow_stages.update_one({"id": stage_id}, {"$set": updates})
    stage = await db.workflow_stages.find_one({"id": stage_id}, {"_id": 0})
    if not stage:
        raise HTTPException(status_code=404, detail="Étape non trouvée")
    return WorkflowStageResponse(**stage)

# =============================================================================
# COMMENTS ROUTES
# =============================================================================

@api_router.post("/projects/{project_id}/comments", response_model=CommentResponse)
async def create_comment(project_id: str, comment: CommentCreate, current_user: dict = Depends(get_current_user)):
    comment_id = generate_uuid()
    comment_doc = {
        "id": comment_id,
        **comment.model_dump(),
        "author_id": current_user["id"],
        "author_name": current_user["full_name"],
        "created_at": now_iso()
    }
    
    await db.comments.insert_one(comment_doc)
    return CommentResponse(**comment_doc)

@api_router.get("/projects/{project_id}/comments", response_model=List[CommentResponse])
async def get_comments(project_id: str, target_type: Optional[str] = None, target_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {"project_id": project_id}
    if target_type:
        query["target_type"] = target_type
    if target_id:
        query["target_id"] = target_id
    
    comments = await db.comments.find(query, {"_id": 0}).to_list(1000)
    return [CommentResponse(**c) for c in comments]

# =============================================================================
# FEASIBILITY ANALYSIS ROUTES
# =============================================================================

@api_router.post("/projects/{project_id}/feasibility", response_model=FeasibilityResponse)
async def create_feasibility(project_id: str, feasibility: FeasibilityCreate, current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER, UserRole.DEVELOPER_INVESTOR])
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    feas_id = generate_uuid()
    now = now_iso()
    
    # Calculate financial metrics
    total_project_cost = (
        feasibility.land_price +
        feasibility.acquisition_fees +
        feasibility.construction_cost +
        feasibility.developer_fees +
        feasibility.financing_cost +
        feasibility.marketing_costs +
        feasibility.contingencies +
        feasibility.taxes_assumptions
    )
    
    surface = project.get("target_surface_m2", 1)
    total_revenue = feasibility.sales_price_per_m2 * surface
    gross_margin = total_revenue - total_project_cost
    margin_percentage = (gross_margin / total_revenue * 100) if total_revenue > 0 else 0
    break_even_sales_price_m2 = total_project_cost / surface if surface > 0 else 0
    residual_land_value = total_revenue - (total_project_cost - feasibility.land_price)
    
    feas_doc = {
        "id": feas_id,
        **feasibility.model_dump(),
        "total_revenue": total_revenue,
        "total_project_cost": total_project_cost,
        "gross_margin": gross_margin,
        "margin_percentage": margin_percentage,
        "break_even_sales_price_m2": break_even_sales_price_m2,
        "residual_land_value": residual_land_value,
        "created_at": now,
        "updated_at": now
    }
    
    await db.feasibility_analyses.insert_one(feas_doc)
    return FeasibilityResponse(**feas_doc)

@api_router.get("/projects/{project_id}/feasibility", response_model=Optional[FeasibilityResponse])
async def get_feasibility(project_id: str, current_user: dict = Depends(get_current_user)):
    feas = await db.feasibility_analyses.find_one({"project_id": project_id}, {"_id": 0})
    if feas:
        return FeasibilityResponse(**feas)
    return None

@api_router.put("/projects/{project_id}/feasibility/{feasibility_id}", response_model=FeasibilityResponse)
async def update_feasibility(project_id: str, feasibility_id: str, updates: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    check_role(current_user, [UserRole.ADMINISTRATOR, UserRole.SENIOR_COST_MANAGER, UserRole.DEVELOPER_INVESTOR])
    
    updates["updated_at"] = now_iso()
    await db.feasibility_analyses.update_one({"id": feasibility_id}, {"$set": updates})
    feas = await db.feasibility_analyses.find_one({"id": feasibility_id}, {"_id": 0})
    if not feas:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return FeasibilityResponse(**feas)

# =============================================================================
# DASHBOARD / STATISTICS ROUTES
# =============================================================================

@api_router.get("/projects/{project_id}/dashboard")
async def get_project_dashboard(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    alerts = await db.alerts.find({"project_id": project_id, "is_resolved": False}, {"_id": 0}).to_list(100)
    tasks = await db.tasks.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    arbitrations = await db.arbitrations.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    
    # Calculate totals
    macro_total = sum(c.get("target_amount", 0) for c in categories)
    micro_total = sum(c.get("estimated_amount", 0) for c in categories)
    variance = micro_total - macro_total
    variance_percentage = (variance / macro_total * 100) if macro_total > 0 else 0
    
    # Category breakdown
    category_breakdown = [
        {
            "name": c["name"],
            "code": c["code"],
            "target": c["target_amount"],
            "estimated": c["estimated_amount"],
            "variance": c["estimated_amount"] - c["target_amount"],
            "variance_percentage": ((c["estimated_amount"] - c["target_amount"]) / c["target_amount"] * 100) if c["target_amount"] > 0 else 0
        }
        for c in categories
    ]
    
    return {
        "project": project,
        "summary": {
            "macro_total": macro_total,
            "micro_total": micro_total,
            "variance": variance,
            "variance_percentage": variance_percentage,
            "target_budget": project.get("target_budget", 0),
            "cost_per_m2": micro_total / project.get("target_surface_m2", 1) if project.get("target_surface_m2") else 0,
            "is_locked": project.get("macro_envelope_locked", False)
        },
        "category_breakdown": category_breakdown,
        "alerts_count": len(alerts),
        "alerts": alerts[:5],
        "pending_tasks": len([t for t in tasks if t.get("status") != "validated"]),
        "pending_arbitrations": len([a for a in arbitrations if a.get("decision_status") == "pending"])
    }

@api_router.get("/dashboard/overview")
async def get_global_dashboard(current_user: dict = Depends(get_current_user)):
    projects = await db.projects.find({}, {"_id": 0}).to_list(1000)
    
    # Handle None values for target_budget and target_surface_m2
    total_budget = sum(p.get("target_budget") or 0 for p in projects)
    total_surface = sum(p.get("target_surface_m2") or 0 for p in projects)
    
    # Get alerts count
    alerts = await db.alerts.find({"is_resolved": False}, {"_id": 0}).to_list(1000)
    
    # Get tasks count
    tasks = await db.tasks.find({}, {"_id": 0}).to_list(1000)
    pending_tasks = [t for t in tasks if t.get("status") != "validated"]
    
    return {
        "total_projects": len(projects),
        "total_budget": total_budget,
        "total_surface": total_surface,
        "total_alerts": len(alerts),
        "pending_tasks": len(pending_tasks),
        "projects_by_usage": {},
        "projects_by_stage": {},
        "recent_projects": projects[:5]
    }

# =============================================================================
# PDF GENERATION ROUTES
# =============================================================================

class PDFExportRequest(BaseModel):
    report_type: str  # macro_budget, detailed_cost, feasibility, arbitration, client_validation
    format: str = "A4_portrait"  # A4_portrait, A4_landscape, A3_landscape, board
    include_signature: bool = False
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None

@api_router.post("/projects/{project_id}/export-pdf")
async def export_pdf(project_id: str, request: PDFExportRequest, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    
    # Determine page size
    if request.format == "A4_portrait":
        pagesize = A4
    elif request.format == "A4_landscape":
        pagesize = landscape(A4)
    elif request.format == "A3_landscape":
        pagesize = landscape(A3)
    else:
        pagesize = landscape(A4)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesize, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='FrenchTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name='FrenchSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#64748B')
    ))
    styles.add(ParagraphStyle(
        name='FrenchBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8
    ))
    
    elements = []
    
    # Cover page
    elements.append(Spacer(1, 3*cm))
    if request.company_name:
        elements.append(Paragraph(request.company_name, styles['FrenchSubtitle']))
    elements.append(Paragraph("DOSSIER ÉCONOMIQUE", styles['FrenchTitle']))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(project['project_name'], styles['Heading1']))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"Client: {project['client_name']}", styles['FrenchBody']))
    elements.append(Paragraph(f"Surface: {project.get('target_surface_m2', 0):,.0f} m²".replace(',', ' '), styles['FrenchBody']))
    elements.append(Paragraph(f"Budget cible: {project.get('target_budget', 0):,.0f} €".replace(',', ' '), styles['FrenchBody']))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y')}", styles['FrenchBody']))
    
    elements.append(PageBreak())
    
    # Summary section
    elements.append(Paragraph("SYNTHÈSE ÉCONOMIQUE", styles['Heading1']))
    elements.append(Spacer(1, 0.5*cm))
    
    macro_total = sum(c.get("target_amount", 0) for c in categories)
    micro_total = sum(c.get("estimated_amount", 0) for c in categories)
    
    summary_data = [
        ["Indicateur", "Valeur"],
        ["Budget cible", f"{project.get('target_budget', 0):,.0f} €".replace(',', ' ')],
        ["Enveloppe macro", f"{macro_total:,.0f} €".replace(',', ' ')],
        ["Estimation micro", f"{micro_total:,.0f} €".replace(',', ' ')],
        ["Écart", f"{micro_total - macro_total:,.0f} €".replace(',', ' ')],
        ["Coût / m²", f"{micro_total / project.get('target_surface_m2', 1):,.0f} €/m²".replace(',', ' ') if project.get('target_surface_m2') else "N/A"],
    ]
    
    summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 1*cm))
    
    # Macro categories table
    elements.append(Paragraph("RÉPARTITION PAR CATÉGORIE", styles['Heading2']))
    elements.append(Spacer(1, 0.5*cm))
    
    cat_data = [["Catégorie", "Cible", "Estimé", "Écart", "%"]]
    for cat in categories:
        variance = cat.get("estimated_amount", 0) - cat.get("target_amount", 0)
        variance_pct = (variance / cat["target_amount"] * 100) if cat["target_amount"] > 0 else 0
        cat_data.append([
            cat["name"],
            f"{cat.get('target_amount', 0):,.0f} €".replace(',', ' '),
            f"{cat.get('estimated_amount', 0):,.0f} €".replace(',', ' '),
            f"{variance:,.0f} €".replace(',', ' '),
            f"{variance_pct:.1f}%"
        ])
    
    cat_table = Table(cat_data, colWidths=[5*cm, 3.5*cm, 3.5*cm, 3*cm, 2*cm])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    elements.append(cat_table)
    
    # Signature section if requested
    if request.include_signature:
        elements.append(PageBreak())
        elements.append(Paragraph("PAGE DE SIGNATURE", styles['Heading1']))
        elements.append(Spacer(1, 2*cm))
        
        sig_data = [
            ["", "Client", "Économiste"],
            ["Nom", "", ""],
            ["Date", "", ""],
            ["Signature", "", ""],
        ]
        sig_table = Table(sig_data, colWidths=[4*cm, 6*cm, 6*cm], rowHeights=[1*cm, 1.5*cm, 1.5*cm, 3*cm])
        sig_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(sig_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"CostPilot_{project['project_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# =============================================================================
# MACRO VS MICRO COMPARISON ROUTE
# =============================================================================

@api_router.get("/projects/{project_id}/macro-vs-micro")
async def get_macro_vs_micro(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    
    comparison = []
    total_macro = 0
    total_micro = 0
    
    for cat in categories:
        macro_amount = cat.get("target_amount", 0)
        micro_amount = cat.get("estimated_amount", 0)
        variance = micro_amount - macro_amount
        variance_pct = (variance / macro_amount * 100) if macro_amount > 0 else 0
        
        status = "green"
        if variance_pct > 10:
            status = "red"
        elif variance_pct > 5:
            status = "orange"
        
        total_macro += macro_amount
        total_micro += micro_amount
        
        comparison.append({
            "category_id": cat["id"],
            "category_name": cat["name"],
            "category_code": cat["code"],
            "validated_macro_amount": macro_amount,
            "current_micro_total": micro_amount,
            "variance_amount": variance,
            "variance_percentage": variance_pct,
            "status_indicator": status
        })
    
    return {
        "project_id": project_id,
        "is_locked": project.get("macro_envelope_locked", False),
        "comparison": comparison,
        "totals": {
            "macro_total": total_macro,
            "micro_total": total_micro,
            "variance": total_micro - total_macro,
            "variance_percentage": ((total_micro - total_macro) / total_macro * 100) if total_macro > 0 else 0
        }
    }

# =============================================================================
# HEALTH CHECK
# =============================================================================

@api_router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": now_iso()}

# =============================================================================
# MODULE IA 1: BUDGET ANALYSIS - Détection d'anomalies
# =============================================================================

@api_router.get("/projects/{project_id}/analysis/budget-health")
async def analyze_budget_health(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Analyse la santé du budget et détecte les anomalies"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    items = await db.micro_items.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    
    # Pricing library for comparison
    pricing = await db.pricing_library.find(
        {"building_type": project.get("project_usage", "housing")},
        {"_id": 0}
    ).to_list(500)
    
    alerts = []
    surface_m2 = project.get("target_surface_m2", 1) or 1
    
    # Calculate totals
    total_micro = sum(item.get("amount", item.get("quantity", 0) * item.get("unit_price", 0)) for item in items) or 0
    total_macro = sum(cat.get("target_amount", 0) or 0 for cat in categories) or 0
    
    # Budget ratios by category
    budget_ratios = {}
    for cat in categories:
        cat_items = [i for i in items if i.get("macro_category_id") == cat.get("id")]
        cat_total = sum(item.get("amount", item.get("quantity", 0) * item.get("unit_price", 0)) for item in cat_items)
        budget_ratios[cat.get("code")] = cat_total / total_micro if total_micro > 0 else 0
    
    # Expected ratios by project type
    expected_ratios = {
        "housing": {"INF": (0.05, 0.12), "SUP": (0.18, 0.28), "FAC": (0.14, 0.22), "INT": (0.20, 0.30), "TEC": (0.14, 0.22)},
        "office": {"INF": (0.04, 0.10), "SUP": (0.16, 0.26), "FAC": (0.16, 0.26), "INT": (0.18, 0.28), "TEC": (0.18, 0.28)},
        "hotel": {"INF": (0.04, 0.10), "SUP": (0.14, 0.24), "FAC": (0.12, 0.22), "INT": (0.25, 0.38), "TEC": (0.18, 0.28)},
    }
    
    project_type = project.get("project_usage", "housing")
    type_ratios = expected_ratios.get(project_type, expected_ratios["housing"])
    
    # 1. Check distribution anomalies
    for cat in categories:
        code = cat.get("code")
        ratio = budget_ratios.get(code, 0)
        expected = type_ratios.get(code)
        
        if expected:
            min_ratio, max_ratio = expected
            if ratio < min_ratio * 0.7:
                alerts.append({
                    "type": "distribution_anomaly",
                    "severity": "critical",
                    "category": code,
                    "message": f"{cat.get('name')} représente {ratio*100:.1f}% (attendu: {min_ratio*100:.0f}-{max_ratio*100:.0f}%)",
                    "recommendation": "Vérifier que tous les postes sont chiffrés"
                })
            elif ratio < min_ratio:
                alerts.append({
                    "type": "distribution_anomaly",
                    "severity": "warning",
                    "category": code,
                    "message": f"{cat.get('name')} semble sous-estimé ({ratio*100:.1f}%)",
                    "recommendation": "Revoir le chiffrage de ce lot"
                })
            elif ratio > max_ratio * 1.3:
                alerts.append({
                    "type": "distribution_anomaly",
                    "severity": "critical",
                    "category": code,
                    "message": f"{cat.get('name')} représente {ratio*100:.1f}% (attendu: {min_ratio*100:.0f}-{max_ratio*100:.0f}%)",
                    "recommendation": "Possible surestimation - vérifier les prix unitaires"
                })
    
    # 2. Check macro vs micro gaps
    for cat in categories:
        cat_items = [i for i in items if i.get("macro_category_id") == cat.get("id")]
        cat_total = sum(item.get("amount", item.get("quantity", 0) * item.get("unit_price", 0)) for item in cat_items)
        target = cat.get("target_amount", 0)
        
        if target > 0 and cat_total > 0:
            gap = (cat_total - target) / target
            if abs(gap) > 0.20:
                alerts.append({
                    "type": "macro_micro_gap",
                    "severity": "critical",
                    "category": cat.get("code"),
                    "message": f"Écart de {gap*100:.1f}% sur {cat.get('name')}",
                    "macro_value": target,
                    "micro_value": cat_total,
                    "recommendation": "Ajuster l'enveloppe ou revoir le chiffrage"
                })
            elif abs(gap) > 0.10:
                alerts.append({
                    "type": "macro_micro_gap",
                    "severity": "warning",
                    "category": cat.get("code"),
                    "message": f"Écart de {gap*100:.1f}% sur {cat.get('name')}",
                    "macro_value": target,
                    "micro_value": cat_total,
                    "recommendation": "À surveiller"
                })
    
    # 3. Check missing categories
    items_by_cat = {i.get("macro_category_id") for i in items}
    for cat in categories:
        if cat.get("id") not in items_by_cat and cat.get("target_amount", 0) > 0:
            alerts.append({
                "type": "missing_items",
                "severity": "warning",
                "category": cat.get("code"),
                "message": f"Aucun poste chiffré pour {cat.get('name')}",
                "recommendation": f"Enveloppe de {cat.get('target_amount'):,.0f} € sans détail"
            })
    
    # 4. Check unit prices vs library
    for item in items[:50]:  # Limit to first 50 for performance
        similar = [p for p in pricing if p.get("lot_code") == item.get("lot_code") and p.get("unit") == item.get("unit")]
        if similar:
            avg_price = sum(p.get("unit_price_avg", 0) for p in similar) / len(similar)
            if avg_price > 0:
                variance = (item.get("unit_price", 0) - avg_price) / avg_price
                if variance > 0.25:
                    alerts.append({
                        "type": "unit_price_anomaly",
                        "severity": "critical" if variance > 0.40 else "warning",
                        "item_id": item.get("id"),
                        "message": f"Prix élevé: {item.get('description')[:40]}...",
                        "current_price": item.get("unit_price"),
                        "reference_price": avg_price,
                        "variance": variance,
                        "recommendation": f"+{variance*100:.0f}% vs référence ({avg_price:.0f} €/{item.get('unit')})"
                    })
                elif variance < -0.35:
                    alerts.append({
                        "type": "unit_price_anomaly",
                        "severity": "warning",
                        "item_id": item.get("id"),
                        "message": f"Prix bas: {item.get('description')[:40]}...",
                        "current_price": item.get("unit_price"),
                        "reference_price": avg_price,
                        "variance": variance,
                        "recommendation": f"{variance*100:.0f}% vs référence - vérifier qualité"
                    })
    
    # Sort by severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda x: severity_order.get(x.get("severity"), 2))
    
    # Calculate health score
    health_score = 100
    for alert in alerts:
        if alert.get("severity") == "critical":
            health_score -= 15
        elif alert.get("severity") == "warning":
            health_score -= 5
    health_score = max(0, health_score)
    
    return {
        "project_id": project_id,
        "analysis_date": now_iso(),
        "health_score": health_score,
        "alerts": alerts,
        "summary": {
            "total_alerts": len(alerts),
            "critical": len([a for a in alerts if a.get("severity") == "critical"]),
            "warnings": len([a for a in alerts if a.get("severity") == "warning"]),
        },
        "metrics": {
            "total_micro": total_micro,
            "total_macro": total_macro,
            "ratio_m2": total_micro / surface_m2 if surface_m2 > 0 else 0,
            "budget_ratios": budget_ratios,
        }
    }

# =============================================================================
# MODULE IA 2: OPTIMIZATION PROPOSALS - Variantes techniques
# =============================================================================

@api_router.get("/projects/{project_id}/analysis/optimization-proposals")
async def get_optimization_proposals(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Génère des propositions d'optimisation budgétaire"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    items = await db.micro_items.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    
    surface_m2 = project.get("target_surface_m2", 1) or 1
    target_budget = project.get("target_budget", 0) or 0
    current_budget = sum(item.get("amount", item.get("quantity", 0) * item.get("unit_price", 0)) for item in items) or 0
    
    # If no target or under budget, no optimization needed
    if target_budget <= 0 or current_budget <= target_budget:
        return {
            "project_id": project_id,
            "needs_optimization": False,
            "current_budget": current_budget,
            "target_budget": target_budget,
            "proposals": []
        }
    
    budget_gap = current_budget - target_budget
    proposals = []
    
    # Technical variants database
    variants_db = {
        "FAC": [
            {"id": "fac_mur_rideau_to_bardage", "name": "Mur rideau → Bardage", "saving_percent": 0.25, "applicable": ["office", "retail"]},
            {"id": "fac_pierre_to_enduit", "name": "Pierre → Enduit", "saving_percent": 0.50, "applicable": ["housing", "hotel"]},
            {"id": "fac_bso_to_stores", "name": "BSO → Stores intérieurs", "saving_percent": 0.35, "applicable": ["office", "housing"]},
        ],
        "SUP": [
            {"id": "sup_beton_to_mixte", "name": "Béton → Mixte", "saving_percent": 0.12, "applicable": ["office", "retail"]},
            {"id": "sup_dalle_to_predalle", "name": "Dalle pleine → Prédalles", "saving_percent": 0.15, "applicable": ["housing", "office"]},
        ],
        "INT": [
            {"id": "int_parquet_to_pvc", "name": "Parquet → PVC LVT", "saving_percent": 0.35, "applicable": ["housing", "office", "hotel"]},
            {"id": "int_cloison_vitree_to_pleine", "name": "Cloison vitrée → Pleine", "saving_percent": 0.85, "applicable": ["office"]},
        ],
        "TEC": [
            {"id": "tec_vmc_df_to_sf", "name": "VMC DF → SF", "saving_percent": 0.60, "applicable": ["housing"]},
            {"id": "tec_gtb_premium_to_standard", "name": "GTB évoluée → Standard", "saving_percent": 0.40, "applicable": ["office", "retail"]},
        ],
    }
    
    project_type = project.get("project_usage", "housing")
    
    for cat in categories:
        cat_code = cat.get("code")
        cat_variants = variants_db.get(cat_code, [])
        
        cat_items = [i for i in items if i.get("macro_category_id") == cat.get("id")]
        cat_total = sum(item.get("amount", item.get("quantity", 0) * item.get("unit_price", 0)) for item in cat_items)
        
        for variant in cat_variants:
            if project_type not in variant.get("applicable", []):
                continue
            
            potential_saving = cat_total * variant.get("saving_percent", 0)
            
            if potential_saving > current_budget * 0.01:  # > 1% du budget
                proposals.append({
                    "variant_id": variant.get("id"),
                    "category": cat_code,
                    "category_name": cat.get("name"),
                    "name": variant.get("name"),
                    "potential_saving": round(potential_saving),
                    "saving_percent": round(potential_saving / current_budget * 100, 1),
                    "saving_per_m2": round(potential_saving / surface_m2, 2),
                    "priority": "high" if potential_saving > budget_gap * 0.3 else "medium" if potential_saving > budget_gap * 0.1 else "low"
                })
    
    # Sort by saving
    proposals.sort(key=lambda x: x.get("potential_saving", 0), reverse=True)
    
    # Add cumulative savings
    cumulative = 0
    for p in proposals:
        cumulative += p.get("potential_saving", 0)
        p["cumulative_saving"] = cumulative
        p["covers_gap"] = cumulative >= budget_gap
    
    return {
        "project_id": project_id,
        "needs_optimization": True,
        "current_budget": current_budget,
        "target_budget": target_budget,
        "budget_gap": budget_gap,
        "gap_percent": round(budget_gap / target_budget * 100, 1),
        "proposals": proposals,
        "summary": {
            "proposals_count": len(proposals),
            "total_potential_savings": sum(p.get("potential_saving", 0) for p in proposals),
            "can_meet_target": any(p.get("covers_gap") for p in proposals),
            "min_proposals_needed": next((i+1 for i, p in enumerate(proposals) if p.get("covers_gap")), len(proposals))
        }
    }

# =============================================================================
# MODULE IA 3: PROJECT INTELLIGENCE - Base de benchmarks
# =============================================================================

@api_router.post("/projects/{project_id}/finalize")
async def finalize_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Finalise un projet et enregistre les données pour le benchmark"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    items = await db.micro_items.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    
    surface_m2 = project.get("target_surface_m2", 1) or 1
    total_cost = sum(item.get("amount", item.get("quantity", 0) * item.get("unit_price", 0)) for item in items) or 0
    
    # Build cost breakdown by category
    breakdown = {}
    for cat in categories:
        cat_items = [i for i in items if i.get("macro_category_id") == cat.get("id")]
        cat_total = sum(item.get("amount", item.get("quantity", 0) * item.get("unit_price", 0)) for item in cat_items)
        breakdown[cat.get("code")] = {
            "amount": cat_total,
            "ratio": cat_total / total_cost if total_cost > 0 else 0,
            "ratio_m2": cat_total / surface_m2 if surface_m2 > 0 else 0
        }
    
    # Create benchmark entry
    benchmark = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "project_name": project.get("project_name"),
        "project_usage": project.get("project_usage"),
        "quality_level": project.get("quality_level"),
        "location": project.get("location"),
        "surface_m2": surface_m2,
        "number_of_levels": project.get("number_of_levels_estimate"),
        "total_cost": total_cost,
        "ratio_m2": total_cost / surface_m2 if surface_m2 > 0 else 0,
        "breakdown": breakdown,
        "items_count": len(items),
        "finalized_at": now_iso(),
        "finalized_by": current_user.get("id"),
    }
    
    await db.project_benchmarks.insert_one(benchmark)
    
    # Update project status
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"status": "finalized", "finalized_at": now_iso(), "final_cost": total_cost}}
    )
    
    return {"success": True, "benchmark_id": benchmark["id"]}

@api_router.get("/benchmarks")
async def get_benchmarks(
    project_usage: Optional[str] = None,
    quality_level: Optional[str] = None,
    min_surface: Optional[int] = None,
    max_surface: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les benchmarks de projets pour comparaison"""
    query = {}
    if project_usage:
        query["project_usage"] = project_usage
    if quality_level:
        query["quality_level"] = quality_level
    if min_surface:
        query["surface_m2"] = {"$gte": min_surface}
    if max_surface:
        if "surface_m2" in query:
            query["surface_m2"]["$lte"] = max_surface
        else:
            query["surface_m2"] = {"$lte": max_surface}
    
    benchmarks = await db.project_benchmarks.find(query, {"_id": 0}).to_list(100)
    
    # Calculate aggregated statistics
    if benchmarks:
        ratios = [b.get("ratio_m2", 0) for b in benchmarks if b.get("ratio_m2")]
        avg_ratio = sum(ratios) / len(ratios) if ratios else 0
        min_ratio = min(ratios) if ratios else 0
        max_ratio = max(ratios) if ratios else 0
    else:
        avg_ratio = min_ratio = max_ratio = 0
    
    return {
        "benchmarks": benchmarks,
        "count": len(benchmarks),
        "statistics": {
            "average_ratio_m2": round(avg_ratio, 2),
            "min_ratio_m2": round(min_ratio, 2),
            "max_ratio_m2": round(max_ratio, 2),
        }
    }

@api_router.get("/benchmarks/compare/{project_id}")
async def compare_project_to_benchmarks(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Compare un projet aux benchmarks similaires"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Get similar benchmarks
    query = {
        "project_usage": project.get("project_usage"),
        "quality_level": project.get("quality_level"),
    }
    
    benchmarks = await db.project_benchmarks.find(query, {"_id": 0}).to_list(50)
    
    # Get current project costs
    items = await db.micro_items.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    surface_m2 = project.get("target_surface_m2", 1) or 1
    current_cost = sum(item.get("amount", item.get("quantity", 0) * item.get("unit_price", 0)) for item in items) or 0
    current_ratio = current_cost / surface_m2 if surface_m2 > 0 else 0
    
    if not benchmarks:
        return {
            "project_id": project_id,
            "current_ratio_m2": round(current_ratio, 2),
            "comparison": None,
            "message": "Pas de benchmarks similaires disponibles"
        }
    
    # Calculate statistics
    ratios = [b.get("ratio_m2", 0) for b in benchmarks]
    avg_ratio = sum(ratios) / len(ratios)
    min_ratio = min(ratios)
    max_ratio = max(ratios)
    
    # Position of current project
    position = "within_range"
    if current_ratio < min_ratio * 0.9:
        position = "below_range"
    elif current_ratio > max_ratio * 1.1:
        position = "above_range"
    
    variance = (current_ratio - avg_ratio) / avg_ratio if avg_ratio > 0 else 0
    
    return {
        "project_id": project_id,
        "current_ratio_m2": round(current_ratio, 2),
        "comparison": {
            "benchmarks_count": len(benchmarks),
            "average_ratio_m2": round(avg_ratio, 2),
            "min_ratio_m2": round(min_ratio, 2),
            "max_ratio_m2": round(max_ratio, 2),
            "variance_vs_average": round(variance * 100, 1),
            "position": position,
        },
        "recommendation": get_benchmark_recommendation(position, variance)
    }

def get_benchmark_recommendation(position: str, variance: float) -> str:
    if position == "below_range":
        return "Le projet est significativement moins cher que les références. Vérifier que tous les postes sont bien chiffrés."
    elif position == "above_range":
        return "Le projet est plus cher que les références. Analyser les postes pour identifier les optimisations possibles."
    elif variance > 0.1:
        return "Le projet est légèrement au-dessus de la moyenne des références."
    elif variance < -0.1:
        return "Le projet est légèrement en-dessous de la moyenne des références."
    else:
        return "Le projet est aligné avec les références de projets similaires."

# =============================================================================
# PHASE 1: LECTURE AUTOMATIQUE DES PLANS (PDF / IFC)
# =============================================================================

class PlanAnalysisRequest(BaseModel):
    project_id: str
    file_name: str
    file_type: str  # pdf, image, ifc
    file_data: Optional[str] = None  # Base64 encoded

class ZoneData(BaseModel):
    id: str
    name: str
    zone_type: str  # habitable, circulation, technique, sanitaire, stockage, parking
    level: int
    surface: float
    confidence: float

class LevelData(BaseModel):
    number: int
    name: str
    altitude: float = 0.0

class PlanAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    file_name: str
    file_type: str
    levels: List[dict]
    zones: List[dict]
    ifc_elements: Optional[dict] = None
    stats: dict
    created_at: str

@api_router.post("/projects/{project_id}/plan-analysis", response_model=PlanAnalysisResponse)
async def analyze_plan(project_id: str, request: PlanAnalysisRequest, current_user: dict = Depends(get_current_user)):
    """Analyse un plan (PDF, image ou IFC) pour extraire les surfaces"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    analysis_id = generate_uuid()
    now = now_iso()
    
    # Générer des données d'analyse basées sur le type de fichier
    levels = []
    zones = []
    ifc_elements = None
    
    if request.file_type == "ifc":
        # Simulation d'extraction IFC plus complète
        levels = [
            {"number": -1, "name": "Sous-sol 1", "altitude": -3.0},
            {"number": 0, "name": "Rez-de-chaussée", "altitude": 0.0},
            {"number": 1, "name": "Étage 1", "altitude": 3.0},
            {"number": 2, "name": "Étage 2", "altitude": 6.0},
            {"number": 3, "name": "Étage 3", "altitude": 9.0},
        ]
        
        zones = [
            # Sous-sol
            {"id": generate_uuid(), "name": "Parking", "zone_type": "parking", "level": -1, "surface": 450, "confidence": 0.95},
            {"id": generate_uuid(), "name": "Local technique TGBT", "zone_type": "technique", "level": -1, "surface": 25, "confidence": 0.92},
            {"id": generate_uuid(), "name": "Local CVC", "zone_type": "technique", "level": -1, "surface": 35, "confidence": 0.90},
            {"id": generate_uuid(), "name": "Caves", "zone_type": "stockage", "level": -1, "surface": 120, "confidence": 0.88},
            # RDC
            {"id": generate_uuid(), "name": "Hall entrée", "zone_type": "circulation", "level": 0, "surface": 45, "confidence": 0.94},
            {"id": generate_uuid(), "name": "Local vélos", "zone_type": "stockage", "level": 0, "surface": 25, "confidence": 0.90},
            {"id": generate_uuid(), "name": "Local poubelles", "zone_type": "technique", "level": 0, "surface": 15, "confidence": 0.88},
            {"id": generate_uuid(), "name": "Logement T3 - A01", "zone_type": "habitable", "level": 0, "surface": 68, "confidence": 0.96},
            {"id": generate_uuid(), "name": "Logement T2 - A02", "zone_type": "habitable", "level": 0, "surface": 48, "confidence": 0.95},
            # Étages
            {"id": generate_uuid(), "name": "Palier niveau 1", "zone_type": "circulation", "level": 1, "surface": 15, "confidence": 0.93},
            {"id": generate_uuid(), "name": "Logement T4 - B01", "zone_type": "habitable", "level": 1, "surface": 88, "confidence": 0.94},
            {"id": generate_uuid(), "name": "Logement T2 - B02", "zone_type": "habitable", "level": 1, "surface": 45, "confidence": 0.95},
            {"id": generate_uuid(), "name": "Logement T3 - B03", "zone_type": "habitable", "level": 1, "surface": 65, "confidence": 0.93},
            {"id": generate_uuid(), "name": "Palier niveau 2", "zone_type": "circulation", "level": 2, "surface": 15, "confidence": 0.93},
            {"id": generate_uuid(), "name": "Logement T4 - C01", "zone_type": "habitable", "level": 2, "surface": 88, "confidence": 0.94},
            {"id": generate_uuid(), "name": "Logement T2 - C02", "zone_type": "habitable", "level": 2, "surface": 45, "confidence": 0.95},
            {"id": generate_uuid(), "name": "Logement T3 - C03", "zone_type": "habitable", "level": 2, "surface": 65, "confidence": 0.93},
            {"id": generate_uuid(), "name": "Palier niveau 3", "zone_type": "circulation", "level": 3, "surface": 15, "confidence": 0.93},
            {"id": generate_uuid(), "name": "Logement T5 - D01", "zone_type": "habitable", "level": 3, "surface": 115, "confidence": 0.92},
            {"id": generate_uuid(), "name": "Logement T3 - D02", "zone_type": "habitable", "level": 3, "surface": 72, "confidence": 0.94},
        ]
        
        ifc_elements = {
            "walls": {"count": 156, "surface": 2450, "linear_meters": 892},
            "slabs": {"count": 12, "surface": 1850, "volume": 370},
            "doors": {"count": 48, "interior": 36, "exterior": 12},
            "windows": {"count": 72, "surface": 145},
            "stairs": {"count": 2, "flights": 8},
            "columns": {"count": 24},
            "beams": {"count": 48, "linear_meters": 384},
            "spaces": {"count": len(zones)}
        }
    else:
        # PDF/Image - simulation avec OCR
        levels = [
            {"number": 0, "name": "Rez-de-chaussée", "altitude": 0.0},
            {"number": 1, "name": "Étage 1", "altitude": 3.0},
        ]
        
        zones = [
            {"id": generate_uuid(), "name": "Zone A - Séjour", "zone_type": "habitable", "level": 0, "surface": 35, "confidence": 0.75},
            {"id": generate_uuid(), "name": "Zone B - Cuisine", "zone_type": "habitable", "level": 0, "surface": 12, "confidence": 0.72},
            {"id": generate_uuid(), "name": "Zone C - Entrée", "zone_type": "circulation", "level": 0, "surface": 8, "confidence": 0.68},
            {"id": generate_uuid(), "name": "Zone D - Sanitaires", "zone_type": "sanitaire", "level": 0, "surface": 6, "confidence": 0.70},
            {"id": generate_uuid(), "name": "Zone E - Chambre 1", "zone_type": "habitable", "level": 1, "surface": 14, "confidence": 0.73},
            {"id": generate_uuid(), "name": "Zone F - Chambre 2", "zone_type": "habitable", "level": 1, "surface": 12, "confidence": 0.71},
            {"id": generate_uuid(), "name": "Zone G - Palier", "zone_type": "circulation", "level": 1, "surface": 5, "confidence": 0.65},
            {"id": generate_uuid(), "name": "Zone H - SDB", "zone_type": "sanitaire", "level": 1, "surface": 5, "confidence": 0.68},
        ]
    
    # Calcul des statistiques
    surface_utile = sum(z["surface"] for z in zones if z["zone_type"] == "habitable")
    circulation = sum(z["surface"] for z in zones if z["zone_type"] == "circulation")
    technique = sum(z["surface"] for z in zones if z["zone_type"] in ["technique", "sanitaire"])
    parking = sum(z["surface"] for z in zones if z["zone_type"] == "parking")
    sdp_total = sum(z["surface"] for z in zones)
    
    stats = {
        "sdp_total": sdp_total,
        "surface_utile": surface_utile,
        "circulation": circulation,
        "technique": technique,
        "parking": parking,
        "ratio_su_sdp": round(surface_utile / sdp_total * 100, 1) if sdp_total > 0 else 0,
        "confidence_moyenne": round(sum(z["confidence"] for z in zones) / len(zones) * 100, 1) if zones else 0
    }
    
    # Sauvegarder l'analyse
    analysis_doc = {
        "id": analysis_id,
        "project_id": project_id,
        "file_name": request.file_name,
        "file_type": request.file_type,
        "levels": levels,
        "zones": zones,
        "ifc_elements": ifc_elements,
        "stats": stats,
        "created_at": now
    }
    
    await db.plan_analyses.insert_one(analysis_doc)
    
    return PlanAnalysisResponse(**analysis_doc)

@api_router.get("/projects/{project_id}/plan-analysis", response_model=List[PlanAnalysisResponse])
async def get_plan_analyses(project_id: str, current_user: dict = Depends(get_current_user)):
    """Récupère les analyses de plans d'un projet"""
    analyses = await db.plan_analyses.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    return [PlanAnalysisResponse(**a) for a in analyses]

@api_router.get("/projects/{project_id}/plan-analysis/{analysis_id}", response_model=PlanAnalysisResponse)
async def get_plan_analysis(project_id: str, analysis_id: str, current_user: dict = Depends(get_current_user)):
    """Récupère une analyse de plan spécifique"""
    analysis = await db.plan_analyses.find_one({"id": analysis_id, "project_id": project_id}, {"_id": 0})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return PlanAnalysisResponse(**analysis)

@api_router.put("/projects/{project_id}/plan-analysis/{analysis_id}/zones")
async def update_plan_zones(
    project_id: str, 
    analysis_id: str, 
    zones: List[dict], 
    current_user: dict = Depends(get_current_user)
):
    """Met à jour les zones d'une analyse (corrections manuelles)"""
    analysis = await db.plan_analyses.find_one({"id": analysis_id, "project_id": project_id}, {"_id": 0})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    # Recalculer les statistiques
    surface_utile = sum(z["surface"] for z in zones if z.get("zone_type") == "habitable")
    circulation = sum(z["surface"] for z in zones if z.get("zone_type") == "circulation")
    technique = sum(z["surface"] for z in zones if z.get("zone_type") in ["technique", "sanitaire"])
    parking = sum(z["surface"] for z in zones if z.get("zone_type") == "parking")
    sdp_total = sum(z["surface"] for z in zones)
    
    stats = {
        "sdp_total": sdp_total,
        "surface_utile": surface_utile,
        "circulation": circulation,
        "technique": technique,
        "parking": parking,
        "ratio_su_sdp": round(surface_utile / sdp_total * 100, 1) if sdp_total > 0 else 0,
        "confidence_moyenne": round(sum(z.get("confidence", 1) for z in zones) / len(zones) * 100, 1) if zones else 0
    }
    
    await db.plan_analyses.update_one(
        {"id": analysis_id},
        {"$set": {"zones": zones, "stats": stats}}
    )
    
    return {"message": "Zones mises à jour", "stats": stats}

@api_router.delete("/projects/{project_id}/plan-analysis/{analysis_id}")
async def delete_plan_analysis(project_id: str, analysis_id: str, current_user: dict = Depends(get_current_user)):
    """Supprime une analyse de plan"""
    result = await db.plan_analyses.delete_one({"id": analysis_id, "project_id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return {"message": "Analyse supprimée"}

# =============================================================================
# PHASE 2: GÉNÉRATEUR DPGF AUTOMATIQUE
# =============================================================================

# Structure des macro-lots DPGF
MACRO_LOTS_DPGF = [
    {"code": "01", "name": "Terrassements", "category": "infrastructure"},
    {"code": "02", "name": "VRD", "category": "infrastructure"},
    {"code": "03", "name": "Gros œuvre", "category": "structure"},
    {"code": "04", "name": "Charpente / Superstructure", "category": "structure"},
    {"code": "05", "name": "Couverture / Étanchéité", "category": "envelope"},
    {"code": "06", "name": "Façade / Enveloppe", "category": "envelope"},
    {"code": "07", "name": "Menuiseries extérieures", "category": "envelope"},
    {"code": "08", "name": "Cloisonnement / Doublages", "category": "interior"},
    {"code": "09", "name": "Revêtements sols", "category": "interior"},
    {"code": "10", "name": "Revêtements muraux", "category": "interior"},
    {"code": "11", "name": "Peinture", "category": "interior"},
    {"code": "12", "name": "Menuiseries intérieures", "category": "interior"},
    {"code": "13", "name": "Plomberie / Sanitaires", "category": "technical"},
    {"code": "14", "name": "CVC (Chauffage, Ventilation, Clim)", "category": "technical"},
    {"code": "15", "name": "Électricité CFO", "category": "technical"},
    {"code": "16", "name": "Courants faibles CFA", "category": "technical"},
    {"code": "17", "name": "Ascenseurs", "category": "technical"},
    {"code": "18", "name": "Équipements spéciaux", "category": "technical"},
    {"code": "19", "name": "Aménagements extérieurs", "category": "exterior"},
    {"code": "20", "name": "Aléas et imprévus", "category": "contingency"},
]

class DPGFMode(str, Enum):
    FEASIBILITY = "feasibility"  # Mode Faisabilité - ratios simplifiés
    APS_APD = "aps_apd"         # Mode APS/APD - détail intermédiaire
    DCE = "dce"                  # Mode DCE simplifié - détail complet

class DPGFGenerateRequest(BaseModel):
    project_id: str
    mode: DPGFMode = DPGFMode.APS_APD
    plan_analysis_id: Optional[str] = None  # Utiliser les données d'une analyse de plan
    use_pricing_library: bool = True
    custom_adjustments: Dict[str, float] = {}  # Ajustements par lot (%)

class DPGFLineItem(BaseModel):
    lot_code: str
    lot_name: str
    sub_lot_code: Optional[str] = None
    sub_lot_name: Optional[str] = None
    item_code: str
    description: str
    unit: str
    quantity: float
    unit_price: float
    total_price: float

class DPGFLotSummary(BaseModel):
    code: str
    name: str
    category: str
    items_count: int
    total_ht: float
    percentage: float

class DPGFResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    mode: str
    created_at: str
    lots: List[dict]
    items: List[dict]
    summary: dict

@api_router.post("/projects/{project_id}/dpgf/generate", response_model=DPGFResponse)
async def generate_dpgf(project_id: str, request: DPGFGenerateRequest, current_user: dict = Depends(get_current_user)):
    """Génère un DPGF automatique basé sur le programme et les ratios"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    dpgf_id = generate_uuid()
    now = now_iso()
    
    # Récupérer les données du projet
    surface_sdp = project.get("target_surface_m2", 1000) or 1000
    quality_level = project.get("quality_level", "standard") or "standard"
    project_usage = project.get("project_usage", "housing") or "housing"
    complexity = project.get("complexity_level", "medium") or "medium"
    
    # Récupérer les données d'analyse de plan si disponible
    plan_data = None
    if request.plan_analysis_id:
        plan_data = await db.plan_analyses.find_one({"id": request.plan_analysis_id}, {"_id": 0})
    
    # Surface utile (estimation si pas de données plan)
    if plan_data:
        surface_utile = plan_data.get("stats", {}).get("surface_utile", surface_sdp * 0.8)
        surface_circulation = plan_data.get("stats", {}).get("circulation", surface_sdp * 0.12)
        surface_technique = plan_data.get("stats", {}).get("technique", surface_sdp * 0.05)
        parking_surface = plan_data.get("stats", {}).get("parking", 0)
    else:
        surface_utile = surface_sdp * 0.80
        surface_circulation = surface_sdp * 0.12
        surface_technique = surface_sdp * 0.05
        parking_surface = 0
    
    # Récupérer les ratios de référence
    ratio_query = {
        "building_type": project_usage,
        "quality_level": quality_level
    }
    reference_ratio = await db.reference_ratios.find_one(ratio_query, {"_id": 0})
    
    # Prix de base au m² selon qualité
    base_prices = {
        "economic": {"infrastructure": 180, "structure": 380, "envelope": 220, "interior": 280, "technical": 320, "exterior": 80},
        "standard": {"infrastructure": 220, "structure": 450, "envelope": 320, "interior": 380, "technical": 420, "exterior": 120},
        "premium": {"infrastructure": 280, "structure": 580, "envelope": 480, "interior": 550, "technical": 580, "exterior": 180},
        "luxury": {"infrastructure": 380, "structure": 780, "envelope": 680, "interior": 780, "technical": 780, "exterior": 280}
    }
    
    prices = base_prices.get(quality_level, base_prices["standard"])
    
    # Génération des lignes DPGF
    items = []
    lots_summary = []
    
    # Facteurs de complexité
    complexity_factor = {"simple": 0.85, "medium": 1.0, "complex": 1.20, "very_complex": 1.45}.get(complexity, 1.0)
    
    # Mode de détail
    detail_level = {"feasibility": 1, "aps_apd": 2, "dce": 3}.get(request.mode, 2)
    
    for lot in MACRO_LOTS_DPGF:
        lot_items = []
        base_price = prices.get(lot["category"], 300)
        
        # Ajustement personnalisé
        adjustment = 1 + request.custom_adjustments.get(lot["code"], 0) / 100
        
        # Génération des postes selon le lot
        if lot["code"] == "01":  # Terrassements
            lot_items.append({
                "item_code": "01.01", "description": "Terrassements généraux", "unit": "m³",
                "quantity": round(surface_sdp * 0.8, 0), "unit_price": 25 * complexity_factor * adjustment
            })
            if detail_level >= 2:
                lot_items.append({
                    "item_code": "01.02", "description": "Évacuation des terres", "unit": "m³",
                    "quantity": round(surface_sdp * 0.6, 0), "unit_price": 18 * adjustment
                })
        
        elif lot["code"] == "02":  # VRD
            lot_items.append({
                "item_code": "02.01", "description": "Réseaux extérieurs (EU/EP/AEP)", "unit": "ml",
                "quantity": round(surface_sdp * 0.15, 0), "unit_price": 180 * complexity_factor * adjustment
            })
            if detail_level >= 2:
                lot_items.append({
                    "item_code": "02.02", "description": "Voirie et accès", "unit": "m²",
                    "quantity": round(surface_sdp * 0.1, 0), "unit_price": 85 * adjustment
                })
        
        elif lot["code"] == "03":  # Gros œuvre
            lot_items.append({
                "item_code": "03.01", "description": "Fondations", "unit": "m²",
                "quantity": round(surface_sdp / 3, 0), "unit_price": 95 * complexity_factor * adjustment
            })
            lot_items.append({
                "item_code": "03.02", "description": "Structure béton", "unit": "m²",
                "quantity": round(surface_sdp, 0), "unit_price": 280 * complexity_factor * adjustment
            })
            if detail_level >= 2:
                lot_items.append({
                    "item_code": "03.03", "description": "Maçonnerie", "unit": "m²",
                    "quantity": round(surface_sdp * 0.4, 0), "unit_price": 65 * adjustment
                })
        
        elif lot["code"] == "04":  # Charpente
            lot_items.append({
                "item_code": "04.01", "description": "Charpente / Structure haute", "unit": "m²",
                "quantity": round(surface_sdp / 3, 0), "unit_price": 120 * complexity_factor * adjustment
            })
        
        elif lot["code"] == "05":  # Couverture
            lot_items.append({
                "item_code": "05.01", "description": "Étanchéité toiture terrasse", "unit": "m²",
                "quantity": round(surface_sdp / 3, 0), "unit_price": 85 * complexity_factor * adjustment
            })
            if detail_level >= 2:
                lot_items.append({
                    "item_code": "05.02", "description": "Accessoires toiture", "unit": "ens",
                    "quantity": 1, "unit_price": round(surface_sdp * 8, 0) * adjustment
                })
        
        elif lot["code"] == "06":  # Façade
            facade_surface = surface_sdp * 0.6  # Estimation surface façade
            lot_items.append({
                "item_code": "06.01", "description": "Revêtement façade", "unit": "m²",
                "quantity": round(facade_surface, 0), "unit_price": 180 * complexity_factor * adjustment
            })
            if detail_level >= 2:
                lot_items.append({
                    "item_code": "06.02", "description": "Isolation thermique extérieure", "unit": "m²",
                    "quantity": round(facade_surface, 0), "unit_price": 95 * adjustment
                })
        
        elif lot["code"] == "07":  # Menuiseries ext
            nb_menuiseries = int(surface_sdp / 25)  # 1 menuiserie / 25m²
            lot_items.append({
                "item_code": "07.01", "description": "Fenêtres et portes-fenêtres", "unit": "u",
                "quantity": nb_menuiseries, "unit_price": 850 * complexity_factor * adjustment
            })
            lot_items.append({
                "item_code": "07.02", "description": "Portes d'entrée", "unit": "u",
                "quantity": max(1, int(surface_sdp / 150)), "unit_price": 2200 * adjustment
            })
        
        elif lot["code"] == "08":  # Cloisonnement
            lot_items.append({
                "item_code": "08.01", "description": "Cloisons intérieures", "unit": "m²",
                "quantity": round(surface_sdp * 0.8, 0), "unit_price": 55 * complexity_factor * adjustment
            })
            lot_items.append({
                "item_code": "08.02", "description": "Doublages", "unit": "m²",
                "quantity": round(surface_sdp * 0.5, 0), "unit_price": 42 * adjustment
            })
        
        elif lot["code"] == "09":  # Revêtements sols
            lot_items.append({
                "item_code": "09.01", "description": "Carrelage", "unit": "m²",
                "quantity": round(surface_utile * 0.4, 0), "unit_price": 75 * complexity_factor * adjustment
            })
            lot_items.append({
                "item_code": "09.02", "description": "Parquet / Sol souple", "unit": "m²",
                "quantity": round(surface_utile * 0.6, 0), "unit_price": 65 * adjustment
            })
        
        elif lot["code"] == "10":  # Revêtements murs
            lot_items.append({
                "item_code": "10.01", "description": "Faïence sanitaires", "unit": "m²",
                "quantity": round(surface_technique * 3, 0), "unit_price": 85 * complexity_factor * adjustment
            })
        
        elif lot["code"] == "11":  # Peinture
            lot_items.append({
                "item_code": "11.01", "description": "Peinture murs et plafonds", "unit": "m²",
                "quantity": round(surface_sdp * 2.5, 0), "unit_price": 18 * complexity_factor * adjustment
            })
        
        elif lot["code"] == "12":  # Menuiseries int
            nb_portes = int(surface_sdp / 20)
            lot_items.append({
                "item_code": "12.01", "description": "Portes intérieures", "unit": "u",
                "quantity": nb_portes, "unit_price": 450 * complexity_factor * adjustment
            })
            if detail_level >= 2:
                lot_items.append({
                    "item_code": "12.02", "description": "Placards", "unit": "ml",
                    "quantity": round(surface_utile * 0.15, 0), "unit_price": 380 * adjustment
                })
        
        elif lot["code"] == "13":  # Plomberie
            lot_items.append({
                "item_code": "13.01", "description": "Distribution eau / évacuation", "unit": "m²",
                "quantity": round(surface_sdp, 0), "unit_price": 45 * complexity_factor * adjustment
            })
            lot_items.append({
                "item_code": "13.02", "description": "Appareils sanitaires", "unit": "ens",
                "quantity": max(1, int(surface_sdp / 80)), "unit_price": 3500 * adjustment
            })
        
        elif lot["code"] == "14":  # CVC
            lot_items.append({
                "item_code": "14.01", "description": "Chauffage", "unit": "m²",
                "quantity": round(surface_sdp, 0), "unit_price": 65 * complexity_factor * adjustment
            })
            lot_items.append({
                "item_code": "14.02", "description": "Ventilation", "unit": "m²",
                "quantity": round(surface_sdp, 0), "unit_price": 35 * adjustment
            })
            if detail_level >= 2:
                lot_items.append({
                    "item_code": "14.03", "description": "Climatisation", "unit": "m²",
                    "quantity": round(surface_sdp * 0.3, 0), "unit_price": 85 * adjustment
                })
        
        elif lot["code"] == "15":  # CFO
            lot_items.append({
                "item_code": "15.01", "description": "Installation électrique", "unit": "m²",
                "quantity": round(surface_sdp, 0), "unit_price": 85 * complexity_factor * adjustment
            })
        
        elif lot["code"] == "16":  # CFA
            lot_items.append({
                "item_code": "16.01", "description": "Courants faibles", "unit": "m²",
                "quantity": round(surface_sdp, 0), "unit_price": 25 * complexity_factor * adjustment
            })
        
        elif lot["code"] == "17":  # Ascenseurs
            nb_asc = max(0, int(surface_sdp / 2000))
            if nb_asc > 0:
                lot_items.append({
                    "item_code": "17.01", "description": "Ascenseurs", "unit": "u",
                    "quantity": nb_asc, "unit_price": 45000 * complexity_factor * adjustment
                })
        
        elif lot["code"] == "18":  # Équipements spéciaux
            if project_usage in ["hotel", "public_facility"]:
                lot_items.append({
                    "item_code": "18.01", "description": "Équipements spécifiques", "unit": "ens",
                    "quantity": 1, "unit_price": round(surface_sdp * 50, 0) * adjustment
                })
        
        elif lot["code"] == "19":  # Aménagements ext
            lot_items.append({
                "item_code": "19.01", "description": "Espaces verts", "unit": "m²",
                "quantity": round(surface_sdp * 0.15, 0), "unit_price": 45 * complexity_factor * adjustment
            })
            if detail_level >= 2:
                lot_items.append({
                    "item_code": "19.02", "description": "Clôtures et portails", "unit": "ml",
                    "quantity": round(surface_sdp * 0.08, 0), "unit_price": 180 * adjustment
                })
        
        # Calculer les totaux pour chaque item
        for item in lot_items:
            item["total_price"] = round(item["quantity"] * item["unit_price"], 2)
            item["lot_code"] = lot["code"]
            item["lot_name"] = lot["name"]
            items.append(item)
        
        # Résumé du lot
        lot_total = sum(item["total_price"] for item in lot_items)
        lots_summary.append({
            "code": lot["code"],
            "name": lot["name"],
            "category": lot["category"],
            "items_count": len(lot_items),
            "total_ht": lot_total,
            "percentage": 0  # Calculé après
        })
    
    # Aléas (lot 20)
    subtotal = sum(lot["total_ht"] for lot in lots_summary)
    aleas_amount = subtotal * 0.05  # 5% d'aléas
    lots_summary.append({
        "code": "20",
        "name": "Aléas et imprévus",
        "category": "contingency",
        "items_count": 1,
        "total_ht": aleas_amount,
        "percentage": 5.0
    })
    items.append({
        "item_code": "20.01",
        "lot_code": "20",
        "lot_name": "Aléas et imprévus",
        "description": "Provision pour aléas et imprévus",
        "unit": "ens",
        "quantity": 1,
        "unit_price": aleas_amount,
        "total_price": aleas_amount
    })
    
    # Calcul des pourcentages
    total_ht = sum(lot["total_ht"] for lot in lots_summary)
    for lot in lots_summary:
        lot["percentage"] = round(lot["total_ht"] / total_ht * 100, 1) if total_ht > 0 else 0
    
    # Résumé global
    summary = {
        "total_ht": round(total_ht, 2),
        "total_tva": round(total_ht * 0.20, 2),
        "total_ttc": round(total_ht * 1.20, 2),
        "cost_per_m2_ht": round(total_ht / surface_sdp, 2) if surface_sdp > 0 else 0,
        "cost_per_m2_ttc": round(total_ht * 1.20 / surface_sdp, 2) if surface_sdp > 0 else 0,
        "surface_sdp": surface_sdp,
        "mode": request.mode,
        "lots_count": len(lots_summary),
        "items_count": len(items),
        "by_category": {}
    }
    
    # Totaux par catégorie
    for cat in ["infrastructure", "structure", "envelope", "interior", "technical", "exterior", "contingency"]:
        cat_total = sum(lot["total_ht"] for lot in lots_summary if lot["category"] == cat)
        summary["by_category"][cat] = {
            "total_ht": round(cat_total, 2),
            "percentage": round(cat_total / total_ht * 100, 1) if total_ht > 0 else 0
        }
    
    # Sauvegarder le DPGF
    dpgf_doc = {
        "id": dpgf_id,
        "project_id": project_id,
        "mode": request.mode,
        "plan_analysis_id": request.plan_analysis_id,
        "lots": lots_summary,
        "items": items,
        "summary": summary,
        "created_at": now
    }
    
    await db.dpgf.insert_one(dpgf_doc)
    
    return DPGFResponse(**dpgf_doc)

@api_router.get("/projects/{project_id}/dpgf", response_model=List[DPGFResponse])
async def get_dpgf_list(project_id: str, current_user: dict = Depends(get_current_user)):
    """Récupère la liste des DPGF d'un projet"""
    dpgf_list = await db.dpgf.find({"project_id": project_id}, {"_id": 0}).to_list(50)
    return [DPGFResponse(**d) for d in dpgf_list]

@api_router.get("/projects/{project_id}/dpgf/{dpgf_id}", response_model=DPGFResponse)
async def get_dpgf(project_id: str, dpgf_id: str, current_user: dict = Depends(get_current_user)):
    """Récupère un DPGF spécifique"""
    dpgf = await db.dpgf.find_one({"id": dpgf_id, "project_id": project_id}, {"_id": 0})
    if not dpgf:
        raise HTTPException(status_code=404, detail="DPGF non trouvé")
    return DPGFResponse(**dpgf)

@api_router.put("/projects/{project_id}/dpgf/{dpgf_id}/items")
async def update_dpgf_items(
    project_id: str,
    dpgf_id: str,
    items: List[dict],
    current_user: dict = Depends(get_current_user)
):
    """Met à jour les lignes du DPGF (corrections manuelles)"""
    dpgf = await db.dpgf.find_one({"id": dpgf_id, "project_id": project_id}, {"_id": 0})
    if not dpgf:
        raise HTTPException(status_code=404, detail="DPGF non trouvé")
    
    # Recalculer les totaux
    lots_summary = {}
    for item in items:
        lot_code = item.get("lot_code", "99")
        if lot_code not in lots_summary:
            lots_summary[lot_code] = {
                "code": lot_code,
                "name": item.get("lot_name", "Autre"),
                "category": "other",
                "items_count": 0,
                "total_ht": 0
            }
        lots_summary[lot_code]["items_count"] += 1
        lots_summary[lot_code]["total_ht"] += item.get("total_price", 0)
    
    lots_list = list(lots_summary.values())
    total_ht = sum(lot["total_ht"] for lot in lots_list)
    
    for lot in lots_list:
        lot["percentage"] = round(lot["total_ht"] / total_ht * 100, 1) if total_ht > 0 else 0
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    surface_sdp = (project.get("target_surface_m2", 1) if project else 1) or 1
    
    summary = {
        "total_ht": round(total_ht, 2),
        "total_tva": round(total_ht * 0.20, 2),
        "total_ttc": round(total_ht * 1.20, 2),
        "cost_per_m2_ht": round(total_ht / surface_sdp, 2),
        "cost_per_m2_ttc": round(total_ht * 1.20 / surface_sdp, 2),
        "surface_sdp": surface_sdp,
        "lots_count": len(lots_list),
        "items_count": len(items)
    }
    
    await db.dpgf.update_one(
        {"id": dpgf_id},
        {"$set": {"items": items, "lots": lots_list, "summary": summary}}
    )
    
    return {"message": "DPGF mis à jour", "summary": summary}

@api_router.delete("/projects/{project_id}/dpgf/{dpgf_id}")
async def delete_dpgf(project_id: str, dpgf_id: str, current_user: dict = Depends(get_current_user)):
    """Supprime un DPGF"""
    result = await db.dpgf.delete_one({"id": dpgf_id, "project_id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="DPGF non trouvé")
    return {"message": "DPGF supprimé"}

# =============================================================================
# PHASE 3: ASSISTANT IA D'OPTIMISATION COÛT
# =============================================================================

class OptimizationCategory(str, Enum):
    NO_IMPACT = "economie_sans_impact"  # Économie sans impact majeur
    ARCH_IMPACT = "arbitrage_architectural"  # Arbitrage avec impact architectural
    TECH_IMPACT = "arbitrage_technique"  # Arbitrage avec impact technique
    OPS_IMPACT = "arbitrage_exploitation"  # Arbitrage avec impact exploitation

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class OptimizationSuggestion(BaseModel):
    id: str
    title: str
    explanation: str
    impacted_lot: str
    impacted_lot_name: str
    savings_min: float
    savings_max: float
    confidence: float
    risk_level: str
    category: str
    implementation_difficulty: str
    priority: int

class CostAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    dpgf_id: Optional[str] = None
    analysis_date: str
    health_score: float
    anomalies: List[dict]
    suggestions: List[dict]
    comparison_with_references: dict
    summary: dict

@api_router.post("/projects/{project_id}/cost-optimization/analyze")
async def analyze_cost_optimization(
    project_id: str,
    dpgf_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Analyse IA d'optimisation des coûts"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    analysis_id = generate_uuid()
    now = now_iso()
    
    # Récupérer les données du DPGF si disponible
    dpgf_data = None
    if dpgf_id:
        dpgf_data = await db.dpgf.find_one({"id": dpgf_id, "project_id": project_id}, {"_id": 0})
    
    # Si pas de DPGF, utiliser les micro-items
    if not dpgf_data:
        items = await db.micro_items.find({"project_id": project_id}, {"_id": 0}).to_list(5000)
        total_cost = sum(item.get("amount", item.get("quantity", 0) * item.get("unit_price", 0)) for item in items)
    else:
        items = dpgf_data.get("items", [])
        total_cost = dpgf_data.get("summary", {}).get("total_ht", 0)
    
    surface_m2 = project.get("target_surface_m2", 1000) or 1000
    quality_level = project.get("quality_level", "standard") or "standard"
    project_usage = project.get("project_usage", "housing") or "housing"
    
    # Récupérer les ratios de référence
    reference_ratio = await db.reference_ratios.find_one({
        "building_type": project_usage,
        "quality_level": quality_level
    }, {"_id": 0})
    
    # Définir les ratios de référence par défaut
    default_references = {
        "housing": {"economic": 1400, "standard": 1850, "premium": 2500, "luxury": 3500},
        "office": {"economic": 1200, "standard": 1650, "premium": 2300, "luxury": 3200},
        "hotel": {"economic": 1800, "standard": 2400, "premium": 3500, "luxury": 5000},
        "retail": {"economic": 1000, "standard": 1400, "premium": 2000, "luxury": 2800},
        "public_facility": {"economic": 1600, "standard": 2100, "premium": 2800, "luxury": 3800}
    }
    
    ref_cost_m2 = default_references.get(project_usage, default_references["housing"]).get(quality_level, 1850)
    if reference_ratio:
        ref_cost_m2 = reference_ratio.get("total_cost_m2", ref_cost_m2) or reference_ratio.get("cost_avg_m2", ref_cost_m2)
    
    current_cost_m2 = total_cost / surface_m2 if surface_m2 > 0 else 0
    
    # Analyse des anomalies
    anomalies = []
    
    # Vérifier le coût global
    variance_global = (current_cost_m2 - ref_cost_m2) / ref_cost_m2 if ref_cost_m2 > 0 else 0
    
    if variance_global > 0.15:
        anomalies.append({
            "id": generate_uuid(),
            "type": "global_overrun",
            "severity": "high" if variance_global > 0.25 else "medium",
            "message": f"Coût global supérieur de {variance_global*100:.0f}% aux références ({current_cost_m2:.0f} €/m² vs {ref_cost_m2:.0f} €/m²)",
            "value": current_cost_m2,
            "reference": ref_cost_m2,
            "variance_pct": round(variance_global * 100, 1)
        })
    
    # Analyser les lots si DPGF disponible
    lot_references = {
        "01": {"name": "Terrassements", "ratio": 0.02},
        "02": {"name": "VRD", "ratio": 0.03},
        "03": {"name": "Gros œuvre", "ratio": 0.22},
        "04": {"name": "Charpente", "ratio": 0.04},
        "05": {"name": "Couverture", "ratio": 0.03},
        "06": {"name": "Façade", "ratio": 0.10},
        "07": {"name": "Menuiseries ext", "ratio": 0.06},
        "08": {"name": "Cloisonnement", "ratio": 0.05},
        "09": {"name": "Revêtements sols", "ratio": 0.05},
        "10": {"name": "Revêtements murs", "ratio": 0.02},
        "11": {"name": "Peinture", "ratio": 0.03},
        "12": {"name": "Menuiseries int", "ratio": 0.04},
        "13": {"name": "Plomberie", "ratio": 0.06},
        "14": {"name": "CVC", "ratio": 0.10},
        "15": {"name": "Électricité", "ratio": 0.07},
        "16": {"name": "Courants faibles", "ratio": 0.02},
        "17": {"name": "Ascenseurs", "ratio": 0.02},
        "18": {"name": "Équip. spéciaux", "ratio": 0.01},
        "19": {"name": "Aménag. ext", "ratio": 0.02},
        "20": {"name": "Aléas", "ratio": 0.05}
    }
    
    if dpgf_data:
        for lot in dpgf_data.get("lots", []):
            lot_code = lot.get("code", "")
            lot_ref = lot_references.get(lot_code, {"ratio": 0.05})
            expected_ratio = lot_ref["ratio"]
            actual_ratio = lot.get("total_ht", 0) / total_cost if total_cost > 0 else 0
            
            if actual_ratio > expected_ratio * 1.3:
                anomalies.append({
                    "id": generate_uuid(),
                    "type": "lot_overrun",
                    "severity": "medium" if actual_ratio < expected_ratio * 1.5 else "high",
                    "lot_code": lot_code,
                    "lot_name": lot.get("name", ""),
                    "message": f"Lot {lot_code} - {lot.get('name', '')} : ratio {actual_ratio*100:.1f}% vs {expected_ratio*100:.1f}% attendu",
                    "value": actual_ratio,
                    "reference": expected_ratio,
                    "variance_pct": round((actual_ratio - expected_ratio) / expected_ratio * 100, 1)
                })
    
    # Générer des suggestions d'optimisation
    suggestions = []
    
    # Suggestion 1: Gros œuvre
    suggestions.append({
        "id": generate_uuid(),
        "title": "Optimisation de la structure béton",
        "explanation": "Réduction de l'épaisseur des voiles et optimisation du ferraillage selon les contraintes réelles calculées. Utilisation de bétons hautes performances pour réduire les sections.",
        "impacted_lot": "03",
        "impacted_lot_name": "Gros œuvre",
        "savings_min": round(total_cost * 0.01, 0),
        "savings_max": round(total_cost * 0.025, 0),
        "confidence": 0.85,
        "risk_level": "low",
        "category": "economie_sans_impact",
        "implementation_difficulty": "facile",
        "priority": 1
    })
    
    # Suggestion 2: Façade
    suggestions.append({
        "id": generate_uuid(),
        "title": "Simplification du calepinage façade",
        "explanation": "Rationalisation des formats de bardage/revêtement pour réduire les chutes. Standardisation des teintes et finitions. Réduction du nombre de types de fixations.",
        "impacted_lot": "06",
        "impacted_lot_name": "Façade / Enveloppe",
        "savings_min": round(total_cost * 0.008, 0),
        "savings_max": round(total_cost * 0.02, 0),
        "confidence": 0.75,
        "risk_level": "low",
        "category": "arbitrage_architectural",
        "implementation_difficulty": "moyen",
        "priority": 2
    })
    
    # Suggestion 3: CVC
    suggestions.append({
        "id": generate_uuid(),
        "title": "Optimisation du système de chauffage",
        "explanation": "Passage d'une solution radiateurs à un plancher chauffant permet de réduire la puissance de la chaufferie et les coûts d'exploitation. Couplage avec une PAC air/eau.",
        "impacted_lot": "14",
        "impacted_lot_name": "CVC",
        "savings_min": round(total_cost * 0.005, 0),
        "savings_max": round(total_cost * 0.015, 0),
        "confidence": 0.70,
        "risk_level": "medium",
        "category": "arbitrage_technique",
        "implementation_difficulty": "moyen",
        "priority": 3
    })
    
    # Suggestion 4: Menuiseries extérieures
    suggestions.append({
        "id": generate_uuid(),
        "title": "Standardisation des menuiseries",
        "explanation": "Réduction du nombre de dimensions différentes de menuiseries. Utilisation de châssis standards avec adaptateurs plutôt que sur-mesure. Passage en aluminium thermolaqué standard.",
        "impacted_lot": "07",
        "impacted_lot_name": "Menuiseries extérieures",
        "savings_min": round(total_cost * 0.004, 0),
        "savings_max": round(total_cost * 0.012, 0),
        "confidence": 0.80,
        "risk_level": "low",
        "category": "economie_sans_impact",
        "implementation_difficulty": "facile",
        "priority": 2
    })
    
    # Suggestion 5: Revêtements sols
    suggestions.append({
        "id": generate_uuid(),
        "title": "Choix de revêtements optimisés",
        "explanation": "Remplacement du carrelage grand format par un format standard (60x60). Utilisation de sols souples PVC haut de gamme dans les circulations à la place du carrelage.",
        "impacted_lot": "09",
        "impacted_lot_name": "Revêtements sols",
        "savings_min": round(total_cost * 0.003, 0),
        "savings_max": round(total_cost * 0.008, 0),
        "confidence": 0.85,
        "risk_level": "low",
        "category": "arbitrage_architectural",
        "implementation_difficulty": "facile",
        "priority": 3
    })
    
    # Suggestion 6: Électricité
    suggestions.append({
        "id": generate_uuid(),
        "title": "Rationalisation du réseau électrique",
        "explanation": "Optimisation du nombre de points lumineux par zone. Utilisation de câblage standard au lieu de chemins de câbles. Regroupement des tableaux divisionnaires.",
        "impacted_lot": "15",
        "impacted_lot_name": "Électricité CFO",
        "savings_min": round(total_cost * 0.003, 0),
        "savings_max": round(total_cost * 0.007, 0),
        "confidence": 0.75,
        "risk_level": "low",
        "category": "economie_sans_impact",
        "implementation_difficulty": "moyen",
        "priority": 4
    })
    
    # Suggestion 7: VRD
    if project_usage != "office":
        suggestions.append({
            "id": generate_uuid(),
            "title": "Mutualisation des réseaux VRD",
            "explanation": "Regroupement des tranchées pour les différents réseaux (EU/EP/AEP). Utilisation de regards multi-fonctions. Optimisation du tracé des réseaux.",
            "impacted_lot": "02",
            "impacted_lot_name": "VRD",
            "savings_min": round(total_cost * 0.002, 0),
            "savings_max": round(total_cost * 0.005, 0),
            "confidence": 0.70,
            "risk_level": "low",
            "category": "economie_sans_impact",
            "implementation_difficulty": "facile",
            "priority": 5
        })
    
    # Suggestion avec impact exploitation
    suggestions.append({
        "id": generate_uuid(),
        "title": "Réduction des parties communes",
        "explanation": "Réduction de la surface des paliers et circulations de 15% à 12% de la SDP. Optimisation de la conception des escaliers. Impact sur le confort des usagers.",
        "impacted_lot": "03",
        "impacted_lot_name": "Gros œuvre + Second œuvre",
        "savings_min": round(total_cost * 0.015, 0),
        "savings_max": round(total_cost * 0.03, 0),
        "confidence": 0.60,
        "risk_level": "high",
        "category": "arbitrage_exploitation",
        "implementation_difficulty": "difficile",
        "priority": 6
    })
    
    # Calcul du score de santé
    health_score = 100
    
    # Pénalités pour anomalies
    for anomaly in anomalies:
        if anomaly["severity"] == "high":
            health_score -= 15
        elif anomaly["severity"] == "medium":
            health_score -= 8
        else:
            health_score -= 3
    
    # Pénalité pour variance globale
    if variance_global > 0.1:
        health_score -= min(20, variance_global * 50)
    
    health_score = max(0, min(100, health_score))
    
    # Comparaison avec références
    comparison = {
        "current_cost_m2": round(current_cost_m2, 2),
        "reference_cost_m2": round(ref_cost_m2, 2),
        "variance_pct": round(variance_global * 100, 1),
        "position": "above" if variance_global > 0.05 else "below" if variance_global < -0.05 else "aligned",
        "quality_level": quality_level,
        "project_usage": project_usage
    }
    
    # Résumé
    total_potential_savings_min = sum(s["savings_min"] for s in suggestions)
    total_potential_savings_max = sum(s["savings_max"] for s in suggestions)
    
    summary = {
        "health_score": round(health_score, 0),
        "anomalies_count": len(anomalies),
        "suggestions_count": len(suggestions),
        "total_project_cost": round(total_cost, 2),
        "cost_per_m2": round(current_cost_m2, 2),
        "potential_savings_min": round(total_potential_savings_min, 2),
        "potential_savings_max": round(total_potential_savings_max, 2),
        "potential_savings_pct_min": round(total_potential_savings_min / total_cost * 100, 1) if total_cost > 0 else 0,
        "potential_savings_pct_max": round(total_potential_savings_max / total_cost * 100, 1) if total_cost > 0 else 0,
        "by_category": {
            "economie_sans_impact": len([s for s in suggestions if s["category"] == "economie_sans_impact"]),
            "arbitrage_architectural": len([s for s in suggestions if s["category"] == "arbitrage_architectural"]),
            "arbitrage_technique": len([s for s in suggestions if s["category"] == "arbitrage_technique"]),
            "arbitrage_exploitation": len([s for s in suggestions if s["category"] == "arbitrage_exploitation"])
        }
    }
    
    # Sauvegarder l'analyse
    analysis_doc = {
        "id": analysis_id,
        "project_id": project_id,
        "dpgf_id": dpgf_id,
        "analysis_date": now,
        "health_score": health_score,
        "anomalies": anomalies,
        "suggestions": suggestions,
        "comparison_with_references": comparison,
        "summary": summary
    }
    
    await db.cost_optimizations.insert_one(analysis_doc)
    
    # Retourner le document sans _id
    if "_id" in analysis_doc:
        del analysis_doc["_id"]
    return analysis_doc

@api_router.get("/projects/{project_id}/cost-optimization")
async def get_cost_optimization_analyses(project_id: str, current_user: dict = Depends(get_current_user)):
    """Récupère les analyses d'optimisation d'un projet"""
    analyses = await db.cost_optimizations.find({"project_id": project_id}, {"_id": 0}).to_list(50)
    return analyses

@api_router.get("/projects/{project_id}/cost-optimization/{analysis_id}")
async def get_cost_optimization_analysis(project_id: str, analysis_id: str, current_user: dict = Depends(get_current_user)):
    """Récupère une analyse d'optimisation spécifique"""
    analysis = await db.cost_optimizations.find_one({"id": analysis_id, "project_id": project_id}, {"_id": 0})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return analysis

@api_router.post("/projects/{project_id}/cost-optimization/{analysis_id}/apply-suggestion")
async def apply_optimization_suggestion(
    project_id: str,
    analysis_id: str,
    suggestion_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Applique une suggestion d'optimisation (crée un arbitrage)"""
    analysis = await db.cost_optimizations.find_one({"id": analysis_id, "project_id": project_id}, {"_id": 0})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    suggestion = next((s for s in analysis.get("suggestions", []) if s["id"] == suggestion_id), None)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion non trouvée")
    
    # Créer un arbitrage à partir de la suggestion
    arb_id = generate_uuid()
    now = now_iso()
    
    arb_doc = {
        "id": arb_id,
        "project_id": project_id,
        "subject": suggestion["title"],
        "linked_lot": suggestion["impacted_lot"],
        "initial_assumption": f"Lot {suggestion['impacted_lot']} - {suggestion['impacted_lot_name']}",
        "current_cost_impact": 0,
        "reason_for_drift": "Optimisation IA suggérée",
        "suggested_optimization": suggestion["explanation"],
        "estimated_saving": (suggestion["savings_min"] + suggestion["savings_max"]) / 2,
        "planning_impact": "À évaluer",
        "quality_impact": suggestion["category"],
        "responsible_persons": [current_user["id"]],
        "decision_status": "pending",
        "created_at": now,
        "updated_at": now,
        "source": "ai_optimization",
        "source_analysis_id": analysis_id,
        "source_suggestion_id": suggestion_id
    }
    
    await db.arbitrations.insert_one(arb_doc)
    
    return {
        "message": "Arbitrage créé à partir de la suggestion",
        "arbitration_id": arb_id
    }

@api_router.delete("/projects/{project_id}/cost-optimization/{analysis_id}")
async def delete_cost_optimization_analysis(project_id: str, analysis_id: str, current_user: dict = Depends(get_current_user)):
    """Supprime une analyse d'optimisation"""
    result = await db.cost_optimizations.delete_one({"id": analysis_id, "project_id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return {"message": "Analyse supprimée"}

# =============================================================================
# AI ESTIMATION ENDPOINT
# =============================================================================

class AIEstimationRequest(BaseModel):
    typology: str
    surface_m2: float
    location: str
    quality_level: str
    complexity: str
    number_of_floors: int
    parking_places: int

@api_router.post("/ai-estimation")
async def get_ai_estimation(request: AIEstimationRequest, current_user: dict = Depends(get_current_user)):
    """AI-powered cost estimation based on project parameters"""
    
    # Base ratios by typology and quality
    base_ratios = {
        "housing": {"economic": 1400, "standard": 1850, "premium": 2500, "luxury": 3500},
        "office": {"economic": 1200, "standard": 1650, "premium": 2300, "luxury": 3200},
        "hotel": {"economic": 1800, "standard": 2400, "premium": 3500, "luxury": 5000},
        "retail": {"economic": 1000, "standard": 1400, "premium": 2000, "luxury": 2800},
        "public_facility": {"economic": 1600, "standard": 2100, "premium": 2800, "luxury": 3800},
        "industrial": {"economic": 800, "standard": 1100, "premium": 1500, "luxury": 2000},
        "logistics": {"economic": 600, "standard": 850, "premium": 1200, "luxury": 1600},
        "mixed_use": {"economic": 1400, "standard": 1800, "premium": 2400, "luxury": 3200},
        "healthcare": {"economic": 2000, "standard": 2600, "premium": 3500, "luxury": 4500},
        "education": {"economic": 1500, "standard": 2000, "premium": 2700, "luxury": 3500},
    }
    
    location_coefficients = {
        "ile_de_france": 1.15,
        "grande_couronne": 0.95,
        "grandes_metropoles": 1.00,
        "regions": 0.85,
    }
    
    complexity_coefficients = {
        "simple": 0.90,
        "medium": 1.00,
        "complex": 1.15,
        "very_complex": 1.30,
    }
    
    # Get base ratio
    type_ratios = base_ratios.get(request.typology, base_ratios["housing"])
    base_ratio = type_ratios.get(request.quality_level, type_ratios["standard"])
    
    # Apply coefficients
    location_coef = location_coefficients.get(request.location, 1.0)
    complexity_coef = complexity_coefficients.get(request.complexity, 1.0)
    
    # Height adjustment (more floors = slightly lower cost per m²)
    height_coef = 1.0 - (min(request.number_of_floors, 20) - 5) * 0.005
    height_coef = max(0.90, min(1.10, height_coef))
    
    # Scale adjustment
    if request.surface_m2 < 2000:
        scale_coef = 1.10
    elif request.surface_m2 < 10000:
        scale_coef = 1.00
    elif request.surface_m2 < 30000:
        scale_coef = 0.95
    else:
        scale_coef = 0.90
    
    # Calculate final cost per m²
    final_ratio = base_ratio * location_coef * complexity_coef * height_coef * scale_coef
    
    # Parking cost (25,000€ per underground place)
    parking_cost = request.parking_places * 25000
    
    # Total estimation
    construction_cost = request.surface_m2 * final_ratio
    estimated_total = construction_cost + parking_cost
    
    # Confidence range
    confidence_min = estimated_total * 0.85
    confidence_max = estimated_total * 1.15
    risk_margin = estimated_total * 0.05
    
    # Recommendations
    recommendations = []
    if request.complexity in ["complex", "very_complex"]:
        recommendations.append("Complexité élevée - prévoir provision supplémentaire de 5-10%")
    if request.surface_m2 < 1000:
        recommendations.append("Petite surface - coûts fixes proportionnellement plus élevés")
    if request.number_of_floors > 10:
        recommendations.append("Grande hauteur - vérifier les contraintes structurelles")
    if request.quality_level == "luxury":
        recommendations.append("Finitions haut de gamme - détailler les prestations")
    if not recommendations:
        recommendations.append("Budget cohérent avec les ratios du marché")
    
    # Budget alert
    budget_status = "coherent"
    if final_ratio > base_ratio * 1.3:
        budget_status = "high"
        recommendations.append("Budget supérieur à la moyenne - optimisations possibles")
    elif final_ratio < base_ratio * 0.7:
        budget_status = "low"
        recommendations.append("Budget bas - vérifier la faisabilité technique")
    
    return {
        "estimated_total": round(estimated_total, 2),
        "cost_per_m2": round(final_ratio, 2),
        "construction_cost": round(construction_cost, 2),
        "parking_cost": parking_cost,
        "confidence_min": round(confidence_min, 2),
        "confidence_max": round(confidence_max, 2),
        "risk_margin": round(risk_margin, 2),
        "confidence_level": "medium",
        "budget_status": budget_status,
        "coefficients": {
            "base": base_ratio,
            "location": location_coef,
            "complexity": complexity_coef,
            "height": round(height_coef, 3),
            "scale": scale_coef,
            "final": round(final_ratio, 2)
        },
        "recommendations": recommendations
    }

# =============================================================================
# BUDGET REPORT PDF ENDPOINT
# =============================================================================

class BudgetReportRequest(BaseModel):
    project_name: str
    client_name: str
    typology: str
    surface_m2: float
    location: str
    quality_level: str
    total_budget: float
    cost_per_m2: float
    macro_lots: List[Dict[str, Any]]
    coefficients: Optional[Dict[str, Any]] = None
    ai_estimation: Optional[Dict[str, Any]] = None

@api_router.post("/budget-report/pdf")
async def generate_budget_report_pdf(request: BudgetReportRequest, current_user: dict = Depends(get_current_user)):
    """Generate PDF budget report"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='FrenchTitle', parent=styles['Heading1'], fontSize=20, spaceAfter=20, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionTitle', parent=styles['Heading2'], fontSize=14, spaceBefore=15, spaceAfter=10))
    
    elements = []
    
    # Title
    elements.append(Paragraph("RAPPORT D'ESTIMATION BUDGÉTAIRE", styles['FrenchTitle']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Project info
    elements.append(Paragraph("1. INFORMATIONS PROJET", styles['SectionTitle']))
    project_data = [
        ["Projet:", request.project_name],
        ["Client:", request.client_name],
        ["Typologie:", request.typology.replace("_", " ").title()],
        ["Surface SDP:", f"{request.surface_m2:,.0f} m²".replace(",", " ")],
        ["Localisation:", request.location.replace("_", " ").title()],
        ["Niveau qualité:", request.quality_level.title()],
        ["Date:", datetime.now().strftime("%d/%m/%Y")],
    ]
    t = Table(project_data, colWidths=[120, 300])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))
    
    # Budget summary
    elements.append(Paragraph("2. SYNTHÈSE BUDGÉTAIRE", styles['SectionTitle']))
    budget_data = [
        ["Budget total HT:", f"{request.total_budget:,.0f} €".replace(",", " ")],
        ["Coût au m²:", f"{request.cost_per_m2:,.0f} €/m²".replace(",", " ")],
    ]
    t = Table(budget_data, colWidths=[150, 270])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3b82f6')),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))
    
    # Macro lots breakdown
    elements.append(Paragraph("3. RÉPARTITION PAR MACRO-LOTS", styles['SectionTitle']))
    lots_data = [["Code", "Désignation", "Montant HT", "%"]]
    for lot in request.macro_lots:
        lots_data.append([
            lot.get("code", ""),
            lot.get("name", ""),
            f"{lot.get('amount', 0):,.0f} €".replace(",", " "),
            f"{lot.get('ratio', 0) * 100:.1f}%"
        ])
    lots_data.append(["", "TOTAL", f"{request.total_budget:,.0f} €".replace(",", " "), "100%"])
    
    t = Table(lots_data, colWidths=[50, 230, 100, 50])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    
    # AI estimation if available
    if request.ai_estimation:
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("4. ESTIMATION IA", styles['SectionTitle']))
        ai_data = [
            ["Estimation IA:", f"{request.ai_estimation.get('estimated_total', 0):,.0f} €".replace(",", " ")],
            ["Fourchette basse:", f"{request.ai_estimation.get('confidence_min', 0):,.0f} €".replace(",", " ")],
            ["Fourchette haute:", f"{request.ai_estimation.get('confidence_max', 0):,.0f} €".replace(",", " ")],
            ["Marge risque:", f"{request.ai_estimation.get('risk_margin', 0):,.0f} €".replace(",", " ")],
        ]
        t = Table(ai_data, colWidths=[150, 270])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)
    
    # Footer
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        f"<i>Rapport généré par CostPilot le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</i>",
        styles['Normal']
    ))
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=budget_{request.project_name}.pdf"}
    )

# Inclure les nouveaux routers modulaires
from routers.senior_economist import router as senior_economist_router
from routers.advanced_modules import router as advanced_modules_router
from routers.professional_tools import router as professional_tools_router
from routers.admin import router as admin_router
from routers.advanced_features import router as advanced_features_router
from routers.project_modules import router as project_modules_router

api_router.include_router(senior_economist_router)
api_router.include_router(advanced_modules_router)
api_router.include_router(professional_tools_router)
api_router.include_router(admin_router)
api_router.include_router(advanced_features_router)
api_router.include_router(project_modules_router)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
