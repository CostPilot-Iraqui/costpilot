"""
Backend API Tests for CostPilot Senior Advanced Modules
Tests: Senior Economist, Market Intelligence, Benchmark, Cost Prediction, Multi-Scenario, Design Optimization
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://feasibility-platform.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test"
TEST_PROJECT_ID = "8e94d4b8-feff-4bd6-ba61-f070b54cc26d"


class TestAuthentication:
    """Authentication and login tests"""
    
    def test_health_endpoint(self):
        """Test API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✓ Health endpoint working")
    
    def test_login_success(self):
        """Test user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
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
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestSeniorEconomistModule:
    """Senior Economist Module API Tests"""
    
    def test_get_senior_economist_overview(self, headers):
        """Test senior economist overview endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/senior-economist/projects/{TEST_PROJECT_ID}/overview",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert "workflow_status" in data
        print(f"✓ Senior economist overview: {data.get('workflow_status')}")
    
    def test_get_macro_analysis(self, headers):
        """Test macro analysis endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/senior-economist/projects/{TEST_PROJECT_ID}/macro-analysis",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "market_context" in data or "economic_indicators" in data
        print("✓ Macro analysis retrieved")
    
    def test_get_risk_assessment(self, headers):
        """Test risk assessment endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/senior-economist/projects/{TEST_PROJECT_ID}/risk-assessment",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "risks" in data or isinstance(data, list)
        print(f"✓ Risk assessment retrieved")
    
    def test_get_cost_strategy(self, headers):
        """Test cost strategy endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/senior-economist/projects/{TEST_PROJECT_ID}/cost-strategy",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "strategy_name" in data or "target_savings" in data
        print("✓ Cost strategy retrieved")
    
    def test_get_project_phasing(self, headers):
        """Test project phasing endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/senior-economist/projects/{TEST_PROJECT_ID}/phasing",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "phases" in data or "summary" in data
        print("✓ Project phasing retrieved")
    
    def test_get_workflow(self, headers):
        """Test workflow endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/senior-economist/projects/{TEST_PROJECT_ID}/workflow",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "current_phase" in data or "timeline" in data
        print(f"✓ Workflow retrieved: current phase = {data.get('current_phase')}")
    
    def test_get_team_structure(self, headers):
        """Test team structure endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/senior-economist/projects/{TEST_PROJECT_ID}/team",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data or "raci_matrix" in data
        print("✓ Team structure retrieved")
    
    def test_get_final_validation(self, headers):
        """Test final validation endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/senior-economist/projects/{TEST_PROJECT_ID}/validation",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data or "checklist" in data
        print("✓ Final validation retrieved")
    
    def test_generate_all_analyses(self, headers):
        """Test generate all analyses endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/senior-economist/projects/{TEST_PROJECT_ID}/generate-all",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "analyses" in data
        print(f"✓ Generated all analyses: {data.get('analyses')}")


