"""
CostPilot Senior - Final Production Validation Test Suite
Tests all 19 modules requested for production deployment validation
"""
import pytest
import requests
import os
import time
import json
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
TEST_EMAIL = f"admin_test_{int(time.time())}@costpilot.com"
TEST_PASSWORD = "AdminTest123!"
TEST_USER_NAME = "Admin Tester"

class TestAuthAndSetup:
    """1. Authentication and user setup tests"""
    
    token = None
    user_id = None
    project_id = None
    
    @classmethod
    def setup_class(cls):
        """Register administrator user for all tests"""
        register_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_USER_NAME,
            "role": "administrator"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code == 200:
            data = response.json()
            cls.token = data.get("access_token")
            cls.user_id = data.get("user", {}).get("id")
            print(f"✓ Registered admin user: {TEST_EMAIL}")
        elif response.status_code == 400 and "utilisé" in response.json().get("detail", "").lower():
            # User exists, try login
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if login_response.status_code == 200:
                data = login_response.json()
                cls.token = data.get("access_token")
                cls.user_id = data.get("user", {}).get("id")
                print(f"✓ Logged in existing admin user: {TEST_EMAIL}")
            else:
                pytest.fail(f"Could not login: {login_response.status_code}")
        else:
            pytest.fail(f"Registration failed: {response.status_code} - {response.text}")
    
    def test_00_auth_register(self):
        """Verify auth registration works"""
        assert self.__class__.token is not None
        assert len(self.__class__.token) > 50
        print("✓ Auth registration verified")
    
    def test_01_auth_me(self):
        """Verify /api/auth/me endpoint"""
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("role") == "administrator"
        print(f"✓ Auth me verified: {data.get('full_name')}")


class TestProjectCreation:
    """2. Project creation with all fields"""
    
    project_id = None
    token = None
    
    @classmethod
    def setup_class(cls):
        """Get existing token or create new"""
        # Login with admin user
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            cls.token = login_response.json().get("access_token")
        else:
            pytest.skip("Could not login to run project tests")
    
    def test_02_create_project(self):
        """Create full project with all fields"""
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        project_data = {
            "project_name": "TEST_Validation_Production",
            "client_name": "Client Test Production",
            "location": "Paris, France",
            "project_usage": "housing",
            "target_surface_m2": 5000,
            "estimated_usable_area_m2": 4200,
            "number_of_levels_estimate": 6,
            "basement_presence": "full",
            "parking_requirement": "underground",
            "quality_level": "premium",
            "complexity_level": "complex",
            "facade_ambition": "premium",
            "technical_ambition": "high",
            "sustainability_target": "hqe_breeam_leed",
            "specific_constraints": "Zone sismique 2",
            "timeline_target": "24 mois",
            "target_budget": 12000000,
            "confidence_level": "medium"
        }
        
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        self.__class__.project_id = data.get("id")
        
        # Verify all fields
        assert data.get("project_name") == "TEST_Validation_Production"
        assert data.get("project_usage") == "housing"
        assert data.get("target_surface_m2") == 5000
        assert data.get("quality_level") == "premium"
        assert data.get("complexity_level") == "complex"
        assert data.get("target_budget") == 12000000
        
        print(f"✓ Project created: {self.__class__.project_id}")
    
    def test_03_get_project(self):
        """Verify project retrieval"""
        if not self.__class__.project_id:
            pytest.skip("No project created")
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{BASE_URL}/api/projects/{self.__class__.project_id}", headers=headers)
        assert response.status_code == 200
        print(f"✓ Project retrieved successfully")


# Global fixtures to share project data between test classes
@pytest.fixture(scope="module")
def test_context():
    """Shared test context"""
    ctx = {}
    
    # Login
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if login_response.status_code == 200:
        ctx["token"] = login_response.json().get("access_token")
        ctx["user_id"] = login_response.json().get("user", {}).get("id")
    
    # Get or create project
    headers = {"Authorization": f"Bearer {ctx['token']}"}
    projects = requests.get(f"{BASE_URL}/api/projects", headers=headers)
    if projects.status_code == 200 and len(projects.json()) > 0:
        ctx["project_id"] = projects.json()[0]["id"]
    
    return ctx


