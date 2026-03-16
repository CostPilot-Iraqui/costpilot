# CostPilot Senior - Complete API Routes Documentation

## Base URL
```
Production: https://your-domain.com/api
Development: http://localhost:8001/api
```

## Authentication

All protected routes require JWT Bearer token in header:
```
Authorization: Bearer <access_token>
```

---

# AUTHENTICATION ENDPOINTS

## POST /api/auth/register
Create new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "Jean Dupont",
  "role": "senior_cost_manager",
  "company": "Cabinet Économiste",
  "company_id": "optional-company-uuid"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "Jean Dupont",
    "role": "senior_cost_manager",
    "company": "Cabinet Économiste",
    "company_id": "company-uuid",
    "subscription_plan": "pro",
    "created_at": "2024-03-14T10:30:00Z"
  }
}
```

---

## POST /api/auth/login
Authenticate existing user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK` - Same as register

---

## GET /api/auth/me
Get current user profile.

**Headers:** `Authorization: Bearer <token>`

**Response:** `UserResponse`

---

## GET /api/users
List all users (Admin/Senior only).

**Response:** `List[UserResponse]`

---

# PROJECT ENDPOINTS

## POST /api/projects
Create new project.

**Roles:** `administrator`, `senior_cost_manager`

**Request:**
```json
{
  "project_name": "Résidence Les Jardins",
  "client_name": "Promoteur XYZ",
  "location": "Paris 15e",
  "project_usage": "housing",
  "target_surface_m2": 5000,
  "estimated_usable_area_m2": 4200,
  "number_of_levels_estimate": 7,
  "basement_presence": "partial",
  "parking_requirement": "underground",
  "quality_level": "standard",
  "complexity_level": "medium",
  "facade_ambition": "moderate",
  "technical_ambition": "standard",
  "sustainability_target": "hqe_breeam_leed",
  "specific_constraints": "Zone sismique 3",
  "timeline_target": "24 mois",
  "target_budget": 15000000,
  "confidence_level": "medium"
}
```

**Response:** `ProjectResponse` with auto-generated macro categories

---

## GET /api/projects
List all projects for current company.

**Query Params:** None (filtered by company_id)

---

## GET /api/projects/{project_id}
Get single project details.

---

## PUT /api/projects/{project_id}
Update project.

**Request:** Partial project fields

---

## DELETE /api/projects/{project_id}
Delete project and all related data.

**Roles:** `administrator`

---

## POST /api/projects/{project_id}/lock-macro
Lock macro envelope (prevents edits).

---

## POST /api/projects/{project_id}/unlock-macro
Unlock macro envelope.

---

# MACRO CATEGORIES

## GET /api/projects/{project_id}/macro-categories
Get all macro categories for project.

**Response:**
```json
[
  {
    "id": "uuid",
    "project_id": "project-uuid",
    "name": "Infrastructure",
    "code": "INF",
    "target_amount": 1200000,
    "estimated_amount": 1150000,
    "percentage_allocation": 8,
    "is_locked": false,
    "created_at": "2024-03-01T00:00:00Z"
  }
]
```

---

## PUT /api/projects/{project_id}/macro-categories/{category_id}
Update macro category.

---

# MICRO ITEMS (DPGF)

## POST /api/projects/{project_id}/micro-items
Create new micro item.

**Request:**
```json
{
  "macro_category_id": "uuid",
  "lot_code": "SUP.01",
  "lot_name": "Gros Œuvre",
  "sub_lot_code": "SUP.01.01",
  "sub_lot_name": "Fondations",
  "item_code": "SUP.01.01.001",
  "description": "Béton armé C30/37 pour fondations",
  "unit": "m³",
  "quantity": 250,
  "unit_price": 180,
  "pricing_source": "internal_benchmark",
  "responsible_user_id": "user-uuid",
  "notes": "Prix fournisseur local"
}
```

---

## GET /api/projects/{project_id}/micro-items
List micro items with filters.

**Query Params:**
- `macro_category_id` (optional)
- `lot_code` (optional)

---

## PUT /api/projects/{project_id}/micro-items/{item_id}
Update micro item.

---

## DELETE /api/projects/{project_id}/micro-items/{item_id}
Delete micro item.

