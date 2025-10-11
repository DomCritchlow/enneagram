"""
Business logic for quiz operations.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.config import settings
from core.security import generate_delete_token, sanitize_input
from models.database import db_manager, get_db_connection, Result
from models.schemas import (
    Question, TypeBlurb, EnneagramResult, EnneagramScores, 
    ValidityStats, QuizAnswers
)


class QuizService:
    """Service for quiz-related operations."""
    
    @staticmethod
    def load_questions() -> List[Question]:
        """Load quiz questions directly from file."""
        try:
            questions_data = json.loads(settings.questions_path.read_text())
            return [Question(**q) for q in questions_data]
        except Exception as e:
            raise ValueError(f"Failed to load questions: {e}")
    
    @staticmethod
    def load_type_blurbs() -> Dict[int, TypeBlurb]:
        """Load type descriptions directly from file."""
        try:
            blurbs_data = json.loads(settings.blurbs_path.read_text())
            return {int(k): TypeBlurb(**v) for k, v in blurbs_data.items()}
        except Exception as e:
            raise ValueError(f"Failed to load type blurbs: {e}")
    
    @staticmethod
    def reverse_score(value: int) -> int:
        """Apply reverse scoring for negatively worded questions."""
        if value < 1 or value > 5:
            return 0
        return 6 - value
    
    @staticmethod
    def calculate_validity_stats(all_values: List[int]) -> ValidityStats:
        """Calculate response validity statistics."""
        if not all_values:
            return ValidityStats(mean=0.0, sd=0.0)
        
        n = len(all_values)
        mean = sum(all_values) / n
        variance = sum((x - mean) ** 2 for x in all_values) / n
        sd = variance ** 0.5
        
        return ValidityStats(mean=mean, sd=sd)
    
    def calculate_type_scores(self, quiz_answers: Dict[str, int]) -> Dict[int, int]:
        """Calculate scores for each Enneagram type."""
        questions = self.load_questions()
        by_type = {t: 0 for t in range(1, 10)}
        
        for question in questions:
            key = f"q_{question.id}"
            raw_value = quiz_answers.get(key, 0)
            
            # Apply reverse scoring if needed
            score_value = self.reverse_score(raw_value) if question.reverse else raw_value
            by_type[question.type] += score_value
        
        return by_type
    
    def determine_top_type(self, type_scores: Dict[int, int]) -> Tuple[int, List[int]]:
        """
        Determine the top Enneagram type, handling ties with center analysis.
        
        Returns:
            Tuple of (top_type, tied_types)
        """
        max_score = max(type_scores.values())
        tied_types = [t for t, s in type_scores.items() if s == max_score]
        
        if len(tied_types) == 1:
            return tied_types[0], tied_types
        
        # Handle ties using Enneagram center analysis
        centers = {
            'gut': type_scores[8] + type_scores[9] + type_scores[1],
            'heart': type_scores[2] + type_scores[3] + type_scores[4],
            'head': type_scores[5] + type_scores[6] + type_scores[7],
        }
        
        center_map = {
            1: 'gut', 2: 'heart', 3: 'heart', 4: 'heart',
            5: 'head', 6: 'head', 7: 'head', 8: 'gut', 9: 'gut'
        }
        
        best_type = None
        best_center_score = -1
        
        for t in sorted(tied_types):
            center = center_map[t]
            if centers[center] > best_center_score:
                best_center_score = centers[center]
                best_type = t
        
        return best_type, tied_types
    
    def calculate_wings(self, top_type: int, type_scores: Dict[int, int]) -> Dict[str, int]:
        """Calculate highest wing for the top type."""
        # Wing mapping: each type has two adjacent wings
        wing_map = {
            1: [9, 2], 2: [1, 3], 3: [2, 4], 4: [3, 5],
            5: [4, 6], 6: [5, 7], 7: [6, 8], 8: [7, 9], 9: [8, 1]
        }
        
        wings = wing_map.get(top_type, [])
        if not wings:
            return {'wing': None, 'wing_score': 0}
        
        # Get scores for both wings
        left_score = type_scores.get(wings[0], 0)
        right_score = type_scores.get(wings[1], 0)
        
        # Return the highest scoring wing
        if left_score >= right_score:
            return {'wing': wings[0], 'wing_score': left_score}
        else:
            return {'wing': wings[1], 'wing_score': right_score}
    
    def process_quiz_submission(self, name: str, quiz_answers: Dict[str, int]) -> EnneagramResult:
        """
        Process a complete quiz submission and return results.
        
        Args:
            name: User's name (sanitized)
            quiz_answers: Dictionary of question responses
            
        Returns:
            EnneagramResult object
            
        Raises:
            ValueError: If name already exists or invalid data
        """
        # Sanitize name
        clean_name = sanitize_input(name, settings.name_max_length)
        
        # Validate answers
        questions = self.load_questions()
        all_values = []
        
        for question in questions:
            key = f"q_{question.id}"
            value = quiz_answers.get(key)
            if value is None:
                raise ValueError(f"Missing answer for question {question.id}")
            all_values.append(value)
        
        # Calculate scores and determine top type
        type_scores = self.calculate_type_scores(quiz_answers)
        top_type, tied_types = self.determine_top_type(type_scores)
        
        # Calculate validity statistics
        validity = self.calculate_validity_stats(all_values)
        
        # Generate delete token
        delete_token = generate_delete_token()
        
        # Create result object
        result = EnneagramResult(
            name=clean_name,
            top_type=top_type,
            scores=EnneagramScores.from_dict(type_scores),
            validity=validity,
            delete_token=delete_token,
            tied_types=tied_types if len(tied_types) > 1 else None
        )
        
        return result
    
    def save_quiz_result(self, result: EnneagramResult) -> None:
        """
        Save quiz result to database.
        
        Args:
            result: EnneagramResult to save
            
        Raises:
            ValueError: If name already exists
        """
        # Use legacy database connection for now
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            # Insert new result (database UNIQUE constraint will handle duplicates)
            cur.execute(
                """INSERT INTO results 
                   (ts, name, top_type, scores_json, raw_json, validity_json, delete_token) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.utcnow().isoformat(),
                    result.name,
                    result.top_type,
                    json.dumps(result.scores.to_dict()),
                    json.dumps({}),  # Raw answers - could be added if needed
                    json.dumps({"mean": result.validity.mean, "sd": result.validity.sd}),
                    result.delete_token,
                )
            )
            conn.commit()
            
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Database constraint violation: {e}")
        finally:
            conn.close()
    
    def get_admin_stats(self) -> Dict[int, int]:
        """Get type distribution statistics for admin dashboard."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT top_type, COUNT(*) FROM results GROUP BY top_type ORDER BY top_type")
            rows = cur.fetchall()
            return {int(t): int(c) for t, c in rows}
        finally:
            conn.close()
    
    def delete_entry_by_token(self, delete_token: str) -> Optional[str]:
        """
        Delete an entry by its delete token.
        
        Args:
            delete_token: The delete token
            
        Returns:
            Name of deleted entry, or None if not found
        """
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            # Find entry
            cur.execute("SELECT id, name FROM results WHERE delete_token = ?", (delete_token,))
            row = cur.fetchone()
            
            if not row:
                return None
            
            entry_id, name = row
            
            # Delete entry
            cur.execute("DELETE FROM results WHERE id = ?", (entry_id,))
            conn.commit()
            
            return name
            
        finally:
            conn.close()
    
    def export_results_csv(self) -> List[List[str]]:
        """Export all results as CSV data."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, ts, name, top_type, scores_json FROM results ORDER BY id")
            rows = cur.fetchall()
            
            # Prepare CSV data
            csv_data = []
            header = ["id", "timestamp_utc", "name", "top_type"] + [f"type{i}" for i in range(1, 10)]
            csv_data.append(header)
            
            for row in rows:
                rid, ts, name, top_type, scores_json = row
                scores = json.loads(scores_json)
                type_scores = [str(scores.get(str(i), 0)) for i in range(1, 10)]
                csv_row = [str(rid), ts, name or "", str(top_type)] + type_scores
                csv_data.append(csv_row)
            
            return csv_data
            
        finally:
            conn.close()

    def get_result_by_token(self, delete_token: str) -> Optional[Dict]:
        """Get quiz result by delete token."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT name, top_type, scores_json, validity_json FROM results WHERE delete_token = ?",
                (delete_token,)
            )
            row = cur.fetchone()
            
            if not row:
                return None
                
            name, top_type, scores_json, validity_json = row
            scores = json.loads(scores_json)
            validity = json.loads(validity_json) if validity_json else {"mean": 3.0, "sd": 1.0}
            
            # Convert string keys to integers for scores
            int_scores = {int(k): v for k, v in scores.items()}
            
            # Calculate wings
            wings = self.calculate_wings(top_type, int_scores)
            
            return {
                "name": name,
                "top_type": top_type,
                "scores": int_scores,
                "validity": validity,
                "wings": wings
            }
            
        except Exception as e:
            app_logger.error("Error fetching result by token", exception=e)
            return None
        finally:
            conn.close()


# Global service instance
quiz_service = QuizService()
