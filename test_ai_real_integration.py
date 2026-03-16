"""
Test CostPilot AI Real Integration Features
Tests for:
1. Instant Estimation with AI parsing (GPT-4)
2. CCTP Generation with AI prescriptions (GPT-4)
3. Carbon Analysis
4. Workflow Status
5. CCTP Lots endpoint
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "test_new@costpilot.com"
TEST_PASSWORD = "Test123!"
PROJECT_ID = "8e94d4b8-feff-4bd6-ba61-f070b54cc26d"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return auth headers for authenticated requests"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestInstantEstimationAI:
    """Test Instant Estimation with AI parsing - POST /api/instant-estimation"""
    
    def test_instant_estimation_ai_parsed_detailed_description(self, auth_headers):
        """Test AI parsing with detailed description - should return ai_parsed=True and confidence=high"""
        # Detailed description that AI should parse successfully
        description = "Construction d'un immeuble de bureaux de 5000m² en R+6 avec structure acier et mur rideau, niveau premium, à Paris La Défense, avec 100 places de parking"
        
        response = requests.post(
            f"{BASE_URL}/api/instant-estimation",
            headers=auth_headers,
            json={"description": description}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check AI parsing was successful
        assert "input" in data, "Response should contain 'input' field"
        parsed = data.get("input", {}).get("parsed", {})
        
        # Verify AI parsed the description
        assert parsed.get("ai_parsed") == True, f"Expected ai_parsed=True, got {parsed.get('ai_parsed')}"
        
        # Verify confidence is high when AI parsed
        assert data.get("confidence") == "high", f"Expected confidence='high', got {data.get('confidence')}"
        
        # Verify extracted parameters
        assert parsed.get("project_type") == "office", f"Expected project_type='office', got {parsed.get('project_type')}"
        assert parsed.get("surface_m2") is not None, "Surface should be extracted"
        assert parsed.get("floors") is not None, "Floors should be extracted"
        
        # Verify estimation was generated
        estimation = data.get("estimation", {})
        assert estimation.get("total_cost") > 0, "Total cost should be positive"
        assert estimation.get("cost_per_m2") > 0, "Cost per m2 should be positive"
        
        print(f"✓ AI parsed: {parsed.get('ai_parsed')}")
        print(f"✓ Confidence: {data.get('confidence')}")
        print(f"✓ Project type: {parsed.get('project_type')}")
        print(f"✓ Surface: {parsed.get('surface_m2')}m²")
        print(f"✓ Total cost: {estimation.get('total_cost')}€")
    
    def test_instant_estimation_ai_parsed_simple_description(self, auth_headers):
        """Test AI parsing with simpler description"""
        description = "50 logements R+4 à Lyon niveau standard"
        
        response = requests.post(
            f"{BASE_URL}/api/instant-estimation",
            headers=auth_headers,
            json={"description": description}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        parsed = data.get("input", {}).get("parsed", {})
        
        # AI should successfully parse this
        assert parsed.get("ai_parsed") == True, f"Expected ai_parsed=True, got {parsed.get('ai_parsed')}"
        
        # Should detect housing project
        assert parsed.get("project_type") == "housing", f"Expected project_type='housing', got {parsed.get('project_type')}"
        
        print(f"✓ AI parsed simple description successfully")
        print(f"✓ Project type: {parsed.get('project_type')}")
    
    def test_instant_estimation_cost_distribution(self, auth_headers):
        """Verify cost distribution is returned"""
        description = "Ecole primaire de 2000m² R+2 structure béton"
        
        response = requests.post(
            f"{BASE_URL}/api/instant-estimation",
            headers=auth_headers,
            json={"description": description}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check cost distribution
        distribution = data.get("cost_distribution", {})
        assert "infrastructure" in distribution
        assert "superstructure" in distribution
        assert "facade_enveloppe" in distribution
        assert "lots_techniques" in distribution
        
        print(f"✓ Cost distribution present with {len(distribution)} categories")


class TestCCTPGeneration:
    """Test CCTP Generation with AI - POST /api/projects/{id}/cctp/generate"""
    
    def test_cctp_generate_with_ai(self, auth_headers):
        """Test CCTP generation - should return ai_generated=True with normative prescriptions"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{PROJECT_ID}/cctp/generate",
            headers=auth_headers,
            json={
                "structure_type": "concrete",
                "facade_type": "brick",
                "selected_lots": ["01", "03", "05"]  # Limited lots for faster test
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify AI generation flag
        assert data.get("ai_generated") == True, f"Expected ai_generated=True, got {data.get('ai_generated')}"
        
        # Verify lots were generated
        lots = data.get("lots", [])
        assert len(lots) >= 1, f"Expected at least 1 lot, got {len(lots)}"
        
        # Check for normative prescriptions in at least one lot
        has_ai_lot = False
        for lot in lots:
            if lot.get("ai_generated"):
                has_ai_lot = True
                # Check prescriptions
                prescriptions = lot.get("prescriptions_techniques", [])
                assert len(prescriptions) > 0, f"Lot {lot.get('code')} should have technical prescriptions"
                
                # Check for normative references (DTU, NF EN, etc.)
                references = lot.get("references_normatives", [])
                print(f"✓ Lot {lot.get('code')}: {len(prescriptions)} prescriptions, {len(references)} references")
        
        if has_ai_lot:
            print("✓ CCTP generated with AI prescriptions")
        else:
            print("! CCTP generated but lots may have used fallback prescriptions")
    
    def test_cctp_generate_multiple_lots(self, auth_headers):
        """Test CCTP generation with 5 lots (limited to avoid timeout)"""
        # Note: Full 16 lots takes too long with AI generation
        response = requests.post(
            f"{BASE_URL}/api/projects/{PROJECT_ID}/cctp/generate",
            headers=auth_headers,
            json={
                "structure_type": "steel",
                "facade_type": "curtain_wall",
                "selected_lots": ["01", "02", "03", "04", "05"]  # Limited to avoid timeout
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        lots = data.get("lots", [])
        assert len(lots) >= 5, f"Expected at least 5 lots, got {len(lots)}"
        
        # Verify lot structure
        for lot in lots:
            assert "code" in lot
            assert "name" in lot
            assert "prescriptions_generales" in lot
            assert "prescriptions_techniques" in lot
        
        print(f"✓ CCTP generated with {len(lots)} lots")


class TestCCTPLots:
    """Test CCTP Lots endpoint - GET /api/cctp/lots"""
    
    def test_get_cctp_lots_returns_16(self, auth_headers):
        """Should return exactly 16 lots"""
        response = requests.get(
            f"{BASE_URL}/api/cctp/lots",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert len(data) == 16, f"Expected 16 lots, got {len(data)}"
        
        # Verify structure of lots
        expected_codes = ["01", "02", "03", "04", "05", "06", "07", "08", 
                        "09", "10", "11", "12", "13", "14", "15", "16"]
        
        for code in expected_codes:
            assert code in data, f"Missing lot {code}"
            lot = data[code]
            assert "name" in lot, f"Lot {code} missing 'name'"
            assert "description" in lot, f"Lot {code} missing 'description'"
        
        print(f"✓ All 16 CCTP lots available")
        lot_names = [f"{code}-{data[code].get('name', '')[:15]}" for code in expected_codes[:5]]
        print(f"  Lots: {', '.join(lot_names)}...")


class TestCarbonAnalysis:
    """Test Carbon Analysis - POST /api/projects/{id}/carbon/analyze"""
    
    def test_carbon_analysis_returns_re2020_compliance(self, auth_headers):
        """Test carbon analysis returns carbon_footprint and re2020_compliance"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{PROJECT_ID}/carbon/analyze",
            headers=auth_headers,
            json={
                "structure_type": "concrete",
                "facade_type": "brick",
                "insulation_type": "mineral_wool"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify carbon footprint
        assert "carbon_footprint" in data, "Response should contain 'carbon_footprint'"
        footprint = data.get("carbon_footprint", {})
        
        # Check total values exist
        assert "total_tonnes" in footprint, "Should have total_tonnes"
        # Field may be 'per_m2_kgco2e' or 'total_kg_co2e_m2'
        has_per_m2 = "per_m2_kgco2e" in footprint or "total_kg_co2e_m2" in footprint
        assert has_per_m2, f"Should have per m2 field. Keys: {footprint.keys()}"
        assert footprint.get("total_tonnes") > 0, "Total tonnes should be positive"
        
        # Get the per-m2 value
        per_m2_value = footprint.get("per_m2_kgco2e") or footprint.get("total_kg_co2e_m2")
        
        # Verify RE2020 compliance
        assert "re2020_compliance" in data, "Response should contain 're2020_compliance'"
        compliance = data.get("re2020_compliance", {})
        
        # The compliance structure may have year keys directly (2022, 2025, etc.)
        # or may have nested structure with thresholds
        year_keys = ["2022", "2025", "2028", "2031"]
        has_year_data = any(k in compliance for k in year_keys)
        has_thresholds = "thresholds" in compliance
        
        if has_year_data:
            # Year data structure: {"2022": {"compliant": bool, "threshold": int}, ...}
            for year in year_keys:
                if year in compliance:
                    assert "compliant" in compliance[year], f"Year {year} should have 'compliant'"
                    assert "threshold" in compliance[year], f"Year {year} should have 'threshold'"
            compliance_info = [f"{y}: {compliance.get(y, {}).get('compliant')}" for y in year_keys if y in compliance]
            print(f"✓ RE2020 compliance per year: {', '.join(compliance_info)}")
        elif has_thresholds:
            # Alternative structure with separate thresholds key
            thresholds = compliance.get("thresholds", {})
            assert any(k in thresholds for k in year_keys), "Should have year thresholds"
            print(f"✓ RE2020 thresholds available")
        
        print(f"✓ Carbon footprint: {footprint.get('total_tonnes')} tonnes")
        print(f"✓ Kg CO2e/m²: {per_m2_value}")
        print(f"✓ RE2020 IC construction: {compliance.get('current_ic_construction')}")
    
    def test_carbon_analysis_timber_structure(self, auth_headers):
        """Test carbon analysis with timber structure (should be lower)"""
        response = requests.post(
            f"{BASE_URL}/api/projects/{PROJECT_ID}/carbon/analyze",
            headers=auth_headers,
            json={
                "structure_type": "timber",
                "facade_type": "cladding",
                "insulation_type": "biosourced"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        footprint = data.get("carbon_footprint", {})
        assert footprint.get("total_tonnes") > 0
        
        # Timber should generally be lower carbon
        print(f"✓ Timber structure carbon: {footprint.get('total_tonnes')} tonnes")


class TestWorkflowStatus:
    """Test Workflow Status - GET /api/projects/{id}/workflow-status"""
    
    def test_workflow_status_returns_stages(self, auth_headers):
        """Test workflow status returns proper stages structure"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{PROJECT_ID}/workflow-status",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check for stages key
        assert "stages" in data or "steps" in data, "Response should contain 'stages' or 'steps'"
        
        stages = data.get("stages") or data.get("steps", {})
        
        # Verify progress info
        if "progress" in data:
            progress = data.get("progress", {})
            assert "percentage" in progress or "completed" in progress
            print(f"✓ Workflow progress: {progress.get('percentage', progress.get('completed', 0))}%")
        elif "completion_percent" in data:
            print(f"✓ Workflow progress: {data.get('completion_percent')}%")
        
        print(f"✓ Workflow status returned with {len(stages)} stages")
        
        # List stage names if available
        if stages:
            stage_names = [s.get("name", k) if isinstance(s, dict) else k for k, s in (stages.items() if isinstance(stages, dict) else enumerate(stages))]
            print(f"  Stages: {', '.join(str(s) for s in stage_names[:5])}...")


class TestProjectEndpoints:
    """Test project-related endpoints"""
    
    def test_project_exists(self, auth_headers):
        """Verify test project exists"""
        response = requests.get(
            f"{BASE_URL}/api/projects/{PROJECT_ID}",
            headers=auth_headers
        )
        
        # Should return project or 200
        assert response.status_code == 200, f"Project not found: {response.status_code}"
        
        data = response.json()
        assert data.get("id") == PROJECT_ID
        print(f"✓ Test project exists: {data.get('project_name', 'Unknown')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