---

# AI MODULES

## POST /api/instant-estimation
AI-powered instant cost estimation (GPT-4o).

**Request:**
```json
{
  "project_id": "uuid",
  "description": "Immeuble de bureaux R+7, 3500m², standing premium, Paris La Défense"
}
```

**Response:**
```json
{
  "id": "uuid",
  "total_cost": 12500000,
  "cost_per_m2": 3571,
  "breakdown": [
    {"category": "Infrastructure", "amount": 1000000, "percentage": 8},
    {"category": "Superstructure", "amount": 3125000, "percentage": 25}
  ],
  "confidence": 0.85,
  "assumptions": [
    "Terrain plat",
    "Façade mur rideau standard"
  ]
}
```

---

## POST /api/projects/{project_id}/plan-ai/upload
Upload and analyze floor plan with GPT Vision.

**Content-Type:** `multipart/form-data`

**Request:** File field `file` (image/pdf)

**Response:**
```json
{
  "id": "uuid",
  "filename": "plan_rdc.pdf",
  "rooms": [
    {"name": "Séjour", "surface_m2": 35.5, "dimensions": "7.1m x 5m"},
    {"name": "Chambre 1", "surface_m2": 14.2, "dimensions": "4.2m x 3.4m"}
  ],
  "total_surface_m2": 95.7,
  "confidence": 0.90
}
```

---

## GET /api/projects/{project_id}/plan-ai/{analysis_id}/export-pdf
Export plan analysis as PDF report.

**Response:** PDF file stream

---

## GET /api/cctp/lots
Get available CCTP lots (16 standard French construction lots).

**Response:**
```json
[
  {"code": "01", "name": "Terrassement - VRD"},
  {"code": "02", "name": "Fondations spéciales"},
  {"code": "03", "name": "Gros Œuvre"},
  {"code": "04", "name": "Charpente"},
  {"code": "05", "name": "Couverture - Étanchéité"},
  {"code": "06", "name": "Bardage - Façade"},
  {"code": "07", "name": "Menuiseries extérieures"},
  {"code": "08", "name": "Serrurerie"},
  {"code": "09", "name": "Cloisons - Doublages"},
  {"code": "10", "name": "Menuiseries intérieures"},
  {"code": "11", "name": "Revêtements de sols"},
  {"code": "12", "name": "Peinture - Revêtements muraux"},
  {"code": "13", "name": "Plomberie - Sanitaires"},
  {"code": "14", "name": "CVC - Chauffage - Ventilation"},
  {"code": "15", "name": "Électricité - Courants forts"},
  {"code": "16", "name": "Courants faibles - Sécurité"}
]
```

---

## POST /api/projects/{project_id}/cctp/generate
Generate CCTP prescriptions for a lot (GPT-4o).

**Request:**
```json
{
  "lot_id": "03",
  "project_context": "Immeuble R+5, béton armé, zone sismique 3"
}
```

**Response:**
```json
{
  "lot_name": "Gros Œuvre",
  "prescriptions": [
    {
      "title": "Béton armé",
      "content": "Le béton sera de classe C30/37 minimum conformément...",
      "dtu_ref": "DTU 21"
    }
  ],
  "dtu_references": ["DTU 21", "DTU 23.1"],
  "nf_references": ["NF EN 206", "NF EN 13670"]
}
```

---

## GET /api/carbon/factors
Get carbon emission factors database.

**Response:**
```json
{
  "materials": {
    "beton_arme": 250,
    "acier_structure": 1800,
    "bois_lamelle": 150
  },
  "unit": "kg CO2/m³ or kg CO2/tonne"
}
```

---

## GET /api/carbon/re2020-thresholds
Get RE2020 compliance thresholds.

**Response:**
```json
{
  "housing": {
    "2022": 740,
    "2025": 650,
    "2028": 580,
    "2031": 490
  },
  "office": {
    "2022": 980,
    "2025": 870
  }
}
```

---

## POST /api/projects/{project_id}/carbon/analyze
Analyze project carbon footprint.

