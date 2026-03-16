"""
CostPilot Senior - Phase 2 Backend API Tests
Tests for micro spreadsheet, pricing library, and lot structure features
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://feasibility-platform.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "economiste@costpilot.fr"
TEST_PASSWORD = "CostPilot2024!"
TEST_PROJECT_ID = "8e94d4b8-feff-4bd6-ba61-f070b54cc26d"


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
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401


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


class TestMicroItems:
    """Micro items (lot/sous-lot) API tests"""
    
    def test_get_micro_items(self, auth_token):
        """Test retrieving micro items for a project"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/micro-items",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have items from previous tests
        
        # Verify item structure
        item = data[0]
        assert "id" in item
        assert "lot_code" in item
        assert "lot_name" in item
        assert "description" in item
        assert "quantity" in item
        assert "unit_price" in item
        assert "amount" in item
        assert "cost_ratio" in item
    
    def test_create_micro_item(self, auth_token):
        """Test creating a new micro item"""
        # Get macro category ID first
        categories_response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/macro-categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        categories = categories_response.json()
        inf_category = next((c for c in categories if c["code"] == "INF"), None)
        assert inf_category is not None, "INF category not found"
        
        new_item = {
            "project_id": TEST_PROJECT_ID,
            "macro_category_id": inf_category["id"],
            "lot_code": "INF.01",
            "lot_name": "Terrassements",
            "sub_lot_code": "INF.01.TEST",
            "sub_lot_name": "TEST_Poste de test API",
            "item_code": "INF.01.TEST",
            "description": "TEST_Poste créé via API test",
            "unit": "m³",
            "quantity": 100,
            "unit_price": 50
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/micro-items",
            json=new_item,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify created item
        assert data["description"] == "TEST_Poste créé via API test"
        assert data["quantity"] == 100
        assert data["unit_price"] == 50
        assert data["amount"] == 5000  # 100 * 50
        assert "cost_ratio" in data
        
        # Store ID for update/delete tests
        pytest.test_item_id = data["id"]
    
    def test_update_micro_item(self, auth_token):
        """Test updating a micro item"""
        if not hasattr(pytest, "test_item_id"):
            pytest.skip("No test item created")
        
        update_data = {
            "quantity": 200,
            "unit_price": 75
        }
        
        response = requests.put(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/micro-items/{pytest.test_item_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify update
        assert data["quantity"] == 200
        assert data["unit_price"] == 75
        assert data["amount"] == 15000  # 200 * 75
    
    def test_delete_micro_item(self, auth_token):
        """Test deleting a micro item"""
        if not hasattr(pytest, "test_item_id"):
            pytest.skip("No test item created")
        
        response = requests.delete(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/micro-items/{pytest.test_item_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        # Verify deletion
        verify_response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/micro-items",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        items = verify_response.json()
        assert not any(item["id"] == pytest.test_item_id for item in items)


class TestMacroCategories:
    """Macro categories API tests"""
    
    def test_get_macro_categories(self, auth_token):
        """Test retrieving macro categories for a project"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/macro-categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have 7 default categories
        assert len(data) == 7
        
        # Verify category codes
        codes = {cat["code"] for cat in data}
        expected_codes = {"INF", "SUP", "FAC", "INT", "TEC", "EXT", "ALE"}
        assert codes == expected_codes
        
        # Verify category structure
        cat = data[0]
        assert "id" in cat
        assert "name" in cat
        assert "code" in cat
        assert "target_amount" in cat
        assert "estimated_amount" in cat


class TestPricingLibrary:
    """Pricing library API tests"""
    
    def test_get_pricing_entries(self, auth_token):
        """Test retrieving pricing library entries"""
        response = requests.get(
            f"{BASE_URL}/api/pricing-library",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should have entries from import test
        if len(data) > 0:
            entry = data[0]
            assert "building_type" in entry
            assert "lot_code" in entry
            assert "item" in entry
            assert "unit_price_avg" in entry
            assert "unit_price_min" in entry
            assert "unit_price_max" in entry
    
    def test_create_pricing_entry(self, auth_token):
        """Test creating a new pricing entry"""
        new_entry = {
            "building_type": "office",
            "region": "idf",
            "year_reference": 2026,
            "quality_level": "standard",
            "complexity_level": "medium",
            "category": "TEST",
            "lot_code": "TEST.01",
            "lot": "Test Lot",
            "item": "TEST_API Created Entry",
            "unit": "m²",
            "unit_price_min": 80,
            "unit_price_avg": 100,
            "unit_price_max": 120
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing-library",
            json=new_entry,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify created entry
        assert data["item"] == "TEST_API Created Entry"
        assert data["unit_price_avg"] == 100
        
        # Store ID for cleanup
        pytest.test_pricing_id = data["id"]
    
    def test_delete_pricing_entry(self, auth_token):
        """Test deleting a pricing entry"""
        if not hasattr(pytest, "test_pricing_id"):
            pytest.skip("No test pricing entry created")
        
        response = requests.delete(
            f"{BASE_URL}/api/pricing-library/{pytest.test_pricing_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200


class TestProjectDashboard:
    """Project dashboard API tests"""
    
    def test_get_dashboard(self, auth_token):
        """Test retrieving project dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify dashboard structure
        assert "project" in data
        assert "summary" in data
        assert "category_breakdown" in data
        
        # Verify summary fields
        summary = data["summary"]
        assert "macro_total" in summary
        assert "micro_total" in summary
        assert "variance" in summary
        assert "cost_per_m2" in summary
    
    def test_macro_vs_micro_comparison(self, auth_token):
        """Test macro vs micro comparison endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/macro-vs-micro",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify comparison data
        assert "comparison" in data
        assert "totals" in data
        
        totals = data["totals"]
        assert "macro_total" in totals
        assert "micro_total" in totals
        assert "variance" in totals
        
        # Verify comparison has category data
        assert len(data["comparison"]) > 0
        comparison_item = data["comparison"][0]
        assert "category_code" in comparison_item
        assert "current_micro_total" in comparison_item


class TestProjectEndpoints:
    """Basic project endpoint tests"""
    
    def test_get_project(self, auth_token):
        """Test retrieving a specific project"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == TEST_PROJECT_ID
        assert "project_name" in data
        assert "target_surface_m2" in data
        assert "target_budget" in data
    
    def test_get_projects_list(self, auth_token):
        """Test retrieving projects list"""
        response = requests.get(
            f"{BASE_URL}/api/projects",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
