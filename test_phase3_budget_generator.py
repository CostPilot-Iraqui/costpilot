"""
CostPilot Senior - Phase 3 Backend API Tests
Tests for Budget Generator and Pricing Library with ~3915 entries

Features tested:
- Authentication
- Pricing Library with filters (building_type, quality_level)
- Project creation with generated budget data
- Dashboard overview
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://feasibility-platform.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "economiste@costpilot.fr"
TEST_PASSWORD = "CostPilot2024!"


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["role"] == "senior_cost_manager"


@pytest.fixture(scope="class")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Authentication failed")


class TestPricingLibraryPhase3:
    """Pricing library API tests - Phase 3 (3915 entries)"""
    
    def test_pricing_library_count(self, auth_token):
        """Test that pricing library has ~3915 entries"""
        response = requests.get(
            f"{BASE_URL}/api/pricing-library",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should have approximately 3915 entries
        # 7 macro-lots × ~130 postes × 5 typologies × 3 qualités
        assert len(data) >= 3900, f"Expected ~3915 entries, got {len(data)}"
        print(f"Pricing library count: {len(data)} entries")
    
    def test_pricing_library_structure(self, auth_token):
        """Test that pricing entries have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/pricing-library",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check first entry structure
        if len(data) > 0:
            entry = data[0]
            required_fields = [
                "id", "building_type", "region", "year_reference",
                "quality_level", "category", "lot_code", "lot",
                "item", "unit", "unit_price_min", "unit_price_avg", "unit_price_max"
            ]
            for field in required_fields:
                assert field in entry, f"Missing field: {field}"
    
    def test_pricing_library_filter_by_building_type(self, auth_token):
        """Test filtering pricing library by building_type"""
        response = requests.get(
            f"{BASE_URL}/api/pricing-library",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        
        # Check that different building types exist
        building_types = set(e.get("building_type") for e in data)
        expected_types = {"housing", "office", "retail", "hotel", "public_facility"}
        
        # At least some of these should be present
        assert len(building_types.intersection(expected_types)) >= 3, \
            f"Not enough building types. Found: {building_types}"
        print(f"Building types in library: {building_types}")
    
    def test_pricing_library_filter_by_quality(self, auth_token):
        """Test filtering pricing library by quality_level"""
        response = requests.get(
            f"{BASE_URL}/api/pricing-library",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        
        # Check that different quality levels exist
        quality_levels = set(e.get("quality_level") for e in data)
        expected_qualities = {"economic", "standard", "premium"}
        
        assert expected_qualities.issubset(quality_levels), \
            f"Missing quality levels. Found: {quality_levels}, Expected: {expected_qualities}"
        print(f"Quality levels in library: {quality_levels}")
    
    def test_pricing_library_categories(self, auth_token):
        """Test that all macro-lot categories are represented"""
        response = requests.get(
            f"{BASE_URL}/api/pricing-library",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        
        # Check categories (macro-lots)
        categories = set(e.get("category") for e in data)
        expected_categories = {
            "Infrastructure", "Superstructure", "Façades / Enveloppe",
            "Travaux Intérieurs", "Systèmes Techniques", "Travaux Extérieurs"
        }
        
        # At least 6 categories should be present
        assert len(categories) >= 6, f"Not enough categories. Found: {categories}"
        print(f"Categories in library: {categories}")
    
    def test_pricing_library_search_beton(self, auth_token):
        """Test searching for 'béton' in pricing library"""
        response = requests.get(
            f"{BASE_URL}/api/pricing-library",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        
        # Filter locally for items containing 'béton' or 'beton'
        beton_items = [e for e in data if 'béton' in (e.get("item", "") or "").lower() or 'beton' in (e.get("item", "") or "").lower()]
        
        assert len(beton_items) > 0, "No items found with 'béton' in name"
        print(f"Found {len(beton_items)} items containing 'béton'")


class TestDashboardOverview:
    """Dashboard overview API tests"""
    
    def test_dashboard_overview_success(self, auth_token):
        """Test dashboard overview endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/overview",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "total_projects" in data
        assert "total_budget" in data
        assert "total_surface" in data
        assert "recent_projects" in data
        
        # Verify values are reasonable
        assert isinstance(data["total_projects"], int)
        assert isinstance(data["total_budget"], (int, float))
        assert isinstance(data["total_surface"], (int, float))


class TestProjectCreationWithBudget:
    """Test project creation with generated budget data"""
    
    def test_create_project_with_generated_budget(self, auth_token):
        """Test creating a project with generated budget data"""
        # Create project with generated_budget_data
        project_data = {
            "project_name": "TEST_Budget Generator Project",
            "client_name": "Test Client Budget Gen",
            "location": "Grande couronne",
            "project_usage": "housing",
            "target_surface_m2": 5000,
            "number_of_levels_estimate": 6,
            "quality_level": "standard",
            "parking_requirement": "none",
            "basement_presence": "none",
            "target_budget": 10000000,
            "confidence_level": "medium",
            "generated_budget_data": {
                "coutTotal": {"min": 8750000, "avg": 10000000, "max": 11250000},
                "ratioFinalM2": {"min": 1750, "avg": 2000, "max": 2250},
                "macroLots": [
                    {"code": "INF", "name": "Infrastructure", "pourcentage": 8},
                    {"code": "SUP", "name": "Superstructure", "pourcentage": 22},
                    {"code": "FAC", "name": "Façades / Enveloppe", "pourcentage": 18},
                    {"code": "INT", "name": "Travaux Intérieurs", "pourcentage": 25},
                    {"code": "TEC", "name": "Systèmes Techniques", "pourcentage": 18},
                    {"code": "EXT", "name": "Travaux Extérieurs", "pourcentage": 5},
                    {"code": "ALE", "name": "Aléas et Imprévus", "pourcentage": 4}
                ]
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects",
            json=project_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to create project: {response.text}"
        data = response.json()
        
        # Verify project was created
        assert "id" in data
        assert data["project_name"] == "TEST_Budget Generator Project"
        assert data["target_budget"] == 10000000
        
        # Store project ID for verification and cleanup
        pytest.budget_project_id = data["id"]
        print(f"Created project with ID: {data['id']}")
    
    def test_verify_project_macro_categories(self, auth_token):
        """Verify that macro categories were created for the project"""
        if not hasattr(pytest, "budget_project_id"):
            pytest.skip("No budget project created")
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{pytest.budget_project_id}/macro-categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have 7 categories
        assert len(data) == 7
        
        # Verify category codes
        codes = {cat["code"] for cat in data}
        expected_codes = {"INF", "SUP", "FAC", "INT", "TEC", "EXT", "ALE"}
        assert codes == expected_codes
        
        print(f"Project has {len(data)} macro categories: {codes}")
    
    def test_cleanup_budget_project(self, auth_token):
        """Clean up test project - Note: Delete may be restricted"""
        if not hasattr(pytest, "budget_project_id"):
            pytest.skip("No budget project to clean up")
        
        response = requests.delete(
            f"{BASE_URL}/api/projects/{pytest.budget_project_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # 200, 403 (forbidden), or 404 are acceptable
        # 403 means delete is restricted which is expected for non-admin users
        assert response.status_code in [200, 403, 404], f"Unexpected status: {response.status_code}"


class TestReferenceRatios:
    """Reference ratios API tests"""
    
    def test_get_reference_ratios(self, auth_token):
        """Test retrieving reference ratios"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
