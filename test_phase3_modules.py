"""
CostPilot Senior - Phase 3 Backend Tests
Testing the 3 new business modules:
1. Plan Reading (PDF/IFC analysis)
2. DPGF Auto Generator
3. Cost Optimization AI
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://feasibility-platform.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "demo@costpilot.fr"
TEST_PASSWORD = "demo123456"
TEST_PROJECT_ID = "429f51fe-124d-4253-855b-c785904a6e53"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

# ============================================================================
# Module 1: Plan Analysis (PDF/IFC) Tests
# ============================================================================

class TestPlanAnalysis:
    """Tests for plan reading/analysis endpoints"""
    
    analysis_id = None
    
    def test_create_plan_analysis_ifc(self, headers):
        """Test POST /api/projects/{project_id}/plan-analysis with IFC file"""
        payload = {
            "project_id": TEST_PROJECT_ID,
            "file_name": "test_building.ifc",
            "file_type": "ifc"
        }
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/plan-analysis",
            json=payload,
            headers=headers
        )
        assert response.status_code == 200, f"Plan analysis failed: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "id" in data
        assert "levels" in data
        assert "zones" in data
        assert "stats" in data
        assert "ifc_elements" in data  # IFC-specific
        
        # Verify levels detected
        assert len(data["levels"]) >= 2, "Should detect multiple levels"
        
        # Verify zones detected
        assert len(data["zones"]) >= 5, "Should detect multiple zones"
        
        # Verify stats calculated
        assert data["stats"]["sdp_total"] > 0, "SDP total should be > 0"
        assert data["stats"]["surface_utile"] > 0, "Surface utile should be > 0"
        assert "confidence_moyenne" in data["stats"]
        
        # Verify IFC elements extracted
        assert "walls" in data["ifc_elements"]
        assert "doors" in data["ifc_elements"]
        assert "windows" in data["ifc_elements"]
        
        TestPlanAnalysis.analysis_id = data["id"]
        print(f"✓ IFC Analysis: {len(data['zones'])} zones, {len(data['levels'])} levels, SDP={data['stats']['sdp_total']}m²")
    
    def test_create_plan_analysis_pdf(self, headers):
        """Test POST /api/projects/{project_id}/plan-analysis with PDF file"""
        payload = {
            "project_id": TEST_PROJECT_ID,
            "file_name": "plan_rdc.pdf",
            "file_type": "pdf"
        }
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/plan-analysis",
            json=payload,
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["zones"]) > 0, "PDF should detect zones"
        # PDF analysis has lower confidence
        assert data["stats"]["confidence_moyenne"] < 80, "PDF confidence should be lower than IFC"
        print(f"✓ PDF Analysis: {len(data['zones'])} zones detected")
    
    def test_get_plan_analyses_list(self, headers):
        """Test GET /api/projects/{project_id}/plan-analysis - list all"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/plan-analysis",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Should have at least one analysis"
        print(f"✓ Found {len(data)} plan analyses")
    
    def test_get_specific_plan_analysis(self, headers):
        """Test GET /api/projects/{project_id}/plan-analysis/{analysis_id}"""
        if not TestPlanAnalysis.analysis_id:
            pytest.skip("No analysis_id from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/plan-analysis/{TestPlanAnalysis.analysis_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == TestPlanAnalysis.analysis_id
        print(f"✓ Retrieved analysis {TestPlanAnalysis.analysis_id[:8]}...")
    
    def test_update_plan_zones(self, headers):
        """Test PUT /api/projects/{project_id}/plan-analysis/{analysis_id}/zones"""
        if not TestPlanAnalysis.analysis_id:
            pytest.skip("No analysis_id from previous test")
        
        # First get current zones
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/plan-analysis/{TestPlanAnalysis.analysis_id}",
            headers=headers
        )
        current_zones = response.json()["zones"]
        
        # Modify first zone surface
        if current_zones:
            current_zones[0]["surface"] = 999
            current_zones[0]["zone_type"] = "habitable"
        
        # Update zones
        response = requests.put(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/plan-analysis/{TestPlanAnalysis.analysis_id}/zones",
            json=current_zones,
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "stats" in data
        print("✓ Zones updated successfully")

# ============================================================================
# Module 2: DPGF Generator Tests
# ============================================================================

class TestDPGFGenerator:
    """Tests for DPGF automatic generation endpoints"""
    
    dpgf_id = None
    
    def test_generate_dpgf_aps_apd(self, headers):
        """Test POST /api/projects/{project_id}/dpgf/generate with APS/APD mode"""
        payload = {
            "project_id": TEST_PROJECT_ID,
            "mode": "aps_apd",
            "plan_analysis_id": None,
            "use_pricing_library": True,
            "custom_adjustments": {}
        }
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf/generate",
            json=payload,
            headers=headers
        )
        assert response.status_code == 200, f"DPGF generation failed: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "id" in data
        assert "lots" in data
        assert "items" in data
        assert "summary" in data
        
        # Verify lots (should have 20 macro-lots)
        assert len(data["lots"]) >= 15, "Should have multiple lots"
        
        # Verify items generated
        assert len(data["items"]) >= 20, "Should have multiple line items"
        
        # Verify summary
        assert data["summary"]["total_ht"] > 0, "Total HT should be > 0"
        assert data["summary"]["total_ttc"] > data["summary"]["total_ht"], "TTC > HT"
        assert data["summary"]["cost_per_m2_ht"] > 0
        assert "by_category" in data["summary"]
        
        TestDPGFGenerator.dpgf_id = data["id"]
        print(f"✓ DPGF APS/APD: {len(data['lots'])} lots, {len(data['items'])} items, Total={data['summary']['total_ht']:,.0f}€ HT")
    
    def test_generate_dpgf_feasibility(self, headers):
        """Test POST /api/projects/{project_id}/dpgf/generate with feasibility mode"""
        payload = {
            "project_id": TEST_PROJECT_ID,
            "mode": "feasibility",
            "plan_analysis_id": None,
            "use_pricing_library": True,
            "custom_adjustments": {}
        }
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf/generate",
            json=payload,
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        # Feasibility mode has less detail
        assert len(data["items"]) > 0
        print(f"✓ DPGF Feasibility: {len(data['items'])} items")
    
    def test_get_dpgf_list(self, headers):
        """Test GET /api/projects/{project_id}/dpgf - list all DPGFs"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Should have at least one DPGF"
        print(f"✓ Found {len(data)} DPGFs")
    
    def test_get_specific_dpgf(self, headers):
        """Test GET /api/projects/{project_id}/dpgf/{dpgf_id}"""
        if not TestDPGFGenerator.dpgf_id:
            pytest.skip("No dpgf_id from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf/{TestDPGFGenerator.dpgf_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == TestDPGFGenerator.dpgf_id
        print(f"✓ Retrieved DPGF {TestDPGFGenerator.dpgf_id[:8]}...")
    
    def test_dpgf_lots_have_correct_structure(self, headers):
        """Test that DPGF lots have all required fields"""
        if not TestDPGFGenerator.dpgf_id:
            pytest.skip("No dpgf_id from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf/{TestDPGFGenerator.dpgf_id}",
            headers=headers
        )
        data = response.json()
        
        for lot in data["lots"]:
            assert "code" in lot, "Lot should have code"
            assert "name" in lot, "Lot should have name"
            assert "category" in lot, "Lot should have category"
            assert "total_ht" in lot, "Lot should have total_ht"
            assert "percentage" in lot, "Lot should have percentage"
        
        # Check percentages sum to ~100%
        total_pct = sum(lot["percentage"] for lot in data["lots"])
        assert 95 < total_pct < 105, f"Percentages should sum to ~100%, got {total_pct}%"
        print(f"✓ All lots have correct structure, total percentage: {total_pct:.1f}%")
    
    def test_update_dpgf_items(self, headers):
        """Test PUT /api/projects/{project_id}/dpgf/{dpgf_id}/items"""
        if not TestDPGFGenerator.dpgf_id:
            pytest.skip("No dpgf_id from previous test")
        
        # Get current items
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf/{TestDPGFGenerator.dpgf_id}",
            headers=headers
        )
        current_items = response.json()["items"]
        
        # Modify first item
        if current_items:
            current_items[0]["unit_price"] = 999
            current_items[0]["total_price"] = current_items[0]["quantity"] * 999
        
        # Update items
        response = requests.put(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf/{TestDPGFGenerator.dpgf_id}/items",
            json=current_items,
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        print("✓ DPGF items updated successfully")

# ============================================================================
# Module 3: Cost Optimization AI Tests
# ============================================================================

class TestCostOptimization:
    """Tests for AI cost optimization endpoints"""
    
    analysis_id = None
    
    def test_analyze_cost_optimization(self, headers):
        """Test POST /api/projects/{project_id}/cost-optimization/analyze"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-optimization/analyze",
            headers=headers
        )
        assert response.status_code == 200, f"Cost optimization analysis failed: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "id" in data
        assert "health_score" in data
        assert "anomalies" in data
        assert "suggestions" in data
        assert "comparison_with_references" in data
        assert "summary" in data
        
        # Verify health score (0-100)
        assert 0 <= data["health_score"] <= 100, "Health score should be 0-100"
        
        # Verify suggestions generated
        assert len(data["suggestions"]) >= 3, "Should have multiple suggestions"
        
        # Verify suggestions have correct structure
        for suggestion in data["suggestions"]:
            assert "id" in suggestion
            assert "title" in suggestion
            assert "explanation" in suggestion
            assert "impacted_lot" in suggestion
            assert "savings_min" in suggestion
            assert "savings_max" in suggestion
            assert "confidence" in suggestion
            assert "risk_level" in suggestion
            assert "category" in suggestion
        
        # Verify comparison
        assert "current_cost_m2" in data["comparison_with_references"]
        assert "reference_cost_m2" in data["comparison_with_references"]
        
        # Verify summary
        assert data["summary"]["total_project_cost"] > 0 or data["summary"]["cost_per_m2"] >= 0
        assert "potential_savings_min" in data["summary"]
        assert "potential_savings_max" in data["summary"]
        
        TestCostOptimization.analysis_id = data["id"]
        print(f"✓ Cost Optimization: Health={data['health_score']:.0f}, {len(data['suggestions'])} suggestions, {len(data['anomalies'])} anomalies")
    
    def test_analyze_with_dpgf(self, headers):
        """Test POST /api/projects/{project_id}/cost-optimization/analyze with DPGF"""
        # First get a DPGF
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf",
            headers=headers
        )
        dpgf_list = response.json()
        
        if not dpgf_list:
            pytest.skip("No DPGF available for testing")
        
        dpgf_id = dpgf_list[0]["id"]
        
        # Analyze with DPGF
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-optimization/analyze?dpgf_id={dpgf_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "suggestions" in data
        print(f"✓ Cost Optimization with DPGF: {len(data['suggestions'])} suggestions")
    
    def test_get_cost_optimization_analyses(self, headers):
        """Test GET /api/projects/{project_id}/cost-optimization - list all"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-optimization",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Should have at least one analysis"
        print(f"✓ Found {len(data)} cost optimization analyses")
    
    def test_get_specific_analysis(self, headers):
        """Test GET /api/projects/{project_id}/cost-optimization/{analysis_id}"""
        if not TestCostOptimization.analysis_id:
            pytest.skip("No analysis_id from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-optimization/{TestCostOptimization.analysis_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == TestCostOptimization.analysis_id
        print(f"✓ Retrieved analysis {TestCostOptimization.analysis_id[:8]}...")
    
    def test_suggestion_categories(self, headers):
        """Test that suggestions have valid categories"""
        if not TestCostOptimization.analysis_id:
            pytest.skip("No analysis_id from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-optimization/{TestCostOptimization.analysis_id}",
            headers=headers
        )
        data = response.json()
        
        valid_categories = [
            "economie_sans_impact",
            "arbitrage_architectural",
            "arbitrage_technique",
            "arbitrage_exploitation"
        ]
        
        for suggestion in data["suggestions"]:
            assert suggestion["category"] in valid_categories, f"Invalid category: {suggestion['category']}"
        
        # Check summary has category breakdown
        assert "by_category" in data["summary"]
        for cat in valid_categories:
            assert cat in data["summary"]["by_category"]
        
        print(f"✓ All suggestion categories are valid")
    
    def test_apply_suggestion(self, headers):
        """Test POST /api/projects/{project_id}/cost-optimization/{analysis_id}/apply-suggestion"""
        if not TestCostOptimization.analysis_id:
            pytest.skip("No analysis_id from previous test")
        
        # Get the analysis to find a suggestion
        response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-optimization/{TestCostOptimization.analysis_id}",
            headers=headers
        )
        data = response.json()
        
        if not data.get("suggestions"):
            pytest.skip("No suggestions to apply")
        
        suggestion_id = data["suggestions"][0]["id"]
        
        # Apply the suggestion
        response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-optimization/{TestCostOptimization.analysis_id}/apply-suggestion?suggestion_id={suggestion_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "arbitration_id" in result
        print(f"✓ Suggestion applied, arbitration created: {result['arbitration_id'][:8]}...")

# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests across modules"""
    
    def test_plan_to_dpgf_flow(self, headers):
        """Test flow: Plan Analysis -> DPGF with plan data"""
        # 1. Create plan analysis
        plan_payload = {
            "project_id": TEST_PROJECT_ID,
            "file_name": "integration_test.ifc",
            "file_type": "ifc"
        }
        plan_response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/plan-analysis",
            json=plan_payload,
            headers=headers
        )
        assert plan_response.status_code == 200
        plan_id = plan_response.json()["id"]
        
        # 2. Generate DPGF using plan data
        dpgf_payload = {
            "project_id": TEST_PROJECT_ID,
            "mode": "aps_apd",
            "plan_analysis_id": plan_id,
            "use_pricing_library": True,
            "custom_adjustments": {}
        }
        dpgf_response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf/generate",
            json=dpgf_payload,
            headers=headers
        )
        assert dpgf_response.status_code == 200
        
        dpgf_data = dpgf_response.json()
        assert dpgf_data["summary"]["total_ht"] > 0
        print(f"✓ Plan→DPGF flow: Plan SDP to DPGF {dpgf_data['summary']['total_ht']:,.0f}€")
    
    def test_dpgf_to_optimization_flow(self, headers):
        """Test flow: DPGF -> Cost Optimization"""
        # 1. Get existing DPGF
        dpgf_response = requests.get(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/dpgf",
            headers=headers
        )
        dpgf_list = dpgf_response.json()
        
        if not dpgf_list:
            pytest.skip("No DPGF for integration test")
        
        dpgf_id = dpgf_list[0]["id"]
        
        # 2. Run optimization on DPGF
        opt_response = requests.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/cost-optimization/analyze?dpgf_id={dpgf_id}",
            headers=headers
        )
        assert opt_response.status_code == 200
        
        opt_data = opt_response.json()
        assert len(opt_data["suggestions"]) > 0
        
        # Verify savings relate to DPGF total
        dpgf_total = dpgf_list[0]["summary"]["total_ht"]
        savings_max = opt_data["summary"]["potential_savings_max"]
        
        # Savings should be less than total cost
        assert savings_max < dpgf_total, "Potential savings should be less than total cost"
        print(f"✓ DPGF→Optimization flow: {opt_data['summary']['potential_savings_pct_max']:.1f}% potential savings")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
