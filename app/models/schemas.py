"""
Pydantic schemas for request/response validation.
"""
import re
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator

from core.config import settings


class QuizSubmission(BaseModel):
    """Schema for quiz submission validation."""
    name: str = Field(..., min_length=1, max_length=settings.name_max_length)
    consent: str = Field(..., pattern=r'^yes$')
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate and clean name input."""
        v = v.strip()
        # Allow alphanumeric, spaces, hyphens, underscores only
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', v):
            raise ValueError('Name can only contain letters, numbers, spaces, hyphens, and underscores')
        return v


class QuizResponse(BaseModel):
    """Schema for individual quiz question response."""
    question_id: int = Field(..., ge=1)
    value: int = Field(..., ge=1, le=5)


class QuizAnswers(BaseModel):
    """Schema for complete quiz answers validation."""
    answers: Dict[str, int] = Field(...)
    
    @model_validator(mode='before')
    @classmethod
    def validate_answers(cls, values):
        """Validate quiz answers format and values."""
        if isinstance(values, dict):
            answers = values.get('answers', {})
            
            for key, value in answers.items():
                # Validate key format
                if not key.startswith('q_') or not key[2:].isdigit():
                    raise ValueError(f'Invalid answer key format: {key}')
                
                # Validate value range
                if not isinstance(value, int) or value < 1 or value > 5:
                    raise ValueError(f'Answer value must be 1-5, got {value} for {key}')
        
        return values


class EnneagramScores(BaseModel):
    """Schema for Enneagram type scores."""
    type_1: int = Field(..., ge=0)
    type_2: int = Field(..., ge=0)
    type_3: int = Field(..., ge=0)
    type_4: int = Field(..., ge=0)
    type_5: int = Field(..., ge=0)
    type_6: int = Field(..., ge=0)
    type_7: int = Field(..., ge=0)
    type_8: int = Field(..., ge=0)
    type_9: int = Field(..., ge=0)
    
    @classmethod
    def from_dict(cls, scores_dict: Dict[int, int]) -> 'EnneagramScores':
        """Create from dictionary with integer keys."""
        return cls(
            type_1=scores_dict.get(1, 0),
            type_2=scores_dict.get(2, 0),
            type_3=scores_dict.get(3, 0),
            type_4=scores_dict.get(4, 0),
            type_5=scores_dict.get(5, 0),
            type_6=scores_dict.get(6, 0),
            type_7=scores_dict.get(7, 0),
            type_8=scores_dict.get(8, 0),
            type_9=scores_dict.get(9, 0),
        )
    
    def to_dict(self) -> Dict[int, int]:
        """Convert to dictionary with integer keys."""
        return {
            1: self.type_1,
            2: self.type_2,
            3: self.type_3,
            4: self.type_4,
            5: self.type_5,
            6: self.type_6,
            7: self.type_7,
            8: self.type_8,
            9: self.type_9,
        }


class ValidityStats(BaseModel):
    """Schema for response validity statistics."""
    mean: float = Field(..., ge=0, le=5)
    sd: float = Field(..., ge=0)
    
    @property
    def has_extreme_mean(self) -> bool:
        """Check if mean is extreme (>4.6 or <1.4)."""
        return self.mean > 4.6 or self.mean < 1.4
    
    @property
    def has_low_variance(self) -> bool:
        """Check if standard deviation suggests low variance."""
        return self.sd < 0.5


class EnneagramResult(BaseModel):
    """Schema for complete Enneagram result."""
    name: str
    top_type: int = Field(..., ge=1, le=9)
    scores: EnneagramScores
    validity: ValidityStats
    delete_token: str
    tied_types: Optional[List[int]] = None
    
    class Config:
        json_encoders = {
            EnneagramScores: lambda v: v.to_dict(),
        }


class Question(BaseModel):
    """Schema for quiz question."""
    id: int = Field(..., ge=1)
    text: str = Field(..., min_length=1)
    type: int = Field(..., ge=1, le=9)
    reverse: bool = False


class TypeBlurb(BaseModel):
    """Schema for Enneagram type description."""
    name: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    svg_icon: str = Field(..., min_length=1)


class AdminCredentials(BaseModel):
    """Schema for admin authentication."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=settings.password_min_length)