class TestMacroMicroWorkflow:
    """4. Workflow Macro → Micro tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_context):
        self.ctx = test_context
    
    def test_04_get_macro_categories(self, test_context):
        """Get macro categories (enveloppe)"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/macro-categories", 
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5  # Default categories
        print(f"✓ Macro categories: {len(data)} categories")
    
    def test_05_lock_macro_envelope(self, test_context):
        """Lock macro envelope"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        response = requests.post(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/lock-macro",
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Macro envelope locked")
        
        # Unlock for subsequent tests
        requests.post(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/unlock-macro",
            headers=headers
        )


class TestProgramGenerator:
    """3. Program Generator tests"""
    
    def test_06_generate_program_from_brief(self, test_context):
        """POST /api/program/generate-from-brief"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        program_data = {
            "description": "Résidence de 50 logements collectifs avec commerces en RDC",
            "project_type": "housing",
            "target_units": 50
        }
        
        response = requests.post(
            f"{BASE_URL}/api/program/generate-from-brief",
            json=program_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "typologies" in data or "programme" in data
        assert "surfaces" in data
        assert data.get("target_units") == 50
        print(f"✓ Program generated: {data.get('surfaces', {}).get('sdp_estimee', 0)} m² SDP")


class TestInstantEstimation:
    """5. Instant Estimation IA GPT-4o tests"""
    
    def test_07_instant_estimation(self, test_context):
        """POST /api/instant-estimation"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        estimation_data = {
            "description": "Construction d'un immeuble de bureaux de 3000 m² sur 4 niveaux à Lyon, qualité premium avec certifications HQE",
            "project_id": test_context.get("project_id")
        }
        
        response = requests.post(
            f"{BASE_URL}/api/instant-estimation",
            json=estimation_data,
            headers=headers,
            timeout=60  # AI call may take time
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify AI estimation structure
        assert "estimated_cost" in data or "total_cost" in data or "estimation" in data
        print(f"✓ Instant estimation generated via GPT-4o")


class TestCCTPGenerator:
    """6. CCTP Generator (16 lots) tests"""
    
    def test_08_get_cctp_lots(self, test_context):
        """GET /api/cctp/lots"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/cctp/lots",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 10  # At least 10 lots
        print(f"✓ CCTP lots available: {len(data)} lots")
    
    def test_09_generate_cctp(self, test_context):
        """POST /api/projects/{id}/cctp/generate"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        cctp_data = {
            "structure_type": "concrete",
            "facade_type": "render",
            "selected_lots": None  # Generate all lots
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/cctp/generate",
            json=cctp_data,
            headers=headers,
            timeout=90  # AI generation
        )
        assert response.status_code == 200
        data = response.json()
        assert "lots" in data or "cctp" in data or "content" in data
        print(f"✓ CCTP generated with AI prescriptions")


class TestCarbonAnalysis:
    """8. Carbon Analysis RE2020 tests"""
    
    def test_10_carbon_factors(self, test_context):
        """GET /api/carbon/factors"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/carbon/factors",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        print(f"✓ Carbon factors retrieved")
    
    def test_11_re2020_thresholds(self, test_context):
        """GET /api/carbon/re2020-thresholds"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/carbon/re2020-thresholds",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "housing" in data or len(data) > 0
        print(f"✓ RE2020 thresholds retrieved")
    
    def test_12_carbon_analysis(self, test_context):
        """POST /api/projects/{id}/carbon/analyze"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        carbon_data = {
            "structure_type": "concrete",
            "facade_type": "brick",
            "insulation_type": "mineral_wool"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/carbon/analyze",
            json=carbon_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_carbon" in data or "emissions" in data or "carbon_footprint" in data
        print(f"✓ Carbon analysis completed")


class TestQuantityTakeoff:
    """17. Quantity Takeoff tests"""
    
    def test_13_generate_takeoff(self, test_context):
        """POST /api/projects/{id}/quantity-takeoff/generate"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        takeoff_data = {
            "surface_m2": 5000,
            "floors": 6,
            "quality_level": "premium"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/quantity-takeoff/generate",
            json=takeoff_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "lots" in data or "quantities" in data
        print(f"✓ Quantity takeoff generated")


class TestPlanning:
    """11. Planning Module tests"""
    
    def test_14_get_planning(self, test_context):
        """GET /api/projects/{id}/planning"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/planning",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "phases" in data
        print(f"✓ Planning retrieved: {len(data.get('phases', []))} phases")


class TestTeamManagement:
    """12. Team Management tests"""
    
    def test_15_get_team(self, test_context):
        """GET /api/projects/{id}/team"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/team",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data or "members" in data
        print(f"✓ Team management data retrieved")
    
    def test_16_add_team_member(self, test_context):
        """POST /api/projects/{id}/team/member"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        member_data = {
            "name": "TEST_Member_Final",
            "role_code": "architect",
            "company": "Test Archi Co",
            "email": "test.arch@example.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/team/member",
            json=member_data,
            headers=headers
        )
        assert response.status_code == 200
        print(f"✓ Team member added")


