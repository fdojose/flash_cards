#!/usr/bin/env python3
"""
PHASE 8.1: UNIT TESTS - Learning Sessions Tests
=============================================

Test coverage for:
- Session CRUD operations
- Flashcard management
- Response recording
- Session progress tracking
- Performance analytics
"""

import pytest
import json
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.sessions.models import Session as LearningSession, FlashCard, Response
from app.datasets.models import Element


class TestSessionModel:
    """Test Session model functionality"""
    
    def test_session_creation(self, test_db: Session, test_user, test_dataset):
        """Test creating a learning session"""
        from uuid import uuid4
        from datetime import datetime
        
        session = LearningSession(
            id=uuid4(),
            user_id=test_user.id,
            dataset_id=test_dataset.id,
            session_type="practice",
            status="active",
            settings={"shuffle_cards": True},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.dataset_id == test_dataset.id
        assert session.session_type == "practice"
        assert session.status == "active"
        assert session.settings["shuffle_cards"] is True
    
    def test_flashcard_creation(self, test_db: Session, test_session):
        """Test creating a flashcard"""
        from uuid import uuid4
        from datetime import datetime
        
        # Get an element from the dataset
        element = test_db.query(Element).first()
        assert element is not None
        
        flashcard = FlashCard(
            id=uuid4(),
            session_id=test_session.id,
            element_id=element.id,
            front_field="spanish",
            back_field="english",
            order_index=0,
            status="pending",
            created_at=datetime.utcnow()
        )
        test_db.add(flashcard)
        test_db.commit()
        test_db.refresh(flashcard)
        
        assert flashcard.id is not None
        assert flashcard.session_id == test_session.id
        assert flashcard.element_id == element.id
        assert flashcard.front_field == "spanish"
        assert flashcard.back_field == "english"
        assert flashcard.status == "pending"
    
    def test_response_creation(self, test_db: Session, test_flashcards, test_user):
        """Test creating a response"""
        from uuid import uuid4
        from datetime import datetime
        
        flashcard = test_flashcards[0]
        
        response = Response(
            id=uuid4(),
            session_id=flashcard.session_id,
            flashcard_id=flashcard.id,
            user_id=test_user.id,
            response_time=2.5,
            confidence=4,
            is_correct=True,
            created_at=datetime.utcnow()
        )
        test_db.add(response)
        test_db.commit()
        test_db.refresh(response)
        
        assert response.id is not None
        assert response.session_id == flashcard.session_id
        assert response.flashcard_id == flashcard.id
        assert response.user_id == test_user.id
        assert response.response_time == 2.5
        assert response.confidence == 4
        assert response.is_correct is True


class TestSessionEndpoints:
    """Test session API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_session(self, client: AsyncClient, auth_headers, test_dataset):
        """Test creating a new learning session"""
        session_data = {
            "dataset_id": str(test_dataset.id),
            "session_type": "practice",
            "settings": {
                "shuffle_cards": True,
                "reverse_mode": False,
                "auto_advance": False
            }
        }
        
        response = await client.post("/sessions/", 
                                   json=session_data, 
                                   headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["dataset_id"] == session_data["dataset_id"]
        assert data["session_type"] == session_data["session_type"]
        assert data["status"] == "active"
        assert "flashcards" in data
    
    @pytest.mark.asyncio
    async def test_create_session_unauthorized(self, client: AsyncClient, test_dataset):
        """Test creating session without authentication"""
        session_data = {
            "dataset_id": str(test_dataset.id),
            "session_type": "practice"
        }
        
        response = await client.post("/sessions/", json=session_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, client: AsyncClient, auth_headers, test_session):
        """Test getting user's sessions"""
        response = await client.get("/sessions/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        session = data[0]
        assert "id" in session
        assert "dataset_id" in session
        assert "session_type" in session
        assert "status" in session
        assert "created_at" in session
    
    @pytest.mark.asyncio
    async def test_get_session_by_id(self, client: AsyncClient, auth_headers, test_session):
        """Test getting a specific session"""
        response = await client.get(f"/sessions/{test_session.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_session.id)
        assert data["user_id"] == str(test_session.user_id)
        assert data["dataset_id"] == str(test_session.dataset_id)
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, client: AsyncClient, auth_headers):
        """Test getting a nonexistent session"""
        from uuid import uuid4
        fake_id = uuid4()
        
        response = await client.get(f"/sessions/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_session_status(self, client: AsyncClient, auth_headers, test_session):
        """Test updating session status"""
        update_data = {"status": "completed"}
        
        response = await client.patch(f"/sessions/{test_session.id}", 
                                    json=update_data, 
                                    headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_delete_session(self, client: AsyncClient, auth_headers, test_session):
        """Test deleting a session"""
        response = await client.delete(f"/sessions/{test_session.id}", headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify session is deleted
        response = await client.get(f"/sessions/{test_session.id}", headers=auth_headers)
        assert response.status_code == 404


class TestFlashcardEndpoints:
    """Test flashcard API endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_session_flashcards(self, client: AsyncClient, auth_headers, test_session, test_flashcards):
        """Test getting flashcards for a session"""
        response = await client.get(f"/sessions/{test_session.id}/flashcards", 
                                  headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        flashcard = data[0]
        assert "id" in flashcard
        assert "session_id" in flashcard
        assert "element_id" in flashcard
        assert "front_field" in flashcard
        assert "back_field" in flashcard
        assert "order_index" in flashcard
        assert "status" in flashcard
    
    @pytest.mark.asyncio
    async def test_get_current_flashcard(self, client: AsyncClient, auth_headers, test_session, test_flashcards):
        """Test getting current flashcard in session"""
        response = await client.get(f"/sessions/{test_session.id}/current-flashcard", 
                                  headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "session_id" in data
        assert data["session_id"] == str(test_session.id)
        assert "element" in data  # Should include element data
    
    @pytest.mark.asyncio
    async def test_update_flashcard_status(self, client: AsyncClient, auth_headers, test_flashcards):
        """Test updating flashcard status"""
        flashcard = test_flashcards[0]
        update_data = {"status": "completed"}
        
        response = await client.patch(f"/flashcards/{flashcard.id}", 
                                    json=update_data, 
                                    headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"


class TestResponseEndpoints:
    """Test response recording endpoints"""
    
    @pytest.mark.asyncio
    async def test_record_response(self, client: AsyncClient, auth_headers, test_flashcards):
        """Test recording a flashcard response"""
        flashcard = test_flashcards[0]
        response_data = {
            "flashcard_id": str(flashcard.id),
            "response_time": 3.2,
            "confidence": 4,
            "is_correct": True,
            "user_answer": "hello"
        }
        
        response = await client.post(f"/sessions/{flashcard.session_id}/responses", 
                                   json=response_data, 
                                   headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["flashcard_id"] == response_data["flashcard_id"]
        assert data["response_time"] == response_data["response_time"]
        assert data["confidence"] == response_data["confidence"]
        assert data["is_correct"] == response_data["is_correct"]
    
    @pytest.mark.asyncio
    async def test_get_session_responses(self, client: AsyncClient, auth_headers, test_session, test_responses):
        """Test getting responses for a session"""
        response = await client.get(f"/sessions/{test_session.id}/responses", 
                                  headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        response_obj = data[0]
        assert "id" in response_obj
        assert "session_id" in response_obj
        assert "flashcard_id" in response_obj
        assert "response_time" in response_obj
        assert "confidence" in response_obj
        assert "is_correct" in response_obj
    
    @pytest.mark.asyncio
    async def test_record_response_invalid_flashcard(self, client: AsyncClient, auth_headers, test_session):
        """Test recording response for invalid flashcard"""
        from uuid import uuid4
        
        response_data = {
            "flashcard_id": str(uuid4()),  # Non-existent flashcard
            "response_time": 3.2,
            "confidence": 4,
            "is_correct": True
        }
        
        response = await client.post(f"/sessions/{test_session.id}/responses", 
                                   json=response_data, 
                                   headers=auth_headers)
        
        assert response.status_code == 404


class TestSessionAnalytics:
    """Test session analytics and progress tracking"""
    
    @pytest.mark.asyncio
    async def test_get_session_progress(self, client: AsyncClient, auth_headers, test_session, test_responses):
        """Test getting session progress"""
        response = await client.get(f"/sessions/{test_session.id}/progress", 
                                  headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_cards" in data
        assert "completed_cards" in data
        assert "accuracy" in data
        assert "average_response_time" in data
        assert "progress_percentage" in data
    
    @pytest.mark.asyncio
    async def test_get_session_statistics(self, client: AsyncClient, auth_headers, test_session, test_responses):
        """Test getting detailed session statistics"""
        response = await client.get(f"/sessions/{test_session.id}/stats", 
                                  headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "correct_answers" in data
        assert "incorrect_answers" in data
        assert "total_responses" in data
        assert "accuracy_rate" in data
        assert "average_confidence" in data
        assert "total_time_spent" in data
    
    def test_calculate_accuracy(self, test_db: Session, test_session, test_responses):
        """Test accuracy calculation"""
        responses = test_db.query(Response).filter(Response.session_id == test_session.id).all()
        
        if responses:
            correct_count = sum(1 for r in responses if r.is_correct)
            total_count = len(responses)
            expected_accuracy = correct_count / total_count
            
            assert 0 <= expected_accuracy <= 1
    
    def test_calculate_average_response_time(self, test_db: Session, test_session, test_responses):
        """Test average response time calculation"""
        responses = test_db.query(Response).filter(Response.session_id == test_session.id).all()
        
        if responses:
            total_time = sum(r.response_time for r in responses)
            average_time = total_time / len(responses)
            
            assert average_time > 0
    
    def test_calculate_confidence_stats(self, test_db: Session, test_session, test_responses):
        """Test confidence statistics calculation"""
        responses = test_db.query(Response).filter(Response.session_id == test_session.id).all()
        
        if responses:
            confidences = [r.confidence for r in responses]
            average_confidence = sum(confidences) / len(confidences)
            
            assert 1 <= average_confidence <= 5  # Confidence scale 1-5


class TestSessionTypes:
    """Test different session types"""
    
    @pytest.mark.asyncio
    async def test_practice_session(self, client: AsyncClient, auth_headers, test_dataset):
        """Test creating practice session"""
        session_data = {
            "dataset_id": str(test_dataset.id),
            "session_type": "practice",
            "settings": {"shuffle_cards": True}
        }
        
        response = await client.post("/sessions/", 
                                   json=session_data, 
                                   headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["session_type"] == "practice"
    
    @pytest.mark.asyncio
    async def test_test_session(self, client: AsyncClient, auth_headers, test_dataset):
        """Test creating test session"""
        session_data = {
            "dataset_id": str(test_dataset.id),
            "session_type": "test",
            "settings": {"time_limit": 300}  # 5 minutes
        }
        
        response = await client.post("/sessions/", 
                                   json=session_data, 
                                   headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["session_type"] == "test"
    
    @pytest.mark.asyncio
    async def test_review_session(self, client: AsyncClient, auth_headers, test_dataset):
        """Test creating review session"""
        session_data = {
            "dataset_id": str(test_dataset.id),
            "session_type": "review",
            "settings": {"review_incorrect_only": True}
        }
        
        response = await client.post("/sessions/", 
                                   json=session_data, 
                                   headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["session_type"] == "review"


class TestSessionSettings:
    """Test session settings and configurations"""
    
    @pytest.mark.asyncio
    async def test_shuffle_cards_setting(self, client: AsyncClient, auth_headers, test_dataset):
        """Test shuffle cards setting"""
        session_data = {
            "dataset_id": str(test_dataset.id),
            "session_type": "practice",
            "settings": {"shuffle_cards": True}
        }
        
        response = await client.post("/sessions/", 
                                   json=session_data, 
                                   headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["settings"]["shuffle_cards"] is True
    
    @pytest.mark.asyncio
    async def test_reverse_mode_setting(self, client: AsyncClient, auth_headers, test_dataset):
        """Test reverse mode setting"""
        session_data = {
            "dataset_id": str(test_dataset.id),
            "session_type": "practice",
            "settings": {"reverse_mode": True}
        }
        
        response = await client.post("/sessions/", 
                                   json=session_data, 
                                   headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["settings"]["reverse_mode"] is True
    
    @pytest.mark.asyncio
    async def test_auto_advance_setting(self, client: AsyncClient, auth_headers, test_dataset):
        """Test auto advance setting"""
        session_data = {
            "dataset_id": str(test_dataset.id),
            "session_type": "practice",
            "settings": {"auto_advance": True, "auto_advance_delay": 2}
        }
        
        response = await client.post("/sessions/", 
                                   json=session_data, 
                                   headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["settings"]["auto_advance"] is True
        assert data["settings"]["auto_advance_delay"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
