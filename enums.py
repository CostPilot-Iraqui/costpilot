# /app/backend/models/enums.py
# Enums partagés pour CostPilot Senior

from enum import Enum

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

class OptimizationCategory(str, Enum):
    NO_IMPACT = "economie_sans_impact"
    ARCH_IMPACT = "arbitrage_architectural"
    TECH_IMPACT = "arbitrage_technique"
    OPS_IMPACT = "arbitrage_exploitation"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Phases de projet pour l'économiste senior
class EconomistPhase(str, Enum):
    MACRO_ANALYSIS = "macro_analysis"
    RISK_IDENTIFICATION = "risk_identification"
    COST_STRATEGY = "cost_strategy"
    PROJECT_PHASING = "project_phasing"
    TEAM_MANAGEMENT = "team_management"
    WORKFLOW_TIMELINE = "workflow_timeline"
    FINAL_VALIDATION = "final_validation"

# Types de scénarios
class ScenarioType(str, Enum):
    ECONOMIC = "economic"
    STANDARD = "standard"
    PREMIUM = "premium"
    CUSTOM = "custom"

# Niveaux de priorité
class PriorityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Statut de benchmark
class BenchmarkStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    ARCHIVED = "archived"
