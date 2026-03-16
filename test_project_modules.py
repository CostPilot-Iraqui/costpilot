# /app/backend/tests/test_project_modules.py
# Test suite for new project modules: quantity_takeoff, planning, team, exports, diagnostic, alerts, arbitrage, decisions
# Tests all endpoints from project_modules.py router

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_new@costpilot.com"
TEST_PASSWORD = "Test123!"
TEST_PROJECT_ID = "8e94d4b8-feff-4bd6-ba61-f070b54cc26d"


@pytest.fixture(scope="module")
def auth_token():
    """Authenticate and get token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in response"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


# =============================================================================
# QUANTITY TAKEOFF TESTS (Métré automatique)
# =============================================================================

class TestQuantityTakeoff:
    """Tests for /api/projects/{id}/quantity-takeoff endpoints"""
    
    def test_generate_quantity_takeoff(self, auth_headers):
        """POST /api/projects/{id}/quantity-takeoff/generate - génération métré automatique"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/quantity-takeoff/generate",
            headers=auth_headers,
            json={"surface_m2": 5000, "floors": 5, "quality_level": "standard"}
        )
        assert response.status_code == 200, f"Failed to generate takeoff: {response.text}"
        
        data = response.json()
        # Verify structure
        assert "id" in data, "No id in response"
        assert "project_id" in data, "No project_id in response"
        assert data["project_id"] == TEST_PROJECT_ID
        assert "lots" in data, "No lots array in response"
        assert "total_cost" in data, "No total_cost in response"
        assert "cost_per_m2" in data, "No cost_per_m2 in response"
        assert "macro_lots" in data, "No macro_lots in response"
        
        # Verify lots structure (should have 15 lots)
        lots = data["lots"]
        assert len(lots) == 15, f"Expected 15 lots, got {len(lots)}"
        
        # Verify each lot has required fields
        for lot in lots:
            assert "code" in lot, "Lot missing code"
            assert "name" in lot, "Lot missing name"
            assert "unit" in lot, "Lot missing unit"
            assert "quantity" in lot, "Lot missing quantity"
            assert "unit_price" in lot, "Lot missing unit_price"
            assert "total_cost" in lot, "Lot missing total_cost"
            assert "percentage" in lot, "Lot missing percentage"
        
        # Verify total cost is substantial (for 5000m² should be millions)
        assert data["total_cost"] > 1000000, f"Total cost {data['total_cost']} seems too low"
        print(f"Generated takeoff: {len(lots)} lots, Total: {data['total_cost']:,.0f} €, {data['cost_per_m2']:,.0f} €/m²")
    
    def test_get_quantity_takeoff(self, auth_headers):
        """GET /api/projects/{id}/quantity-takeoff - récupère le dernier métré"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/quantity-takeoff",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get takeoff: {response.text}"
        
        data = response.json()
        assert "lots" in data, "No lots in response"
        assert "total_cost" in data, "No total_cost in response"
        print(f"Retrieved takeoff: Total HT {data['total_cost']:,.0f} €")
    
    def test_list_quantity_takeoffs(self, auth_headers):
        """GET /api/projects/{id}/quantity-takeoffs - liste tous les métrés"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/quantity-takeoffs",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list takeoffs: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} takeoff(s) for project")


# =============================================================================
# DIAGNOSTIC TESTS (Diagnostic IA)
# =============================================================================