class TestMarketIntelligenceModule:
    """Market Intelligence Module API Tests"""
    
    def test_get_market_trends(self, headers):
        """Test market trends endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/market-intelligence/trends",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "category" in data[0] or "trend_type" in data[0]
        print(f"✓ Market trends retrieved: {len(data)} trends")
    
    def test_get_regional_indices(self, headers):
        """Test regional indices endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/market-intelligence/regional-indices",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "region" in data[0] or "coefficient" in data[0]
        print(f"✓ Regional indices retrieved: {len(data)} regions")
    
    def test_get_construction_activity(self, headers):
        """Test construction activity endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/market-intelligence/activity",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data or "market_outlook" in data
        print("✓ Construction activity retrieved")
    
    def test_get_price_forecasts(self, headers):
        """Test price forecasts endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/market-intelligence/forecasts",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Price forecasts retrieved: {len(data)} forecasts")
    
    def test_get_market_overview(self, headers):
        """Test market overview endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/market-intelligence/overview",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert "regional_indices" in data
        assert "activity" in data
        assert "forecasts" in data
        print("✓ Market overview retrieved with all sections")


class TestBenchmarkModule:
    """Benchmark Module API Tests"""
    
    def test_get_benchmark_projects(self, headers):
        """Test get benchmark projects endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/benchmark/projects",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "name" in data[0]
            assert "building_type" in data[0]
            assert "cost_per_m2" in data[0]
        print(f"✓ Benchmark projects retrieved: {len(data)} projects")
    
    def test_get_benchmark_projects_filtered(self, headers):
        """Test get benchmark projects with filter"""
        response = requests.get(
            f"{BASE_URL}/api/benchmark/projects?building_type=housing",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Benchmark projects (housing) retrieved: {len(data)} projects")
    
    def test_get_benchmark_statistics(self, headers):
        """Test get benchmark statistics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/benchmark/statistics",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_projects" in data or "by_building_type" in data
        print(f"✓ Benchmark statistics retrieved")
    
    def test_get_project_benchmark(self, headers):
        """Test get project benchmark comparison"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/benchmark",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data or "similar_projects" in data
        print("✓ Project benchmark comparison retrieved")
    
    def test_compare_project_to_benchmarks(self, headers):
        """Test compare project to benchmarks POST endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/benchmark/compare",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data or "variance_vs_average" in data
        print(f"✓ Project compared to benchmarks: variance = {data.get('variance_vs_average')}%")


class TestCostPredictionModule:
    """Cost Prediction Module API Tests"""
    
    def test_get_cost_predictions(self, headers):
        """Test get cost predictions endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-prediction",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Cost predictions retrieved: {len(data)} predictions")
    
    def test_create_cost_prediction(self, headers):
        """Test create cost prediction endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-prediction",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "predicted_cost_avg" in data or "predicted_cost_m2_avg" in data
        assert "confidence_interval" in data
        print(f"✓ Cost prediction created: avg = {data.get('predicted_cost_avg')}, confidence = {data.get('confidence_interval')}")
    
    def test_get_latest_cost_prediction(self, headers):
        """Test get latest cost prediction endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-prediction/latest",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "predicted_cost_avg" in data or "predicted_cost_m2_avg" in data
        print("✓ Latest cost prediction retrieved")


class TestMultiScenarioModule:
    """Multi-Scenario Module API Tests"""
    
    def test_get_multi_scenario_analyses(self, headers):
        """Test get multi-scenario analyses endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/multi-scenario",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Multi-scenario analyses retrieved: {len(data)} analyses")
    
    def test_create_multi_scenario_analysis(self, headers):
        """Test create multi-scenario analysis endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/multi-scenario",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert len(data.get("scenarios", [])) == 3  # economic, standard, premium
        print(f"✓ Multi-scenario analysis created: {len(data.get('scenarios', []))} scenarios")
        
        # Verify scenarios structure
        scenarios = data.get("scenarios", [])
        for scenario in scenarios:
            assert "type" in scenario
            assert "total_cost" in scenario
            assert "cost_per_m2" in scenario
            print(f"  - {scenario.get('type')}: {scenario.get('total_cost')} €, {scenario.get('cost_per_m2')} €/m²")


class TestDesignOptimizationModule:
    """Design Optimization Module API Tests"""
    
    def test_get_design_optimizations(self, headers):
        """Test get design optimizations endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/design-optimization",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Design optimizations retrieved: {len(data)} analyses")
    
    def test_create_design_optimization(self, headers):
        """Test create design optimization endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/design-optimization",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data or "total_potential_savings" in data
        print(f"✓ Design optimization created: potential savings = {data.get('total_potential_savings')}")


class TestQuantityTakeoff:
    """Quantity Takeoff (DPGF) API Tests - verify existing functionality"""
    
    def test_get_dpgfs(self, headers):
        """Test get DPGFs endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ DPGFs retrieved: {len(data)} DPGFs")
    
    def test_generate_dpgf(self, headers):
        """Test DPGF generation (quantity takeoff)"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf/generate",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "lots" in data
        assert "total_ht" in data
        print(f"✓ DPGF generated: {len(data.get('lots', []))} lots, total = {data.get('total_ht')} €")


class TestProjectEndpoints:
    """Project-level endpoint tests"""
    
    def test_get_project(self, headers):
        """Test get project endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "project_name" in data
        print(f"✓ Project retrieved: {data.get('project_name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