**Response:**
```json
{
  "total_carbon_kg": 850000,
  "carbon_per_m2": 170,
  "re2020_threshold": 740,
  "compliance_status": "warning",
  "breakdown": [
    {"category": "Structure béton", "carbon_kg": 425000, "percentage": 50}
  ],
  "recommendations": [
    "Optimiser le ratio béton/acier"
  ]
}
```

---

## POST /api/program/generate-from-brief
Generate building program from brief.

**Request:**
```json
{
  "brief": "Résidence 50 logements, du T2 au T4, standing standard",
  "surface_terrain_m2": 2500
}
```

**Response:**
```json
{
  "typologies": [
    {"type": "T2", "count": 15, "surface_avg": 45},
    {"type": "T3", "count": 25, "surface_avg": 70},
    {"type": "T4", "count": 10, "surface_avg": 95}
  ],
  "total_surface_habitable": 3375,
  "surface_plancher_estimee": 4500,
  "parking_count": 60,
  "common_areas": 450
}
```

---

# PROJECT MODULES

## POST /api/projects/{project_id}/quantity-takeoff/generate
Generate automatic quantity takeoff.

**Request:**
```json
{
  "surface_m2": 5000,
  "floors": 7,
  "quality_level": "standard"
}
```

**Response:**
```json
{
  "id": "uuid",
  "lots": [
    {"code": "01", "name": "Terrassement", "quantity": 2500, "unit": "m³", "unit_price": 45, "total_ht": 112500}
  ],
  "total_ht": 5700000,
  "cost_per_m2": 1140,
  "macro_lots": {
    "INF": 456000,
    "SUP": 1425000
  }
}
```

---

## GET /api/projects/{project_id}/quantity-takeoff
Get latest quantity takeoff.

---

## GET /api/projects/{project_id}/planning
Get project planning (Gantt phases).

**Response:**
```json
{
  "phases": [
    {
      "id": "P1",
      "name": "Études préliminaires",
      "start": "2024-01-01",
      "end": "2024-03-31",
      "duration_months": 3,
      "progress": 100
    },
    {
      "id": "P2",
      "name": "APS",
      "start": "2024-04-01",
      "end": "2024-06-30",
      "duration_months": 3,
      "progress": 75
    }
  ],
  "milestones": [
    {"name": "Dépôt PC", "date": "2024-07-15"},
    {"name": "Obtention PC", "date": "2024-10-15"}
  ],
  "total_duration_months": 24
}
```

---

## PUT /api/projects/{project_id}/planning/phase
Update phase progress.

**Request:**
```json
{
  "phase_id": "P2",
  "progress": 80,
  "status": "in_progress"
}
```

---

## GET /api/projects/{project_id}/team
Get project team structure.

---

## POST /api/projects/{project_id}/team/member
Add team member.

**Request:**
```json
{
  "name": "Jean Dupont",
  "role_code": "MOE_ECO",
  "company": "Cabinet XYZ",
  "email": "jean@cabinet.com",
  "phone": "+33 6 12 34 56 78"
}
```

---

## DELETE /api/projects/{project_id}/team/member/{member_id}
Remove team member.

---

## GET /api/projects/{project_id}/diagnostic
Get AI diagnostic for project.

**Response:**
```json
{
  "health_score": 78,
  "status": "warning",
  "issues": [
    {"type": "budget_overrun", "severity": "medium", "message": "Dépassement lot Façade +12%"}
  ],
  "recommendations": [
    "Revoir les hypothèses de prix façade",
    "Valider le planning avec la MOA"
  ]
}
```

---

## GET /api/projects/{project_id}/alerts
Get project alerts.

---

## PUT /api/projects/{project_id}/alerts/{alert_id}/resolve
Mark alert as resolved.

---

## GET /api/projects/{project_id}/scenarios
List scenarios.

---

## POST /api/projects/{project_id}/scenarios
Create scenario.

**Request:**
```json
{
  "name": "Scénario Optimisé",
  "description": "Réduction façade et techniques",
  "macro_adjustments": {
    "FAC": -15,
    "TEC": -10
  }
}
```

---

## DELETE /api/projects/{project_id}/scenarios/{scenario_id}
Delete scenario.

---

## GET /api/projects/{project_id}/arbitrage
Get arbitrage suggestions.