class TestDiagnostic:
    """Tests for /api/projects/{id}/diagnostic endpoint"""
    
    def test_get_diagnostic(self, auth_headers):
        """GET /api/projects/{id}/diagnostic - diagnostic IA du projet"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/diagnostic",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get diagnostic: {response.text}"
        
        data = response.json()
        # Verify structure
        assert "id" in data, "No id in response"
        assert "project_id" in data, "No project_id in response"
        assert "health_score" in data, "No health_score in response"
        assert "status" in data, "No status in response"
        assert "analysis" in data, "No analysis in response"
        assert "issues" in data, "No issues in response"
        assert "recommendations" in data, "No recommendations in response"
        
        # Verify health_score is valid
        assert 0 <= data["health_score"] <= 100, f"Invalid health_score: {data['health_score']}"
        assert data["status"] in ["healthy", "warning", "critical"], f"Invalid status: {data['status']}"
        
        print(f"Diagnostic: health_score={data['health_score']}, status={data['status']}, issues={len(data['issues'])}")


# =============================================================================
# ALERTS TESTS (Alertes projet)
# =============================================================================

class TestAlerts:
    """Tests for /api/projects/{id}/alerts endpoint"""
    
    def test_get_alerts(self, auth_headers):
        """GET /api/projects/{id}/alerts - alertes projet"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/alerts",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get alerts: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If there are alerts, verify structure (from main server.py alerts endpoint)
        if data:
            alert = data[0]
            assert "id" in alert, "Alert missing id"
            assert "type" in alert, "Alert missing type"
            assert "severity" in alert, "Alert missing severity"
            assert "message" in alert, "Alert missing message"
            # These alerts use 'message' instead of 'title' - server.py format
        
        print(f"Found {len(data)} alert(s) for project")


# =============================================================================
# PLANNING TESTS (Planning avec phases)
# =============================================================================

class TestPlanning:
    """Tests for /api/projects/{id}/planning endpoint"""
    
    def test_get_planning(self, auth_headers):
        """GET /api/projects/{id}/planning - planning avec phases"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/planning",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get planning: {response.text}"
        
        data = response.json()
        # Verify structure
        assert "id" in data, "No id in response"
        assert "project_id" in data, "No project_id in response"
        assert "phases" in data, "No phases in response"
        assert "total_duration_months" in data, "No total_duration_months in response"
        assert "milestones" in data, "No milestones in response"
        
        # Verify phases structure (should have 7 phases)
        phases = data["phases"]
        assert len(phases) == 7, f"Expected 7 phases, got {len(phases)}"
        
        # Verify each phase has required fields
        for phase in phases:
            assert "id" in phase, "Phase missing id"
            assert "name" in phase, "Phase missing name"
            assert "code" in phase, "Phase missing code"
            assert "start_date" in phase, "Phase missing start_date"
            assert "end_date" in phase, "Phase missing end_date"
            assert "status" in phase, "Phase missing status"
            assert "deliverables" in phase, "Phase missing deliverables"
        
        print(f"Planning: {len(phases)} phases, {data['total_duration_months']} months total")


# =============================================================================
# TEAM TESTS (Équipe avec rôles)
# =============================================================================

class TestTeam:
    """Tests for /api/projects/{id}/team endpoint"""
    
    def test_get_team(self, auth_headers):
        """GET /api/projects/{id}/team - équipe avec rôles"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/team",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get team: {response.text}"
        
        data = response.json()
        # Verify structure
        assert "id" in data, "No id in response"
        assert "project_id" in data, "No project_id in response"
        assert "members" in data, "No members in response"
        assert "roles" in data, "No roles in response"
        
        # Verify roles structure (should have 9 roles)
        roles = data["roles"]
        assert len(roles) == 9, f"Expected 9 roles, got {len(roles)}"
        
        # Verify each role has required fields
        for role in roles:
            assert "code" in role, "Role missing code"
            assert "name" in role, "Role missing name"
            assert "required" in role, "Role missing required"
        
        print(f"Team: {len(data['members'])} members, {len(roles)} roles defined")
    
    def test_add_team_member(self, auth_headers):
        """POST /api/projects/{id}/team/member - ajoute un membre"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/team/member",
            headers=auth_headers,
            json={
                "name": "TEST_Jean Dupont",
                "role_code": "ARCHI",
                "company": "Cabinet Architecture Test",
                "email": "jean@test.com",
                "phone": "0612345678"
            }
        )
        assert response.status_code == 200, f"Failed to add team member: {response.text}"
        
        data = response.json()
        assert "members" in data, "No members in response"
        
        # Verify member was added
        members = data["members"]
        test_member = next((m for m in members if m.get("name") == "TEST_Jean Dupont"), None)
        assert test_member is not None, "Test member not found in response"
        assert test_member["role_code"] == "ARCHI"
        print(f"Added team member: {test_member['name']}")


# =============================================================================
# ARBITRAGE TESTS (Suggestions d'arbitrage)
# =============================================================================

class TestArbitrage:
    """Tests for /api/projects/{id}/arbitrage endpoint"""
    
    def test_get_arbitrage(self, auth_headers):
        """GET /api/projects/{id}/arbitrage - suggestions d'arbitrage"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/arbitrage",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get arbitrage: {response.text}"
        
        data = response.json()
        # Verify structure
        assert "id" in data, "No id in response"
        assert "project_id" in data, "No project_id in response"
        assert "suggestions" in data, "No suggestions in response"
        assert "total_potential_savings" in data, "No total_potential_savings in response"
        assert "savings_percentage" in data, "No savings_percentage in response"
        
        # Verify suggestions
        suggestions = data["suggestions"]
        assert len(suggestions) >= 2, f"Expected at least 2 suggestions, got {len(suggestions)}"
        
        for suggestion in suggestions:
            assert "id" in suggestion, "Suggestion missing id"
            assert "category" in suggestion, "Suggestion missing category"
            assert "title" in suggestion, "Suggestion missing title"
            assert "description" in suggestion, "Suggestion missing description"
            assert "estimated_savings" in suggestion, "Suggestion missing estimated_savings"
        
        print(f"Arbitrage: {len(suggestions)} suggestions, {data['total_potential_savings']:,.0f} € potential savings ({data['savings_percentage']:.1f}%)")


