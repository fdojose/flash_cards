"""
FSRS Integration Unit Tests

Comprehensive test suite for FSRS integration mastery calculation logic.
Tests all scenarios including isolation phase, integration confirmation, 
reconsolidation, and stability scoring.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

# Import the functions we're testing
from app.sessions.routes import (
    get_integration_config, 
    calculate_integration_mastery,
    get_dynamic_mastery_window
)
from app.sessions.models import UserElementReview, UserLearningSet, UserFieldAttempt
from app.admin.models import SystemConfig


class TestGetIntegrationConfig:
    """Test admin configuration loading for FSRS parameters"""
    
    def test_get_integration_config_with_defaults(self):
        """Test loading config with default values when no admin config exists"""
        # Mock database session
        db_mock = Mock(spec=Session)
        db_mock.query.return_value.filter.return_value.all.return_value = []
        
        config = get_integration_config(db_mock)
        
        # Verify all default values are present
        assert config['integration_enhancement_enabled'] == False
        assert config['integration_confirmation_threshold'] == 1.0
        assert config['integration_max_attempts'] == 3
        assert config['stability_boost_factor'] == 1.2
        assert config['stability_decay_factor'] == 0.8
        assert config['stability_max_score'] == 3.0
        assert config['default_mastery_window'] == 3
        assert config['isolation_mastery_percentage'] == 0.8
        
    def test_get_integration_config_with_admin_overrides(self):
        """Test loading config with admin-configured values"""
        # Mock admin configurations
        mock_configs = [
            Mock(key='integration_enhancement_enabled', value='true'),
            Mock(key='integration_confirmation_threshold', value='0.85'),
            Mock(key='integration_max_attempts', value='2'),
            Mock(key='stability_boost_factor', value='1.3'),
        ]
        
        db_mock = Mock(spec=Session)
        db_mock.query.return_value.filter.return_value.all.return_value = mock_configs
        
        config = get_integration_config(db_mock)
        
        # Verify admin values override defaults
        assert config['integration_enhancement_enabled'] == True
        assert config['integration_confirmation_threshold'] == 0.85
        assert config['integration_max_attempts'] == 2
        assert config['stability_boost_factor'] == 1.3
        # Defaults still present for non-overridden values
        assert config['stability_decay_factor'] == 0.8


class TestDynamicMasteryWindow:
    """Test dynamic mastery window calculation with phase awareness"""
    
    def test_isolation_phase_single_field(self):
        """Test isolation phase mastery window for single-field cards"""
        db_mock = Mock()
        learning_set = Mock()
        learning_set.isolation_phase = True
        
        config = {
            'isolation_min_mastery_window': 2,
            'single_field_mastery_window': 2
        }
        
        result = get_dynamic_mastery_window(db_mock, "dataset_id", learning_set, config, field_count_override=1)
        assert result == 2
        
    def test_isolation_phase_two_field(self):
        """Test isolation phase mastery window for two-field cards"""
        db_mock = Mock()
        learning_set = Mock()
        learning_set.isolation_phase = True
        
        config = {
            'two_field_mastery_window': 3
        }
        
        result = get_dynamic_mastery_window(db_mock, "dataset_id", learning_set, config, field_count_override=2)
        assert result == 3
        
    def test_isolation_phase_multi_field_with_cap(self):
        """Test isolation phase with field multiplier and max cap"""
        db_mock = Mock()
        learning_set = Mock()
        learning_set.isolation_phase = True
        
        config = {
            'isolation_max_mastery_window': 8,
            'isolation_field_multiplier': 1.5
        }
        
        # 6 fields * 1.5 = 9, but capped at 8
        result = get_dynamic_mastery_window(db_mock, "dataset_id", learning_set, config, field_count_override=6)
        assert result == 8
        
    def test_integration_phase_window(self):
        """Test integration phase uses integration-specific window"""
        db_mock = Mock()
        learning_set = Mock()
        learning_set.isolation_phase = False
        
        config = {
            'integration_mastery_window': 1
        }
        
        result = get_dynamic_mastery_window(db_mock, "dataset_id", learning_set, config, field_count_override=5)
        assert result == 1


class TestCalculateIntegrationMastery:
    """Test comprehensive FSRS integration mastery calculation"""
    
    def setUp(self):
        """Set up common test data"""
        self.db_mock = Mock(spec=Session)
        self.config = {
            'integration_enhancement_enabled': True,
            'integration_confirmation_threshold': 0.8,
            'integration_max_attempts': 3,
            'stability_boost_factor': 1.2,
            'stability_decay_factor': 0.8,
            'stability_max_score': 3.0,
            'integration_failure_penalty': 0.85,
            'reconsolidation_threshold': 2,
            'stability_maintenance_boost': 1.05,
            'integration_mastery_window': 1,
            'required_mastery_window': 3,
            'isolation_mastery_percentage': 0.75,
            'initial_stability_score': 1.0
        }
        
    def test_isolation_phase_mastery_success(self):
        """Test successful mastery in isolation phase"""
        self.setUp()
        
        # Create review in learning status
        review = Mock()
        review.status = "learning"
        review.stability_score = None
        
        # Create learning set in isolation phase
        learning_set = Mock()
        learning_set.isolation_phase = True
        
        # Create recent attempts with 75% accuracy (meets threshold)
        recent_attempts = [
            Mock(is_correct=True),   # Correct
            Mock(is_correct=True),   # Correct  
            Mock(is_correct=True),   # Correct
            Mock(is_correct=False)   # Incorrect - 75% accuracy
        ]
        
        result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
        
        # Should achieve mastery
        assert result == True
        assert review.status == "mastered"
        assert review.stability_score == 1.0  # Initial stability score
        
    def test_isolation_phase_mastery_failure(self):
        """Test failed mastery in isolation phase"""
        self.setUp()
        
        review = Mock()
        review.status = "learning"
        
        learning_set = Mock()
        learning_set.isolation_phase = True
        
        # Create recent attempts with 50% accuracy (below threshold)
        recent_attempts = [
            Mock(is_correct=True),   # Correct
            Mock(is_correct=False),  # Incorrect
            Mock(is_correct=True),   # Correct
            Mock(is_correct=False)   # Incorrect - 50% accuracy
        ]
        
        result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
        
        # Should not achieve mastery
        assert result == False
        assert review.status == "learning"  # Status unchanged
        
    def test_integration_confirmation_success_single_attempt(self):
        """Test successful integration confirmation on first attempt"""
        self.setUp()
        
        review = Mock()
        review.status = "mastered"
        review.integration_confirmed = False
        review.integration_attempts = 0
        review.stability_score = 1.0
        
        learning_set = Mock()
        learning_set.isolation_phase = False
        
        # Single correct attempt for integration confirmation
        recent_attempts = [Mock(is_correct=True)]
        
        result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
        
        # Should confirm integration
        assert result == True
        assert review.integration_confirmed == True
        assert review.status == "mastered"
        assert review.stability_score == 1.2  # Boosted by stability_boost_factor
        
    def test_integration_confirmation_failure_first_attempt(self):
        """Test failed integration confirmation on first attempt"""
        self.setUp()
        
        review = Mock()
        review.status = "mastered"
        review.integration_confirmed = False
        review.integration_attempts = 0
        review.stability_score = 1.0
        
        learning_set = Mock()
        learning_set.isolation_phase = False
        
        # Single incorrect attempt
        recent_attempts = [Mock(is_correct=False)]
        
        result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
        
        # Should fail integration confirmation
        assert result == False
        assert review.integration_confirmed == False
        assert review.status == "integration_review"
        assert review.integration_attempts == 1
        assert review.stability_score == 0.8  # Decayed by stability_decay_factor
        
    def test_integration_review_success_after_failure(self):
        """Test successful integration re-confirmation after failure"""
        self.setUp()
        
        review = Mock()
        review.status = "integration_review"
        review.integration_confirmed = False
        review.integration_attempts = 1
        review.stability_score = 0.8
        
        learning_set = Mock()
        learning_set.isolation_phase = False
        
        # Correct attempt for re-confirmation
        recent_attempts = [Mock(is_correct=True)]
        
        result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
        
        # Should achieve integration confirmation
        assert result == True
        assert review.integration_confirmed == True
        assert review.status == "mastered"
        assert review.stability_score == 0.96  # 0.8 * 1.2 (boost factor)
        
    def test_integration_review_max_attempts_reached(self):
        """Test reconsolidation after reaching max integration attempts"""
        self.setUp()
        
        review = Mock()
        review.status = "integration_review"
        review.integration_confirmed = False
        review.integration_attempts = 2  # Already at 2 attempts
        review.stability_score = 0.64
        
        learning_set = Mock()
        learning_set.isolation_phase = False
        
        # Another failed attempt (would be 3rd attempt)
        recent_attempts = [Mock(is_correct=False)]
        
        result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
        
        # Should trigger reconsolidation (return to learning)
        assert result == False
        assert review.status == "learning"
        assert review.integration_confirmed == False
        assert review.stability_score == 0.5  # Reset for re-isolation
        
    def test_confirmed_card_maintenance_success(self):
        """Test confirmed card maintenance with success"""
        self.setUp()
        
        review = Mock()
        review.status = "mastered"
        review.integration_confirmed = True
        review.stability_score = 2.0
        
        learning_set = Mock()
        learning_set.isolation_phase = False
        
        # Correct maintenance attempt
        recent_attempts = [Mock(is_correct=True)]
        
        result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
        
        # Should maintain mastery with stability boost
        assert result == True
        assert review.status == "mastered"
        assert review.stability_score == 2.1  # 2.0 * 1.05 (maintenance boost)
        
    def test_confirmed_card_maintenance_failure(self):
        """Test confirmed card maintenance with failure"""
        self.setUp()
        
        review = Mock()
        review.status = "mastered" 
        review.integration_confirmed = True
        review.stability_score = 2.0
        
        learning_set = Mock()
        learning_set.isolation_phase = False
        
        # Incorrect maintenance attempt
        recent_attempts = [Mock(is_correct=False)]
        
        result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
        
        # Should remain mastered but with stability penalty
        assert result == True  # Still mastered
        assert review.status == "mastered"
        assert review.stability_score == 1.7  # 2.0 * 0.85 (failure penalty)
        
    def test_stability_score_max_cap(self):
        """Test that stability score respects maximum cap"""
        self.setUp()
        
        review = Mock()
        review.status = "mastered"
        review.integration_confirmed = False
        review.stability_score = 2.8  # Close to max
        
        learning_set = Mock()
        learning_set.isolation_phase = False
        
        recent_attempts = [Mock(is_correct=True)]
        
        result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
        
        # Should be capped at stability_max_score (3.0)
        assert review.stability_score == 3.0  # Capped at max
        
    def test_enhancement_disabled_fallback(self):
        """Test fallback to original logic when enhancement is disabled"""
        self.setUp()
        
        # Disable FSRS enhancement
        self.config['integration_enhancement_enabled'] = False
        
        review = Mock()
        review.status = "mastered"
        review.integration_confirmed = False
        
        learning_set = Mock()
        learning_set.isolation_phase = False
        
        recent_attempts = [Mock(is_correct=False)]
        
        # Mock the isolation mastery calculation
        with pytest.mock.patch('app.sessions.routes.calculate_isolation_mastery') as mock_isolation:
            mock_isolation.return_value = True
            
            result = calculate_integration_mastery(self.db_mock, review, recent_attempts, learning_set, self.config)
            
            # Should call isolation logic instead of FSRS logic
            mock_isolation.assert_called_once()
            assert result == True


# Test fixtures for integration testing
@pytest.fixture
def sample_review():
    """Create a sample UserElementReview for testing"""
    review = UserElementReview()
    review.user_id = "user123"
    review.element_id = "element456"
    review.status = "learning"
    review.stability_score = 1.0
    review.integration_confirmed = False
    review.integration_attempts = 0
    review.accuracy_percentage = None
    review.review_count = 0
    review.is_difficult = False
    return review

@pytest.fixture
def sample_learning_set():
    """Create a sample UserLearningSet for testing"""
    learning_set = UserLearningSet()
    learning_set.id = "set789"
    learning_set.user_id = "user123"
    learning_set.dataset_id = "dataset101"
    learning_set.isolation_phase = True
    learning_set.current_batch_start = 1
    learning_set.current_batch_end = 10
    learning_set.stage = 1
    learning_set.mode = "progressive"
    return learning_set

@pytest.fixture
def sample_config():
    """Create a sample FSRS configuration for testing"""
    return {
        'integration_enhancement_enabled': True,
        'integration_confirmation_threshold': 0.8,
        'integration_max_attempts': 3,
        'stability_boost_factor': 1.2,
        'stability_decay_factor': 0.8,
        'stability_max_score': 3.0,
        'integration_failure_penalty': 0.85,
        'reconsolidation_threshold': 2,
        'stability_maintenance_boost': 1.05,
        'default_mastery_window': 3,
        'isolation_min_mastery_window': 2,
        'isolation_max_mastery_window': 8,
        'isolation_field_multiplier': 1.5,
        'single_field_mastery_window': 2,
        'two_field_mastery_window': 3,
        'integration_mastery_window': 1,
        'required_mastery_window': 3,
        'isolation_mastery_percentage': 0.75,
        'initial_stability_score': 1.0
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
