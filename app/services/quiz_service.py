"""
Business logic for quiz operations.
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

from core.config import settings
from core.security import sanitize_input
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
    def load_type_blurbs() -> Dict[str, dict]:
        """Load type descriptions directly from file."""
        try:
            blurbs_data = json.loads(settings.blurbs_path.read_text())
            return blurbs_data  # Return raw dictionary data to support enhanced fields
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
    
    def process_quiz_submission(self, name: str, quiz_answers: Dict[str, int], team: Optional[str] = None) -> EnneagramResult:
        """
        Process a complete quiz submission and return results.
        
        Args:
            name: User's name (sanitized)
            quiz_answers: Dictionary of question responses
            team: Optional team name (sanitized)
            
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
        
        # Create result object
        result = EnneagramResult(
            name=clean_name,
            team=team,
            top_type=top_type,
            scores=EnneagramScores.from_dict(type_scores),
            validity=validity,
            tied_types=tied_types if len(tied_types) > 1 else None
        )
        
        return result
    


# Global service instance
quiz_service = QuizService()