# =============================================================================
# DECISIONS TESTS (Journal de décisions)
# =============================================================================

class TestDecisions:
    """Tests for /api/projects/{id}/decisions endpoint"""
    
    def test_get_decisions(self, auth_headers):
        """GET /api/projects/{id}/decisions - journal de décisions"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/decisions",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get decisions: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} decision(s) in journal")
    
    def test_add_decision(self, auth_headers):
        """POST /api/projects/{id}/decisions - ajoute une décision"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/decisions",
            headers=auth_headers,
            json={
                "title": "TEST_Choix structure béton",
                "description": "Décision de maintenir la structure béton armé",
                "category": "structure",
                "impact": "high",
                "decision_maker": "Jean Dupont",
                "participants": ["Marie Martin", "Pierre Duval"]
            }
        )
        assert response.status_code == 200, f"Failed to add decision: {response.text}"
        
        data = response.json()
        assert "id" in data, "No id in response"
        assert "title" in data, "No title in response"
        assert data["title"] == "TEST_Choix structure béton"
        assert data["category"] == "structure"
        print(f"Added decision: {data['title']}")


# =============================================================================
# EXPORTS TESTS (Exports PDF/CSV)
# =============================================================================

class TestExports:
    """Tests for /api/projects/{id}/export/* endpoints"""
    
    def test_list_exports(self, auth_headers):
        """GET /api/projects/{id}/exports - liste des exports disponibles"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/exports",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list exports: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 5, f"Expected 5 export options, got {len(data)}"
        
        # Verify export structure
        for export in data:
            assert "id" in export, "Export missing id"
            assert "name" in export, "Export missing name"
            assert "format" in export, "Export missing format"
            assert "available" in export, "Export missing available"
        
        export_names = [e["name"] for e in data]
        print(f"Available exports: {export_names}")
    
    def test_export_csv(self, auth_headers):
        """GET /api/projects/{id}/export/csv - export CSV projet"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/export/csv",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to export CSV: {response.text}"
        
        # Verify content type
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type, f"Wrong content-type: {content_type}"
        
        # Verify content disposition
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp, "Missing attachment header"
        
        # Verify CSV content
        content = response.text
        assert "RAPPORT PROJET" in content or "COSTPILOT" in content, "Invalid CSV content"
        print(f"CSV export: {len(content)} bytes")
    
    def test_export_dpgf(self, auth_headers):
        """GET /api/projects/{id}/export/dpgf - export CSV DPGF"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/export/dpgf",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to export DPGF: {response.text}"
        
        # Verify content type
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type, f"Wrong content-type: {content_type}"
        
        # Verify CSV content
        content = response.text
        assert "DPGF" in content, "Missing DPGF header in content"
        print(f"DPGF export: {len(content)} bytes")
    
    def test_export_client_report(self, auth_headers):
        """GET /api/projects/{id}/export/client-report - export PDF rapport client"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/export/client-report",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to export client report: {response.text}"
        
        # Verify content type
        content_type = response.headers.get("content-type", "")
        assert "application/pdf" in content_type, f"Wrong content-type: {content_type}"
        
        # Verify PDF header
        content = response.content
        assert content[:4] == b'%PDF', "Invalid PDF header"
        print(f"Client report PDF: {len(content)} bytes")
    
    def test_export_technical_report(self, auth_headers):
        """GET /api/projects/{id}/export/technical-report - export PDF rapport technique"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/export/technical-report",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to export technical report: {response.text}"
        
        # Verify content type
        content_type = response.headers.get("content-type", "")
        assert "application/pdf" in content_type, f"Wrong content-type: {content_type}"
        
        # Verify PDF header
        content = response.content
        assert content[:4] == b'%PDF', "Invalid PDF header"
        print(f"Technical report PDF: {len(content)} bytes")


# =============================================================================
# FEASIBILITY ANALYSIS TESTS (from project_analysis service)
# Note: GET /feasibility in server.py returns stored data (may be null)
# The generate_feasibility_analysis is in project_analysis service
# =============================================================================

class TestFeasibilityAnalysis:
    """Tests for feasibility analysis - verifies the service works"""
    
    def test_get_feasibility_stored(self, auth_headers):
        """GET /api/projects/{id}/feasibility - returns stored feasibility (may be null)"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/feasibility",
            headers=auth_headers
        )
        # This endpoint returns stored data from main server.py (can be null)
        assert response.status_code == 200, f"Failed to get feasibility: {response.text}"
        data = response.json()
        # Data may be null if no feasibility was created via POST
        if data:
            assert "id" in data, "No id in response"
            print(f"Found stored feasibility analysis")
        else:
            print("No stored feasibility analysis (null response - expected if none created)")


