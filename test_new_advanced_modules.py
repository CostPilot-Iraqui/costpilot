"""
Backend API Tests for CostPilot New Advanced Modules
Tests: BIM/IFC Import, Instant Estimation, CCTP Generator, Carbon Analysis, Plan AI Reading, PLU Zones
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://feasibility-platform.preview.emergentagent.com').rstrip('/')

# Test credentials - using the new test user
TEST_EMAIL = "test_new@costpilot.com"
TEST_PASSWORD = "Test123!"
TEST_PROJECT_ID = "8e94d4b8-feff-4bd6-ba61-f070b54cc26d"


class TestAuthentication:
    """Authentication tests for new credentials"""
    
    def test_health_endpoint(self):
        """Test API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✓ Health endpoint working")
    
    def test_login_new_user(self):
        """Test login with new test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text[:500] if response.text else 'empty'}")
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"✓ Login successful for {TEST_EMAIL}")
        return data["access_token"]


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    
    # Fallback to old test user if new one doesn't exist
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@test.com",
        "password": "test"
    })
    if response.status_code == 200:
        print("Warning: Using fallback test user test@test.com")
        return response.json()["access_token"]
    
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


# =============================================================================
# INSTANT ESTIMATION MODULE TESTS
# =============================================================================
class TestInstantEstimation:
    """Instant Estimation API Tests"""
    
    def test_instant_estimation_with_description(self, headers):
        """Test instant estimation with natural language description"""
        response = requests.post(
            f"{BASE_URL}/api/instant-estimation",
            headers=headers,
            json={
                "description": "Un immeuble de 50 logements en R+5, structure béton, façade enduit, qualité standard, avec parking souterrain de 60 places",
                "project_id": TEST_PROJECT_ID
            }
        )
        print(f"Instant estimation status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "estimation_id" in data
        assert "generated_at" in data
        assert "input" in data
        assert "estimation" in data
        assert "cost_distribution" in data
        
        # Verify parsed input
        assert data["input"]["parsed"]["project_type"] == "housing"
        assert data["estimation"]["total_cost"] > 0
        
        print(f"✓ Instant estimation generated: {data['estimation']['total_cost']} €")
        print(f"  - Type: {data['input']['parsed']['project_type']}")
        print(f"  - Surface: {data['input']['parsed']['surface_m2']} m²")
        print(f"  - Cost/m²: {data['estimation']['cost_per_m2']} €/m²")
    
    def test_instant_estimation_short_description_fails(self, headers):
        """Test instant estimation with too short description fails"""
        response = requests.post(
            f"{BASE_URL}/api/instant-estimation",
            headers=headers,
            json={"description": "test"}
        )
        assert response.status_code == 400
        print("✓ Short description correctly rejected")
    
    def test_instant_estimation_history(self, headers):
        """Test instant estimation history endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/instant-estimation/history?limit=5",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Estimation history retrieved: {len(data)} items")