class TestAlerts:
    """13. Alerts System tests"""
    
    def test_17_get_alerts(self, test_context):
        """GET /api/projects/{id}/alerts"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/alerts",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Alerts retrieved: {len(data)} alerts")


class TestScenarios:
    """14. Scenario Simulation tests"""
    
    def test_18_create_scenario(self, test_context):
        """POST /api/projects/{id}/scenarios"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        scenario_data = {
            "project_id": test_context['project_id'],
            "name": "TEST_Scenario_Optimistic",
            "description": "Scénario optimiste avec économies sur façade",
            "macro_adjustments": {
                "FAC": -10,
                "INT": -5
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/scenarios",
            json=scenario_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ Scenario created")
    
    def test_19_get_scenarios(self, test_context):
        """GET /api/projects/{id}/scenarios"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/scenarios",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Scenarios retrieved: {len(data)}")


class TestArbitrage:
    """15. Arbitrage Module tests"""
    
    def test_20_get_arbitrage(self, test_context):
        """GET /api/projects/{id}/arbitrage"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/arbitrage",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data or "arbitrage" in data
        print(f"✓ Arbitrage suggestions retrieved")


class TestDecisionJournal:
    """16. Decision Journal tests"""
    
    def test_21_get_decisions(self, test_context):
        """GET /api/projects/{id}/decisions"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/decisions",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "decisions" in data
        print(f"✓ Decision journal retrieved")
    
    def test_22_add_decision(self, test_context):
        """POST /api/projects/{id}/decisions"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        decision_data = {
            "title": "TEST_Decision_Final",
            "description": "Validation choix structure béton armé",
            "category": "technical",
            "impact": "high",
            "decision_maker": "Admin Test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/decisions",
            json=decision_data,
            headers=headers
        )
        assert response.status_code == 200
        print(f"✓ Decision added")


class TestDiagnostic:
    """18. Diagnostic IA tests"""
    
    def test_23_diagnostic(self, test_context):
        """GET /api/projects/{id}/diagnostic"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/diagnostic",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data or "diagnostic" in data or "status" in data
        print(f"✓ AI Diagnostic generated")


class TestFeasibility:
    """19. Feasibility Analysis tests"""
    
    def test_24_feasibility(self, test_context):
        """GET /api/projects/{id}/feasibility"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/feasibility",
            headers=headers
        )
        # 200 or 404 are both valid (may not have feasibility analysis created)
        assert response.status_code in [200, 404]
        print(f"✓ Feasibility endpoint verified")


class TestExports:
    """9, 10. Export tests (DPGF, PDF, Excel)"""
    
    def test_25_list_exports(self, test_context):
        """GET /api/projects/{id}/exports"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/exports",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least CSV, DPGF, PDF
        print(f"✓ Exports available: {len(data)} formats")
    
    def test_26_export_csv(self, test_context):
        """GET /api/projects/{id}/export/csv"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/export/csv",
            headers=headers
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print(f"✓ CSV export working")
    
    def test_27_export_dpgf(self, test_context):
        """GET /api/projects/{id}/export/dpgf"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/export/dpgf",
            headers=headers
        )
        assert response.status_code == 200
        print(f"✓ DPGF export working")
    
    def test_28_export_client_report(self, test_context):
        """GET /api/projects/{id}/export/client-report"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/export/client-report",
            headers=headers
        )
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        print(f"✓ Client report PDF export working")
    
    def test_29_export_technical_report(self, test_context):
        """GET /api/projects/{id}/export/technical-report"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/export/technical-report",
            headers=headers
        )
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        print(f"✓ Technical report PDF export working")


class TestWorkflowStatus:
    """Workflow status verification"""
    
    def test_30_workflow_status(self, test_context):
        """GET /api/projects/{id}/workflow-status"""
        headers = {"Authorization": f"Bearer {test_context['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{test_context['project_id']}/workflow-status",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data or "progress" in data
        print(f"✓ Workflow status retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