# =============================================================================
# SCENARIOS TESTS (from project_analysis service via project_modules router)
# Note: server.py has ScenarioCreate which requires project_id in body
# =============================================================================

class TestScenarios:
    """Tests for /api/projects/{id}/scenarios endpoints"""
    
    def test_create_scenario(self, auth_headers):
        """POST /api/projects/{id}/scenarios - crée un scénario (requires ADMIN/SENIOR role)"""
        # Main server.py requires project_id in body (ScenarioCreate model)
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/scenarios",
            headers=auth_headers,
            json={
                "project_id": TEST_PROJECT_ID,
                "name": "TEST_Scénario économique",
                "description": "Réduction du niveau de finition",
                "macro_adjustments": {
                    "INF": -5,
                    "SUP": -10
                }
            }
        )
        # Note: This requires ADMINISTRATOR or SENIOR_COST_MANAGER role
        # Test user has readonly_client role, so 403 is expected
        if response.status_code == 403:
            print("Scenario creation requires elevated permissions (ADMIN/SENIOR role)")
            pytest.skip("User has readonly_client role - scenario creation requires elevated permissions")
        
        assert response.status_code == 200, f"Failed to create scenario: {response.text}"
        
        data = response.json()
        assert "id" in data, "No id in response"
        assert "name" in data, "No name in response"
        print(f"Created scenario: {data['name']}")
    
    def test_list_scenarios(self, auth_headers):
        """GET /api/projects/{id}/scenarios - liste les scénarios"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/scenarios",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list scenarios: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} scenario(s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
