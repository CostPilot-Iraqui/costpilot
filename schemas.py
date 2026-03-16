# /app/backend/models/schemas.py
# Schémas Pydantic pour CostPilot Senior

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from .enums import (
    UserRole, ProjectUsage, QualityLevel, ComplexityLevel,
    FacadeAmbition, TechnicalAmbition, SustainabilityTarget,
    BasementPresence, ParkingType, ConfidenceLevel, ValidationStatus,
    AlertSeverity, WorkflowStage, SourceType, EconomistPhase,
    ScenarioType, PriorityLevel, BenchmarkStatus
)

# =============================================================================
# AUTH MODELS
# =============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.READONLY_CLIENT
    company: Optional[str] = None

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
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# =============================================================================
# PROJECT MODELS
# =============================================================================

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

# =============================================================================
# MACRO CATEGORY MODELS
# =============================================================================

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

# =============================================================================
# MICRO ITEM MODELS
# =============================================================================

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

# =============================================================================
# PRICING LIBRARY MODELS
# =============================================================================

class PricingEntryCreate(BaseModel):
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

# =============================================================================
# REFERENCE RATIO MODELS
# =============================================================================

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
    building_type: str
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

# =============================================================================
# SCENARIO MODELS
# =============================================================================

class ScenarioCreate(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    scenario_type: ScenarioType = ScenarioType.CUSTOM
    macro_adjustments: Dict[str, float] = {}
    notes: Optional[str] = None

class ScenarioResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    scenario_type: ScenarioType = ScenarioType.CUSTOM
    total_cost: float = 0
    cost_per_m2: float = 0
    macro_adjustments: Dict[str, float] = {}
    notes: Optional[str] = None
    created_at: str
    updated_at: str

# =============================================================================
# ARBITRATION MODELS
# =============================================================================

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

# =============================================================================
# ALERT MODELS
# =============================================================================

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

# =============================================================================
# TASK MODELS
# =============================================================================

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

# =============================================================================
# WORKFLOW STAGE MODELS
# =============================================================================

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

# =============================================================================
# COMMENT MODELS
# =============================================================================

class CommentCreate(BaseModel):
    project_id: str
    target_type: str
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

# =============================================================================
# FEASIBILITY MODELS
# =============================================================================

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
# SENIOR ECONOMIST MODELS
# =============================================================================

class MacroAnalysis(BaseModel):
    """Analyse macro-économique du projet"""
    id: str
    project_id: str
    market_context: str
    economic_indicators: Dict[str, float]
    regional_factors: Dict[str, float]
    inflation_forecast: float
    material_price_trends: List[Dict[str, Any]]
    labor_cost_trends: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_level: float
    created_at: str

class RiskAssessment(BaseModel):
    """Identification et évaluation des risques"""
    id: str
    project_id: str
    risk_category: str
    description: str
    probability: float
    impact_level: str
    mitigation_strategy: str
    contingency_amount: float
    responsible_person: Optional[str]
    status: str
    created_at: str

class CostStrategy(BaseModel):
    """Stratégie de maîtrise des coûts"""
    id: str
    project_id: str
    strategy_name: str
    target_savings: float
    implementation_phases: List[Dict[str, Any]]
    key_levers: List[str]
    monitoring_indicators: List[str]
    status: str
    created_at: str

class ProjectPhasing(BaseModel):
    """Phasage du projet"""
    id: str
    project_id: str
    phase_name: str
    phase_number: int
    start_date: str
    end_date: str
    budget_allocation: float
    deliverables: List[str]
    milestones: List[Dict[str, Any]]
    dependencies: List[str]
    status: str

class EconomistWorkflow(BaseModel):
    """Workflow de l'économiste senior"""
    id: str
    project_id: str
    current_phase: EconomistPhase
    completed_phases: List[str]
    pending_validations: List[str]
    action_items: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    last_update: str

# =============================================================================
# BENCHMARK MODELS
# =============================================================================

class BenchmarkProject(BaseModel):
    """Projet de référence pour benchmark"""
    id: str
    name: str
    location: str
    building_type: str
    surface_m2: float
    total_cost: float
    cost_per_m2: float
    year_completed: int
    quality_level: str
    complexity: str
    key_metrics: Dict[str, float]
    lots_breakdown: Dict[str, float]
    source: str
    validated: bool
    created_at: str

class BenchmarkComparison(BaseModel):
    """Comparaison avec les projets de référence"""
    project_id: str
    benchmark_projects: List[str]
    variance_analysis: Dict[str, float]
    position_percentile: float
    recommendations: List[str]
    created_at: str

# =============================================================================
# MARKET INTELLIGENCE MODELS
# =============================================================================

class MarketTrend(BaseModel):
    """Tendance du marché de la construction"""
    id: str
    region: str
    category: str
    trend_type: str
    current_value: float
    previous_value: float
    variation_pct: float
    forecast_6m: float
    forecast_12m: float
    confidence: float
    data_source: str
    updated_at: str

class RegionalCostIndex(BaseModel):
    """Indice de coût régional"""
    region: str
    region_name: str
    base_index: float
    current_index: float
    variation_ytd: float
    components: Dict[str, float]
    last_update: str

# =============================================================================
# COST PREDICTION MODELS
# =============================================================================

class CostPredictionInput(BaseModel):
    """Entrée pour la prédiction de coûts"""
    building_type: str
    surface_m2: float
    location: str
    quality_level: str
    complexity: str
    sustainability_target: str
    specific_features: List[str] = []

class CostPrediction(BaseModel):
    """Prédiction de coût IA"""
    id: str
    project_id: str
    predicted_cost_min: float
    predicted_cost_avg: float
    predicted_cost_max: float
    confidence_interval: float
    contributing_factors: List[Dict[str, Any]]
    similar_projects: List[str]
    model_version: str
    created_at: str

# =============================================================================
# DESIGN OPTIMIZATION MODELS
# =============================================================================

class DesignOptimization(BaseModel):
    """Suggestion d'optimisation de conception"""
    id: str
    project_id: str
    category: str
    title: str
    description: str
    current_cost: float
    optimized_cost: float
    savings_potential: float
    implementation_complexity: str
    impact_on_quality: str
    impact_on_timeline: str
    architectural_implications: List[str]
    technical_requirements: List[str]
    priority: int
    status: str
    created_at: str

# =============================================================================
# QUANTITY TAKEOFF MODELS
# =============================================================================

class QuantityItem(BaseModel):
    """Élément de métré"""
    id: str
    lot_code: str
    lot_name: str
    description: str
    unit: str
    quantity: float
    unit_price: float
    total_price: float
    source: str
    confidence: float

class QuantityTakeoff(BaseModel):
    """Métré automatisé"""
    id: str
    project_id: str
    source_type: str
    source_file: Optional[str]
    items: List[QuantityItem]
    summary: Dict[str, Any]
    created_at: str
    updated_at: str

# =============================================================================
# MULTI-SCENARIO MODELS
# =============================================================================

class MultiScenarioAnalysis(BaseModel):
    """Analyse multi-scénarios"""
    id: str
    project_id: str
    scenarios: List[Dict[str, Any]]
    comparison_metrics: List[str]
    recommended_scenario: Optional[str]
    sensitivity_analysis: Dict[str, Any]
    created_at: str