# =============================================================================
# CCTP GENERATOR MODULE TESTS
# =============================================================================
class TestCCTPGenerator:
    """CCTP Generator API Tests"""
    
    def test_get_cctp_lots(self, headers):
        """Test get CCTP lots list"""
        response = requests.get(
            f"{BASE_URL}/api/cctp/lots",
            headers=headers
        )
        print(f"CCTP lots status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify lots structure - should have 16 lots
        assert isinstance(data, dict)
        assert len(data) >= 10  # At least 10 lots
        
        # Check some expected lots
        assert "01" in data  # Installation de chantier
        assert "03" in data  # Gros œuvre
        assert "13" in data  # Électricité
        
        print(f"✓ CCTP lots retrieved: {len(data)} lots")
        for code, info in list(data.items())[:3]:
            print(f"  - {code}: {info['name']}")
    
    def test_generate_cctp(self, headers):
        """Test CCTP generation"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cctp/generate",
            headers=headers,
            json={
                "structure_type": "concrete",
                "facade_type": "render",
                "selected_lots": ["01", "02", "03", "05", "13"]
            }
        )
        print(f"CCTP generate status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify CCTP structure
        assert "id" in data
        assert "project" in data
        assert "general_clauses" in data
        assert "lots" in data
        
        print(f"✓ CCTP generated: {len(data['lots'])} lots")
        print(f"  - Project: {data['project'].get('name')}")
    
    def test_get_project_cctps(self, headers):
        """Test get project CCTPs"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cctp",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Project CCTPs retrieved: {len(data)} documents")


# =============================================================================
# CARBON ANALYSIS MODULE TESTS
# =============================================================================
class TestCarbonAnalysis:
    """Carbon Analysis API Tests"""
    
    def test_analyze_carbon(self, headers):
        """Test carbon analysis for project"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/carbon/analyze",
            headers=headers,
            json={
                "structure_type": "concrete",
                "facade_type": "brick",
                "insulation_type": "mineral_wool"
            }
        )
        print(f"Carbon analysis status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "analysis_id" in data
        assert "carbon_footprint" in data
        assert "breakdown_by_category" in data
        assert "re2020_compliance" in data
        assert "recommendations" in data
        
        # Verify carbon footprint
        assert data["carbon_footprint"]["total_kgco2e"] > 0
        assert data["carbon_footprint"]["per_m2_kgco2e"] > 0
        
        print(f"✓ Carbon analysis generated:")
        print(f"  - Total: {data['carbon_footprint']['total_tonnes']} tonnes CO2e")
        print(f"  - Per m²: {data['carbon_footprint']['per_m2_kgco2e']} kgCO2e/m²")
        print(f"  - Benchmark: {data['benchmark']['label']}")
    
    def test_get_carbon_analyses(self, headers):
        """Test get carbon analyses for project"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/carbon",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Carbon analyses retrieved: {len(data)} analyses")
    
    def test_get_carbon_factors(self, headers):
        """Test get carbon factors"""
        response = requests.get(
            f"{BASE_URL}/api/carbon/factors",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "beton_m3" in data
        print(f"✓ Carbon factors retrieved: {len(data)} factors")
    
    def test_get_re2020_thresholds(self, headers):
        """Test get RE2020 thresholds"""
        response = requests.get(
            f"{BASE_URL}/api/carbon/re2020-thresholds",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "housing" in data
        print(f"✓ RE2020 thresholds retrieved")


# =============================================================================
# PLU ZONES MODULE TESTS
# =============================================================================
class TestPLUZones:
    """PLU Zones API Tests"""
    
    def test_get_plu_zones(self, headers):
        """Test get PLU zones"""
        response = requests.get(
            f"{BASE_URL}/api/plu-zones",
            headers=headers
        )
        print(f"PLU zones status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # API returns list or dict depending on implementation
        assert isinstance(data, (dict, list))
        print(f"✓ PLU zones retrieved: {len(data)} zones")
        if isinstance(data, dict):
            for zone, info in list(data.items())[:3]:
                print(f"  - {zone}: CES={info.get('ces')}, COS={info.get('cos')}")
        else:
            for zone in data[:3]:
                print(f"  - {zone.get('code')}: CES={zone.get('ces')}, COS={zone.get('cos')}")


# =============================================================================
# BIM/IFC MODULE TESTS
# =============================================================================
class TestBIMIFC:
    """BIM/IFC Import API Tests"""
    
    def test_get_ifc_analyses(self, headers):
        """Test get IFC analyses for project"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/ifc/analyses",
            headers=headers
        )
        print(f"IFC analyses status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ IFC analyses retrieved: {len(data)} analyses")


# =============================================================================
# PLAN AI READING MODULE TESTS
# =============================================================================
class TestPlanAIReading:
    """Plan AI Reading API Tests"""
    
    def test_get_plan_analyses(self, headers):
        """Test get plan AI analyses for project"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/plan-ai/analyses",
            headers=headers
        )
        print(f"Plan AI analyses status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Plan AI analyses retrieved: {len(data)} analyses")


# =============================================================================
# PROGRAM GENERATOR MODULE TESTS
# =============================================================================
class TestProgramGenerator:
    """Program Generator API Tests"""
    
    def test_generate_program_from_brief(self, headers):
        """Test generate program from brief"""
        response = requests.post(
            f"{BASE_URL}/api/program/generate-from-brief",
            headers=headers,
            json={
                "description": "Résidence de 60 logements collectifs avec parking souterrain à Lyon",
                "project_type": "housing",
                "target_units": 60
            }
        )
        print(f"Program generate status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "target_units" in data
        assert "typologies" in data or "programme" in data
        assert "surfaces" in data
        
        print(f"✓ Program generated: {data.get('target_units')} units")
    
    def test_generate_program_for_project(self, headers):
        """Test generate program for a project"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/program/generate",
            headers=headers,
            json={
                "land_surface_m2": 2500,
                "plu_zone": "UB",
                "building_type": "housing",
                "quality_level": "standard"
            }
        )
        print(f"Project program generate status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ Project program generated")


# =============================================================================
# WORKFLOW STATUS MODULE TESTS
# =============================================================================
class TestWorkflowStatus:
    """Workflow Status API Tests"""
    
    def test_get_workflow_status(self, headers):
        """Test get workflow status for project"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/workflow-status",
            headers=headers
        )
        print(f"Workflow status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "project_id" in data
        assert "steps" in data
        assert "progress" in data
        
        print(f"✓ Workflow status retrieved: {data['progress']['percentage']}% complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
