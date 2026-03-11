"""
Ranking Service

Handles calculation and retrieval of user rankings for gamification system.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, text, Integer
from datetime import datetime, timedelta
import logging

from .models import UserGameStats, DailyStats
from ..gamification.models import UserAchievement
from ..sessions.models import UserFieldAttempt
from ..auth.models import User
from ..admin.models import SystemConfig

logger = logging.getLogger(__name__)


class RankingService:
    """Service for calculating and retrieving user rankings"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_user_statistics(self, user_id: str) -> UserGameStats:
        """Calculate and update user statistics using SQL aggregates (O(log n))"""
        try:
            # Use SQL aggregates — no Python-side iteration over all attempts
            total_cards = self.db.query(func.count(UserFieldAttempt.id)).filter(
                UserFieldAttempt.user_id == user_id
            ).scalar() or 0

            correct_answers = self.db.query(func.count(UserFieldAttempt.id)).filter(
                UserFieldAttempt.user_id == user_id,
                UserFieldAttempt.is_correct == True
            ).scalar() or 0

            # Coalesce NULL response times to 3 000 ms (same default as before)
            total_response_time = self.db.query(
                func.sum(func.coalesce(UserFieldAttempt.response_time_ms, 3000))
            ).filter(
                UserFieldAttempt.user_id == user_id
            ).scalar() or 0

            if total_cards == 0:
                # Create default stats for new user
                stats = UserGameStats(
                    user_id=user_id,
                    total_cards_answered=0,
                    correct_answers=0,
                    total_response_time_ms=0
                )
                self.db.add(stats)
                self.db.commit()
                return stats

            accuracy = (correct_answers / total_cards * 100)
            avg_response_time = total_response_time // total_cards
            
            # Calculate speed score (volume-weighted)
            speed_score = self._calculate_speed_score(total_cards, avg_response_time)
            
            # Calculate overall score
            achievements_count = self.db.query(func.count(UserAchievement.id)).filter(
                UserAchievement.user_id == user_id
            ).scalar() or 0
            
            overall_score = self._calculate_overall_score(
                total_cards, accuracy, speed_score, achievements_count
            )
            
            # Get or create user stats
            stats = self.db.query(UserGameStats).filter(
                UserGameStats.user_id == user_id
            ).first()
            
            if not stats:
                stats = UserGameStats(user_id=user_id)
                self.db.add(stats)
            
            # Update stats
            stats.total_cards_answered = total_cards
            stats.correct_answers = correct_answers
            stats.total_response_time_ms = total_response_time
            stats.accuracy_percentage = accuracy
            stats.average_response_time_ms = avg_response_time
            stats.speed_score = speed_score
            stats.overall_score = overall_score
            stats.achievements_count = achievements_count
            stats.last_activity_date = datetime.utcnow()
            
            self.db.commit()
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating user statistics for {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def _calculate_speed_score(self, total_cards: int, avg_response_time_ms: int) -> float:
        """Calculate volume-weighted speed score"""
        if total_cards == 0 or avg_response_time_ms == 0:
            return 0.0
        
        # Volume multiplier increases with more cards (max 5x)
        volume_multiplier = min(total_cards / 100, 5.0)
        
        # Base score: cards per second
        base_score = total_cards / (avg_response_time_ms / 1000)
        
        return base_score * volume_multiplier
    
    def _calculate_overall_score(self, cards_answered: int, accuracy: float, 
                               speed_score: float, achievements_count: int) -> float:
        """Calculate combined overall ranking score"""
        score = (
            cards_answered * 0.4 +                    # 40% cards answered
            (accuracy / 100) * 1000 * 0.3 +          # 30% accuracy
            speed_score * 0.2 +                       # 20% speed
            achievements_count * 50 * 0.1            # 10% achievements
        )
        return round(score, 2)
    
    def get_cards_answered_ranking(self, limit: int = 10) -> List[Dict]:
        """Get leaderboard by total cards answered (with minimum threshold from config)"""
        try:
            # Get minimum cards threshold from SystemConfig
            min_threshold = SystemConfig.get_value(self.db, "cards_answered_min_threshold", 20)
            
            # Query with join to User table for name information
            ranking = self.db.query(
                UserGameStats,
                User.email,
                User.name
            ).join(User, UserGameStats.user_id == User.id).filter(
                UserGameStats.total_cards_answered >= min_threshold
            ).order_by(
                desc(UserGameStats.total_cards_answered),
                desc(UserGameStats.overall_score)  # Tiebreaker
            ).limit(limit).all()
            
            result = []
            for i, (stats, email, name) in enumerate(ranking, 1):
                result.append({
                    "rank": i,
                    "user_id": str(stats.user_id),
                    "user_name": name or email.split('@')[0],
                    "email": email,
                    "total_cards_answered": stats.total_cards_answered,
                    "accuracy_percentage": stats.accuracy_percentage,
                    "average_response_time_ms": stats.average_response_time_ms,
                    "overall_score": stats.overall_score
                })
            return result
        except Exception as e:
            logger.error(f"Error fetching cards answered ranking: {str(e)}")
            return []
    
    def get_accuracy_ranking(self, limit: int = 10, min_cards: int = None) -> List[Dict]:
        """Get top users by accuracy (minimum cards threshold from config)"""
        # Get minimum cards threshold from SystemConfig, fallback to parameter or default
        if min_cards is None:
            min_cards = SystemConfig.get_value(self.db, "accuracy_min_cards", 5)
        
        results = self.db.query(
            UserGameStats,
            User.email,
            User.name
        ).join(
            User, UserGameStats.user_id == User.id
        ).filter(
            UserGameStats.total_cards_answered >= min_cards
        ).order_by(
            desc(UserGameStats.accuracy_percentage)
        ).limit(limit).all()
        
        return [
            {
                "rank": idx + 1,
                "user_id": str(stats.user_id),
                "user_name": name or email.split('@')[0],
                "email": email,
                "accuracy_percentage": round(stats.accuracy_percentage, 1),
                "total_cards_answered": stats.total_cards_answered,
                "average_response_time_ms": stats.average_response_time_ms,
                "last_activity": stats.last_activity_date
            }
            for idx, (stats, email, name) in enumerate(results)
        ]
    
    def get_speed_ranking(self, limit: int = 10, min_cards: int = None) -> List[Dict]:
        """Get top users by speed score (volume-weighted, minimum cards from config)"""
        # Get minimum cards threshold from SystemConfig, fallback to parameter or default
        if min_cards is None:
            min_cards = SystemConfig.get_value(self.db, "speed_min_cards", 10)
        
        results = self.db.query(
            UserGameStats,
            User.email,
            User.name
        ).join(
            User, UserGameStats.user_id == User.id
        ).filter(
            UserGameStats.total_cards_answered >= min_cards,
            UserGameStats.speed_score > 0
        ).order_by(
            desc(UserGameStats.speed_score)
        ).limit(limit).all()
        
        return [
            {
                "rank": idx + 1,
                "user_id": str(stats.user_id),
                "user_name": name or email.split('@')[0],
                "email": email,
                "speed_score": round(stats.speed_score, 2),
                "average_response_time_ms": stats.average_response_time_ms,
                "total_cards_answered": stats.total_cards_answered,
                "last_activity": stats.last_activity_date
            }
            for idx, (stats, email, name) in enumerate(results)
        ]
    
    def get_overall_ranking(self, limit: int = 10) -> List[Dict]:
        """Get top users by overall combined score"""
        results = self.db.query(
            UserGameStats,
            User.email,
            User.name
        ).join(
            User, UserGameStats.user_id == User.id
        ).filter(
            UserGameStats.overall_score > 0
        ).order_by(
            desc(UserGameStats.overall_score)
        ).limit(limit).all()
        
        return [
            {
                "rank": idx + 1,
                "user_id": str(stats.user_id),
                "user_name": name or email.split('@')[0],
                "email": email,
                "overall_score": stats.overall_score,
                "total_cards_answered": stats.total_cards_answered,
                "accuracy_percentage": round(stats.accuracy_percentage, 1),
                "speed_score": round(stats.speed_score, 2),
                "achievements_count": stats.achievements_count,
                "last_activity": stats.last_activity_date
            }
            for idx, (stats, email, name) in enumerate(results)
        ]
    
    def get_user_rank_in_category(self, user_id: str, category: str) -> Dict:
        """Get user's rank in a specific category using SQL COUNT for O(log n) performance"""
        try:
            category_map = {
                "cards_answered": UserGameStats.total_cards_answered,
                "accuracy": UserGameStats.accuracy_percentage,
                "speed": UserGameStats.speed_score,
                "overall": UserGameStats.overall_score,
            }
            if category not in category_map:
                return {"rank": 0, "total_users": 0}

            sort_col = category_map[category]

            # Get the current user's value
            user_stats = self.db.query(UserGameStats).filter(
                UserGameStats.user_id == user_id
            ).first()

            if not user_stats:
                return {"rank": 0, "total_users": 0}

            user_value = getattr(user_stats, sort_col.key)

            # COUNT users with a strictly higher score (= users ranked above)
            users_above = self.db.query(func.count(UserGameStats.id)).filter(
                sort_col > user_value
            ).scalar() or 0

            total_users = self.db.query(func.count(UserGameStats.id)).scalar() or 0

            return {
                "rank": users_above + 1,
                "total_users": total_users,
            }
        except Exception as e:
            logger.error(f"Error getting user rank for {user_id} in {category}: {str(e)}")
            return {"rank": 0, "total_users": 0}
    
    def update_all_user_statistics(self):
        """Batch update statistics for all users (for background jobs)"""
        try:
            # Get all users who have attempted cards
            user_ids = self.db.query(UserFieldAttempt.user_id.distinct()).all()
            
            updated_count = 0
            for (user_id,) in user_ids:
                self.calculate_user_statistics(str(user_id))
                updated_count += 1
            
            logger.info(f"Updated statistics for {updated_count} users")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating all user statistics: {str(e)}")
            raise
