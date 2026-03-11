"""
FSRS Integration API Tests

Integration tests for FSRS-enhanced API endpoints including
session progress, statistics, and admin configuration.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import json

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_fsrs.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestSessionProgressAPI:
    """Test FSRS-enhanced session progress endpoints"""
    
    def test_progress_with_integration_fields(self, client, auth_headers, sample_learning_set):
        """Test that progress response includes FSRS integration fields"""
        response = client.get(
            f"/sessions/progress?learning_set_id={sample_learning_set.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic fields are present
        assert "stage" in data
        assert "total_items" in data
        assert "mastered_count" in data
        
        # Verify FSRS integration fields are present
        assert "isolation_mastered_count" in data
        assert "integration_confirmed_count" in data
        assert "integration_review_count" in data
        assert "phase_description" in data
        assert "integration_efficiency" in data
        assert "average_stability_score" in data
        assert "high_stability_count" in data
        assert "low_stability_count" in data
        
    def test_progress_isolation_phase_description(self, client, auth_headers):
        """Test phase description for isolation phase"""
        # Create learning set in isolation phase
        learning_set_data = {
            "dataset_id": "test-dataset",
            "mode": "progressive",
            "isolation_phase": True,
            "current_batch_start": 1,
            "current_batch_end": 10
        }
        
        # Mock learning set
        with client.post("/sessions/start", json=learning_set_data, headers=auth_headers) as response:
            learning_set_id = response.json()["learning_set_id"]
        
        response = client.get(
            f"/sessions/progress?learning_set_id={learning_set_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Isolation Phase - Batch 1-10" in data["phase_description"]
        
    def test_progress_integration_phase_description(self, client, auth_headers):
        """Test phase description for integration phase"""
        learning_set_data = {
            "dataset_id": "test-dataset", 
            "mode": "progressive",
            "isolation_phase": False,
            "current_batch_end": 20
        }
        
        with client.post("/sessions/start", json=learning_set_data, headers=auth_headers) as response:
            learning_set_id = response.json()["learning_set_id"]
        
        response = client.get(
            f"/sessions/progress?learning_set_id={learning_set_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Integration Phase - Cards 1-20" in data["phase_description"]


class TestFSRSStatsAPI:
    """Test FSRS integration statistics endpoints"""
    
    def test_fsrs_stats_endpoint_exists(self, client, auth_headers, sample_learning_set):
        """Test that FSRS stats endpoint is accessible"""
        response = client.get(
            f"/sessions/fsrs-stats/{sample_learning_set.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
    def test_fsrs_stats_comprehensive_fields(self, client, auth_headers, sample_learning_set):
        """Test that FSRS stats response contains all expected fields"""
        response = client.get(
            f"/sessions/fsrs-stats/{sample_learning_set.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Basic identification fields
        assert "learning_set_id" in data
        assert "dataset_id" in data
        assert "user_id" in data
        
        # Phase information
        assert "current_phase" in data
        assert "phase_description" in data
        
        # Count fields
        assert "total_cards" in data
        assert "mastered_count" in data
        assert "isolation_mastered_count" in data
        assert "integration_confirmed_count" in data
        assert "integration_review_count" in data
        assert "learning_count" in data
        
        # Efficiency metrics
        assert "integration_efficiency" in data
        assert "first_attempt_success_rate" in data
        assert "average_integration_attempts" in data
        assert "reconsolidation_rate" in data
        
        # Stability statistics
        assert "stability_stats" in data
        stability_stats = data["stability_stats"]
        assert "average_stability" in stability_stats
        assert "median_stability" in stability_stats
        assert "high_stability_count" in stability_stats
        
        # Session timing
        assert "session_start_time" in data
        assert "last_activity_time" in data
        assert "total_session_time_minutes" in data
        
    def test_fsrs_stats_with_card_details(self, client, auth_headers, sample_learning_set):
        """Test FSRS stats with detailed card information"""
        response = client.get(
            f"/sessions/fsrs-stats/{sample_learning_set.id}?include_card_details=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "card_details" in data
        if data["card_details"]:  # If there are cards
            card_detail = data["card_details"][0]
            assert "element_id" in card_detail
            assert "status" in card_detail
            assert "integration_confirmed" in card_detail
            assert "integration_attempts" in card_detail
            assert "stability_score" in card_detail
            
    def test_fsrs_stats_unauthorized_access(self, client, sample_learning_set):
        """Test that FSRS stats requires authentication"""
        response = client.get(f"/sessions/fsrs-stats/{sample_learning_set.id}")
        
        assert response.status_code == 401
        
    def test_fsrs_stats_nonexistent_learning_set(self, client, auth_headers):
        """Test FSRS stats with non-existent learning set"""
        response = client.get(
            "/sessions/fsrs-stats/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestAdminFSRSConfigAPI:
    """Test admin FSRS configuration endpoints"""
    
    def test_get_integration_config(self, client, admin_headers):
        """Test retrieving FSRS integration configuration"""
        response = client.get(
            "/admin/config/integration",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all FSRS integration parameters are present
        fsrs_integration_params = [
            'integration_enhancement_enabled',
            'integration_confirmation_threshold',
            'integration_max_attempts',
            'stability_boost_factor',
            'stability_decay_factor',
            'stability_max_score',
            'integration_failure_penalty',
            'reconsolidation_threshold',
            'stability_maintenance_boost'
        ]
        
        for param in fsrs_integration_params:
            assert param in data
            
        # Verify all mastery window parameters are present  
        mastery_window_params = [
            'default_mastery_window',
            'isolation_min_mastery_window',
            'isolation_max_mastery_window',
            'isolation_field_multiplier',
            'single_field_mastery_window',
            'two_field_mastery_window',
            'integration_mastery_window',
            'required_mastery_window',
            'isolation_mastery_percentage',
            'initial_stability_score'
        ]
        
        for param in mastery_window_params:
            assert param in data
            
    def test_update_integration_config(self, client, admin_headers):
        """Test updating FSRS integration configuration"""
        update_data = {
            "integration_enhancement_enabled": True,
            "integration_confirmation_threshold": 0.85,
            "integration_max_attempts": 2,
            "stability_boost_factor": 1.3,
            "default_mastery_window": 4
        }
        
        response = client.put(
            "/admin/config/integration",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify updated values are returned
        assert data["integration_enhancement_enabled"] == True
        assert data["integration_confirmation_threshold"] == 0.85
        assert data["integration_max_attempts"] == 2
        assert data["stability_boost_factor"] == 1.3
        assert data["default_mastery_window"] == 4
        
    def test_integration_config_validation(self, client, admin_headers):
        """Test validation of FSRS integration configuration"""
        # Test invalid threshold (too high)
        invalid_data = {
            "integration_confirmation_threshold": 1.5  # Above max of 1.0
        }
        
        response = client.put(
            "/admin/config/integration",
            json=invalid_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test invalid attempts (too low)
        invalid_data = {
            "integration_max_attempts": 1  # Below min of 2
        }
        
        response = client.put(
            "/admin/config/integration", 
            json=invalid_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error
        
    def test_integration_config_non_admin_access(self, client, auth_headers):
        """Test that integration config requires admin access"""
        response = client.get(
            "/admin/config/integration",
            headers=auth_headers  # Regular user, not admin
        )
        
        assert response.status_code == 403  # Forbidden


class TestAdminPerformanceMetrics:
    """Test system-wide FSRS performance metrics"""
    
    def test_fsrs_performance_endpoint(self, client, admin_headers):
        """Test FSRS system performance metrics endpoint"""
        response = client.get(
            "/admin/fsrs-performance",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Basic system metrics
        assert "total_users" in data
        assert "active_integration_sessions" in data
        
        # Efficiency metrics
        assert "overall_integration_efficiency" in data
        assert "overall_first_attempt_success" in data
        assert "overall_reconsolidation_rate" in data
        
        # Configuration tracking
        assert "current_config_hash" in data
        assert "config_last_updated" in data
        
        # Performance categories
        assert "high_performers" in data
        assert "medium_performers" in data
        assert "low_performers" in data
        
        # System health
        assert "error_rate" in data
        assert "average_response_time_ms" in data
        
    def test_performance_metrics_non_admin_access(self, client, auth_headers):
        """Test that performance metrics requires admin access"""
        response = client.get(
            "/admin/fsrs-performance",
            headers=auth_headers
        )
        
        assert response.status_code == 403


# Test fixtures
@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)

@pytest.fixture 
def auth_headers():
    """Create authentication headers for regular user"""
    return {"Authorization": "Bearer test-user-token"}

@pytest.fixture
def admin_headers():
    """Create authentication headers for admin user"""
    return {"Authorization": "Bearer test-admin-token"}

@pytest.fixture
def sample_learning_set():
    """Create sample learning set for testing"""
    from app.sessions.models import UserLearningSet
    
    learning_set = UserLearningSet()
    learning_set.id = "test-learning-set"
    learning_set.user_id = "test-user"
    learning_set.dataset_id = "test-dataset"
    learning_set.isolation_phase = True
    learning_set.current_batch_start = 1
    learning_set.current_batch_end = 10
    learning_set.stage = 1
    learning_set.mode = "progressive"
    
    return learning_set


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
