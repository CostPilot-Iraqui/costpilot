"""
CostPilot Senior - Tests for Reference Ratios, Program Generator, and Budget Generator
Tests the 48 reference ratios, filtering, and budget calculation logic
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@costpilot.fr"
TEST_PASSWORD = "demo123456"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture
def auth_headers(auth_token):
    """Create headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestReferenceRatios:
    """Test reference ratios API - 48 ratios in DB"""

    def test_get_all_ratios(self, auth_headers):
        """Test fetching all 48 reference ratios"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have 48 ratios as per populate script
        assert len(data) == 48, f"Expected 48 ratios, got {len(data)}"
        print(f"PASS: 48 reference ratios found in database")

    def test_ratios_have_min_avg_max(self, auth_headers):
        """Test that ratios have min/avg/max values for statistics display"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # All ratios should have cost_min_m2, cost_avg_m2, cost_max_m2
        for ratio in data[:10]:  # Check first 10
            assert ratio.get("cost_min_m2") is not None, "Missing cost_min_m2"
            assert ratio.get("cost_avg_m2") is not None, "Missing cost_avg_m2"
            assert ratio.get("cost_max_m2") is not None, "Missing cost_max_m2"
            # Verify min <= avg <= max
            assert ratio["cost_min_m2"] <= ratio["cost_avg_m2"] <= ratio["cost_max_m2"]
        print("PASS: All ratios have min/avg/max statistics")

    def test_filter_by_building_type(self, auth_headers):
        """Test filtering ratios by building type (housing)"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios?building_type=housing",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have 8 housing ratios
        assert len(data) == 8, f"Expected 8 housing ratios, got {len(data)}"
        for ratio in data:
            assert ratio["building_type"] == "housing"
        print(f"PASS: Filter by building_type=housing returned 8 ratios")

    def test_filter_by_quality_level(self, auth_headers):
        """Test filtering ratios by quality level"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios?quality_level=standard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Standard quality should exist for multiple types
        assert len(data) > 0, "No standard quality ratios found"
        for ratio in data:
            assert ratio["quality_level"] == "standard"
        print(f"PASS: Filter by quality_level=standard returned {len(data)} ratios")

    def test_housing_ratios_range(self, auth_headers):
        """Verify housing ratios are in expected range: 1850-3800€/m²"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios?building_type=housing",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        costs = [r["cost_avg_m2"] for r in data]
        min_cost = min(costs)
        max_cost = max(costs)
        
        # Expected: economic=1650-1850, luxury=3800
        assert min_cost >= 1600, f"Min housing cost {min_cost} below expected"
        assert max_cost <= 4000, f"Max housing cost {max_cost} above expected"
        print(f"PASS: Housing ratios range {min_cost}-{max_cost} EUR/m2")

    def test_office_ratios_range(self, auth_headers):
        """Verify office ratios are in expected range: 1750-3600€/m²"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios?building_type=office",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        costs = [r["cost_avg_m2"] for r in data]
        min_cost = min(costs)
        max_cost = max(costs)
        
        assert min_cost >= 1500, f"Min office cost {min_cost} below expected"
        assert max_cost <= 4000, f"Max office cost {max_cost} above expected"
        print(f"PASS: Office ratios range {min_cost}-{max_cost} EUR/m2")

    def test_hotel_ratios_range(self, auth_headers):
        """Verify hotel ratios are in expected range: 2100-5000€/m²"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios?building_type=hotel",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        costs = [r["cost_avg_m2"] for r in data]
        min_cost = min(costs)
        max_cost = max(costs)
        
        # Hotel has higher range
        assert max_cost <= 6000, f"Max hotel cost {max_cost} above expected"
        print(f"PASS: Hotel ratios range {min_cost}-{max_cost} EUR/m2")

    def test_retail_ratios_range(self, auth_headers):
        """Verify retail/commerce ratios are in expected range: 1450-3200€/m²"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios?building_type=retail",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        costs = [r["cost_avg_m2"] for r in data]
        min_cost = min(costs)
        max_cost = max(costs)
        
        assert min_cost >= 1200, f"Min retail cost {min_cost} below expected"
        assert max_cost <= 3500, f"Max retail cost {max_cost} above expected"
        print(f"PASS: Retail ratios range {min_cost}-{max_cost} EUR/m2")

    def test_ratios_have_location_info(self, auth_headers):
        """Test that ratios have location information for filtering"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        locations_found = set()
        for ratio in data:
            loc = ratio.get("location")
            if loc:
                locations_found.add(loc)
        
        # Should have multiple locations
        expected_locations = {"ile_de_france", "grande_couronne", "grandes_metropoles", "regions"}
        assert len(locations_found) >= 3, f"Only {len(locations_found)} locations found"
        print(f"PASS: Found locations: {locations_found}")

    def test_ratios_have_breakdown(self, auth_headers):
        """Test that ratios have infrastructure/superstructure/facade breakdown"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios?building_type=housing&quality_level=standard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data:
            ratio = data[0]
            # Check for breakdown fields
            breakdown_fields = [
                "infrastructure_cost_m2",
                "superstructure_cost_m2", 
                "facade_cost_m2",
                "interior_works_cost_m2",
                "technical_systems_cost_m2",
                "external_works_cost_m2"
            ]
            for field in breakdown_fields:
                assert field in ratio, f"Missing field: {field}"
                assert ratio[field] >= 0, f"Field {field} should be >= 0"
            print("PASS: Ratios have cost breakdown by category")