**Response:**
```json
{
  "suggestions": [
    {
      "category": "Façade",
      "current_cost": 1500000,
      "optimized_cost": 1200000,
      "saving": 300000,
      "recommendation": "Remplacer mur rideau par façade semi-rideau"
    }
  ],
  "total_potential_savings": 450000,
  "savings_percentage": 3.5
}
```

---

## GET /api/projects/{project_id}/decisions
Get decision journal.

---

## POST /api/projects/{project_id}/decisions
Add decision.

**Request:**
```json
{
  "title": "Choix structure béton",
  "description": "Structure tout béton retenue",
  "category": "technique",
  "impact": "high",
  "decision_maker": "Jean Dupont",
  "participants": ["Marie Martin"]
}
```

---

## GET /api/projects/{project_id}/feasibility
Get feasibility analysis.

---

## POST /api/projects/{project_id}/feasibility
Create/update feasibility analysis.

---

# EXPORTS

## GET /api/projects/{project_id}/exports
List available exports.

---

## GET /api/projects/{project_id}/export/csv
Export project data as CSV.

---

## GET /api/projects/{project_id}/export/dpgf
Export DPGF (Décomposition du Prix Global et Forfaitaire) as CSV.

---

## GET /api/projects/{project_id}/export/client-report
Generate client PDF report.

---

## GET /api/projects/{project_id}/export/technical-report
Generate technical PDF report.

---

## POST /api/projects/{project_id}/export-pdf
Export custom PDF report.

**Request:**
```json
{
  "report_type": "macro_budget",
  "format": "A4_portrait",
  "include_signature": false,
  "company_name": "Cabinet XYZ"
}
```

---

# LIBRARIES

## GET /api/pricing-library
Get pricing library entries.

**Query Params:**
- `building_type` (optional)
- `quality_level` (optional)
- `category` (optional)

---

## POST /api/pricing-library
Create pricing entry.

---

## PUT /api/pricing-library/{entry_id}
Update pricing entry.

---

## DELETE /api/pricing-library/{entry_id}
Delete pricing entry.

---

## GET /api/reference-ratios
Get reference ratios.

**Query Params:**
- `building_type` (optional)
- `quality_level` (optional)

---

## POST /api/reference-ratios
Create reference ratio.

---

## PUT /api/reference-ratios/{ratio_id}
Update reference ratio.

---

## DELETE /api/reference-ratios/{ratio_id}
Delete reference ratio.

---

# DASHBOARD

## GET /api/projects/{project_id}/dashboard
Get project dashboard data.

**Response:**
```json
{
  "project": {...},
  "summary": {
    "macro_total": 15000000,
    "micro_total": 14850000,
    "variance": -150000,
    "variance_percentage": -1.0,
    "cost_per_m2": 2970
  },
  "category_breakdown": [...],
  "alerts_count": 3,
  "pending_tasks": 5,
  "pending_arbitrations": 2
}
```

---

## GET /api/dashboard/overview
Get global dashboard overview.

**Response:**
```json
{
  "total_projects": 28,
  "total_budget": 315145000,
  "total_surface": 119500,
  "total_alerts": 11,
  "pending_tasks": 45,
  "recent_projects": [...]
}
```

---

## GET /api/projects/{project_id}/macro-vs-micro
Get macro vs micro comparison.

---

# ADMIN

## GET /api/admin/companies
List all companies (Admin only).

---

## POST /api/admin/companies
Create company.

---

## PUT /api/admin/companies/{company_id}
Update company.

---

## GET /api/admin/users
List all users with company info.

---

# HEALTH

## GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-14T10:30:00Z",
  "version": "1.0.0"
}
```

---

# BIM / IFC

## POST /api/projects/{project_id}/bim/upload
Upload IFC file for analysis.

**Content-Type:** `multipart/form-data`

---

## GET /api/projects/{project_id}/bim/elements
Get extracted BIM elements.

---

# BENCHMARK

## GET /api/benchmark/projects
Get benchmark data for similar projects.

**Query Params:**
- `building_type`
- `quality_level`
- `region`

---

## GET /api/benchmark/market-trends
Get market trends data.

---

# ERROR RESPONSES

All errors follow this format:

```json
{
  "detail": "Error message in French"
}
```

| Status | Description |
|--------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/expired token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |
