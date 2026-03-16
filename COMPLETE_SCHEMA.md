# CostPilot Senior - Complete Database Schema

## MongoDB Collections Overview

This document describes all MongoDB collections used in CostPilot Senior.

---

## 1. USERS COLLECTION

### Purpose
User accounts with role-based access control (RBAC)

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "email": "user@example.com",           // Unique
  "password_hash": "bcrypt-hash",
  "full_name": "Jean Dupont",
  "role": "senior_cost_manager",          // Enum: see roles below
  "company": "Cabinet Économiste",        // Optional company name
  "company_id": "uuid-ref",               // Reference to companies collection
  "is_active": true,
  "created_at": "2024-03-14T10:30:00Z"
}
```

### Roles (UserRole Enum)
| Role | Description | Permissions |
|------|-------------|-------------|
| `administrator` | System admin | Full access |
| `senior_cost_manager` | Senior economist | Create/modify projects, validate |
| `junior_estimator` | Junior economist | Data entry, modify items |
| `architect` | Architect | View, comment |
| `engineer` | Engineer | View, comment |
| `developer_investor` | Developer/Investor | Feasibility access |
| `readonly_client` | Read-only client | View only |

### Indexes
```javascript
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "company_id": 1 })
```

---

## 2. COMPANIES COLLECTION

### Purpose
Multi-tenant company management with subscription tiers

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "name": "Cabinet XYZ",
  "subscription_plan": "pro",             // Enum: starter | pro | enterprise
  "subscription_status": "active",        // Enum: active | inactive | trial
  "max_projects": -1,                     // -1 = unlimited
  "max_users": -1,
  "features": [
    "basic_estimation",
    "advanced_analysis",
    "pdf_export",
    "ai_optimization",
    "scenarios"
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-03-14T10:30:00Z"
}
```

---

## 3. PROJECTS COLLECTION

### Purpose
Main project data storage

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_name": "Résidence Les Jardins",
  "client_name": "Promoteur XYZ",
  "location": "Paris 15e",
  
  // Project characteristics
  "project_usage": "housing",             // Enum: housing, office, hotel, retail, mixed_use, public_facility, industrial, logistics, other
  "target_surface_m2": 5000.0,
  "estimated_usable_area_m2": 4200.0,
  "number_of_levels_estimate": 7,
  
  // Site constraints
  "basement_presence": "partial",         // Enum: none, partial, full
  "parking_requirement": "underground",   // Enum: none, external, underground
  
  // Quality & complexity
  "quality_level": "standard",            // Enum: economic, standard, premium, luxury
  "complexity_level": "medium",           // Enum: simple, medium, complex, very_complex
  "facade_ambition": "moderate",          // Enum: simple, moderate, premium, iconic
  "technical_ambition": "standard",       // Enum: low, standard, high
  "sustainability_target": "hqe_breeam_leed",  // Enum: none, standard, hqe_breeam_leed, high_performance
  
  // Budget & timeline
  "specific_constraints": "Zone sismique 3, PLU restrictif",
  "timeline_target": "24 mois",
  "target_budget": 15000000.0,
  "confidence_level": "medium",           // Enum: low, medium, high
  
  // Workflow state
  "current_stage": "apd",                 // Enum: early_feasibility, concept_program, aps, apd, pro, tender_negotiation, client_validation
  "macro_envelope_locked": false,
  
  // Ownership
  "created_by": "user-uuid",
  "company_id": "company-uuid",
  "created_at": "2024-03-01T00:00:00Z",
  "updated_at": "2024-03-14T10:30:00Z"
}
```

### Indexes
```javascript
db.projects.createIndex({ "company_id": 1 })
db.projects.createIndex({ "created_by": 1 })
db.projects.createIndex({ "project_usage": 1 })
db.projects.createIndex({ "current_stage": 1 })
```

---

## 4. MACRO_CATEGORIES COLLECTION

### Purpose
High-level budget categories (7 default categories per project)

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "name": "Superstructure",
  "code": "SUP",                          // Standard codes: INF, SUP, FAC, INT, TEC, EXT, ALE
  "target_amount": 3750000.0,
  "estimated_amount": 3825000.0,          // Sum of micro items
  "percentage_allocation": 25.0,
  "notes": "Incluant voiles BA et dalles",
  "is_locked": false,
  "created_at": "2024-03-01T00:00:00Z"
}
```