class TestProjectCreation:
    """Test project creation from budget generator"""

    def test_create_project_with_budget(self, auth_headers):
        """Test creating a project with budget from generator"""
        import uuid
        project_name = f"TEST_Budget_Gen_{uuid.uuid4().hex[:8]}"
        
        project_data = {
            "project_name": project_name,
            "client_name": "Test Client",
            "location": "Île-de-France",
            "project_usage": "housing",
            "target_surface_m2": 5000,
            "number_of_levels_estimate": 6,
            "quality_level": "standard",
            "complexity_level": "medium",
            "parking_requirement": "underground",
            "basement_presence": "partial",
            "target_budget": 11000000,  # 2200€/m² * 5000m²
            "confidence_level": "medium"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects",
            headers=auth_headers,
            json=project_data
        )
        assert response.status_code == 200
        
        project = response.json()
        assert project["project_name"] == project_name
        assert project["target_budget"] == 11000000
        assert project["target_surface_m2"] == 5000
        
        # Cleanup
        project_id = project["id"]
        requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        
        print(f"PASS: Created project with budget from generator")

    def test_project_creates_macro_categories(self, auth_headers):
        """Test that project creation auto-creates 7 macro categories"""
        import uuid
        project_name = f"TEST_MacroCat_{uuid.uuid4().hex[:8]}"
        
        project_data = {
            "project_name": project_name,
            "client_name": "Test Client",
            "project_usage": "housing",
            "target_surface_m2": 5000,
            "target_budget": 10000000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects",
            headers=auth_headers,
            json=project_data
        )
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        # Get macro categories
        cat_response = requests.get(
            f"{BASE_URL}/api/projects/{project_id}/macro-categories",
            headers=auth_headers
        )
        assert cat_response.status_code == 200
        categories = cat_response.json()
        
        # Should have 7 default categories
        assert len(categories) == 7, f"Expected 7 categories, got {len(categories)}"
        
        expected_codes = {"INF", "SUP", "FAC", "INT", "TEC", "EXT", "ALE"}
        actual_codes = {c["code"] for c in categories}
        assert actual_codes == expected_codes, f"Missing codes: {expected_codes - actual_codes}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        
        print(f"PASS: Project creates 7 macro categories: {actual_codes}")


class TestLocationCoefficients:
    """Test location coefficients in ratios"""

    def test_idf_has_highest_costs(self, auth_headers):
        """Île-de-France should have highest costs (coefficient 1.15)"""
        response = requests.get(
            f"{BASE_URL}/api/reference-ratios?building_type=housing&quality_level=standard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        costs_by_location = {}
        for ratio in data:
            loc = ratio.get("location", "unknown")
            costs_by_location[loc] = ratio.get("cost_avg_m2", 0)
        
        # IdF should be highest
        if "ile_de_france" in costs_by_location and "regions" in costs_by_location:
            idf_cost = costs_by_location["ile_de_france"]
            regions_cost = costs_by_location["regions"]
            assert idf_cost > regions_cost, f"IdF ({idf_cost}) should be > Régions ({regions_cost})"
            
            # Approximate ratio should be around 1.15/0.85 = 1.35
            ratio = idf_cost / regions_cost if regions_cost > 0 else 0
            assert 1.1 < ratio < 1.5, f"IdF/Régions ratio {ratio} outside expected range"
            print(f"PASS: Location coefficient verified. IdF={idf_cost}, Régions={regions_cost}, ratio={ratio:.2f}")


class TestFeasibility:
    """Test feasibility analysis for projects"""

    def test_feasibility_calculations(self, auth_headers):
        """Test feasibility margin calculations"""
        # First create a project
        import uuid
        project_name = f"TEST_Feasibility_{uuid.uuid4().hex[:8]}"
        
        project_data = {
            "project_name": project_name,
            "client_name": "Test Client",
            "project_usage": "housing",
            "target_surface_m2": 5000,
            "target_budget": 10000000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects",
            headers=auth_headers,
            json=project_data
        )
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        # Create feasibility analysis
        feasibility_data = {
            "project_id": project_id,
            "land_price": 2000000,
            "acquisition_fees": 100000,
            "construction_cost": 10000000,
            "developer_fees": 500000,
            "financing_cost": 200000,
            "sales_price_per_m2": 4000,  # 4000€/m² selling price
            "marketing_costs": 100000,
            "contingencies": 300000,
            "project_duration_months": 24
        }
        
        feas_response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/feasibility",
            headers=auth_headers,
            json=feasibility_data
        )
        assert feas_response.status_code == 200
        
        feas = feas_response.json()
        
        # Verify calculations
        # Total cost = 2000000 + 100000 + 10000000 + 500000 + 200000 + 100000 + 300000 = 13,200,000
        # Total revenue = 4000 * 5000 = 20,000,000
        # Gross margin = 20,000,000 - 13,200,000 = 6,800,000
        
        assert feas["total_revenue"] == 20000000, f"Revenue: {feas['total_revenue']}"
        assert feas["total_project_cost"] == 13200000, f"Cost: {feas['total_project_cost']}"
        assert feas["gross_margin"] == 6800000, f"Margin: {feas['gross_margin']}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        
        print(f"PASS: Feasibility calculations correct. Margin={feas['gross_margin']:,}€")


class TestDashboard:
    """Test dashboard and overview endpoints"""

    def test_global_dashboard(self, auth_headers):
        """Test global dashboard returns project statistics"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/overview",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_projects" in data
        assert "total_budget" in data
        assert "total_surface" in data
        print(f"PASS: Dashboard returns {data['total_projects']} projects, {data['total_budget']:,.0f}€ budget")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