### Default Categories
| Code | Name | Default % |
|------|------|-----------|
| INF | Infrastructure | 8% |
| SUP | Superstructure | 25% |
| FAC | Façade / Enveloppe | 15% |
| INT | Travaux Intérieurs | 22% |
| TEC | Systèmes Techniques | 20% |
| EXT | Travaux Extérieurs | 5% |
| ALE | Aléas | 5% |

---

## 5. MICRO_ITEMS COLLECTION

### Purpose
Detailed cost breakdown items (DPGF line items)

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "macro_category_id": "macro-uuid",
  
  // Lot structure
  "lot_code": "SUP.01",
  "lot_name": "Gros Œuvre",
  "sub_lot_code": "SUP.01.01",
  "sub_lot_name": "Fondations",
  "item_code": "SUP.01.01.001",
  
  // Item details
  "description": "Béton armé C30/37 pour fondations superficielles",
  "unit": "m³",
  "quantity": 250.0,
  "unit_price": 180.0,
  
  // Calculated fields
  "amount": 45000.0,                      // quantity × unit_price
  "cost_ratio": 9.0,                      // amount / surface_m2
  
  // Source & validation
  "pricing_source": "internal_benchmark", // Enum: internal_benchmark, historical_project, manual_input, adjusted_value
  "validation_status": "validated",       // Enum: draft, pending, validated, rejected
  "responsible_user_id": "user-uuid",
  "notes": "Prix négocié fournisseur local",
  
  // Versioning
  "revision_number": 3,
  "created_at": "2024-03-01T00:00:00Z",
  "updated_at": "2024-03-14T10:30:00Z"
}
```

### Indexes
```javascript
db.micro_items.createIndex({ "project_id": 1 })
db.micro_items.createIndex({ "macro_category_id": 1 })
db.micro_items.createIndex({ "lot_code": 1 })
db.micro_items.createIndex({ "validation_status": 1 })
```

---

## 6. PRICING_LIBRARY COLLECTION

### Purpose
Reference price database for cost estimation

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "building_type": "housing",
  "geographic_region": "Île-de-France",
  "region": "idf",                        // Code: idf, paca, rhone_alpes, etc.
  "year_reference": 2024,
  "quality_level": "standard",
  "complexity_level": "medium",
  
  // Classification
  "category": "Superstructure",
  "lot_code": "SUP.01",
  "lot": "Gros Œuvre",
  "sub_lot": "Fondations",
  "item": "Béton armé fondations",
  
  // Pricing
  "unit": "m³",
  "unit_price_min": 160.0,
  "unit_price_avg": 180.0,
  "unit_price_max": 210.0,
  "confidence_score": 0.85,
  
  // Metadata
  "source_type": "internal_benchmark",
  "notes": "Basé sur 15 projets similaires",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-03-01T00:00:00Z"
}
```

---

## 7. REFERENCE_RATIOS COLLECTION

### Purpose
Cost ratios by building type for macro estimation

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "building_type": "housing",
  "geographic_region": "Île-de-France",
  "year_reference": 2024,
  
  // Project parameters
  "quality_level": "standard",
  "complexity_level": "medium",
  "facade_ambition": "moderate",
  "technical_ambition": "standard",
  "basement_presence": "partial",
  "parking_type": "underground",
  "sustainability_target": "hqe_breeam_leed",
  
  // Cost ratios (€/m²)
  "total_cost_m2": 2800.0,
  "cost_min_m2": 2400.0,
  "cost_avg_m2": 2800.0,
  "cost_max_m2": 3400.0,
  
  // Breakdown by category (€/m²)
  "infrastructure_cost_m2": 224.0,
  "superstructure_cost_m2": 700.0,
  "facade_cost_m2": 420.0,
  "interior_works_cost_m2": 616.0,
  "technical_systems_cost_m2": 560.0,
  "external_works_cost_m2": 140.0,
  
  // Additional costs
  "parking_cost_unit": 25000.0,           // Per parking space
  "contingency_percentage": 5.0,
  "fees_percentage": 10.0,
  
  // Metadata
  "confidence_level": "high",
  "source": "Internal benchmark 2024",
  "notes": "Basé sur 25 projets IDF",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-03-01T00:00:00Z"
}
```

---

## 8. SCENARIOS COLLECTION

### Purpose
Budget scenario variants for comparison

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "name": "Scénario Optimisé",
  "description": "Réduction façade, optimisation techniques",
  
  // Calculated totals
  "total_cost": 14200000.0,
  "cost_per_m2": 2840.0,
  
  // Adjustments by category (%)
  "macro_adjustments": {
    "INF": 0,
    "SUP": -5,
    "FAC": -15,
    "INT": 0,
    "TEC": -10,
    "EXT": 0,
    "ALE": 0
  },
  
  "notes": "Option présentée au client",
  "created_at": "2024-03-10T00:00:00Z",
  "updated_at": "2024-03-14T00:00:00Z"
}
```

---

## 9. ARBITRATIONS COLLECTION

### Purpose
Cost optimization decisions tracking

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "subject": "Choix type de façade",
  "linked_category_id": "macro-uuid",
  "linked_lot": "FAC.01",
  
  // Analysis
  "initial_assumption": "Mur rideau VEC",
  "current_cost_impact": 450000.0,
  "reason_for_drift": "Demande architecte",
  
  // Options
  "design_option_a": "Mur rideau standard",
  "design_option_b": "Façade semi-rideau",
  "suggested_optimization": "Panneaux préfabriqués",
  "estimated_saving": 120000.0,
  
  // Impact assessment
  "planning_impact": "Aucun",
  "quality_impact": "Faible - aspect visuel similaire",
  
  // Workflow
  "decision_status": "validated",         // Enum: draft, pending, validated, rejected
  "responsible_persons": ["user-uuid-1", "user-uuid-2"],
  
  "created_at": "2024-03-05T00:00:00Z",
  "updated_at": "2024-03-12T00:00:00Z"
}
```

---

## 10. ALERTS COLLECTION

### Purpose
Budget warnings and notifications

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "type": "macro_overrun",                // Types: macro_overrun, high_cost_item, deadline_warning, data_quality
  "message": "Dépassement Superstructure: +12.5%",
  "severity": "orange",                   // Enum: green, orange, red
  
  // References
  "linked_category_id": "macro-uuid",
  "linked_item_id": null,
  
  // Values
  "value": 4218750.0,
  "threshold": 3750000.0,
  
  "is_resolved": false,
  "created_at": "2024-03-14T10:00:00Z"
}
```

---

## 11. TASKS COLLECTION

### Purpose
Project task management

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "title": "Finaliser chiffrage lot CVC",
  "description": "Obtenir devis entreprises",
  "assigned_to": "user-uuid",
  "deadline": "2024-03-20T00:00:00Z",
  "priority": 2,                          // 1 (highest) to 5 (lowest)
  "stage": "apd",
  "progress": 60,                         // 0-100
  "status": "pending",                    // Enum: draft, pending, validated, rejected
  "created_at": "2024-03-01T00:00:00Z",
  "updated_at": "2024-03-14T10:30:00Z"
}
```

---

## 12. WORKFLOW_STAGES COLLECTION

### Purpose
Project phase tracking

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "stage": "apd",
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-04-30T00:00:00Z",
  "responsible_users": ["user-uuid-1", "user-uuid-2"],
  "deliverables": [
    "Estimation APD",
    "DPGF provisoire",
    "Planning prévisionnel"
  ],
  "validation_status": "pending",
  "completion_percentage": 75,
  "notes": "En attente validation MOA",
  "created_at": "2024-02-01T00:00:00Z",
  "updated_at": "2024-03-14T10:30:00Z"
}
```

---

## 13. COMMENTS COLLECTION

### Purpose
Collaborative comments on items

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "target_type": "micro_item",            // Types: project, macro_category, micro_item, arbitration
  "target_id": "item-uuid",
  "content": "Prix à revoir avec fournisseur",
  "author_id": "user-uuid",
  "author_name": "Jean Dupont",
  "created_at": "2024-03-14T09:30:00Z"
}
```

---

## 14. FEASIBILITY_ANALYSES COLLECTION

### Purpose
Financial feasibility calculations

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  
  // Costs
  "land_price": 3000000.0,
  "acquisition_fees": 210000.0,
  "construction_cost": 15000000.0,
  "developer_fees": 750000.0,
  "financing_cost": 450000.0,
  "marketing_costs": 300000.0,
  "contingencies": 500000.0,
  "taxes_assumptions": 800000.0,
  
  // Revenue assumptions
  "sales_price_per_m2": 5500.0,
  "rental_income_assumption": 0.0,
  "project_duration_months": 24,
  
  // Calculated results
  "total_revenue": 27500000.0,
  "total_project_cost": 21010000.0,
  "gross_margin": 6490000.0,
  "margin_percentage": 23.6,
  "break_even_sales_price_m2": 4202.0,
  "residual_land_value": 3490000.0,
  
  "notes": "Hypothèse vente 100% en VEFA",
  "created_at": "2024-03-01T00:00:00Z",
  "updated_at": "2024-03-14T10:30:00Z"
}
```

---

## 15. PLAN_ANALYSES COLLECTION (AI Vision)

### Purpose
GPT Vision floor plan analysis results

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "filename": "plan_rdc.pdf",
  "file_type": "application/pdf",
  
  "analysis_result": {
    "rooms": [
      {
        "name": "Séjour",
        "surface_m2": 35.5,
        "dimensions": "7.1m x 5.0m"
      },
      {
        "name": "Chambre 1",
        "surface_m2": 14.2,
        "dimensions": "4.2m x 3.4m"
      },
      {
        "name": "Cuisine",
        "surface_m2": 12.0,
        "dimensions": "4.0m x 3.0m"
      },
      {
        "name": "SdB",
        "surface_m2": 6.5,
        "dimensions": "2.6m x 2.5m"
      }
    ],
    "total_surface_m2": 95.7,
    "confidence": 0.90,
    "raw_analysis": "Detailed GPT Vision response..."
  },
  
  "created_at": "2024-03-14T10:00:00Z"
}
```

---

## 16. CCTP_GENERATIONS COLLECTION

### Purpose
AI-generated technical specifications (CCTP)

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "lot_id": "03",
  "lot_name": "Gros Œuvre",
  
  "prescriptions": [
    {
      "title": "Béton armé",
      "content": "Le béton sera de classe C30/37 minimum...",
      "dtu_ref": "DTU 21"
    },
    {
      "title": "Armatures",
      "content": "Aciers haute adhérence FeE500...",
      "nf_ref": "NF EN 10080"
    }
  ],
  
  "dtu_references": ["DTU 21", "DTU 23.1", "DTU 26.1"],
  "nf_references": ["NF EN 206", "NF EN 13670", "NF EN 10080"],
  
  "created_at": "2024-03-14T11:00:00Z"
}
```

---

## 17. INSTANT_ESTIMATIONS COLLECTION

### Purpose
AI instant cost estimation results

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  "description": "Immeuble de bureaux R+7, 3500m², standing premium, La Défense",
  
  "estimation_result": {
    "total_cost": 12500000,
    "cost_per_m2": 3571,
    "breakdown": [
      { "category": "Infrastructure", "amount": 1000000, "percentage": 8 },
      { "category": "Superstructure", "amount": 3125000, "percentage": 25 },
      { "category": "Façade", "amount": 1875000, "percentage": 15 },
      { "category": "Intérieurs", "amount": 2750000, "percentage": 22 },
      { "category": "Techniques", "amount": 2500000, "percentage": 20 },
      { "category": "Extérieurs", "amount": 625000, "percentage": 5 },
      { "category": "Aléas", "amount": 625000, "percentage": 5 }
    ],
    "confidence": 0.85,
    "assumptions": [
      "Terrain plat, pas de fondations spéciales",
      "Façade mur rideau standard",
      "CVC avec VRV",
      "Finitions premium"
    ]
  },
  
  "created_at": "2024-03-14T10:30:00Z"
}
```

---

## 18. CARBON_ANALYSES COLLECTION

### Purpose
RE2020 carbon footprint analysis results

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  
  "total_carbon_kg": 850000,
  "carbon_per_m2": 170,
  "re2020_threshold": 740,                // kg CO2/m² threshold
  "compliance_status": "warning",         // Enum: compliant, warning, non_compliant
  
  "breakdown": [
    { "category": "Structure béton", "carbon_kg": 425000, "percentage": 50 },
    { "category": "Façade", "carbon_kg": 127500, "percentage": 15 },
    { "category": "Techniques CVC", "carbon_kg": 170000, "percentage": 20 },
    { "category": "Menuiseries", "carbon_kg": 85000, "percentage": 10 },
    { "category": "Autres", "carbon_kg": 42500, "percentage": 5 }
  ],
  
  "recommendations": [
    "Optimiser le ratio béton/acier de la structure",
    "Envisager des menuiseries bois plutôt qu'aluminium",
    "Étudier une solution PAC géothermique"
  ],
  
  "created_at": "2024-03-14T11:30:00Z"
}
```

---

## 19. QUANTITY_TAKEOFFS COLLECTION

### Purpose
Automatic quantity takeoff results

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  
  "parameters": {
    "surface_m2": 5000,
    "floors": 7,
    "quality_level": "standard"
  },
  
  "lots": [
    {
      "code": "01",
      "name": "Terrassement - VRD",
      "quantity": 2500,
      "unit": "m³",
      "unit_price": 45,
      "total_ht": 112500
    },
    {
      "code": "02",
      "name": "Fondations spéciales",
      "quantity": 0,
      "unit": "forfait",
      "unit_price": 0,
      "total_ht": 0
    }
    // ... 15 lots total
  ],
  
  "total_ht": 5700000,
  "cost_per_m2": 1140,
  
  "macro_lots": {
    "INF": 456000,
    "SUP": 1425000,
    "FAC": 855000,
    "INT": 1254000,
    "TEC": 1140000,
    "EXT": 285000,
    "ALE": 285000
  },
  
  "created_at": "2024-03-14T12:00:00Z"
}
```

---

## 20. PROJECT_TEAMS COLLECTION

### Purpose
Project team member assignments

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  
  "members": [
    {
      "id": "member-uuid",
      "name": "Jean Dupont",
      "role_code": "MOE_ECO",
      "company": "Cabinet XYZ",
      "email": "jean@cabinet.com",
      "phone": "+33 6 12 34 56 78"
    }
  ],
  
  "roles": {
    "MOA": "Maîtrise d'Ouvrage",
    "AMO": "Assistance MOA",
    "MOE_ARCHI": "Architecte",
    "MOE_ECO": "Économiste",
    "MOE_BET_STRUCT": "BET Structure",
    "MOE_BET_FLUIDES": "BET Fluides",
    "MOE_BET_ELEC": "BET Électricité",
    "OPC": "OPC",
    "SPS": "Coordinateur SPS"
  },
  
  "updated_at": "2024-03-14T10:00:00Z"
}
```

---

## 21. DECISION_JOURNALS COLLECTION

### Purpose
Project decision history tracking

### Schema
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",
  "project_id": "project-uuid",
  
  "decisions": [
    {
      "id": "decision-uuid",
      "title": "Choix structure béton vs mixte",
      "description": "Après analyse comparative, la structure tout béton est retenue pour des raisons de coût et de délai.",
      "category": "technique",            // Categories: budget, technique, planning, qualite
      "impact": "high",                   // Enum: low, medium, high
      "decision_maker": "Jean Dupont",
      "participants": ["Marie Martin", "Pierre Duval"],
      "date": "2024-03-10T14:00:00Z"
    }
  ],
  
  "updated_at": "2024-03-14T10:30:00Z"
}
```

---

## Index Summary

```javascript
// Essential indexes for performance
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "company_id": 1 })

db.projects.createIndex({ "company_id": 1 })
db.projects.createIndex({ "created_by": 1 })
db.projects.createIndex({ "project_usage": 1 })
db.projects.createIndex({ "current_stage": 1 })

db.macro_categories.createIndex({ "project_id": 1 })

db.micro_items.createIndex({ "project_id": 1 })
db.micro_items.createIndex({ "macro_category_id": 1 })
db.micro_items.createIndex({ "lot_code": 1 })
db.micro_items.createIndex({ "validation_status": 1 })

db.pricing_library.createIndex({ "building_type": 1, "quality_level": 1 })
db.pricing_library.createIndex({ "lot_code": 1 })

db.reference_ratios.createIndex({ "building_type": 1, "quality_level": 1 })

db.alerts.createIndex({ "project_id": 1, "is_resolved": 1 })

db.tasks.createIndex({ "project_id": 1 })
db.tasks.createIndex({ "assigned_to": 1 })
db.tasks.createIndex({ "deadline": 1 })

db.scenarios.createIndex({ "project_id": 1 })
db.arbitrations.createIndex({ "project_id": 1 })
db.comments.createIndex({ "project_id": 1, "target_type": 1, "target_id": 1 })
```
